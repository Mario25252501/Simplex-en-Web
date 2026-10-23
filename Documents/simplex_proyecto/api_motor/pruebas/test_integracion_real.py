"""Cadena real API 2 -> API 3. No usa base de datos ni un preparador simulado."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient

from api_motor.integracion_api4 import modelo_para_api2
from api_motor.main import app


class PruebasIntegracionReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        carpeta = Path(__file__).resolve().parents[2] / "api_preparacion"
        if not (carpeta / "main.py").exists():
            raise unittest.SkipTest("Falta la carpeta de referencia api_preparacion del compañero.")
        sys.path.insert(0, str(carpeta))
        try:
            spec = importlib.util.spec_from_file_location("preparacion_companero_main", carpeta / "main.py")
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
        finally:
            sys.path.pop(0)
        cls.preparacion = TestClient(modulo.app)
        cls.motor = TestClient(app)
        cls.carpeta = carpeta

    def resolver_cadena(self, objetivo, restricciones, tipo="MAX", estado="OPTIMO", z=None):
        modelo = {"nombre": "Integración", "tipo": tipo, "objetivo": objetivo, "restricciones": []}
        for coeficientes, signo, rhs in restricciones:
            modelo["restricciones"].append({
                "coeficientes": dict(zip(objetivo, coeficientes)),
                "signo": signo, "termino_independiente": rhs,
            })
        entrada2 = modelo_para_api2(modelo)
        # El preparador del compañero imprime diagnósticos; no son el resultado.
        with contextlib.redirect_stdout(io.StringIO()):
            respuesta2 = self.preparacion.post("/preparar", json=entrada2)
        self.assertEqual(respuesta2.status_code, 200, respuesta2.text)
        respuesta3 = self.motor.post("/resolver", json=respuesta2.json())
        self.assertEqual(respuesta3.status_code, 200, respuesta3.text)
        resultado = respuesta3.json()
        self.assertEqual(resultado["estado"], estado)
        if z is not None:
            self.assertAlmostEqual(resultado["valor_z"], z)
        self.assertTrue(all(it["tabla"]["filas"][0][0] == "Z" for it in resultado["iteraciones"]))
        return resultado

    def test_max_real(self):
        self.resolver_cadena({"a": 3, "b": 5}, [
            ([1, 0], "<=", 4), ([0, 2], "<=", 12),
        ], z=42)

    def test_max_ejercicio_del_grupo(self):
        self.resolver_cadena({"a": 3, "b": 5}, [
            ([1, 0], "<=", 4), ([0, 1], "<=", 6), ([3, 2], "<=", 18),
        ], z=36)

    def test_min_real_con_igualdad(self):
        r = self.resolver_cadena({"a": 2, "b": 3}, [
            ([1, 1], ">=", 4), ([1, 2], "=", 6),
        ], "MIN", z=10)
        self.assertEqual(r["solucion"], {"a": 2, "b": 2})

    def test_mixto_real(self):
        self.resolver_cadena({"a": 4, "b": 3}, [
            ([1, 1], "<=", 10), ([2, 1], ">=", 6), ([1, 2], "=", 8),
        ], z=32)

    def test_infactibilidad_real_entre_restricciones(self):
        self.resolver_cadena({"a": 1, "b": 1}, [
            ([1, 1], ">=", 3), ([1, 1], "<=", 1),
        ], estado="INFACTIBLE")

    def test_no_acotado_real(self):
        self.resolver_cadena({"a": 1, "b": 1}, [([1, -1], "<=", 1)], estado="NO_ACOTADO")

    def test_solo_restricciones_redundantes(self):
        self.resolver_cadena({"a": 0, "b": 0}, [([0, 0], "<=", 10)], z=0)
        self.resolver_cadena({"a": 1, "b": 1}, [([0, 0], "<=", 10)], estado="NO_ACOTADO")

    def test_json_real_guardado_por_companero(self):
        entrada = json.loads((self.carpeta / "ejemplo_respuesta_api.json").read_text(encoding="utf-8-sig"))
        respuesta = self.motor.post("/resolver", json=entrada)
        self.assertEqual(respuesta.status_code, 200, respuesta.text)
        self.assertEqual(respuesta.json()["valor_z"], 10)

    def test_diagnostica_desajuste_api4_original(self):
        modelo = {"tipo": "MAX", "objetivo": {"a": 3, "b": 5}, "restricciones": []}
        respuesta = self.preparacion.post("/preparar", json=modelo)
        self.assertEqual(respuesta.status_code, 422)

    def test_conversion_api4_respeta_orden_y_ceros(self):
        convertido = modelo_para_api2({
            "tipo": "MAX", "objetivo": {"b": 5, "a": 3},
            "restricciones": [{"coeficientes": {"b": 2}, "signo": "<=", "termino_independiente": 12}],
        })
        self.assertEqual(convertido["coeficientes_objetivo"], [3, 5])
        self.assertEqual(convertido["restricciones"][0]["coeficientes"], [0, 2])

    def test_metadatos_inconsistentes_se_rechazan(self):
        entrada = json.loads((self.carpeta / "ejemplo_respuesta_api.json").read_text(encoding="utf-8-sig"))
        entrada["factor_recuperacion_z"] = 1
        self.assertEqual(self.motor.post("/resolver", json=entrada).status_code, 422)


if __name__ == "__main__":
    unittest.main()
