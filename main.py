# Importa FastAPI, la herramienta para crear la API
from fastapi import FastAPI, HTTPException
# Permite escribir consultas SQL directamente
from sqlalchemy import text
# Importa la conexión a MySQL creada en database.py
from database import SessionLocal
# Permite limitar un campo a valores exactos (ej. solo MAX o MIN)
from typing import Literal
# Permite definir la estructura y validar los datos que llegan
from pydantic import BaseModel
import json
from fastapi.staticfiles import StaticFiles  # Permite servir archivos HTML, CSS y JS

import httpx  # Permite llamar a las otras APIs
# Direcciones de las APIs de tus compañeros (cada una en su propio puerto)
URL_PREPARACION = "http://localhost:8001"
URL_MOTOR = "http://localhost:8002"

def llamar_api(url, datos):
    try:
        r = httpx.post(url, json=datos, timeout=30)  # Hace la petición POST
        r.raise_for_status()  # Lanza error si la respuesta no fue exitosa
        return r.json()  # Convierte la respuesta a diccionario
    except httpx.HTTPError:
        raise HTTPException(503, f"No se pudo conectar con el servicio: {url}")

# Crea la aplicación y ahi uvicorn la busca con este nombre
app = FastAPI()

# ruta de prueba para comprobar que la conexión a MySQL funciona
@app.get("/prueba-bd")
def prueba_bd():
    db = SessionLocal()  # Abre la conexión a la base de datos
    filas = db.execute(text("SELECT id, nombre, tipo FROM problemas")).fetchall()  # Lee los problemas
    db.close()  # Cierra la conexión
    return [{"id": f[0], "nombre": f[1], "tipo": f[2]} for f in filas]  # Devuelve los datos como JSON


# Estructura de una restriccion valida que los datos lleguen completos y correctos
class RestriccionIn(BaseModel):
    coeficientes: dict[str, float]  # Coeficientes por variable, ej. {"a": 3, "b": 2}
    signo: Literal["<=", ">=", "="]  # Solo acepta estos tres signos
    termino_independiente: float  # Número del lado derecho de la restricción

# Estructura del problema completo que envía el formulario
class ProblemaIn(BaseModel):
    nombre: str  # Nombre del problema
    tipo: Literal["MAX", "MIN"]  # Solo maximizar o minimizar
    objetivo: dict[str, float]  # Coeficientes de Z, ej. {"a": 3, "b": 5}
    restricciones: list[RestriccionIn]  # Lista de restricciones del modelo


# recibe un problema desde el formulario y lo guarda en MySQL
@app.post("/problemas")
def guardar_problema(p: ProblemaIn):
    n = len(p.objetivo)  # Cuenta cuántas variables tiene el modelo
    if not 2 <= n <= 6:  # Valida el rango permitido por el proyecto
        raise HTTPException(400, "El modelo debe tener entre 2 y 6 variables")  # Devuelve error al usuario
    db = SessionLocal()  # Abre la conexión a la base de datos
    try:
        # guarda los datos generales del problema
        r = db.execute(text(
            "INSERT INTO problemas (nombre, tipo, num_variables, num_restricciones) "
            "VALUES (:n, :t, :v, :r)"),
            {"n": p.nombre, "t": p.tipo, "v": n, "r": len(p.restricciones)})
        pid = r.lastrowid  # Obtiene el id que MySQL le asignó al problema
        for var, coef in p.objetivo.items():  # Recorre cada coeficiente de Z
            # guarda un coeficiente de la función objetivo
            db.execute(text(
                "INSERT INTO coeficientes_objetivo (problema_id, variable, coeficiente) "
                "VALUES (:p, :v, :c)"), {"p": pid, "v": var, "c": coef})
        for i, res in enumerate(p.restricciones, start=1):  # Recorre cada restricción numerándola
            # guarda el signo y el término independiente de la restricción
            r2 = db.execute(text(
                "INSERT INTO restricciones (problema_id, numero, signo, termino_independiente) "
                "VALUES (:p, :n, :s, :t)"),
                {"p": pid, "n": i, "s": res.signo, "t": res.termino_independiente})
            rid = r2.lastrowid  # Obtiene el id de la restricción recién guardada
            for var in p.objetivo:  # Recorre todas las variables del modelo
                # guarda el coeficiente de cada variable (0 si no se indicó)
                db.execute(text(
                    "INSERT INTO coeficientes_restriccion (restriccion_id, variable, coeficiente) "
                    "VALUES (:r, :v, :c)"),
                    {"r": rid, "v": var, "c": res.coeficientes.get(var, 0)})
        db.commit()  # confirma y guarda todos los cambios juntos
        return {"id": pid, "mensaje": "Problema guardado"}  # Responde con el id del nuevo problema
    except Exception:
        db.rollback()  # si algo falla, deshace todo para no dejar datos incompletos
        raise  # muestra el error
    finally:
        db.close()  # siempre cierra la conexión al terminar


# Devuelve la lista de problemas guardados (para el historial)
@app.get("/problemas")
def listar_problemas():
    db = SessionLocal()  # Abre la conexión a la base de datos
    filas = db.execute(text(
        "SELECT id, nombre, tipo, num_variables, creado_en FROM problemas ORDER BY id DESC"
    )).fetchall()  # Lee los problemas, del más reciente al más antiguo
    db.close()  # Cierra la conexión
    return [{"id": f[0], "nombre": f[1], "tipo": f[2],
             "num_variables": f[3], "creado_en": str(f[4])} for f in filas] 

# Segundo Enpoint

