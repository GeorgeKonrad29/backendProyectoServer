#!/bin/bash

echo "Iniciando configuración del entorno del proyecto..."

# --- Variables de Configuración ---
REPO_URL="https://github.com/GeorgeKonrad29/backendProyectoServer.git" # ¡CAMBIA ESTO POR LA URL DE TU REPOSITORIO!
REPO_DIR="nombre-de-tu-repo" # El nombre de la carpeta que creará GitHub al clonar
APP_DIR="app" # Directorio de tu aplicación Python
REQUIREMENTS_FILE="${APP_DIR}/requirements.txt" # Ruta correcta del requirements.txt
DB_SCHEMA_FILE="db_schema.sql" # Archivo SQL para la estructura de la DB (ej: tus CREATE TABLE)
EXAMPLE_DB_FILE="example_data.sql" # Archivo SQL con datos de ejemplo (cambia la extensión si es diferente)

# 1. Clonar el repositorio (si no existe)
if [ ! -d "$REPO_DIR" ]; then
    echo "Clonando el repositorio desde $REPO_URL..."
    git clone "$REPO_URL" "$REPO_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo clonar el repositorio. Asegúrate de que la URL es correcta y tienes acceso."
        exit 1
    fi
    echo "Repositorio clonado en '$REPO_DIR'."
    cd "$REPO_DIR" # Entrar al directorio del repo para el resto de las operaciones
else
    echo "El directorio del repositorio '$REPO_DIR' ya existe. Saltando clonación."
    cd "$REPO_DIR" # Asegurarse de estar en el directorio del repo
fi

# 2. Crear el entorno virtual (si no existe)
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual 'venv'..."
    python3 -m venv venv
    echo "Entorno virtual creado."
else
    echo "Entorno virtual 'venv' ya existe."
fi

# 3. Activar el entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate
echo "Entorno virtual activado."

# 4. Instalar/Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip

# 5. Instalar las dependencias
echo "Instalando dependencias desde $REQUIREMENTS_FILE..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -r "$REQUIREMENTS_FILE"
    echo "Dependencias instaladas correctamente."
else
    echo "Error: '$REQUIREMENTS_FILE' no encontrado. Asegúrate de que la ruta es correcta."
    echo "Puedes generarlo con: pip freeze > ${APP_DIR}/requirements.txt (dentro del entorno virtual)"
    exit 1
fi

# 6. Configuración de la base de datos (instrucciones para el usuario)
echo ""
echo "--- CONFIGURACIÓN DE LA BASE DE DATOS ---"
echo "Para configurar tu base de datos MariaDB (o MySQL), sigue estos pasos:"
echo "1. Asegúrate de tener un servidor MariaDB/MySQL instalado y funcionando."
echo "2. Accede a tu cliente MariaDB/MySQL (ej. 'mysql -u root -p')."
echo "3. Crea una nueva base de datos para este proyecto (ej. 'CREATE DATABASE ProyectoReservas;')."
echo "4. Crea un usuario para la aplicación con los permisos adecuados (ej. 'reservas_app')."
echo "   CREATE USER 'reservas_app'@'localhost' IDENTIFIED BY 'Un4C0ntrs3n!4F0rt3';"
echo "   GRANT ALL PRIVILEGES ON ProyectoReservas.* TO 'reservas_app'@'localhost';"
echo "   FLUSH PRIVILEGES;"
echo "5. Ejecuta el script de esquema SQL para crear las tablas:"
echo "   mysql -u tu_usuario -p tu_base_de_datos < ../$DB_SCHEMA_FILE" # Ruta relativa desde el repo
echo "6. (Opcional) Si deseas cargar datos de ejemplo:"
echo "   mysql -u tu_usuario -p tu_base_de_datos < ../$EXAMPLE_DB_FILE" # Ruta relativa desde el repo
echo "   ¡Recuerda cambiar 'tu_usuario' y 'tu_base_de_datos' por los tuyos (si no usas 'reservas_app')!"
echo "-----------------------------------------"

# 7. Configuración de variables de entorno (.env)
echo ""
echo "--- CONFIGURACIÓN DE VARIABLES DE ENTORNO (.env) ---"
echo "Este proyecto requiere un archivo '.env' en la raíz del directorio del proyecto (a la altura de la carpeta 'app')."
echo "¡Este archivo NO debe ser subido a GitHub por razones de seguridad!"
echo "Debe contener variables sensibles como claves secretas y credenciales de la base de datos."
echo "Por favor, crea un archivo llamado '.env' en esta misma carpeta y asegúrate de que contenga lo siguiente:"
echo ""
echo "SECRET_KEY=\"b557d52718b452eeaf13d5abd4709d11d0854cdc308f056598abdad1e7149d49\""
echo "DATABASE_URL = \"mysql+aiomysql://reservas_app:Un4C0ntrs3n!4F0rt3@localhost/ProyectoReservas\""
echo ""
echo "Puedes generar una nueva SECRET_KEY con Python:"
echo "python3 -c 'import secrets; print(secrets.token_hex(32))'"
echo "----------------------------------------------------"

echo ""
echo "Configuración inicial completada. Para ejecutar la aplicación:"
echo "1. Asegúrate de que tu base de datos esté configurada y tu archivo '.env' esté creado."
echo "2. Activa el entorno virtual: source venv/bin/activate"
echo "3. Luego, puedes ejecutar la aplicación FastAPI (ej: uvicorn app.main:app --reload)"
echo "4. Para desactivar el entorno virtual: deactivate"