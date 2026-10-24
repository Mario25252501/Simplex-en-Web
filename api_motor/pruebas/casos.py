"""Datos de prueba. Este constructor NO es una implementación de la API 2.

Únicamente crea fixtures verificables de forma estándar para probar el motor.
El contrato real del compañero todavía no está incluido en el ZIP recibido.
"""

from fractions import Fraction


def preparar_caso(objetivo, restricciones, tipo="MAX"):
    variables = list(objetivo)
    filas_originales = []
    auxiliares = []
    artificiales = []
    bases = []
    for i, (coeficientes, signo, rhs) in enumerate(restricciones, start=1):
        coeficientes = list(coeficientes)
        if rhs < 0:
            coeficientes = [-x for x in coeficientes]
            rhs = -rhs
            signo = {"<=": ">=", ">=": "<=", "=": "="}[signo]
        extras = {}
        if signo == "<=":
            base = f"h{i}"
            extras[base] = 1
        elif signo == ">=":
            extras[f"ex{i}"] = -1
            base = f"A{i}"
            extras[base] = 1
            artificiales.append(base)
        elif signo == "=":
            base = f"A{i}"
            extras[base] = 1
            artificiales.append(base)
        else:
            raise ValueError(signo)
        auxiliares.extend(extras)
        bases.append(base)
        filas_originales.append((coeficientes, extras, rhs))
    columnas = ["Base"] + variables + auxiliares + ["Solución"]
    filas = [["Z"] + [0] * (len(columnas) - 1)]
    for base, (coeficientes, extras, rhs) in zip(bases, filas_originales):
        filas.append([base] + coeficientes + [extras.get(v, 0) for v in auxiliares] + [rhs])
    return {
        "tipo": tipo, "fase": 1 if artificiales else 2,
        "objetivo_original": dict(objetivo),
        "variables_decision": variables,
        "variables_artificiales": artificiales,
        "requiere_fase1": bool(artificiales),
        "columnas": columnas, "filas": filas,
    }


def caso_max():
    return preparar_caso({"a": 3, "b": 5}, [
        ([1, 0], "<=", 4), ([0, 1], "<=", 6), ([3, 2], "<=", 18),
    ])


def caso_min():
    return preparar_caso({"a": 1, "b": 2}, [
        ([1, 1], ">=", 4), ([1, 3], ">=", 6),
    ], tipo="MIN")


def caso_infactible():
    return preparar_caso({"a": 1, "b": 1}, [
        ([1, 1], ">=", 3), ([1, 1], "<=", 1),
    ])


def caso_no_acotado():
    return preparar_caso({"a": 1, "b": 1}, [([1, -1], "<=", 1)])
