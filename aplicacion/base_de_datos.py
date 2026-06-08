# Configuración de la conexión a la base de datos con SQLAlchemy

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# URL de conexión a la base de datos SQLite local
SQLALCHEMY_DATABASE_URL = "sqlite:///./tareas.db"

# Motor de base de datos; check_same_thread es necesario para SQLite con FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Fábrica de sesiones: cada petición obtiene su propia sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Clase base de la que heredan todos los modelos ORM (SQLAlchemy 2.0)
class Base(DeclarativeBase):
    pass


# Dependencia de FastAPI: abre la sesión, la cede y la cierra al terminar
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
