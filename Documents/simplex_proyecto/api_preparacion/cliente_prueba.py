import httpx 
import json

# Dirección de nuestra API independiente
URL_API = "http://127.0.0.1:8001/preparar"

# Modelo matemático que enviaremos
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

try:
    # Enviar solicitud HTTP POST
    respuesta = httpx.post(
        URL_API,
        json=modelo,
        timeout=30
    )

    # Verificar el código de respuesta
    respuesta.raise_for_status()

    # Convertir la respuesta JSON
    datos = respuesta.json()
    # Guardar la respuesta real de nuestra API
    with open(
        "ejemplo_respuesta_api.json",
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            datos,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    print("\nArchivo JSON generado correctamente")


    print("CONEXION EXITOSA")
    print("Codigo HTTP:", respuesta.status_code)
    print("Fase:", datos["fase"])
    print("Columnas:", datos["columnas"])

    print("\nTABLEAU INICIAL:")

    for fila in datos["filas"]:
        print(fila)

    print("\nRequiere Fase I:",
          datos["requiere_fase1"])
    
    print("\nDATOS PARA EL MOTOR SIMPLEX")

    print("Variables basicas:",
      datos["variables_basicas"])

    print("Variables artificiales:",
      datos["variables_artificiales"])

    print("Objetivo Fase II:",
      datos["objetivo_fase2"])

    print("Factor recuperacion Z:",
      datos["factor_recuperacion_z"])

    print("Tipo original:",
      datos["tipo_optimizacion_original"])


except httpx.HTTPError as error:
    print("Error de comunicacion:", error)
