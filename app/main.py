# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status # Añadimos status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select # Necesario para crear tablas
from dotenv import load_dotenv
import os
# --- Importar Base de modelos (necesario para la creación de tablas) ---
from .models.models import Base

# --- Importar los routers ---
from .routers import auth
from .routers import users
from .routers import items 
from .routers import reservas
from .routers import escenarios
from .routers import elementos
# Cargar variables de entorno al inicio de la aplicación
load_dotenv()

# --- Configuración de la base de datos ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está configurada.")

engine = create_async_engine(DATABASE_URL, echo=True)

# Crea una sesión de base de datos asíncrona
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependencia para obtener la sesión de DB
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# --- Instancia de FastAPI ---
app = FastAPI(
    title="Tu API Juana",
    description="Una API para gestionar usuarios, reservas e items.",
    version="0.0.1",
)

# --- Evento de inicio: Crear tablas de la base de datos ---
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Base de datos inicializada y tablas creadas (si no existían).")

# --- Incluir los routers ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router) 
app.include_router(reservas.router)
app.include_router(escenarios.router)
app.include_router(elementos.router)
# --- Ruta raíz ---
@app.get("/")
async def root():
    return {"message": "Bienvenido a la API de Juana! Visita /docs para la documentación."}