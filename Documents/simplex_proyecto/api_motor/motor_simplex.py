"""Motor símplex primal de dos fases, sin conexión a MySQL ni a otras APIs.

Se conserva la interfaz de las funciones aprendidas durante la guía. Por
dentro usamos Fraction: los decimales del JSON se tratan como fracciones
exactas, evitando errores de redondeo durante las operaciones de filas.
Las respuestas se convierten a números JSON al registrar cada tabla.
"""

from fractions import Fraction
import math
from time import monotonic

from .esquemas import TableauEntrada, TOLERANCIA


class ErrorMotor(RuntimeError):
    """Error técnico: no debe confundirse con infactibilidad o no acotación."""


class LimiteCalculo(ErrorMotor):
    """Se alcanzó un límite antes de poder clasificar el problema."""


def _fraccion(valor):
    return valor if isinstance(valor, Fraction) else Fraction(str(valor))


def _numero(valor):
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ErrorMotor("El resultado excede el rango de números JSON.") from error
    if not math.isfinite(numero):
        raise ErrorMotor("El resultado excede el rango de números JSON.")
    return 0.0 if numero == 0 else numero


def _tabla_json(filas):
    return [[fila[0]] + [_numero(v) for v in fila[1:]] for fila in filas]


def seleccionar_columna_entrante(fila_z, regla="mayor_mejora"):
    """Índice que incluye Base=0; excluye la columna Solución.

    La regla inicial elige el coeficiente más negativo, como en la guía.
    Bland elige la primera columna negativa para evitar ciclos.
    """
    candidatas = [j for j in range(1, len(fila_z) - 1) if _fraccion(fila_z[j]) < 0]
    if not candidatas:
        return None
    if regla == "bland":
        return candidatas[0]
    if regla != "mayor_mejora":
        raise ValueError("Regla de entrada desconocida.")
    return min(candidatas, key=lambda j: (_fraccion(fila_z[j]), j))


def seleccionar_fila_saliente(filas, columna_entrante, columnas=None):
    """Razón mínima no negativa, incluyendo el caso degenerado de razón 0.

    Cuando se conocen las columnas, los empates se resuelven por el menor
    índice de variable básica: la regla de salida de Bland.
    """
    if columna_entrante is None:
        return None
    razones = []
    for i in range(1, len(filas)):
        coeficiente = _fraccion(filas[i][columna_entrante])
        rhs = _fraccion(filas[i][-1])
        if rhs < 0:
            raise ValueError("La prueba de razones requiere una base factible (RHS >= 0).")
        if coeficiente > 0:
            desempate = columnas.index(filas[i][0]) if columnas else i
            razones.append((rhs / coeficiente, desempate, i))
    return min(razones)[2] if razones else None


def _normalizar_exacta(fila, columna_pivote):
    pivote = _fraccion(fila[columna_pivote])
    if pivote == 0:
        raise ValueError("El pivote no puede ser cero.")
    return [fila[0]] + [_fraccion(v) / pivote for v in fila[1:]]


def normalizar_fila_pivote(fila, columna_pivote):
    """Versión pública para las pruebas paso a paso; no modifica la fila."""
    return _tabla_json([_normalizar_exacta(fila, columna_pivote)])[0]


def _pivotear(filas, columnas, fila_pivote, columna_pivote):
    nueva = [[fila[0]] + [_fraccion(v) for v in fila[1:]] for fila in filas]
    pivote = nueva[fila_pivote][columna_pivote]
    nueva[fila_pivote] = _normalizar_exacta(nueva[fila_pivote], columna_pivote)
    operaciones = [f"F{fila_pivote} = F{fila_pivote} / ({pivote})"]
    for i in range(len(nueva)):
        if i == fila_pivote:
            continue
        factor = nueva[i][columna_pivote]
        if factor == 0:
            continue
        for j in range(1, len(columnas)):
            nueva[i][j] -= factor * nueva[fila_pivote][j]
        operaciones.append(f"F{i} = F{i} - ({factor}) * F{fila_pivote}")
    nueva[fila_pivote][0] = columnas[columna_pivote]
    return nueva, operaciones


def aplicar_pivote(filas, columnas, fila_pivote, columna_pivote):
    """Devuelve tabla nueva y operaciones; conserva intacta la entrada."""
    nueva, operaciones = _pivotear(filas, columnas, fila_pivote, columna_pivote)
    return _tabla_json(nueva), operaciones


