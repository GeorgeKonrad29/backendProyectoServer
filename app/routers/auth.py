# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

from ..database.database import get_db # Importa la dependencia de DB
from ..models.models import User # Importa el modelo de usuario
from .. import schemas # Importa tus esquemas
from ..security import verify_password # Importa verify_password desde security.py

# --- Cargar variables de entorno (asumiendo que main.py ya llamó load_dotenv()) ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 10 

if not SECRET_KEY:
    raise ValueError("La variable de entorno SECRET_KEY no está configurada.")

# --- Funciones de Tokens JWT ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # Asegúrate de que sea "login"

# Esta función la usaremos para proteger rutas
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if correo is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    
    result = await db.execute(select(User).where(User.correo == correo))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception # El token es válido pero el usuario no existe en DB

    return user # Ahora devuelve el objeto User completo

# --- Crear el router para autenticación ---
router = APIRouter(
    prefix="/login", # Todas las rutas aquí tendrán /login como prefijo
    tags=["Auth"] # Para la documentación en Swagger UI
)

@router.post("/", response_model=schemas.Token) # La ruta final será /login/
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    
    # 1. Buscar al usuario en la DB por correo
    result = await db.execute(select(User).where(User.correo == form_data.username))
    user_in_db = result.scalars().first()

    # Si el usuario no existe, devolvemos un error genérico por seguridad
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales incorrectas (correo o contraseña)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Verificar si el usuario está bloqueado
    if user_in_db.bloqueado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está bloqueada debido a demasiados intentos fallidos. Contacta al soporte.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Verificar la contraseña
    if not verify_password(form_data.password, user_in_db.contrasenia):
        # Contraseña incorrecta: Incrementar intentos de login y actualizar en DB
        new_attempts = user_in_db.intentos_login + 1
        is_blocked = False

        if new_attempts > MAX_LOGIN_ATTEMPTS:
            is_blocked = True
            detail_message = "Tu cuenta ha sido bloqueada debido a demasiados intentos fallidos."
            status_code_to_return = status.HTTP_403_FORBIDDEN
        else:
            detail_message = "Credenciales incorrectas (correo o contraseña)."
            remaining_attempts = MAX_LOGIN_ATTEMPTS - new_attempts
            if remaining_attempts >= 0:
                detail_message += f" Intentos restantes antes del bloqueo: {remaining_attempts}"
            status_code_to_return = status.HTTP_400_BAD_REQUEST

        # Actualizar los intentos de login y el estado de bloqueo en la base de datos
        await db.execute( # Usar db directamente
            update(User)
            .where(User.correo == user_in_db.correo)
            .values(
                intentos_login=new_attempts,
                bloqueado=is_blocked
            )
        )
        await db.commit() # Usar db directamente

        raise HTTPException(
            status_code=status_code_to_return,
            detail=detail_message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Si las credenciales son correctas (login exitoso):
    # Reiniciar intentos_login a 0, desbloquear cuenta y actualizar ultimo_login
    update_values = {
        "intentos_login": 0,
        "bloqueado": False,
        "ultimo_login": datetime.utcnow()
    }
    await db.execute( # Usar db directamente
        update(User)
        .where(User.correo == user_in_db.correo)
        .values(**update_values)
    )
    await db.commit() # Usar db directamente

    # 5. Crear y devolver el token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_in_db.correo},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}