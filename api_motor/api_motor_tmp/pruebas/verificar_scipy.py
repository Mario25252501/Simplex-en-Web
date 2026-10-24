"""Verificación adicional opcional contra HiGHS/SciPy, con semilla fija.

No se importa SciPy desde el motor. Solo se usa como referencia independiente
para comprobar estados, factibilidad y objetivos de 300 modelos de 2-6 variables.
Ejecutar: python -m api_motor.pruebas.verificar_scipy
Requiere instalar scipy por separado.
"""

from collections import Counter
import random

from scipy.optimize import linprog

from api_motor.motor_simplex import resolver_simplex
from .casos import preparar_caso


def verificar(cantidad=300):
    azar = random.Random(20261022)
    estados = Counter()
    for numero in range(cantidad):
        n = azar.randint(2, 6)
        tipo = azar.choice(["MAX", "MIN"])
        costos = [azar.randint(-5, 7) for _ in range(n)]
        objetivo = dict(zip("abcdef"[:n], costos))
        punto = [azar.randint(0, 5) for _ in range(n)]
        restricciones = []
        for _ in range(azar.randint(1, 8)):
            coef = [azar.randint(-5, 5) for _ in range(n)]
            signo = azar.choice(["<=", ">=", "="])
            rhs = sum(a * b for a, b in zip(coef, punto))
            if signo == "<=":
                rhs += azar.randint(0, 5)
            elif signo == ">=":
                rhs -= azar.randint(0, 5)
            restricciones.append((coef, signo, rhs))
        if numero % 3:
            for j in range(n):
                restricciones.append(([int(k == j) for k in range(n)], "<=", 10))
        if numero % 5 == 0:
            restricciones.append(([1] + [0] * (n - 1), "<=", -1))

        aub, bub, aeq, beq = [], [], [], []
        for coef, signo, rhs in restricciones:
            if signo == "=":
                aeq.append(coef); beq.append(rhs)
            else:
                factor = -1 if signo == ">=" else 1
                aub.append([factor * c for c in coef]); bub.append(factor * rhs)
        referencia = linprog(
            [-c if tipo == "MAX" else c for c in costos],
            A_ub=aub or None, b_ub=bub or None,
            A_eq=aeq or None, b_eq=beq or None,
            bounds=(0, None), method="highs", options={"presolve": False},
        )
        if referencia.status not in (0, 2, 3):
            raise AssertionError(f"Referencia sin clasificación en caso {numero}: {referencia.message}")
        esperado = {0: "OPTIMO", 2: "INFACTIBLE", 3: "NO_ACOTADO"}[referencia.status]
        entrada = preparar_caso(objetivo, restricciones, tipo)
        resultado = resolver_simplex(entrada)
        assert resultado["estado"] == esperado, (numero, entrada, resultado, referencia)
        estados[esperado] += 1
        if esperado == "OPTIMO":
            z = -referencia.fun if tipo == "MAX" else referencia.fun
            assert abs(resultado["valor_z"] - z) <= 1e-6 * max(1, abs(z)), (numero, z, resultado)
            x = [resultado["solucion"][v] for v in objetivo]
            assert all(v >= -1e-7 for v in x)
            for coef, signo, rhs in restricciones:
                lhs = sum(c * v for c, v in zip(coef, x))
                assert (
                    lhs <= rhs + 1e-6 if signo == "<=" else
                    lhs >= rhs - 1e-6 if signo == ">=" else abs(lhs - rhs) <= 1e-6
                ), (numero, coef, signo, rhs, x)
    return {"comparaciones": cantidad, "estados": dict(estados), "semilla": 20261022}


if __name__ == "__main__":
    import json
    print(json.dumps(verificar(), ensure_ascii=False, indent=2))
