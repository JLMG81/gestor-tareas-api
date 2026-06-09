# Esquemas Pydantic para validación de datos de entrada y serialización de respuestas

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from aplicacion.modelos import TaskStatus


# Esquema para crear una nueva tarea; título y categoría son obligatorios
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    status: TaskStatus = TaskStatus.pending

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()


# Esquema para actualizar una tarea; todos los campos son opcionales (PATCH parcial)
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[TaskStatus] = None

    @field_validator("title")
    @classmethod
    def strip_and_validate_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if len(stripped) < 3:
            raise ValueError("El título debe tener al menos 3 caracteres")
        return stripped


# Esquema de respuesta que devuelve la API; incluye los campos generados por la BD
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    status: TaskStatus
    created_at: datetime

    # from_attributes permite construir el esquema desde un objeto ORM de SQLAlchemy
    model_config = {"from_attributes": True}