# Devuelve un problema completo (objetivo y restricciones) a partir de su id
@app.get("/problemas/{problema_id}")
def obtener_problema(problema_id: int):
    db = SessionLocal()  # Abre la conexión a la base de datos
    try:
        # Busca los datos generales del problema
        p = db.execute(text(
            "SELECT id, nombre, tipo FROM problemas WHERE id = :id"),
            {"id": problema_id}).fetchone()
        if p is None:  # Si no existe ese id, avisa con error 404
            raise HTTPException(404, "Problema no encontrado")
        # Lee los coeficientes de la función objetivo
        obj = db.execute(text(
            "SELECT variable, coeficiente FROM coeficientes_objetivo "
            "WHERE problema_id = :id ORDER BY variable"),
            {"id": problema_id}).fetchall()
        # Lee las restricciones del problema en orden
        res = db.execute(text(
            "SELECT id, signo, termino_independiente FROM restricciones "
            "WHERE problema_id = :id ORDER BY numero"),
            {"id": problema_id}).fetchall()
        restricciones = []  # Aquí se arma la lista de restricciones
        for r in res:  # Recorre cada restricción
            # Lee los coeficientes de esa restricción
            coefs = db.execute(text(
                "SELECT variable, coeficiente FROM coeficientes_restriccion "
                "WHERE restriccion_id = :id ORDER BY variable"),
                {"id": r[0]}).fetchall()
            restricciones.append({  # Arma la restricción con el mismo formato del JSON acordado
                "coeficientes": {c[0]: float(c[1]) for c in coefs},
                "signo": r[1],
                "termino_independiente": float(r[2])})
        return {  # Devuelve el problema completo en formato JSON
            "id": p[0], "nombre": p[1], "tipo": p[2],
            "objetivo": {o[0]: float(o[1]) for o in obj},
            "restricciones": restricciones}
    finally:
        db.close()  # Siempre cierra la conexión al terminar

        #Enpoint final 

        # Ejecuta el símplex de un problema y guarda las iteraciones y el resultado
@app.post("/problemas/{problema_id}/resolver")
def resolver_problema(problema_id: int):
    modelo = obtener_problema(problema_id)  # Reutiliza la consulta del problema completo
    tableau = llamar_api(URL_PREPARACION + "/preparar", modelo)  # API 2: arma el tableau inicial
    res = llamar_api(URL_MOTOR + "/resolver", tableau)  # API 3: ejecuta el símplex
    db = SessionLocal()  # Abre la conexión a la base de datos
    try:
        # Borra cálculos anteriores para poder resolver de nuevo
        db.execute(text("DELETE FROM iteraciones WHERE problema_id = :p"), {"p": problema_id})
        db.execute(text("DELETE FROM resultados WHERE problema_id = :p"), {"p": problema_id})
        for it in res["iteraciones"]:  # Guarda cada tabla del símplex
            db.execute(text(
                "INSERT INTO iteraciones (problema_id, numero_iteracion, fase, variable_entrante, "
                "variable_saliente, fila_pivote, columna_pivote, elemento_pivote, tabla_json, operaciones_json) "
                "VALUES (:p, :n, :f, :ve, :vs, :fp, :cp, :ep, :t, :o)"),
                {"p": problema_id, "n": it["numero"], "f": it["fase"],
                 "ve": it["variable_entrante"], "vs": it["variable_saliente"],
                 "fp": it["fila_pivote"], "cp": it["columna_pivote"], "ep": it["elemento_pivote"],
                 "t": json.dumps(it["tabla"]), "o": json.dumps(it["operaciones"])})
        # Guarda el resultado final
        db.execute(text(
            "INSERT INTO resultados (problema_id, estado, valor_z, solucion_json, total_iteraciones) "
            "VALUES (:p, :e, :z, :s, :t)"),
            {"p": problema_id, "e": res["estado"], "z": res["valor_z"],
             "s": json.dumps(res["solucion"]), "t": len(res["iteraciones"])})
        db.commit()  # Confirma todos los cambios
        return {"mensaje": "Problema resuelto", "estado": res["estado"]}
    except Exception:
        db.rollback()  # Si algo falla, deshace todo
        raise
    finally:
        db.close()  # Siempre cierra la conexión


# Devuelve el resultado y las tablas guardadas (lo que consume la pantalla de resultados)
@app.get("/problemas/{problema_id}/resultado")
def obtener_resultado(problema_id: int):
    db = SessionLocal()  # Abre la conexión a la base de datos
    try:
        r = db.execute(text(
            "SELECT estado, valor_z, solucion_json FROM resultados WHERE problema_id = :p"),
            {"p": problema_id}).fetchone()
        if r is None:  # Si aún no se resolvió, avisa con error 404
            raise HTTPException(404, "Este problema todavía no se ha resuelto")
        its = db.execute(text(
            "SELECT numero_iteracion, fase, variable_entrante, variable_saliente, fila_pivote, "
            "columna_pivote, elemento_pivote, tabla_json, operaciones_json "
            "FROM iteraciones WHERE problema_id = :p ORDER BY fase, numero_iteracion"),
            {"p": problema_id}).fetchall()
        cargar = lambda x: json.loads(x) if isinstance(x, str) else x  # Convierte texto JSON a objeto
        return {"estado": r[0], "valor_z": float(r[1]) if r[1] is not None else None, "solucion": cargar(r[2]),
                "iteraciones": [{"numero": i[0], "fase": i[1], "variable_entrante": i[2],
                                 "variable_saliente": i[3], "fila_pivote": i[4], "columna_pivote": i[5],
                                 "elemento_pivote": float(i[6]) if i[6] is not None else None,
                                 "tabla": cargar(i[7]), "operaciones": cargar(i[8])} for i in its]}
    finally:
        db.close()  # Siempre cierra la conexión

        # Sirve la carpeta frontend en la dirección /app
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
    