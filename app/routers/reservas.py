# app/routers/reservas.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload # Para cargar relaciones eager
from typing import List
from datetime import date, datetime

from ..database.database import get_db
from ..models.models import Reserva, User, Escenario, Elemento, ReservaElemento # Importa todos los modelos necesarios
from .. import schemas
from .auth import get_current_user

router = APIRouter(
    prefix="/reservas",
    tags=["Reservas"]
)

# Helper para calcular el precio total de una reserva
async def calculate_total_price(db_reserva: Reserva, db: AsyncSession) -> int:
    total_price = 0

    # Precio base del escenario
    if db_reserva.ID_Escenario:
        escenario = await db.get(Escenario, db_reserva.ID_Escenario)
        if escenario:
            total_price += escenario.Precio
        else:
            # Esto no debería pasar si la FK es válida, pero es una buena práctica
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Escenario asociado no encontrado.")

    # Precio de los elementos
    for res_elem in db_reserva.reservas_elementos:
        elemento = await db.get(Elemento, res_elem.Codigo_Elemento)
        if elemento:
            total_price += elemento.Precio * res_elem.Cantidad
        else:
            # Manejar el caso si un elemento ya no existe (raro si hay FK)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Elemento con código {res_elem.Codigo_Elemento} no encontrado.")

    return total_price

# --- Endpoint para crear una reserva ---
@router.post("/", response_model=schemas.Reserva, status_code=status.HTTP_201_CREATED)
async def create_reserva(
    reserva_data: schemas.ReservaCreate, # Renombrado para evitar conflicto con el modelo
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Verificar si ya existe una reserva para el mismo escenario en la misma fecha
    result = await db.execute(
        select(Reserva).where(
            Reserva.ID_Escenario == reserva_data.ID_Escenario,
            Reserva.Fecha == reserva_data.Fecha
        )
    )
    existing_reserva = result.scalars().first()

    if existing_reserva:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este escenario ya está reservado para la fecha especificada."
        )

    # 2. Verificar existencia del escenario y su precio
    escenario = await db.get(Escenario, reserva_data.ID_Escenario)
    if not escenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escenario no encontrado.")

    # 3. Crear la reserva base (sin elementos aún)
    db_reserva = Reserva(
        Lugar=reserva_data.Lugar,
        # El Precio aquí es el precio base del escenario, no el total aún.
        # Puede ser el precio que viene del payload o el precio del escenario.
        # Decidí usar el precio del escenario para consistencia.
        Precio=escenario.Precio,
        Fecha=reserva_data.Fecha,
        ID_Escenario=reserva_data.ID_Escenario,
        Correo_Usuario=current_user.correo,
        Fecha_creacion=datetime.utcnow(),
        Estado="Pendiente" # Default
    )
    db.add(db_reserva)

    try:
        await db.flush() # flush para que db_reserva.ID_Reserva tenga un valor antes de los elementos

        # 4. Añadir elementos si se proporcionaron
        if reserva_data.elementos_seleccionados:
            for elem_data in reserva_data.elementos_seleccionados:
                elemento = await db.get(Elemento, elem_data.Codigo_Elemento)
                if not elemento:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Elemento con código {elem_data.Codigo_Elemento} no encontrado.")
                if elemento.Stock < elem_data.Cantidad:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stock insuficiente para el elemento '{elemento.Nombre}'. Stock disponible: {elemento.Stock}")

                # Crear entrada en la tabla intermedia
                db_reserva_elemento = ReservaElemento(
                    ID_Reserva=db_reserva.ID_Reserva,
                    Codigo_Elemento=elem_data.Codigo_Elemento,
                    Cantidad=elem_data.Cantidad
                )
                db.add(db_reserva_elemento)
                # Opcional: Reducir el stock del elemento
                # elemento.Stock -= elem_data.Cantidad


        await db.commit()
        await db.refresh(db_reserva)

        # Cargar los elementos de la reserva después del refresh
        await db.execute(select(Reserva).options(selectinload(Reserva.reservas_elementos)).where(Reserva.ID_Reserva == db_reserva.ID_Reserva))
        # Re-fetch the object to ensure relationships are loaded
        db_reserva = (await db.execute(select(Reserva).options(selectinload(Reserva.reservas_elementos).selectinload(ReservaElemento.elemento)).where(Reserva.ID_Reserva == db_reserva.ID_Reserva))).scalars().first()


        # Calcular y asignar el precio total antes de devolver la respuesta
        db_reserva.Precio_Total = await calculate_total_price(db_reserva, db)

        return db_reserva
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error de integridad al crear la reserva (ej. ID de elemento duplicado).")
    except HTTPException as e: # Captura HTTPExceptions lanzadas por validaciones internas
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al crear la reserva: {e}"
        )

