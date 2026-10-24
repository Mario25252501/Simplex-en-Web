
from fastapi.testclient import TestClient
from main import app

# Cliente que permite probar nuestra API
client = TestClient(app)


# Prueba 1: Maximización con restricciones <=
def test_maximizacion():
    modelo = {
        "tipo_optimizacion": "max",
        "variables": 2,
        "coeficientes_objetivo": [3, 5],
        "restricciones": [
            {
                "coeficientes": [1, 0],
                "signo": "<=",
                "termino_independiente": 4
            },
            {
                "coeficientes": [0, 2],
                "signo": "<=",
                "termino_independiente": 12
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["fase"] == 2
    assert datos["requiere_fase1"] is False
    assert datos["variables_basicas"] == ["h1", "h2"]
    assert datos["filas"] == [
        ["Z", -3, -5, 0, 0, 0],
        ["h1", 1, 0, 1, 0, 4],
        ["h2", 0, 2, 0, 1, 12]
    ]


# Prueba 2: Minimización con artificiales
def test_minimizacion():
    modelo = {
        "tipo_optimizacion": "min",
        "variables": 2,
        "coeficientes_objetivo": [2, 3],
        "restricciones": [
            {
                "coeficientes": [1, 1],
                "signo": ">=",
                "termino_independiente": 4
            },
            {
                "coeficientes": [1, 2],
                "signo": "=",
                "termino_independiente": 6
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["fase"] == 1
    assert datos["requiere_fase1"] is True
    assert datos["variables_artificiales"] == ["A1", "A2"]
    assert datos["filas"][0] == [
        "P", -2, -3, 1, 0, 0, -10
    ]
    assert datos["factor_recuperacion_z"] == -1


# Prueba 3: Validación de coeficientes
def test_validacion():
    modelo = {
        "tipo_optimizacion": "max",
        "variables": 2,
        "coeficientes_objetivo": [3, 5, 7],
        "restricciones": [
            {
                "coeficientes": [1, 2],
                "signo": "<=",
                "termino_independiente": 10
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)

    assert respuesta.status_code == 422

# PRUEBA 4: Restricciones mixtas
def test_restricciones_mixtas():
    modelo = {
        "tipo_optimizacion": "max",
        "variables": 2,
        "coeficientes_objetivo": [4, 3],
        "restricciones": [
            {
                "coeficientes": [1, 1],
                "signo": "<=",
                "termino_independiente": 10
            },
            {
                "coeficientes": [2, 1],
                "signo": ">=",
                "termino_independiente": 6
            },
            {
                "coeficientes": [1, 2],
                "signo": "=",
                "termino_independiente": 8
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)
    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["fase"] == 1
    assert datos["variables_basicas"] == ["h1", "A2", "A3"]
    assert datos["variables_artificiales"] == ["A2", "A3"]

    assert datos["filas"] == [
        ["P", -3, -3, 0, 1, 0, 0, -14],
        ["h1", 1, 1, 1, 0, 0, 0, 10],
        ["A2", 2, 1, 0, -1, 1, 0, 6],
        ["A3", 1, 2, 0, 0, 0, 1, 8]
    ]


# PRUEBA 5: Término independiente negativo
def test_termino_negativo():
    modelo = {
        "tipo_optimizacion": "max",
        "variables": 2,
        "coeficientes_objetivo": [3, 2],
        "restricciones": [
            {
                "coeficientes": [-2, -1],
                "signo": "<=",
                "termino_independiente": -6
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)
    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert datos["requiere_fase1"] is True
    assert datos["variables_basicas"] == ["A1"]

    assert datos["filas"] == [
        ["P", -2, -1, 1, 0, -6],
        ["A1", 2, 1, -1, 1, 6]
    ]

# PRUEBA 6: Restricciones redundantes
def test_restriccion_redundante():

    modelo = {
        "tipo_optimizacion": "max",
        "variables": 2,
        "coeficientes_objetivo": [3, 5],
        "restricciones": [
            {
                "coeficientes": [0, 0],
                "signo": "<=",
                "termino_independiente": 10
            },
            {
                "coeficientes": [1, 1],
                "signo": "<=",
                "termino_independiente": 8
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)

    assert respuesta.status_code == 200

    datos = respuesta.json()

    print("Variables básicas:", datos["variables_basicas"])
    print("Restricciones redundantes:",
          datos.get("restricciones_redundantes"))

    assert datos["variables_basicas"] == ["h1"]
    assert datos["restricciones_redundantes"] == [1]

    assert datos["filas"] == [
        ["Z", -3, -5, 0, 0],
        ["h1", 1, 1, 1, 8]
    ]

# PRUEBA 7: Restricción matemáticamente imposible
def test_restriccion_infactible():

    modelo = {
        "tipo_optimizacion": "max",
        "variables": 2,
        "coeficientes_objetivo": [3, 5],
        "restricciones": [
            {
                "coeficientes": [0, 0],
                "signo": ">=",
                "termino_independiente": 10
            }
        ],
        "no_negatividad": True
    }

    respuesta = client.post("/preparar", json=modelo)

    assert respuesta.status_code == 422

    datos = respuesta.json()

    assert "infactible" in str(datos).lower()
