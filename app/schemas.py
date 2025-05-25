# app/schemas.py

from pydantic import BaseModel, EmailStr # Asegúrate de importar EmailStr
from datetime import datetime
from typing import Optional # Para campos opcionales si los usas


# Schemas base para reusabilidad
class ItemBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    propietario_id: Optional[int] = None # Si los items tienen propietario
    class Config:
        from_attributes = True # O from_orm = True para Pydantic v1. Para Pydantic v2, es 'from_attributes = True'

class UserBase(BaseModel):
    correo: EmailStr # Usa EmailStr para validación de correo
    nombres: str
    apellidos: str

class UserCreate(UserBase):
    contrasenia: str
    

class User(UserBase):
    id: int
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