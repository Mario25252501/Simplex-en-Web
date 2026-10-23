"""Demostración HTTP real: modelo -> API 2 -> API 3.

Ejecutar desde la carpeta que contiene api_motor y api_preparacion:
python -m api_motor.cliente_prueba --caso min
"""

import argparse
import json
from pathlib import Path

import httpx

from .integracion_api4 import modelo_para_api2


def main():
    parser = argparse.ArgumentParser(description="Probar preparación y motor por HTTP.")
    parser.add_argument("--caso", choices=["max", "min", "infactible", "no_acotado"], default="max")
    parser.add_argument("--api2", default="http://127.0.0.1:8001")
    parser.add_argument("--api3", default="http://127.0.0.1:8002")
    parser.add_argument("--guardar", help="Ruta opcional para guardar el resultado completo en JSON.")
    args = parser.parse_args()
    carpeta = Path(__file__).resolve().parent / "ejemplos"
    modelo = json.loads((carpeta / f"modelo_{args.caso}.json").read_text(encoding="utf-8"))
    try:
        # Servicios locales: conexión directa, sin usar proxies del sistema.
        with httpx.Client(timeout=30, trust_env=False) as cliente:
            preparada = cliente.post(args.api2.rstrip("/") + "/preparar", json=modelo_para_api2(modelo))
            preparada.raise_for_status()
            respuesta = cliente.post(args.api3.rstrip("/") + "/resolver", json=preparada.json())
            respuesta.raise_for_status()
            resultado = respuesta.json()
    except httpx.HTTPStatusError as error:
        print(f"HTTP {error.response.status_code} de {error.request.url}: {error.response.text}")
        return 1
    except httpx.RequestError as error:
        print(f"No se pudo comunicar con las APIs: {error}")
        print("Comprueba que API 2 y API 3 estén encendidas en sus terminales.")
        return 1
    print(json.dumps({
        "caso": args.caso,
        "estado": resultado["estado"],
        "valor_z": resultado["valor_z"],
        "solucion": resultado["solucion"],
        "tablas_registradas": len(resultado["iteraciones"]),
        "fases": sorted({it["fase"] for it in resultado["iteraciones"]}),
    }, ensure_ascii=False, indent=2))
    if args.guardar:
        Path(args.guardar).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Resultado completo guardado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
