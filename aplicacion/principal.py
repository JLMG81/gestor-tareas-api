# Punto de entrada de la aplicación FastAPI

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from aplicacion.base_de_datos import Base, engine
from aplicacion.rutas import tareas


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa las tablas de la BD al arrancar la aplicación."""
    Base.metadata.create_all(bind=engine)
    yield


# Instancia principal de la aplicación con lifespan para inicialización
app = FastAPI(title="API de Gestión de Tareas", lifespan=lifespan)

# Comprime respuestas mayores de 500 bytes para reducir el ancho de banda
app.add_middleware(GZipMiddleware, minimum_size=500)

# Registro del router de tareas bajo el prefijo /tasks
app.include_router(tareas.router)
