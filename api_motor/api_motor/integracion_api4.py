"""Conversión necesaria entre el main.py de API 4 y la API 2 real.

No requiere MySQL y no llama servicios. Solo traduce el modelo del formulario
al contrato que acepta POST /preparar de la rama api-preparacion.
"""

import math


def modelo_para_api2(modelo):
    objetivo = modelo.get("objetivo")
    if not isinstance(objetivo, dict) or not 2 <= len(objetivo) <= 6:
        raise ValueError("El objetivo debe definir entre 2 y 6 variables.")
    nombres = list("abcdef"[:len(objetivo)])
    if set(objetivo) != set(nombres):
        raise ValueError("API 2 espera variables consecutivas desde a: a,b; a,b,c; etc.")
    tipo = modelo.get("tipo")
    if tipo not in ("MAX", "MIN"):
        raise ValueError("tipo debe ser MAX o MIN.")

    def numero(valor):
        if type(valor) not in (int, float) or abs(valor) > 1e12 or not math.isfinite(valor):
            raise ValueError("Los coeficientes deben ser números finitos de magnitud <= 1e12.")
        return valor

    restricciones = modelo.get("restricciones")
    if not isinstance(restricciones, list) or not restricciones:
        raise ValueError("Se necesita al menos una restricción.")
    salida = []
    for restriccion in restricciones:
        if not isinstance(restriccion, dict):
            raise ValueError("Cada restricción debe ser un objeto JSON.")
        coef = restriccion.get("coeficientes")
        if not isinstance(coef, dict) or set(coef) - set(nombres):
            raise ValueError("Una restricción contiene variables desconocidas.")
        signo = restriccion.get("signo")
        if signo not in ("<=", ">=", "="):
            raise ValueError("Signo de restricción inválido.")
        salida.append({
            "coeficientes": [numero(coef.get(v, 0)) for v in nombres],
            "signo": signo,
            "termino_independiente": numero(restriccion.get("termino_independiente")),
        })
    return {
        "tipo_optimizacion": tipo.lower(),
        "variables": len(nombres),
        "coeficientes_objetivo": [numero(objetivo[v]) for v in nombres],
        "restricciones": salida,
        "no_negatividad": True,
    }
