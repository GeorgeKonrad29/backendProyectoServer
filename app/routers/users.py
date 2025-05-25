# app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime
from pydantic import EmailStr
from ..database.database import get_db
from ..models.models import User
from .. import schemas
from ..security import get_password_hash # Importa get_password_hash desde security.py

from .auth import get_current_user # Importa get_current_user desde auth.py para proteger rutas

# --- Crear el router para usuarios ---
router = APIRouter(
    prefix="/signup", # Todas las rutas aquí tendrán /users como prefijo
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
        contrasenia=hashed_password,
        rango="usuario",
        intentos_login=0,
        bloqueado=False,
        fecha_creacion=datetime.utcnow()
    )
    # Aquí es donde se elimina el 'async with db as session:'
    # y se usa 'db' directamente, ya que Depends(get_db) lo maneja.
    db.add(db_user)
    try:
        await db.commit() # Confirma la transacción y guarda el usuario
        await db.refresh(db_user) # Refresca el objeto db_user para obtener el ID generado
        return db_user
    except IntegrityError:
        await db.rollback() # Si hay un error, revierte la transacción
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo electrónico ya está registrado.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el usuario: {e}")

# --- Endpoint para obtener el usuario actual (ruta protegida) ---
@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # get_current_user ya devuelve el objeto User completo, así que solo lo retornamos
    return current_user

# --- Opcional: Obtener un usuario por ID (ejemplo de ruta) ---
@router.get("/{user_correo}", response_model=schemas.User) # Ruta para buscar por correo
async def read_user(user_correo: EmailStr, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.correo == user_correo)) # Buscar por correo
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

# --- Opcional: Obtener todos los usuarios (ejemplo de ruta, requiere autenticación de administrador) ---
@router.get("/", response_model=List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Aquí también se elimina el 'async with db as session:'
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users