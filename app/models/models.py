from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), nullable=True)

class User(Base):
    __tablename__ = "Usuarios"
    # Correo como clave primaria (CP)
    correo = Column(String(255), primary_key=True, index=True, unique=True)
    nombres = Column(String(255), nullable=False)
    apellidos = Column(String(255), nullable=False)
    # Aquí guardaremos el hash de la contraseña, NO la contraseña en texto plano
    contrasenia = Column(String(255), nullable=False)
    # Aquí guardaremos el salt
    rango = Column(String(50), default="usuario", nullable=False) # Siempre 'usuario' por defecto
    intentos_login = Column(Integer, default=0, nullable=False)
    # Usamos un Boolean para bloqueado, que se mapea a 0 o 1 en la mayoría de DBs
    bloqueado = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    ultimo_login = Column(DateTime, nullable=True) # Puede ser nulo al inicio
