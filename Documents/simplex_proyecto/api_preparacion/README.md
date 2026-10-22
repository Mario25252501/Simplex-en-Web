
#  INTEGRANTE 2

## Proyecto
Sistema web para resolver programación lineal
mediante el método símplex.

Universidad Mariano Gálvez
Curso: Investigación de Operaciones

## Responsabilidad
Preparación matemática y construcción del tableau inicial.

## Tecnología
- Python
- FastAPI
- Pydantic
- Uvicorn

## Dirección local
http://127.0.0.1:8001

## Endpoint principal
POST /preparar

## Entrada JSON

{
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
  "no_negatividad": true
}

## Respuesta JSON

{
  "mensaje": "Tableau inicial generado correctamente",
  "tipo": "MAX",
  "fase": 2,
  "columnas": [
    "Base", "a", "b", "h1", "h2", "Solución"
  ],
  "filas": [
    ["Z", -3, -5, 0, 0, 0],
    ["h1", 1, 0, 1, 0, 4],
    ["h2", 0, 2, 0, 1, 12]
  ],
  "variables_basicas": ["h1", "h2"],
  "variables_artificiales": [],
  "requiere_fase1": false,
  "objetivo_original": [3, 5],
  "objetivo_auxiliar": null,
  "estado_preparacion": "tableau_inicial_completo",
  "objetivo_fase2": ["Z", -3, -5, 0, 0, 0],
  "tipo_optimizacion_original": "max",
  "factor_recuperacion_z": 1
}

## Reglas de funcionamiento

1. Se permiten entre 2 y 6 variables.
2. Las variables se denominan a, b, c, d, e, f.
3. Se admiten maximización y minimización.
4. Se admiten restricciones <=, >= y =.
5. Se normalizan términos independientes negativos.
6. Se generan variables de holgura, exceso y artificiales.
7. Se identifica cuándo se necesita la Fase I.
8. Se conserva la función objetivo original para la Fase II.
9. La API no ejecuta las iteraciones del método símplex.

## Interpretación del tableau

- La primera columna identifica la variable básica.
- La última columna contiene el término independiente.
- La primera fila representa la función objetivo.
- La Fase I utiliza P = -suma(artificiales).
- La Fase II utiliza una maximización equivalente.
- Las variables artificiales deben retirarse al
  terminar la Fase I, según el estado de la base.
- La fila objetivo de Fase II es preliminar:
  el motor debe ajustarla a la base resultante.

## Convención del motor

- Se utiliza la convención de maximización.
- Los coeficientes negativos de la fila objetivo
  indican candidatos a variable entrante.
- El motor debe aplicar pruebas de razón y pivoteo.
- Debe detectar optimalidad, infactibilidad y
  ausencia de solución acotada.
- Debe conservar todas las iteraciones para mostrarlas.

## Códigos HTTP

200: Preparación realizada correctamente.
422: Modelo inválido o inconsistente.
500: Error interno inesperado.

## Integración

La API de coordinación debe enviar el modelo
mediante POST /preparar.

La respuesta será utilizada por la API del motor
para ejecutar el método símplex.

El formato debe acordarse con el Integrante 3
antes de la integración final.
