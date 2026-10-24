"""Adaptación al contrato real de la rama api-preparacion del compañero.

Aceptamos el tableau plano acordado y una tabla anidada en ``tabla``.
No intentamos adivinar costos, bases ni variables artificiales.
"""


def adaptar_entrada(datos):
    if not isinstance(datos, dict):
        return datos
    copia = dict(datos)
    if "tabla" in copia:
        tabla = copia.pop("tabla")
        if not isinstance(tabla, dict) or set(tabla) != {"columnas", "filas"}:
            raise ValueError("tabla debe contener exactamente columnas y filas.")
        for campo in ("columnas", "filas"):
            if campo in copia and copia[campo] != tabla[campo]:
                raise ValueError(f"El campo {campo} tiene dos valores distintos.")
            copia[campo] = tabla[campo]
    # Alias documentado para compañeros que conservan el nombre del modelo.
    if "objetivo" in copia:
        objetivo = copia.pop("objetivo")
        if "objetivo_original" in copia and copia["objetivo_original"] != objetivo:
            raise ValueError("objetivo y objetivo_original son distintos.")
        copia["objetivo_original"] = objetivo
    # API 2 devuelve una lista ordenada por las columnas a-f del tableau.
    objetivo = copia.get("objetivo_original")
    columnas = copia.get("columnas")
    if isinstance(objetivo, list) and isinstance(columnas, list):
        nombres = [v for v in columnas if isinstance(v, str) and v in tuple("abcdef")]
        if len(objetivo) != len(nombres):
            raise ValueError("La lista objetivo_original no coincide con las variables a-f.")
        copia["objetivo_original"] = dict(zip(nombres, objetivo))
    # La interfaz del Integrante 4 exige Z en la fila 0, incluso en Fase I.
    filas = copia.get("filas")
    if copia.get("fase") == 1 and isinstance(filas, list) and filas:
        if isinstance(filas[0], list) and filas[0][0:1] == ["P"]:
            copia["filas"] = [f.copy() if isinstance(f, list) else f for f in filas]
            copia["filas"][0][0] = "Z"
    return copia