# --- Endpoint para obtener las reservas de un usuario (rutas protegidas) ---
# Modificado para cargar los elementos asociados
@router.get("/me", response_model=List[schemas.Reserva])
async def get_my_reservas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Reserva)
        .options(selectinload(Reserva.reservas_elementos).selectinload(ReservaElemento.elemento)) # Carga elementos y sus detalles
        .where(Reserva.Correo_Usuario == current_user.correo)
    )
    reservas = result.scalars().unique().all() # .unique() para evitar duplicados si hay muchos elementos

    # Calcular Precio_Total para cada reserva
    for reserva in reservas:
        reserva.Precio_Total = await calculate_total_price(reserva, db)

    return list(reservas)

# --- Endpoint para obtener una reserva específica por ID_Reserva ---
# Modificado para cargar los elementos asociados
@router.get("/{reserva_id}", response_model=schemas.Reserva)
async def get_reserva_by_id(
    reserva_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Reserva)
        .options(selectinload(Reserva.reservas_elementos).selectinload(ReservaElemento.elemento)) # Carga elementos y sus detalles
        .where(
            Reserva.ID_Reserva == reserva_id,
            Reserva.Correo_Usuario == current_user.correo # Asegura que solo el dueño vea su reserva
        )
    )
    reserva = result.scalars().first()
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada o no tienes permiso para verla.")

    # Calcular Precio_Total
    reserva.Precio_Total = await calculate_total_price(reserva, db)

    return reserva

# --- NUEVOS ENDPOINTS: Añadir/Quitar Elementos a una Reserva Existente ---

@router.post("/{reserva_id}/elementos", response_model=schemas.Reserva, status_code=status.HTTP_200_OK)
async def add_elementos_to_reserva(
    reserva_id: int,
    elementos_data: List[schemas.ReservaElementoCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    reserva = await db.get(Reserva, reserva_id)
    if not reserva or reserva.Correo_Usuario != current_user.correo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada o no tienes permiso.")

    for elem_data in elementos_data:
        elemento = await db.get(Elemento, elem_data.Codigo_Elemento)
        if not elemento:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Elemento con código {elem_data.Codigo_Elemento} no encontrado.")
        if elemento.Stock < elem_data.Cantidad:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stock insuficiente para el elemento '{elemento.Nombre}'. Stock disponible: {elemento.Stock}")

        # Comprobar si ya existe para actualizar la cantidad o añadir
        existing_res_elem = (await db.execute(
            select(ReservaElemento).where(
                ReservaElemento.ID_Reserva == reserva_id,
                ReservaElemento.Codigo_Elemento == elem_data.Codigo_Elemento
            )
        )).scalars().first()

        if existing_res_elem:
            existing_res_elem.Cantidad += elem_data.Cantidad
            # Opcional: ajustar stock si se añade más
            # elemento.Stock -= elem_data.Cantidad
        else:
            db_reserva_elemento = ReservaElemento(
                ID_Reserva=reserva_id,
                Codigo_Elemento=elem_data.Codigo_Elemento,
                Cantidad=elem_data.Cantidad
            )
            db.add(db_reserva_elemento)
            # Opcional: reducir stock
            # elemento.Stock -= elem_data.Cantidad
    try:
        await db.commit()
        await db.refresh(reserva)

        # Recargar la reserva con los elementos
        reserva_updated = (await db.execute(select(Reserva).options(selectinload(Reserva.reservas_elementos).selectinload(ReservaElemento.elemento)).where(Reserva.ID_Reserva == reserva_id))).scalars().first()

        # Calcular y devolver el precio total actualizado
        reserva_updated.Precio_Total = await calculate_total_price(reserva_updated, db)
        return reserva_updated
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al añadir elementos a la reserva: {e}")

@router.delete("/{reserva_id}/elementos/{codigo_elemento}", status_code=status.HTTP_200_OK)
async def remove_elemento_from_reserva(
    reserva_id: int,
    codigo_elemento: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    reserva = await db.get(Reserva, reserva_id)
    if not reserva or reserva.Correo_Usuario != current_user.correo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada o no tienes permiso.")

    reserva_elemento = (await db.execute(
        select(ReservaElemento).where(
            ReservaElemento.ID_Reserva == reserva_id,
            ReservaElemento.Codigo_Elemento == codigo_elemento
        )
    )).scalars().first()

    if not reserva_elemento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El elemento no está asociado a esta reserva.")

    try:
        # Opcional: Devolver el stock del elemento
        # elemento = await db.get(Elemento, codigo_elemento)
        # if elemento:
        #     elemento.Stock += reserva_elemento.Cantidad

        await db.delete(reserva_elemento)
        await db.commit()
        await db.refresh(reserva)

        # Recargar la reserva con los elementos
        reserva_updated = (await db.execute(select(Reserva).options(selectinload(Reserva.reservas_elementos).selectinload(ReservaElemento.elemento)).where(Reserva.ID_Reserva == reserva_id))).scalars().first()

        # Calcular y devolver el precio total actualizado
        reserva_updated.Precio_Total = await calculate_total_price(reserva_updated, db)
        return reserva_updated
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al eliminar elemento de la reserva: {e}")