# app/schemas.py

from pydantic import BaseModel, EmailStr, Field # Asegúrate de importar EmailStr
from datetime import datetime, date
from typing import Optional, List # Para campos opcionales si los usas


# Schemas base para reusabilidad
#class ItemBase(BaseModel):
#    nombre: str
#    descripcion: Optional[str] = None
#    precio: float

#class ItemCreate(ItemBase):
#    pass

#class Item(ItemBase):
#    id: int
#    propietario_id: Optional[int] = None # Si los items tienen propietario
#    class Config:
#        from_attributes = True # O from_orm = True para Pydantic v1. Para Pydantic v2, es 'from_attributes = True'

class UserBase(BaseModel):
    correo: EmailStr # Usa EmailStr para validación de correo
    nombres: str
    apellidos: str

class UserCreate(UserBase):
    contrasenia: str

class UserUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None 
       
class UserAdminUpdate(BaseModel):
    bloqueado: Optional[bool] = None # Corresponde a tu campo 'bloqueado'

class User(UserBase):
    rango: str
    intentos_login: int
    bloqueado: bool
    fecha_creacion: datetime
    ultimo_login: Optional[datetime] = None
    # items: List[Item] = [] # Si un usuario puede tener items
    class Config:
        from_attributes = True # O from_orm = True para Pydantic v1

# Nuevo esquema para la respuesta del Token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    correo: Optional[str] = None

# --- NUEVOS ESQUEMAS: Elemento ---
class ElementoBase(BaseModel):
    Nombre: str
    Precio: int
    Stock: int

class ElementoCreate(ElementoBase):
    pass

class ElementoUpdate(ElementoBase):
    pass

class Elemento(ElementoBase):
    Codigo: int
    Fecha_creacion: datetime
    class Config:
        from_attributes = True

# --- NUEVO ESQUEMA: Para la tabla intermedia (ReservaElemento) ---
class ReservaElementoBase(BaseModel):
    Codigo_Elemento: int
    Cantidad: int

class ReservaElementoCreate(ReservaElementoBase):
    pass

class ReservaElementoResponse(ReservaElementoBase):
    # Aquí podemos incluir información del elemento si es necesario
    # Por ejemplo, para mostrar el nombre del elemento en la respuesta
    # elemento: Elemento # Esto requeriría una carga eager en la query

    class Config:
        from_attributes = True

# --- ACTUALIZACIÓN DEL ESQUEMA: Reserva ---
class ReservaBase(BaseModel):
    Lugar: str
    Precio: int # Precio base del escenario, no incluye elementos
    Fecha: date
    ID_Escenario: int

class ReservaCreate(ReservaBase):
    # Cuando creas una reserva, puedes opcionalmente incluir los elementos desde el principio
    elementos_seleccionados: Optional[List[ReservaElementoCreate]] = None

class Reserva(ReservaBase):
    ID_Reserva: int
    Correo_Usuario: EmailStr
    Estado: str
    Fecha_creacion: datetime
    Precio_Total: Optional[int] = None # Nuevo campo para el precio total calculado

    # Incluir la lista de elementos asociados a la reserva
    # Nota: Esto requiere que la query de la reserva haga `options(selectinload(Reserva.reservas_elementos))`
    reservas_elementos: List[ReservaElementoResponse] = []

    class Config:
        from_attributes = True
class ReservaUpdate(BaseModel): # Hereda de BaseModel directamente
    Fecha: Optional[date] = None
    Estado: Optional[str] = None # Si también se puede actualizar el estado

    # Puedes añadir un campo para actualizar los elementos,
    # por ejemplo, si quieres reemplazar la lista completa o añadir/eliminar.
    # Esto depende de cómo quieras manejar la actualización de elementos en una reserva existente.
    # Por ahora, lo dejamos simple.
    # elementos_seleccionados: Optional[List[ReservaElementoCreate]] = None


# ---ESQUEMAS: Escenario ---

class EscenarioBase(BaseModel):
    Direccion: str
    Capacidad: int
    Precio: int # <-- CAMBIADO A INTEGER AQUÍ TAMBIÉN
    Activo: bool

class EscenarioCreate(EscenarioBase):
    pass

class EscenarioUpdate(EscenarioBase):
    pass # Para actualizaciones, se podría hacer más granular con Optional

class Escenario(EscenarioBase):
    ID_Escenario: int
    Fecha_creacion: datetime

    class Config:
        from_attributes = True