class _Motor:
    def __init__(self, entrada):
        self.entrada = entrada
        self.columnas = list(entrada.columnas)
        self.filas = [[f[0]] + [_fraccion(v) for v in f[1:]] for f in entrada.filas]
        self.iteraciones = []
        self.pivotes = 0
        self.celdas_registradas = 0
        self.inicio = monotonic()
        # API 2 puede enviar una identidad con residuos de redondeo <= 1e-9.
        # Solo ajustamos las columnas de la base que ya fueron validadas.
        for i in range(1, len(self.filas)):
            j = self.columnas.index(self.filas[i][0])
            for k in range(1, len(self.filas)):
                self.filas[k][j] = Fraction(int(k == i))
            if -TOLERANCIA <= self.filas[i][-1] < 0:
                self.filas[i][-1] = Fraction(0)

    def _comprobar_limites(self, va_a_pivotear=False):
        if va_a_pivotear and self.pivotes >= self.entrada.max_iteraciones:
            raise LimiteCalculo("Se alcanzó max_iteraciones sin una clasificación final.")
        if monotonic() - self.inicio > 15:
            raise LimiteCalculo("Se alcanzó el límite de 15 segundos de cálculo.")

    def _registrar(self, fase, fila=None, columna=None, operaciones=None):
        self.celdas_registradas += len(self.filas) * len(self.columnas)
        if self.celdas_registradas > 2_000_000:
            raise LimiteCalculo("El historial excede el límite de dos millones de celdas.")
        self.iteraciones.append({
            "numero": len(self.iteraciones),
            "fase": fase,
            "variable_entrante": self.columnas[columna] if columna is not None else None,
            "variable_saliente": self.filas[fila][0] if fila is not None else None,
            "fila_pivote": fila,
            "columna_pivote": columna,
            "elemento_pivote": _numero(self.filas[fila][columna]) if fila is not None else None,
            "tabla": {"columnas": self.columnas.copy(), "filas": _tabla_json(self.filas)},
            "operaciones": list(operaciones or []),
        })

    def _canonizar_objetivo(self):
        operaciones = []
        for i in range(1, len(self.filas)):
            j = self.columnas.index(self.filas[i][0])
            factor = self.filas[0][j]
            if factor:
                for k in range(1, len(self.columnas)):
                    self.filas[0][k] -= factor * self.filas[i][k]
                operaciones.append(f"Preparación ya aplicada: F0 = F0 - ({factor}) * F{i}")
        return operaciones

    def _construir_objetivo(self, costos):
        self.filas[0] = ["Z"] + [
            -_fraccion(costos.get(nombre, 0)) for nombre in self.columnas[1:-1]
        ] + [Fraction(0)]
        return self._canonizar_objetivo()

    def _ejecutar_fase(self, fase, notas=None):
        bases_vistas = set()
        usar_bland = False
        pendientes = list(notas or [])
        while True:
            self._comprobar_limites()
            base = tuple(fila[0] for fila in self.filas[1:])
            if base in bases_vistas and not usar_bland:
                usar_bland = True
                pendientes.append("Base repetida: se activa la regla de Bland para evitar ciclos.")
            bases_vistas.add(base)
            regla = "bland" if usar_bland else "mayor_mejora"
            columna = seleccionar_columna_entrante(self.filas[0], regla)
            if columna is None:
                self._registrar(fase, operaciones=pendientes)
                return "OPTIMO"
            fila = seleccionar_fila_saliente(self.filas, columna, self.columnas)
            if fila is None:
                if fase == 1:
                    raise ErrorMotor("La función auxiliar de Fase I no debería ser no acotada; revisar tableau.")
                pendientes.append(
                    f"No acotado: la columna {self.columnas[columna]} mejora Z y no tiene coeficientes positivos."
                )
                self._registrar(fase, operaciones=pendientes)
                return "NO_ACOTADO"
            self._comprobar_limites(va_a_pivotear=True)
            nueva, operaciones = _pivotear(self.filas, self.columnas, fila, columna)
            # La tabla registrada es la ANTERIOR al pivote, donde se resalta.
            self._registrar(fase, fila, columna, pendientes + operaciones)
            self.filas = nueva
            self.pivotes += 1
            pendientes = []

    def _retirar_artificiales(self):
        artificiales = set(self.entrada.variables_artificiales)
        fila = 1
        while fila < len(self.filas):
            self._comprobar_limites()
            if self.filas[fila][0] not in artificiales:
                fila += 1
                continue
            if self.filas[fila][-1] != 0:
                raise ErrorMotor("Una artificial sigue siendo positiva al terminar Fase I.")
            bases = {f[0] for f in self.filas[1:]}
            candidatas = [
                j for j in range(1, len(self.columnas) - 1)
                if self.columnas[j] not in artificiales | bases and self.filas[fila][j] != 0
            ]
            if candidatas:
                columna = candidatas[0]
                self._comprobar_limites(va_a_pivotear=True)
                nueva, operaciones = _pivotear(self.filas, self.columnas, fila, columna)
                self._registrar(1, fila, columna, ["Retirar artificial básica de valor cero."] + operaciones)
                self.filas = nueva
                self.pivotes += 1
                fila += 1
            else:
                # Fila 0=0: no impone una restricción sobre variables reales.
                self._registrar(1, operaciones=[f"Eliminar F{fila}: restricción redundante 0 = 0."])
                del self.filas[fila]
        conservar = [j for j, nombre in enumerate(self.columnas) if nombre not in artificiales]
        self._registrar(1, operaciones=[
            "Retirar columnas artificiales: " + ", ".join(self.entrada.variables_artificiales)
        ])
        self.columnas = [self.columnas[j] for j in conservar]
        self.filas = [[fila[j] for j in conservar] for fila in self.filas]

    def resolver(self):
        entrada = self.entrada
        if entrada.fase == 1:
            costos_aux = {nombre: -1 for nombre in entrada.variables_artificiales}
            notas = ["Fase I: maximizar Z auxiliar = -suma de variables artificiales."]
            notas += self._construir_objetivo(costos_aux)
            self._ejecutar_fase(1, notas)
            if self.filas[0][-1] < 0:
                self.iteraciones[-1]["operaciones"].append(
                    "Infactible: el mínimo de la suma de artificiales es mayor que cero."
                )
                return self._resultado("INFACTIBLE")
            if self.filas[0][-1] > 0:
                raise ErrorMotor("El objetivo auxiliar tiene un valor incompatible con Fase I.")
            self._retirar_artificiales()

        if entrada.objetivo_original is not None:
            signo = 1 if entrada.tipo == "MAX" else -1
            costos = {v: signo * _fraccion(c) for v, c in entrada.objetivo_original.items()}
            notas = [
                "Fase II: reconstruir el objetivo original."
                if signo == 1 else "Fase II: resolver MIN Z como MAX (-Z)."
            ]
            notas += self._construir_objetivo(costos)
        else:
            # Compatibilidad con el JSON MAX/Fase II de cuatro campos de la guía.
            notas = self._canonizar_objetivo()
        estado = self._ejecutar_fase(2, notas)
        return self._resultado(estado)

    def _resultado(self, estado):
        solucion = {}
        valor_z = None
        if estado == "OPTIMO":
            exacta = {v: Fraction(0) for v in self.entrada.variables_decision}
            for fila in self.filas[1:]:
                if fila[0] in exacta:
                    exacta[fila[0]] = fila[-1]
            solucion = {v: _numero(valor) for v, valor in exacta.items()}
            signo = 1 if self.entrada.tipo == "MAX" else -1
            z = signo * self.filas[0][-1]
            if self.entrada.objetivo_original is not None:
                calculado = sum(
                    _fraccion(c) * exacta[v] for v, c in self.entrada.objetivo_original.items()
                )
                if calculado != z:
                    raise ErrorMotor("El objetivo final no coincide con la solución calculada.")
                z = calculado
            valor_z = _numero(z)
        return {
            "estado": estado,
            "valor_z": valor_z,
            "solucion": solucion,
            "iteraciones": self.iteraciones,
        }


def resolver_simplex(tableau):
    """Recibe un tableau preparado, no el modelo de restricciones original."""
    entrada = tableau if isinstance(tableau, TableauEntrada) else TableauEntrada.model_validate(tableau)
    return _Motor(entrada).resolver()
