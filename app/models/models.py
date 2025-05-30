from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date 

Base = declarative_base()

#class Item(Base):
#    __tablename__ = "items"

#    id = Column(Integer, primary_key=True, index=True)
#    name = Column(String(255), index=True)
#    description = Column(String(255), nullable=True)

class User(Base):
    __tablename__ = "Usuarios"

    correo = Column(String(255), primary_key=True, unique=True, index=True)
    nombres = Column(String(255))
    apellidos = Column(String(255))
    contrasenia = Column(String(255))
    rango = Column(String(50), default="usuario")
    intentos_login = Column(Integer, default=0)
    bloqueado = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ultimo_login = Column(DateTime, nullable=True)

    # ¡ASEGÚRATE DE QUE ESTA LÍNEA ESTÉ PRESENTE Y CORRECTA!
    reservas = relationship("Reserva", back_populates="usuario") # <--- ¡ESTA ES LA LÍNEA QUE FALTA O ESTÁ MAL!

    def __repr__(self):
        return f"<User(correo='{self.correo}')>"

class Escenario(Base):
    __tablename__ = "Escenario" # Basado en tu imagen

    ID_Escenario = Column(Integer, primary_key=True, index=True)
    Direccion = Column(String(255))
    Capacidad = Column(Integer)
    Precio = Column(Integer) # <-- CAMBIADO A INTEGER PARA PESOS COLOMBIANOS
    Activo = Column(Boolean) # Asumimos que tu DB lo maneja como 0/1 para booleano
    Fecha_creacion = Column(DateTime, default=datetime.utcnow)

    reservas = relationship("Reserva", back_populates="escenario")

    def __repr__(self):
        return f"<Escenario(ID_Escenario={self.ID_Escenario}, Direccion='{self.Direccion}')>"

# --- NUEVO MODELO: Elemento (Implemento) ---
class Elemento(Base):
    __tablename__ = "Elementos" # Según tu imagen
    Codigo = Column(Integer, primary_key=True, index=True) # Clave primaria
    Nombre = Column(String(255))
    Precio = Column(Integer) # Según tu imagen
    Stock = Column(Integer)
    Fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relación muchos a muchos a través de la tabla intermedia
    reservas_elementos = relationship("ReservaElemento", back_populates="elemento")

    def __repr__(self):
        return f"<Elemento(Codigo={self.Codigo}, Nombre='{self.Nombre}')>"

# --- NUEVO MODELO: Tabla Intermedia para la relación N:M ---
class ReservaElemento(Base):
    __tablename__ = "Reservas_Elementos" # Según tu imagen

    # Claves primarias compuestas
    ID_Reserva = Column(Integer, ForeignKey("Reservas.ID_Reserva"), primary_key=True)
    Codigo_Elemento = Column(Integer, ForeignKey("Elementos.Codigo"), primary_key=True)
    Cantidad = Column(Integer)

    # Relaciones con los modelos principales
    reserva = relationship("Reserva", back_populates="reservas_elementos")
    elemento = relationship("Elemento", back_populates="reservas_elementos")

    def __repr__(self):
        return f"<ReservaElemento(ID_Reserva={self.ID_Reserva}, Codigo_Elemento={self.Codigo_Elemento}, Cantidad={self.Cantidad})>"


# --- ACTUALIZACIÓN DEL MODELO: Reserva ---
class Reserva(Base):
    __tablename__ = "Reservas"

    ID_Reserva = Column(Integer, primary_key=True, index=True)
    Correo_Usuario = Column(String(255), ForeignKey("Usuarios.correo"))
    Lugar = Column(String(255))
    Precio = Column(Integer) # Precio base del escenario, no incluye elementos aún
    Fecha = Column(Date)
    # Hora = Column(String(50)) # Eliminado según lo acordado
    ID_Escenario = Column(Integer, ForeignKey("Escenario.ID_Escenario"))
    Estado = Column(String(50), default="Pendiente")
    Fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("User", back_populates="reservas")
    escenario = relationship("Escenario", back_populates="reservas")
    # Relación muchos a muchos a través de la tabla intermedia
    reservas_elementos = relationship("ReservaElemento", back_populates="reserva")

    def __repr__(self):
        return f"<Reserva(ID_Reserva={self.ID_Reserva}, Correo_Usuario='{self.Correo_Usuario}')>"