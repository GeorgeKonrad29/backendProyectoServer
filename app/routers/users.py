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

@router.put("/me", response_model=schemas.User)
async def update_user_me(
    user_update: schemas.UserUpdate, # Usamos el nuevo esquema UserUpdate
    current_user: User = Depends(get_current_user), # El usuario actual que está haciendo la solicitud
    db: AsyncSession = Depends(get_db)
):
    # No se permite cambiar el correo aquí ya que es la clave primaria.
    # No se permite cambiar el rango, intentos_login, bloqueado, fecha_creacion, ultimo_login.

    # Itera sobre los campos proporcionados en user_update
    for field, value in user_update.model_dump(exclude_unset=True).items():
        # exclude_unset=True asegura que solo se actualicen los campos que realmente se enviaron
        setattr(current_user, field, value)

    try:
        await db.commit()
        await db.refresh(current_user) # Refresca el objeto current_user con los datos actualizados de la DB
        return current_user
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar el usuario: {e}")
@router.put("/{user_email}/admin_update", response_model=schemas.User)
async def admin_update_user(
    user_email: str, # El correo del usuario a modificar
    user_admin_update: schemas.UserAdminUpdate, # Los campos a actualizar (rango, bloqueado)
    current_user: User = Depends(get_current_user), # El administrador que hace la solicitud
    db: AsyncSession = Depends(get_db)
):
    # 1. Verificar que el usuario actual es un administrador
    if current_user.rango != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción. Se requiere rol de administrador."
        )

    # 2. Buscar el usuario a modificar
    user_to_update = await db.get(User, user_email)
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # 3. Evitar que un administrador se cambie a sí mismo si no es el super-admin (opcional)
    # Por seguridad, un admin no debería poder degradarse o bloquearse a sí mismo accidentalmente
    if user_to_update.correo == current_user.correo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes modificar tu propio rango o estado de bloqueo a través de esta ruta de administración. Usa /users/me para tus propios datos."
        )

    # 4. Actualizar los campos especificados por el administrador
    for field, value in user_admin_update.model_dump(exclude_unset=True).items():
        # Validar los valores del rango para evitar rangos inválidos
        if field == "rango" and value not in ["usuario", "administrador"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rango '{value}' no válido. Los rangos permitidos son 'usuario' y 'administrador'."
            )
        setattr(user_to_update, field, value)

    try:
        await db.commit()
        await db.refresh(user_to_update) # Refresca el objeto con los datos actualizados
        return user_to_update
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar el usuario: {e}")


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