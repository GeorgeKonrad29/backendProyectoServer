# app/routers/escenarios.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime

from ..database.database import get_db
from ..models.models import Escenario, User # Importa el modelo Escenario y User
from .. import schemas
from .auth import get_current_user # Para proteger las rutas

router = APIRouter(
    prefix="/escenarios",
    tags=["Escenarios"]
)

# --- Endpoint para crear un escenario (protegido, por ejemplo, para admins) ---
@router.post("/", response_model=schemas.Escenario, status_code=status.HTTP_201_CREATED)
async def create_escenario(
    escenario: schemas.EscenarioCreate,
    current_user: User = Depends(get_current_user), # Requiere autenticación
    db: AsyncSession = Depends(get_db)
):
    # Opcional: Aquí puedes añadir lógica para verificar si current_user.rango es "administrador"
    if current_user.rango != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden crear escenarios.")

    db_escenario = Escenario(
        **escenario.model_dump(),
        Fecha_creacion=datetime.utcnow()
    )
    db.add(db_escenario)
    try:
        await db.commit()
        await db.refresh(db_escenario)
        return db_escenario
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el escenario: {e}")

# --- Endpoint para obtener todos los escenarios ---
@router.get("/", response_model=List[schemas.Escenario])
async def read_escenarios(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Escenario).offset(skip).limit(limit))
    escenarios = result.scalars().all()
    return list(escenarios)

# --- Endpoint para obtener un escenario por ID ---
@router.get("/{escenario_id}", response_model=schemas.Escenario)
async def read_escenario(
    escenario_id: int,
    db: AsyncSession = Depends(get_db)
):
    escenario = await db.get(Escenario, escenario_id)
    if escenario:
        return escenario
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escenario no encontrado")

# --- Endpoint para actualizar un escenario (protegido) ---
@router.put("/{escenario_id}", response_model=schemas.Escenario)
async def update_escenario(
    escenario_id: int,
    escenario_update: schemas.EscenarioUpdate,
    current_user: User = Depends(get_current_user), # Requiere autenticación
    db: AsyncSession = Depends(get_db)
):
    #Chequeo de rol de administrador
    if current_user.rango != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden actualizar escenarios.")

    db_escenario = await db.get(Escenario, escenario_id)
    if not db_escenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escenario no encontrado")

    # Actualizar los campos
    for key, value in escenario_update.model_dump(exclude_unset=True).items():
        setattr(db_escenario, key, value)

    await db.commit()
    await db.refresh(db_escenario)
    return db_escenario

# --- Endpoint para eliminar un escenario (protegido) ---
@router.delete("/{escenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_escenario(
    escenario_id: int,
    current_user: User = Depends(get_current_user), # Requiere autenticación
    db: AsyncSession = Depends(get_db)
):
    #Chequeo de rol de administrador
    if current_user.rango != "administrador":
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo los administradores pueden eliminar escenarios.")

    db_escenario = await db.get(Escenario, escenario_id)
    if not db_escenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escenario no encontrado")

    await db.delete(db_escenario)
    await db.commit()
    return {"message": "Escenario eliminado exitosamente"}