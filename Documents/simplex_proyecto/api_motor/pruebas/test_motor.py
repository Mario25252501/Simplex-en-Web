import copy
import json
import unittest

from pydantic import ValidationError

from api_motor.esquemas import EJEMPLO_MAX, ResultadoSimplex, TableauEntrada
from api_motor.motor_simplex import (
    LimiteCalculo, aplicar_pivote, normalizar_fila_pivote, resolver_simplex,
    seleccionar_columna_entrante, seleccionar_fila_saliente,
)
from .casos import caso_max, caso_min, caso_infactible, caso_no_acotado, preparar_caso


class PruebasMotor(unittest.TestCase):
    def comprobar_resultado(self, entrada, estado="OPTIMO", z=None):
        copia = copy.deepcopy(entrada)
        resultado = resolver_simplex(entrada)
        self.assertEqual(entrada, copia, "El motor modificó la entrada original")
        self.assertEqual(resultado["estado"], estado)
        ResultadoSimplex.model_validate(resultado)
        json.dumps(resultado, allow_nan=False)
        its = resultado["iteraciones"]
        self.assertTrue(its)
        self.assertEqual([it["numero"] for it in its], list(range(len(its))))
        if z is not None:
            self.assertAlmostEqual(resultado["valor_z"], z, places=7)
        if estado == "OPTIMO":
            self.assertIsNone(its[-1]["fila_pivote"])
            self.assertIsNone(its[-1]["columna_pivote"])
            self.assertIsNone(its[-1]["elemento_pivote"])
            self.assertIsNone(its[-1]["variable_entrante"])
            self.assertIsNone(its[-1]["variable_saliente"])
        else:
            self.assertIsNone(resultado["valor_z"])
            self.assertEqual(resultado["solucion"], {})

        # Rehacer cada pivote desde la tabla mostrada debe producir la siguiente.
        for i, it in enumerate(its):
            fila, columna = it["fila_pivote"], it["columna_pivote"]
            tabla = it["tabla"]
            for f in tabla["filas"]:
                self.assertEqual(len(f), len(tabla["columnas"]))
            self.assertEqual(tabla["filas"][0][0], "Z")
            if fila is None:
                continue
            self.assertEqual(it["variable_entrante"], tabla["columnas"][columna])
            self.assertEqual(it["variable_saliente"], tabla["filas"][fila][0])
            self.assertAlmostEqual(it["elemento_pivote"], tabla["filas"][fila][columna])
            rehecha, _ = aplicar_pivote(tabla["filas"], tabla["columnas"], fila, columna)
            siguiente = its[i + 1]["tabla"]
            self.assertEqual(tabla["columnas"], siguiente["columnas"])
            for actual, esperado in zip(rehecha, siguiente["filas"]):
                self.assertEqual(actual[0], esperado[0])
                for a, b in zip(actual[1:], esperado[1:]):
                    self.assertAlmostEqual(a, b, places=7)
        return resultado

    def test_max_del_proyecto(self):
        r = self.comprobar_resultado(caso_max(), z=36)
        self.assertEqual(r["solucion"], {"a": 2.0, "b": 6.0})

    def test_json_original_de_cuatro_campos(self):
        r = self.comprobar_resultado(copy.deepcopy(EJEMPLO_MAX), z=36)
        self.assertEqual(r["solucion"]["b"], 6)
        legado = copy.deepcopy(EJEMPLO_MAX)
        legado.pop("objetivo_original")
        self.comprobar_resultado(legado, z=36)

    def test_min_dos_fases(self):
        r = self.comprobar_resultado(caso_min(), z=5)
        self.assertEqual(r["solucion"], {"a": 3.0, "b": 1.0})
        self.assertEqual({it["fase"] for it in r["iteraciones"]}, {1, 2})
        self.assertFalse(any(v.startswith("A") for v in r["iteraciones"][-1]["tabla"]["columnas"]))

    def test_infactible(self):
        self.comprobar_resultado(caso_infactible(), "INFACTIBLE")

    def test_no_acotado(self):
        self.comprobar_resultado(caso_no_acotado(), "NO_ACOTADO")

    def test_no_acotado_despues_de_fase1(self):
        p = preparar_caso({"a": 1, "b": 1}, [([1, -1], ">=", 0)])
        self.comprobar_resultado(p, "NO_ACOTADO")

    def test_min_no_acotado(self):
        p = preparar_caso({"a": -1, "b": -1}, [([1, -1], "<=", 1)], "MIN")
        self.comprobar_resultado(p, "NO_ACOTADO")

    def test_igualdad_y_exceso(self):
        p = preparar_caso({"a": 2, "b": 1}, [
            ([1, 1], "=", 4), ([1, -1], ">=", 2), ([1, 0], "<=", 3),
        ])
        self.comprobar_resultado(p, z=7)

    def test_rhs_negativo_ya_normalizado_por_preparacion(self):
        p = preparar_caso({"a": 1, "b": 2}, [
            ([-1, -1], "<=", -4), ([1, 3], ">=", 6),
        ], "MIN")
        self.comprobar_resultado(p, z=5)

    def test_restriccion_redundante(self):
        p = preparar_caso({"a": 1, "b": 1}, [([1, 1], "=", 2), ([1, 1], "=", 2)])
        r = self.comprobar_resultado(p, z=2)
        self.assertTrue(any("redundante" in op for it in r["iteraciones"] for op in it["operaciones"]))

    def test_artificial_cero_con_pivote_de_limpieza_negativo(self):
        p = preparar_caso({"a": 1, "b": 1}, [([-1, 0], "=", 0), ([0, 1], "<=", 1)])
        r = self.comprobar_resultado(p, z=1)
        self.assertTrue(any(it["elemento_pivote"] == -1 for it in r["iteraciones"]))

    def test_todas_las_restricciones_redundantes(self):
        p = preparar_caso({"a": 0, "b": 0}, [([0, 0], "=", 0)])
        self.comprobar_resultado(p, z=0)
        p["objetivo_original"]["a"] = 1
        self.comprobar_resultado(p, "NO_ACOTADO")

    def test_seis_variables(self):
        objetivo = {v: i + 1 for i, v in enumerate("abcdef")}
        restricciones = [([int(i == j) for j in range(6)], "<=", i + 1) for i in range(6)]
        self.comprobar_resultado(preparar_caso(objetivo, restricciones), z=91)

    def test_decimales(self):
        p = preparar_caso({"a": 0.1, "b": 0.2}, [([1, 1], "<=", 0.3)])
        self.comprobar_resultado(p, z=0.06)

    def test_optimos_alternativos(self):
        self.comprobar_resultado(preparar_caso({"a": 1, "b": 1}, [([1, 1], "<=", 4)]), z=4)

    def test_min_negativo(self):
        p = preparar_caso({"a": -3, "b": -5}, [
            ([1, 0], "<=", 4), ([0, 1], "<=", 6), ([3, 2], "<=", 18),
        ], "MIN")
        self.comprobar_resultado(p, z=-36)

    def test_ciclado_beale_activa_bland(self):
        p = preparar_caso({"a": 10, "b": -57, "c": -9, "d": -24}, [
            ([0.5, -5.5, -2.5, 9], "<=", 0),
            ([0.5, -1.5, -0.5, 1], "<=", 0),
            ([1, 0, 0, 0], "<=", 1),
        ])
        r = self.comprobar_resultado(p, z=1)
        self.assertTrue(any("Bland" in op for it in r["iteraciones"] for op in it["operaciones"]))

    def test_limite_no_se_disfraza_de_optimo(self):
        p = caso_max()
        p["max_iteraciones"] = 1
        with self.assertRaises(LimiteCalculo):
            resolver_simplex(p)

    def test_funciones_aprendidas_y_razon_cero(self):
        p = EJEMPLO_MAX
        self.assertEqual(seleccionar_columna_entrante(p["filas"][0]), 2)
        self.assertEqual(seleccionar_fila_saliente(p["filas"], 2), 2)
        self.assertEqual(normalizar_fila_pivote(["h1", 2, 4, 6], 1), ["h1", 1, 2, 3])
        self.assertEqual(seleccionar_fila_saliente([["Z", -1, 0], ["h1", 2, 0]], 1), 1)

    def test_rechaza_entradas_mal_preparadas(self):
        casos = []
        p = caso_max(); p["filas"][1].pop(); casos.append(p)
        p = caso_max(); p["filas"][1][-1] = -1; casos.append(p)
        p = caso_max(); p["filas"][1][3] = 2; casos.append(p)
        p = caso_max(); p["filas"][1][1] = "1"; casos.append(p)
        p = caso_max(); p["filas"][1][1] = True; casos.append(p)
        p = caso_max(); p["filas"][1][1] = float("nan"); casos.append(p)
        p = caso_max(); p["filas"][1][1] = 10 ** 500; casos.append(p)
        p = caso_max(); p["columnas"][2] = "a"; casos.append(p)
        p = caso_min(); p.pop("objetivo_original"); casos.append(p)
        p = caso_min(); p["variables_artificiales"] = []; casos.append(p)
        p = caso_max(); p["requiere_fase1"] = True; casos.append(p)
        p = caso_max(); p["objetivo_original"] = {"a": 1}; casos.append(p)
        p = caso_max(); p["tipo"] = "MAx"; casos.append(p)
        for p in casos:
            with self.subTest(entrada=p), self.assertRaises(ValidationError):
                TableauEntrada.model_validate(p)

    def test_adaptador_tabla_anidada_y_alias_objetivo(self):
        p = caso_max()
        p["tabla"] = {"columnas": p.pop("columnas"), "filas": p.pop("filas")}
        p["objetivo"] = p.pop("objetivo_original")
        self.comprobar_resultado(p, z=36)


if __name__ == "__main__":
    unittest.main()
