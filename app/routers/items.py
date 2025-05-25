# app/routers/items.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..database.database import get_db
from ..models.models import Item # Importa el modelo de Item
from .. import schemas # Importa tus esquemas

# --- Importar get_current_user para proteger rutas (si los items son de usuarios logueados) ---
# Si quieres que las rutas de items estén protegidas, descomenta la siguiente línea:
# from .auth import get_current_user

# --- Crear el router para items ---
router = APIRouter(
    prefix="/items", # Todas las rutas aquí tendrán /items como prefijo
    tags=["Items"] # Para la documentación en Swagger UI
)

# --- Endpoint para crear un item ---
# Si quieres proteger esta ruta, añade Depends(get_current_user)
@router.post("/", response_model=schemas.Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: schemas.ItemCreate, db: AsyncSession = Depends(get_db)):
    db_item = Item(**item.model_dump()) # Usa .model_dump() para Pydantic v2
    # Aquí es donde se elimina el 'async with db as session:'
    # y se usa 'db' directamente, ya que Depends(get_db) lo maneja.
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

# --- Endpoint para obtener un item por ID ---
@router.get("/{item_id}", response_model=schemas.Item)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    # Aquí también se elimina el 'async with db as session:'
    # y se usa 'db' directamente.
    db_item = await db.get(Item, item_id)
    if db_item:
        return db_item
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")

# --- Endpoint para obtener todos los items ---
@router.get("/", response_model=List[schemas.Item])
async def read_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Aquí también se elimina el 'async with db as session:'
    # y se usa 'db' directamente.
    result = await db.execute(select(Item).offset(skip).limit(limit))
    items = result.scalars().all()
    return list(items)