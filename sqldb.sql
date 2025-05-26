-- Crear la base de datos con configuración de seguridad
CREATE DATABASE IF NOT EXISTS ProyectoReservas
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE ProyectoReservas;
-- Tabla Usuarios con seguridad mejorada
CREATE TABLE Usuarios (
Correo VARCHAR(255) PRIMARY KEY,
Nombres VARCHAR(25) NOT NULL,
Apellidos VARCHAR(255) NOT NULL,
Contrasenia VARCHAR(255) NOT NULL,
-- Almacenamiento seguro de contraseñas
Rango ENUM('admin', 'usuario') NOT NULL DEFAULT 'usuario',
Intentos_login INT DEFAULT 0,
Bloqueado BOOLEAN DEFAULT FALSE,
Fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
Ultimo_login TIMESTAMP NULL,
INDEX idx_apellidos (Apellidos)
) ENGINE=InnoDB;
-- Tabla Escenario con auto-incremento
CREATE TABLE Escenario (
ID_Escenario INT AUTO_INCREMENT PRIMARY KEY,
Direccion VARCHAR(255) NOT NULL,
Capacidad INT NOT NULL CHECK (Capacidad > 0),
Precio DECIMAL(10,2) NOT NULL CHECK (Precio >= 0),
Activo BOOLEAN DEFAULT TRUE,
Fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
INDEX idx_direccion (Direccion)
) ENGINE=InnoDB;
-- Tabla Elementos con autoincremento
CREATE TABLE Elementos (
Codigo INT AUTO_INCREMENT PRIMARY KEY,
Nombre VARCHAR(255) NOT NULL,
Precio DECIMAL(10,2) NOT NULL CHECK (Precio >= 0),
Stock INT DEFAULT 1 CHECK (Stock >= 0),

Fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
INDEX idx_nombre (Nombre)
) ENGINE=InnoDB;
-- Tabla Reservas con autoincremento y seguridad
CREATE TABLE Reservas (
ID_Reserva INT AUTO_INCREMENT PRIMARY KEY,
Correo_Usuario VARCHAR(255) NOT NULL,
Lugar VARCHAR(255) NOT NULL,
Precio DECIMAL(10,2) NOT NULL CHECK (Precio >= 0),
Fecha DATE NOT NULL,
Hora TIME NOT NULL,
ID_Escenario INT NOT NULL,
Estado ENUM('pendiente', 'confirmada', 'cancelada', 'completada') DEFAULT 'pendiente',
Fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (Correo_Usuario) REFERENCES Usuarios(Correo) ON UPDATE
CASCADE,
FOREIGN KEY (ID_Escenario) REFERENCES Escenario(ID_Escenario),
CONSTRAINT chk_fecha_valida CHECK (Fecha >= '1000-01-01'), -- Fecha mínima
permitida
INDEX idx_fecha (Fecha)
) ENGINE=InnoDB;
-- Tabla Reservas_Elementos con claves foráneas seguras
CREATE TABLE Reservas_Elementos (
ID_Reserva INT NOT NULL,
Codigo_Elemento INT NOT NULL,
Cantidad INT DEFAULT 1 CHECK (Cantidad > 0),
PRIMARY KEY (ID_Reserva, Codigo_Elemento),
FOREIGN KEY (ID_Reserva) REFERENCES Reservas(ID_Reserva) ON DELETE
CASCADE,
FOREIGN KEY (Codigo_Elemento) REFERENCES Elementos(Codigo) ON UPDATE
CASCADE
) ENGINE=InnoDB;
-- Creación de usuarios con privilegios limitados
CREATE USER 'reservas_app'@'localhost' IDENTIFIED BY 'Un4C0ntrs3n!4F0rt3';
GRANT SELECT, INSERT, UPDATE ON ProyectoReservas.* TO 'reservas_app'@'localhost';
CREATE USER 'reservas_admin'@'localhost' IDENTIFIED BY 'Adm1n$3gur0P4ss!';
GRANT ALL PRIVILEGES ON ProyectoReservas.* TO 'reservas_admin'@'localhost';
-- Creación de vistas para seguridad adicional
CREATE VIEW VistaReservasUsuario AS
SELECT r.ID_Reserva, r.Lugar, r.Precio, r.Fecha, r.Hora, e.Direccion
FROM Reservas r
JOIN Escenario e ON r.ID_Escenario = e.ID_Escenario
WHERE r.Correo_Usuario = CURRENT_USER();
-- Creación de triggers para auditoría
CREATE TABLE AuditoriaReservas (
ID_Auditoria INT AUTO_INCREMENT PRIMARY KEY,

ID_Reserva INT,
Accion VARCHAR(10),
Usuario VARCHAR(255),
Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
Datos_anteriores TEXT
) ENGINE=InnoDB;
DELIMITER //
CREATE TRIGGER after_reserva_insert
AFTER INSERT ON Reservas
FOR EACH ROW
BEGIN
INSERT INTO AuditoriaReservas (ID_Reserva, Accion, Usuario)
VALUES (NEW.ID_Reserva, 'INSERT', CURRENT_USER());
END//
CREATE TRIGGER before_reserva_delete
BEFORE DELETE ON Reservas
FOR EACH ROW
BEGIN
INSERT INTO AuditoriaReservas (ID_Reserva, Accion, Usuario, Datos_anteriores)
VALUES (OLD.ID_Reserva, 'DELETE', CURRENT_USER(),
CONCAT('Lugar: ', OLD.Lugar, ', Precio: ', OLD.Precio));
END//
DELIMITER ;