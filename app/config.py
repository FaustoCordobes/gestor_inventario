import os

from dotenv import load_dotenv

load_dotenv()


def _secret_key():
    key = os.getenv("SECRET_KEY")
    if key:
        return key
    # En Render (que define la variable RENDER) no se arranca con la clave de ejemplo.
    if os.getenv("RENDER"):
        raise RuntimeError("Falta la variable de entorno SECRET_KEY.")
    return "clave-de-desarrollo"


def _database_url():
    url = os.getenv("DATABASE_URL", "sqlite:///inventory.db")
    # Render entrega "postgres://", pero SQLAlchemy necesita "postgresql://".
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


class Config:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Login con Google (credenciales de Google Cloud Console)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
