# app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime # Necesario para fecha_creacion

from ..database.database import get_db
from ..models.models import User # Importa el modelo de usuario
from .. import schemas # Importa tus esquemas

# --- Hashing de Contraseñas (copiado de main.py, idealmente en un modulo 'security.py') ---
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- Importar get_current_user desde auth.py para proteger rutas ---
from .auth import get_current_user

# --- Crear el router para usuarios ---
router = APIRouter(
    prefix="/users", # Todas las rutas aquí tendrán /users como prefijo
    tags=["Users"] # Para la documentación en Swagger UI
)

# --- Endpoint para crear usuarios (signup) ---
@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.contrasenia)

    db_user = User(
        correo=user.correo,
        nombres=user.nombres,
        apellidos=user.apellidos,
        contrasenia=hashed_password, # <--- Asegúrate que tu modelo User.contrasenia almacene el hash
        rango="usuario",
        intentos_login=0,
        bloqueado=False,
        fecha_creacion=datetime.utcnow()
    )
    async with db as session: # Envuelve en un async with session
        session.add(db_user)
        try:
            await session.commit()
            await session.refresh(db_user)
            return db_user
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo electrónico ya está registrado.")
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el usuario: {e}")

# --- Endpoint para obtener el usuario actual (ruta protegida) ---
@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # get_current_user ya devuelve el objeto User completo, así que solo lo retornamos
    return current_user

# --- Opcional: Obtener un usuario por ID (ejemplo de ruta) ---
@router.get("/{user_id}", response_model=schemas.User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    async with db as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

# --- Opcional: Obtener todos los usuarios (ejemplo de ruta, requiere autenticación de administrador) ---
@router.get("/", response_model=List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    async with db as session:
        result = await session.execute(
            select(User).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        return users