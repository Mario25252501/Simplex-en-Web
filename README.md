# Sistema web del método símplex

**Grupo No. 5 · Investigación de Operaciones · Universidad Mariano Gálvez**

Sistema web que resuelve problemas de programación lineal con el **método símplex** y muestra el procedimiento completo, tabla por tabla, con el pivote resaltado.

## Qué hace

- Maximización y minimización.
- Restricciones `≤`, `≥` y `=`.
- De 2 a 6 variables de decisión (a, b, c, d, e, f), todas mayores o iguales a cero.
- Método de dos fases cuando se necesita (Fase I y Fase II).
- Detecta si la solución es **óptima**, **infactible** o **no acotada**.
- Guarda cada problema y cada iteración en MySQL, con un historial de problemas resueltos.

## Integrantes y responsabilidades

| Integrante | Nombre | Responsabilidad |
|---|---|---|
| 1 | Jasson Maziegos | **Formulario (frontend de captura).** Pantalla donde se elige maximizar o minimizar, el número de variables, la función objetivo y las restricciones. Valida los datos, muestra la vista previa matemática y genera el JSON del modelo. |
| 2 | Carlos Arenas | **API de preparación** (puerto 8001). Recibe el modelo y construye la tabla inicial del símplex: variables de holgura, exceso y artificiales, y la preparación para las fases. Endpoint `POST /preparar`. |
| 3 | Jelson Sicay | **Motor del símplex / API del motor** (puerto 8002). Ejecuta las iteraciones de las fases I y II, elige el pivote, aplica las operaciones de fila y determina si el resultado es óptimo, infactible o no acotado. Endpoint `POST /resolver`. |
| 4 | Mario Chávez | **Base de datos, API de datos e integración.** Base `simplex_db` en MySQL (6 tablas), API de datos (puerto 8000) que coordina a las otras dos APIs y guarda todo, pantalla de resultados con historial, pruebas integrales y documentación. |

### Detalle de la parte del Integrante 4

- Script reproducible `base_datos/simplex_db.sql`.
- API de datos con FastAPI y SQLAlchemy: guarda problemas, llama a la preparación y al motor, y devuelve el resultado.
- Pantalla `resultados.html`: historial, resumen (estado, valor de Z, solución) y navegación iteración por iteración con el pivote resaltado.
- Integración del formulario con las tres APIs.
- Pruebas, capturas y manuales.

## Arquitectura

```
Navegador (formulario y resultados)
        │
        ▼
API de datos  :8000  ──►  MySQL (simplex_db)
   │        │
   ▼        ▼
Preparación  Motor
   :8001      :8002
```

El navegador solo habla con la API de datos. Esta llama a la API de preparación, luego al motor, y guarda el resultado en MySQL.

## Estructura del repositorio

```
api_datos/        API de datos (Integrante 4)
api_preparacion/  API de preparación (Integrante 2)
api_motor/        Motor y API del motor (Integrante 3)
base_datos/       Script SQL de la base de datos (Integrante 4)
frontend/         Formulario (Integrante 1) y resultados (Integrante 4)
requirements.txt  Dependencias de Python
```

## Requisitos

- Python 3.10 o superior
- MySQL 8
- Conexión a internet al abrir la página (Bootstrap y la tipografía se cargan por CDN)

## Instalación y ejecución

**1. Base de datos.** Importa el script en MySQL (Workbench o terminal):

```bash
mysql -u root -p < base_datos/simplex_db.sql
```

**2. Entorno virtual y dependencias** (desde la raíz del proyecto):

```bash
python -m venv venv
venv\Scripts\activate          # en Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

**3. Archivo `.env`.** Crea `api_datos/.env` con tu usuario y contraseña de MySQL (este archivo no se sube a GitHub):

```
DATABASE_URL=mysql+pymysql://root:TU_CONTRASEÑA@localhost:3306/simplex_db
```

**4. Levanta las tres APIs**, cada una en su propia terminal:

```bash
# API de preparación (puerto 8001)
cd api_preparacion
python -m uvicorn main:app --reload --port 8001

# API del motor (puerto 8002) — desde la raíz del proyecto
python -m uvicorn api_motor.main:app --reload --port 8002

# API de datos (puerto 8000)
cd api_datos
python -m uvicorn main:app --reload --port 8000
```

**5. Abre la aplicación:**

- Formulario: <http://localhost:8000/app/index.html>
- Resultados e historial: <http://localhost:8000/app/resultados.html>
- Documentación de la API de datos: <http://localhost:8000/docs>

## Cómo se usa

1. En el formulario, elige maximizar o minimizar y el número de variables.
2. Escribe los coeficientes de Z y agrega las restricciones.
3. Pulsa **Resolver y ver resultados** y escribe un nombre para el problema.
4. En la pantalla de resultados navega con **Anterior** y **Siguiente**. El pivote aparece resaltado en cada tabla.

## Endpoints de la API de datos

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/problemas` | Guarda un modelo nuevo |
| GET | `/problemas` | Lista el historial |
| GET | `/problemas/{id}` | Devuelve un modelo guardado |
| POST | `/problemas/{id}/resolver` | Prepara, resuelve y guarda las iteraciones |
| GET | `/problemas/{id}/resultado` | Devuelve el resultado y todas las tablas |

## Tecnologías

Python · FastAPI · Uvicorn · SQLAlchemy · PyMySQL · httpx · MySQL 8 · HTML · CSS · JavaScript · Bootstrap 5

## Seguridad

Las contraseñas van solo en `.env`, que está en `.gitignore`. No subas ese archivo al repositorio.
