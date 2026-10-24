"""Servidor independiente. Ejecutar desde la carpeta PADRE de api_motor:

python -m uvicorn api_motor.main:app --reload --port 8002
"""

from fastapi import FastAPI, HTTPException

from .esquemas import ResultadoSimplex, TableauEntrada
from .motor_simplex import ErrorMotor, LimiteCalculo, resolver_simplex

app = FastAPI(
    title="API Motor Simplex",
    description="Recibe un tableau de API 2 y devuelve iteraciones y resultado a API 4.",
    version="1.0.0",
)


@app.get("/salud")
def comprobar_salud():
    return {"estado": "activo", "servicio": "motor_simplex", "integrante": 3}


@app.post("/validar-tableau")
def validar_tableau(datos: TableauEntrada):
    return {"mensaje": "Tabla validada; lista para /resolver", "tabla": datos.model_dump()}


@app.post("/resolver", response_model=ResultadoSimplex)
def resolver(datos: TableauEntrada):
    """200 incluye OPTIMO, INFACTIBLE y NO_ACOTADO; 422 indica entrada inválida.

    Un límite de cálculo responde 409: nunca se inventa un estado matemático.
    """
    try:
        return resolver_simplex(datos)
    except LimiteCalculo as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ErrorMotor as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
