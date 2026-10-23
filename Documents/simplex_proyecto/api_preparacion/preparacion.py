

def construir_tableau_inicial(modelo):
    cantidad = modelo.variables
    nombres = list("abcdef"[:cantidad])

    restricciones = modelo.restricciones
    
    # Identificar restricciones con coeficientes cero
    restricciones_validas = []
    restricciones_redundantes = []

    for i, restriccion in enumerate(restricciones, 1):

        if all(c == 0 for c in restriccion.coeficientes):

            rhs = restriccion.termino_independiente
            signo = restriccion.signo

            # Comprobar si 0 cumple la restricción
            if signo == "<=":
                se_cumple = 0 <= rhs

            elif signo == ">=":
                se_cumple = 0 >= rhs

            else:
                se_cumple = 0 == rhs

            if se_cumple:
                restricciones_redundantes.append(i)
                continue

            raise ValueError(
                f"Modelo infactible: la restricción {i} "
                "no puede cumplirse porque todos sus "
                "coeficientes son cero."
            )

        restricciones_validas.append(restriccion)

    # Continuar únicamente con restricciones útiles
    restricciones = restricciones_validas
    print("Restricciones originales:", len(modelo.restricciones))
    print("Restricciones válidas:", len(restricciones))
    print("Restricciones redundantes:", restricciones_redundantes)
    print("DEBUG - Restricciones originales:", len(modelo.restricciones))
    print("DEBUG - Restricciones válidas:", len(restricciones))
    print("DEBUG - Redundantes:", restricciones_redundantes)
    print("DEBUG - Normalizadas antes del proceso:", normalizadas if "normalizadas" in locals() else "Todavía no creadas") 
    
    
    # Normalizar restricciones con RHS negativo
    normalizadas = []

    for r in restricciones:
        coeficientes = list(r.coeficientes)
        signo = r.signo
        rhs = r.termino_independiente

        if rhs < 0:
            coeficientes = [-x for x in coeficientes]
            rhs = -rhs

            if signo == "<=":
                signo = ">="
            elif signo == ">=":
                signo = "<="

        normalizadas.append((coeficientes, signo, rhs))

    # Identificar variables auxiliares
    auxiliares = []
    basicas = []
    artificiales = []

    for i, (_, signo, _) in enumerate(normalizadas):
        numero = i + 1

        if signo == "<=":
            holgura = f"h{numero}"
            auxiliares.append(holgura)
            basicas.append(holgura)

        elif signo == ">=":
            exceso = f"e{numero}"
            artificial = f"A{numero}"

            auxiliares.extend([exceso, artificial])
            artificiales.append(artificial)
            basicas.append(artificial)

        else:
            artificial = f"A{numero}"
            auxiliares.append(artificial)
            artificiales.append(artificial)
            basicas.append(artificial)

    columnas = ["Base"] + nombres + auxiliares + ["Solución"]

    filas_restricciones = []

    for i, (coeficientes, signo, rhs) in enumerate(normalizadas):
        fila = {nombre: 0 for nombre in auxiliares}
        numero = i + 1

        if signo == "<=":
            fila[f"h{numero}"] = 1

        elif signo == ">=":
            fila[f"e{numero}"] = -1
            fila[f"A{numero}"] = 1

        else:
            fila[f"A{numero}"] = 1

        filas_restricciones.append(
            [basicas[i]]
            + coeficientes
            + [fila[nombre] for nombre in auxiliares]
            + [rhs]
        )

    requiere_fase1 = len(artificiales) > 0
    
    # Construcción de la fila objetivo
    if requiere_fase1:
        # Fase I: maximizar P = -suma(artificiales)
        # Fila inicial: P + suma(artificiales) = 0
        fila_objetivo = (
            ["P"]
            + [0] * cantidad
            + [
                1 if nombre in artificiales else 0
                for nombre in auxiliares
            ]
            + [0]
        )

        # Eliminar las artificiales básicas de la fila P
        for fila in filas_restricciones:
            if fila[0] in artificiales:
                for j in range(1, len(fila)):
                    fila_objetivo[j] -= fila[j]

    else:
        # Fase II sin artificiales
        coeficientes = list(modelo.coeficientes_objetivo)

        if modelo.tipo_optimizacion == "min":
            coeficientes = [-c for c in coeficientes]

        fila_objetivo = (
            ["Z"]
            + [-c for c in coeficientes]
            + [0] * len(auxiliares)
            + [0]
        )

    filas = [fila_objetivo] + filas_restricciones
    
    # Guardar la función objetivo original
    # para reconstruir la Fase II.
    coeficientes_originales = list(
        modelo.coeficientes_objetivo
    )

    # Convertir minimización a maximización equivalente
    if modelo.tipo_optimizacion == "min":
        coeficientes_motor = [
            -c for c in coeficientes_originales
        ]
    else:
        coeficientes_motor = coeficientes_originales.copy()

    # Fila objetivo de Fase II antes de
    # ajustarla a la base que resulte de Fase I.
    fila_fase2 = (
        ["Z"]
        + [-c for c in coeficientes_motor]
        + [0] * len(auxiliares)
        + [0]
    )



    
    
    return {
        "tipo": modelo.tipo_optimizacion.upper(),
        "fase": 1 if requiere_fase1 else 2,
        "columnas": columnas,
        "filas": filas,
        "variables_basicas": basicas,
        "variables_artificiales": artificiales,
        "requiere_fase1": requiere_fase1,
        "objetivo_original": list(modelo.coeficientes_objetivo),
        "objetivo_auxiliar": (
            "MAX P = -suma(artificiales)"
            if requiere_fase1 else None
        ),
        "estado_preparacion": "tableau_inicial_completo",
        "objetivo_fase2": fila_fase2,
"tipo_optimizacion_original": modelo.tipo_optimizacion,
"factor_recuperacion_z": (
    -1 if modelo.tipo_optimizacion == "min" else 1
),
"restricciones_redundantes": restricciones_redundantes,
    }
