
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from preparacion import construir_tableau_inicial
# Crear nuestra API independiente
app = FastAPI(
    title="API de Preparación - Método Simplex",
    description="Parte Carlos Arenas",
    version="1.0.0"
)

# Ruta principal para comprobar que la API funciona
@app.get("/")
def inicio():
    return {
        "mensaje": "API de Preparación Simplex",
        "modulo": "Preparación matemática y tableau inicial",
}
# Estructura de cada restricción matemática
class Restriccion(BaseModel):
    coeficientes: list[float]
    signo: Literal["<=", ">=", "="]
    termino_independiente: float


# Estructura del modelo que recibirá nuestra API
class ModeloSimplex(BaseModel):
    tipo_optimizacion: Literal["max", "min"]
    variables: int = Field(ge=2, le=6)
    coeficientes_objetivo: list[float]
    restricciones: list[Restriccion] = Field(min_length=1)
    no_negatividad: Literal[True]
    
    @model_validator(mode="after")
    def validar_dimensiones(self):

        # Comprobar cantidad de coeficientes de Z
        if len(self.coeficientes_objetivo) != self.variables:
            raise ValueError(
                "La cantidad de coeficientes de Z "
                "no coincide con el número de variables"
            )

        # Comprobar las restricciones
        for i, restriccion in enumerate(self.restricciones, 1):

            if len(restriccion.coeficientes) != self.variables:
                raise ValueError(
                    f"Restricción {i}: cantidad incorrecta "
                    "de coeficientes"
                )

        

        return self



# Endpoint de preparación matemática
@app.post("/preparar")
def preparar_modelo(modelo: ModeloSimplex):
    try:
        resultado = construir_tableau_inicial(modelo)
        return {
            "mensaje": "Tableau inicial generado correctamente",
            **resultado
        }

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error
