import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Esto encuentra la ruta exacta de la carpeta actual y busca el .env ahí sin importar desde dónde corras la terminal
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

URL = os.getenv("DATABASE_URL")

engine = create_engine(URL)
SessionLocal = sessionmaker(bind=engine)