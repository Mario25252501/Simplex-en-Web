"""Contrato JSON y validaciones previas a los cálculos."""

import math
from typing import Literal

from pydantic import (
    BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr,
    model_validator,
)

from .adaptador import adaptar_entrada

TOLERANCIA = 1e-9
Celda = StrictStr | StrictInt | StrictFloat

EJEMPLO_MAX = {
    "tipo": "MAX", "fase": 2,
    "objetivo_original": {"a": 3, "b": 5},
    "columnas": ["Base", "a", "b", "h1", "h2", "h3", "Solución"],
    "filas": [
        ["Z", -3, -5, 0, 0, 0, 0],
        ["h1", 1, 0, 1, 0, 0, 4],
        ["h2", 0, 1, 0, 1, 0, 6],
        ["h3", 3, 2, 0, 0, 1, 18],
    ],
}


class TableauEntrada(BaseModel):
    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False,
        json_schema_extra={"examples": [EJEMPLO_MAX]},
    )

    tipo: Literal["MAX", "MIN"]
    fase: Literal[1, 2] = 2
    columnas: list[StrictStr] = Field(min_length=4, max_length=128)
    filas: list[list[Celda]] = Field(min_length=1, max_length=61)
    objetivo_original: dict[str, StrictInt | StrictFloat] | list[StrictInt | StrictFloat] | None = Field(
        default=None,
        description="Lista en el orden de las columnas a-f de API 2, o diccionario por variable. Se normaliza a diccionario.",
    )
    variables_decision: list[StrictStr] | None = None
    variables_artificiales: list[StrictStr] = Field(default_factory=list)
    requiere_fase1: bool | None = None
    max_iteraciones: int = Field(default=500, ge=1, le=1000, strict=True)
    # Metadatos que entrega la rama real api-preparacion.
    mensaje: str | None = None
    variables_basicas: list[StrictStr] | None = None
    objetivo_auxiliar: str | None = None
    estado_preparacion: str | None = None
    objetivo_fase2: list[Celda] | None = None
    tipo_optimizacion_original: Literal["max", "min"] | None = None
    factor_recuperacion_z: StrictInt | None = None
    restricciones_redundantes: list[StrictInt] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def adaptar(cls, datos):
        return adaptar_entrada(datos)

    @model_validator(mode="after")
    def validar_tableau(self) -> "TableauEntrada":
        columnas = self.columnas
        if columnas[0] != "Base" or columnas[-1] not in ("Solución", "Solucion"):
            raise ValueError("La primera columna debe ser Base y la última Solución.")
        if any(not nombre.strip() for nombre in columnas):
            raise ValueError("Los nombres de las columnas no pueden estar vacíos.")
        if len(set(columnas)) != len(columnas):
            raise ValueError("Hay nombres de columnas repetidos.")
        nombres = columnas[1:-1]
        if "Z" in nombres:
            raise ValueError("Z está reservado para la fila objetivo.")
        if self.filas[0][0:1] != ["Z"]:
            raise ValueError("La fila 0 debe comenzar con Z, incluso en Fase I.")

        for i, fila in enumerate(self.filas):
            if len(fila) != len(columnas):
                raise ValueError(f"La fila {i} no coincide con la cantidad de columnas.")
            if not isinstance(fila[0], str):
                raise ValueError(f"La fila {i} debe empezar con su nombre de base.")
            for valor in fila[1:]:
                if type(valor) not in (int, float):
                    raise ValueError(f"La fila {i} contiene un coeficiente no numérico.")
                if abs(valor) > 1e12 or not math.isfinite(valor):
                    raise ValueError("Los coeficientes deben ser finitos y de magnitud <= 1e12.")
            if i and fila[-1] < -TOLERANCIA:
                raise ValueError(
                    f"La fila {i} tiene RHS negativo. API 2 debe normalizarla y preparar una base factible."
                )

        bases = [fila[0] for fila in self.filas[1:]]
        if len(set(bases)) != len(bases) or any(b not in nombres for b in bases):
            raise ValueError("Cada fila debe tener una variable básica única presente en columnas.")
        if self.variables_basicas is not None and self.variables_basicas != bases:
            raise ValueError("variables_basicas no coincide con los nombres de las filas.")
        # Una base inicial debe formar una matriz identidad en las restricciones.
        for i, base in enumerate(bases, start=1):
            j = columnas.index(base)
            for k in range(1, len(self.filas)):
                esperado = 1 if i == k else 0
                if abs(self.filas[k][j] - esperado) > TOLERANCIA:
                    raise ValueError(f"La columna básica {base} no forma una columna de identidad.")

        decision = self.variables_decision
        if decision is None:
            decision = [v for v in nombres if v in tuple("abcdef")]
            self.variables_decision = decision
        if not 2 <= len(decision) <= 6 or len(set(decision)) != len(decision):
            raise ValueError("Debe haber entre 2 y 6 variables de decisión distintas.")
        if any(v not in tuple("abcdef") or v not in nombres for v in decision):
            raise ValueError("Las variables de decisión deben llamarse a, b, c, d, e o f y existir en columnas.")
        if set(decision) != {v for v in nombres if v in tuple("abcdef")}:
            raise ValueError("variables_decision debe incluir todas las columnas a-f del tableau.")

        artificiales = self.variables_artificiales
        if len(set(artificiales)) != len(artificiales):
            raise ValueError("Hay variables artificiales repetidas.")
        if any(v not in nombres or v in decision for v in artificiales):
            raise ValueError("Las artificiales deben existir en columnas y no ser variables de decisión.")
        if self.fase == 1 and not artificiales:
            raise ValueError("Fase I necesita la lista explícita variables_artificiales.")
        if self.fase == 2 and artificiales:
            raise ValueError("Un tableau de Fase II no debe conservar variables artificiales.")
        if self.requiere_fase1 is not None and self.requiere_fase1 != (self.fase == 1):
            raise ValueError("requiere_fase1 debe coincidir con fase.")

        objetivo = self.objetivo_original
        if objetivo is None and (self.fase == 1 or self.tipo == "MIN"):
            raise ValueError("Fase I y MIN requieren objetivo_original para reconstruir el objetivo.")
        if objetivo is not None:
            if set(objetivo) != set(decision):
                raise ValueError("objetivo_original debe contener exactamente las variables de decisión.")
            if any(abs(v) > 1e12 or not math.isfinite(v) for v in objetivo.values()):
                raise ValueError("El objetivo debe contener coeficientes finitos de magnitud <= 1e12.")
        if self.tipo_optimizacion_original is not None and self.tipo_optimizacion_original.upper() != self.tipo:
            raise ValueError("tipo_optimizacion_original no coincide con tipo.")
        factor = 1 if self.tipo == "MAX" else -1
        if self.factor_recuperacion_z is not None and self.factor_recuperacion_z != factor:
            raise ValueError("factor_recuperacion_z debe ser 1 para MAX o -1 para MIN.")
        if self.objetivo_fase2 is not None:
            fila = self.objetivo_fase2
            if len(fila) != len(columnas) or fila[0:1] != ["Z"]:
                raise ValueError("objetivo_fase2 debe ser una fila Z del ancho del tableau.")
            if any(type(v) not in (int, float) or abs(v) > 1e12 or not math.isfinite(v) for v in fila[1:]):
                raise ValueError("objetivo_fase2 contiene coeficientes inválidos.")
            if objetivo is not None:
                esperado = [-factor * objetivo.get(v, 0) for v in nombres] + [0]
                if any(abs(a - b) > TOLERANCIA for a, b in zip(fila[1:], esperado)):
                    raise ValueError("objetivo_fase2 no coincide con objetivo_original y tipo.")
        return self


class TablaSalida(BaseModel):
    columnas: list[str]
    filas: list[list[str | float]]


class IteracionSalida(BaseModel):
    numero: int
    fase: Literal[1, 2]
    variable_entrante: str | None
    variable_saliente: str | None
    fila_pivote: int | None
    columna_pivote: int | None
    elemento_pivote: float | None
    tabla: TablaSalida
    operaciones: list[str]


class ResultadoSimplex(BaseModel):
    estado: Literal["OPTIMO", "INFACTIBLE", "NO_ACOTADO"]
    valor_z: float | None
    solucion: dict[str, float]
    iteraciones: list[IteracionSalida]
