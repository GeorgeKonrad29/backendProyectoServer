from passlib.context import CryptContext

# Inicializa el contexto de hashing para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hashea una contraseña en texto plano.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con un hash de contraseña.
    """
    return pwd_context.verify(plain_password, hashed_password)