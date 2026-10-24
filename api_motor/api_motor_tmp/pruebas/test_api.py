import copy
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_motor.main import app
from .casos import caso_max, caso_min, caso_infactible, caso_no_acotado


class PruebasAPI(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)

    def test_salud_y_documentacion(self):
        self.assertEqual(self.cliente.get("/salud").json()["integrante"], 3)
        self.assertEqual(self.cliente.get("/docs").status_code, 200)
        esquema = self.cliente.get("/openapi.json").json()
        self.assertIn("/resolver", esquema["paths"])

    def test_validacion(self):
        r = self.cliente.post("/validar-tableau", json=caso_max())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["tabla"]["tipo"], "MAX")

    def test_estados_y_formato_que_guarda_api4(self):
        for caso, estado, z in [
            (caso_max(), "OPTIMO", 36), (caso_min(), "OPTIMO", 5),
            (caso_infactible(), "INFACTIBLE", None),
            (caso_no_acotado(), "NO_ACOTADO", None),
        ]:
            with self.subTest(estado=estado, tipo=caso["tipo"]):
                r = self.cliente.post("/resolver", json=caso)
                self.assertEqual(r.status_code, 200, r.text)
                datos = r.json()
                self.assertEqual(set(datos), {"estado", "valor_z", "solucion", "iteraciones"})
                self.assertEqual(datos["estado"], estado)
                self.assertEqual(datos["valor_z"], z)
                for it in datos["iteraciones"]:
                    self.assertEqual(set(it), {
                        "numero", "fase", "variable_entrante", "variable_saliente",
                        "fila_pivote", "columna_pivote", "elemento_pivote", "tabla", "operaciones",
                    })

    def test_422_para_json_invalido(self):
        self.assertEqual(self.cliente.post("/resolver", json={}).status_code, 422)
        p = caso_max(); p["tipo"] = "MAx"
        self.assertEqual(self.cliente.post("/resolver", json=p).status_code, 422)
        p = caso_max(); p["filas"][1][1] = "texto"
        self.assertEqual(self.cliente.post("/resolver", json=p).status_code, 422)

    def test_409_para_limite(self):
        p = caso_max(); p["max_iteraciones"] = 1
        r = self.cliente.post("/resolver", json=p)
        self.assertEqual(r.status_code, 409)
        self.assertNotIn("estado", r.json())

    def test_orquestador_con_dobles_sin_mysql(self):
        # Mismo orden de llamadas que main.py del Integrante 4. API 2 es un doble.
        api2 = FastAPI()

        @api2.post("/preparar")
        def preparar(modelo: dict):
            self.assertEqual(modelo["objetivo"], {"a": 3, "b": 5})
            return caso_max()

        modelo = {"nombre": "Prueba", "tipo": "MAX", "objetivo": {"a": 3, "b": 5}}
        tableau = TestClient(api2).post("/preparar", json=modelo).json()
        resultado = self.cliente.post("/resolver", json=tableau)
        self.assertEqual(resultado.status_code, 200)
        self.assertEqual(resultado.json()["valor_z"], 36)


if __name__ == "__main__":
    unittest.main()
