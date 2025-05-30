# app/routers/elementos.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import datetime

from ..database.database import get_db
from ..models.models import Elemento, User # Importa el modelo Elemento y User
from .. import schemas
from .auth import get_current_user # Para proteger las rutas (ej. solo administradores)

router = APIRouter(
    prefix="/elementos",
    tags=["Elementos"]
)

# --- Endpoint para crear un elemento (protegido, por ejemplo, para admins) ---
@router.post("/", response_model=schemas.Elemento, status_code=status.HTTP_201_CREATED)
async def create_elemento(
    elemento: schemas.ElementoCreate,
    current_user: User = Depends(get_current_user), # Requiere autenticación
    db: AsyncSession = Depends(get_db)
):
    #Chequeo de rol de administrador
    if current_user.rango != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden crear elementos.")

    db_elemento = Elemento(
        **elemento.model_dump(),
        Fecha_creacion=datetime.utcnow()
    )
    db.add(db_elemento)
    try:
        await db.commit()
        await db.refresh(db_elemento)
        return db_elemento
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el elemento: {e}")

# --- Endpoint para obtener todos los elementos ---
@router.get("/", response_model=List[schemas.Elemento])
async def read_elementos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Elemento).offset(skip).limit(limit))
    elementos = result.scalars().all()
    return list(elementos)

# --- Endpoint para obtener un elemento por Codigo ---
@router.get("/{codigo_elemento}", response_model=schemas.Elemento)
async def read_elemento(
    codigo_elemento: int,
    db: AsyncSession = Depends(get_db)
):
    elemento = await db.get(Elemento, codigo_elemento)
    if elemento:
        return elemento
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento no encontrado")

# --- Endpoint para actualizar un elemento (protegido) ---
@router.put("/{codigo_elemento}", response_model=schemas.Elemento)
async def update_elemento(
    codigo_elemento: int,
    elemento_update: schemas.ElementoUpdate,
    current_user: User = Depends(get_current_user), # Requiere autenticación
    db: AsyncSession = Depends(get_db)
):
    #Chequeo de rol de administrador
    if current_user.rango != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden actualizar elementos.")

    db_elemento = await db.get(Elemento, codigo_elemento)
    if not db_elemento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento no encontrado")

    for key, value in elemento_update.model_dump(exclude_unset=True).items():
        setattr(db_elemento, key, value)

    await db.commit()
    await db.refresh(db_elemento)
    return db_elemento

# --- Endpoint para eliminar un elemento (protegido) ---
@router.delete("/{codigo_elemento}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_elemento(
    codigo_elemento: int,
    current_user: User = Depends(get_current_user), # Requiere autenticación
    db: AsyncSession = Depends(get_db)
):
    # Chequeo de rol de administrador
    if current_user.rango != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden eliminar elementos.")

    db_elemento = await db.get(Elemento, codigo_elemento)
    if not db_elemento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento no encontrado")

    await db.delete(db_elemento)
    await db.commit()
    return {"message": "Elemento eliminado exitosamente"}