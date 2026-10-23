# Motor temporal: devuelve siempre la solución del ejemplo (se reemplaza por el del Integrante 3)
def resolver_simplex(modelo):
    cols = ["Base", "a", "b", "h1", "h2", "h3", "Solución"]  # Encabezados de cada tabla
    t = 1 / 3  # Valor repetido en la última tabla
    return {
        "estado": "OPTIMO",  # Puede ser OPTIMO, INFACTIBLE o NO_ACOTADO
        "valor_z": 36,  # Valor final de Z
        "solucion": {"a": 2, "b": 6},  # Valor final de cada variable
        "iteraciones": [
            {"numero": 0, "fase": 2, "variable_entrante": "b", "variable_saliente": "h2",
             "fila_pivote": 2, "columna_pivote": 2, "elemento_pivote": 2,
             "tabla": {"columnas": cols, "filas": [
                 ["Z", -3, -5, 0, 0, 0, 0], ["h1", 1, 0, 1, 0, 0, 4],
                 ["h2", 0, 2, 0, 1, 0, 12], ["h3", 3, 2, 0, 0, 1, 18]]},
             "operaciones": ["F2 = F2 / 2", "F0 = F0 + 5·F2", "F3 = F3 - 2·F2"]},
            {"numero": 1, "fase": 2, "variable_entrante": "a", "variable_saliente": "h3",
             "fila_pivote": 3, "columna_pivote": 1, "elemento_pivote": 3,
             "tabla": {"columnas": cols, "filas": [
                 ["Z", -3, 0, 0, 2.5, 0, 30], ["h1", 1, 0, 1, 0, 0, 4],
                 ["b", 0, 1, 0, 0.5, 0, 6], ["h3", 3, 0, 0, -1, 1, 6]]},
             "operaciones": ["F3 = F3 / 3", "F0 = F0 + 3·F3", "F1 = F1 - F3"]},
            {"numero": 2, "fase": 2, "variable_entrante": None, "variable_saliente": None,
             "fila_pivote": None, "columna_pivote": None, "elemento_pivote": None,
             "tabla": {"columnas": cols, "filas": [
                 ["Z", 0, 0, 0, 1.5, 1, 36], ["h1", 0, 0, 1, t, -t, 2],
                 ["b", 0, 1, 0, 0.5, 0, 6], ["a", 1, 0, 0, -t, t, 2]]},
             "operaciones": []},
        ],
    }