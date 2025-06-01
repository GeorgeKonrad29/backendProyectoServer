# app/schemas.py

from pydantic import BaseModel, EmailStr, Field # Asegúrate de importar EmailStr
from datetime import datetime, date
from typing import Optional, List # Para campos opcionales si los usas



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
    bloqueado: Optional[bool] = None # Corresponde a campo 'bloqueado'

class User(UserBase):
    rango: str
    intentos_login: int
    bloqueado: bool
    fecha_creacion: datetime
    ultimo_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True # O from_orm = True para Pydantic v1

# Nuevo esquema para la respuesta del Token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    correo: Optional[str] = None

# --- ESQUEMAS: Elemento ---
class ElementoBase(BaseModel):
    Nombre: str
    Precio: int
    Stock: int

class ElementoCreate(ElementoBase):
    pass

class ElementoUpdate(BaseModel):
    Nombre: Optional[str] = None
    Descripcion: Optional[str] = None
    Stock: Optional[int] = None

    class Config:
        from_attributes = True

class Elemento(ElementoBase):
    Codigo: int
    Fecha_creacion: datetime
    class Config:
        from_attributes = True

# --- ESQUEMA: Para la tabla intermedia (ReservaElemento) ---
class ReservaElementoBase(BaseModel):
    Codigo_Elemento: int
    Cantidad: int

class ReservaElementoCreate(ReservaElementoBase):
    pass

class ReservaElementoResponse(ReservaElementoBase):

    class Config:
        from_attributes = True

# --- ESQUEMA: Reserva ---
class ReservaBase(BaseModel):
    # Estos campos son los que NO queremos recibir en ReservaCreate,
    # pero sí queremos que estén en la respuesta de Reserva
    Fecha: date
    ID_Escenario: int # ID del escenario

class ReservaCreate(BaseModel): # <--- ¡HEREDA DIRECTAMENTE DE BaseModel!
    Fecha: date # La fecha de la reserva, sí se necesita del usuario
    ID_Escenario: int # El ID del escenario, sí se necesita del usuario
    # Lugar y Precio NO están aquí, se obtendrán de la base de datos

    elementos_seleccionados: Optional[List[ReservaElementoCreate]] = None

class Reserva(ReservaBase):
    ID_Reserva: int
    Correo_Usuario: EmailStr
    Lugar: str # Este campo se obtiene de la DB, no del usuario
    Precio: int # Este campo se obtiene de la DB, no del usuario
    Fecha: date
    ID_Escenario: int
    Estado: str
    Fecha_creacion: datetime
    Precio_Total: Optional[int] = None # Campo para el precio total calculado

    # Incluir la lista de elementos asociados a la reserva
    # Nota: Esto requiere que la query de la reserva haga `options(selectinload(Reserva.reservas_elementos))`
    reservas_elementos: List[ReservaElementoResponse] = []

    class Config:
        from_attributes = True
class ReservaUpdate(BaseModel): # Hereda de BaseModel directamente
    Fecha: Optional[date] = None
    Estado: Optional[str] = None # También se puede actualizar el estado

    

# ---ESQUEMAS: Escenario ---

class EscenarioBase(BaseModel):
    Direccion: str
    Capacidad: int
    Precio: int 
    Activo: bool

class EscenarioCreate(EscenarioBase):
    pass


class EscenarioUpdate(BaseModel):
    Direccion: Optional[str] = None
    Capacidad: Optional[int] = None
    Precio: Optional[int] = None
    Activo: Optional[bool] = None

class Escenario(EscenarioBase):
    ID_Escenario: int
    Fecha_creacion: datetime

    class Config:
        from_attributes = True