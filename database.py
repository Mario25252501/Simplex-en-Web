from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os  # Permite leer variables del sistema
from dotenv import load_dotenv  # Lee el archivo .env
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

URL = os.getenv("DATABASE_URL")

engine = create_engine(URL)
SessionLocal = sessionmaker(bind=engine)

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

# Crea la aplicación; uvicorn la busca con este nombre
app = FastAPI()

# Ruta de prueba: sirve para comprobar que la conexión a MySQL funciona
@app.get("/prueba-bd")
def prueba_bd():
    db = SessionLocal()  # Abre la conexión a la base de datos
    filas = db.execute(text("SELECT id, nombre, tipo FROM problemas")).fetchall()  # Lee los problemas
    db.close()  # Cierra la conexión
    return [{"id": f[0], "nombre": f[1], "tipo": f[2]} for f in filas]  # Devuelve los datos como JSON


# Estructura de una restricción: valida que los datos lleguen completos y correctos
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


# Recibe un problema desde el formulario y lo guarda en MySQL
@app.post("/problemas")
def guardar_problema(p: ProblemaIn):
    n = len(p.objetivo)  # Cuenta cuántas variables tiene el modelo
    if not 2 <= n <= 6:  # Valida el rango permitido por el proyecto
        raise HTTPException(400, "El modelo debe tener entre 2 y 6 variables")  # Devuelve error al usuario
    db = SessionLocal()  # Abre la conexión a la base de datos
    try:
        # Guarda los datos generales del problema
        r = db.execute(text(
            "INSERT INTO problemas (nombre, tipo, num_variables, num_restricciones) "
            "VALUES (:n, :t, :v, :r)"),
            {"n": p.nombre, "t": p.tipo, "v": n, "r": len(p.restricciones)})
        pid = r.lastrowid  # Obtiene el id que MySQL le asignó al problema
        for var, coef in p.objetivo.items():  # Recorre cada coeficiente de Z
            # Guarda un coeficiente de la función objetivo
            db.execute(text(
                "INSERT INTO coeficientes_objetivo (problema_id, variable, coeficiente) "
                "VALUES (:p, :v, :c)"), {"p": pid, "v": var, "c": coef})
        for i, res in enumerate(p.restricciones, start=1):  # Recorre cada restricción numerándola
            # Guarda el signo y el término independiente de la restricción
            r2 = db.execute(text(
                "INSERT INTO restricciones (problema_id, numero, signo, termino_independiente) "
                "VALUES (:p, :n, :s, :t)"),
                {"p": pid, "n": i, "s": res.signo, "t": res.termino_independiente})
            rid = r2.lastrowid  # Obtiene el id de la restricción recién guardada
            for var in p.objetivo:  # Recorre todas las variables del modelo
                # Guarda el coeficiente de cada variable (0 si no se indicó)
                db.execute(text(
                    "INSERT INTO coeficientes_restriccion (restriccion_id, variable, coeficiente) "
                    "VALUES (:r, :v, :c)"),
                    {"r": rid, "v": var, "c": res.coeficientes.get(var, 0)})
        db.commit()  # Confirma y guarda todos los cambios juntos
        return {"id": pid, "mensaje": "Problema guardado"}  # Responde con el id del nuevo problema
    except Exception:
        db.rollback()  # Si algo falla, deshace todo para no dejar datos incompletos
        raise  # Muestra el error
    finally:
        db.close()  # Siempre cierra la conexión al terminar


# Devuelve la lista de problemas guardados (para el historial)
@app.get("/problemas")
def listar_problemas():
    db = SessionLocal()  # Abre la conexión a la base de datos
    filas = db.execute(text(
        "SELECT id, nombre, tipo, num_variables, creado_en FROM problemas ORDER BY id DESC"
        )).fetchall()  # Lee los problemas, del más reciente al más antiguo
    db.close()  # Cierra la conexión
    return [{"id": f[0], "nombre": f[1], "tipo": f[2],
             "num_variables": f[3], "creado_en": str(f[4])} for f in filas]  # Convierte el resultado a JSON