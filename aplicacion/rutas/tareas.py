# Definición de los endpoints REST para la gestión de tareas

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

# Límite máximo de resultados por página para evitar respuestas excesivas
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

# Router con prefijo /tasks; agrupa todos los endpoints de tareas
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE,
        description="Máximo de registros a devolver",
    ),
    db: Session = Depends(get_db),
):
    """Devuelve una página de tareas almacenadas.

    Args:
        skip (int): Número de registros a saltar (offset).
        limit (int): Cantidad máxima de registros a devolver
            por página (entre 1 y 100, por defecto 20).
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.

    Returns:
        list[Task]: Lista paginada de tareas.
    """
    stmt = select(Task).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/status/{status}", response_model=list[TaskResponse])
def list_tasks_by_status(
    status: TaskStatus,
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(
        DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE,
        description="Máximo de registros a devolver",
    ),
    db: Session = Depends(get_db),
):
    """Devuelve una página de tareas filtradas por estado.

    Args:
        status (TaskStatus): Estado por el que filtrar las
            tareas (pending, in_progress o done).
        skip (int): Número de registros a saltar (offset).
        limit (int): Cantidad máxima de registros a devolver
            por página (entre 1 y 100, por defecto 20).
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.

    Returns:
        list[Task]: Lista paginada de tareas con el estado
            solicitado.
    """
    stmt = (
        select(Task)
        .where(Task.status == status)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Obtiene una tarea por su identificador.

    Args:
        task_id (int): Identificador único de la tarea.
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.

    Returns:
        Task: Instancia de la tarea correspondiente al
            identificador proporcionado.

    Raises:
        HTTPException: Error 404 si no existe una tarea con
            el ``task_id`` indicado.
    """
    stmt = select(Task).where(Task.id == task_id)
    task = db.scalars(stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y la persiste en la base de datos.

    Args:
        payload (TaskCreate): Esquema con los datos de la
            nueva tarea (título y categoría obligatorios,
            descripción y estado opcionales).
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.

    Returns:
        Task: Instancia de la tarea recién creada con el
            identificador y la fecha de creación asignados
            por la base de datos.

    Raises:
        HTTPException: Error 422 si el título tiene menos de
            3 caracteres.
    """
    if len(payload.title) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El título debe tener al menos 3 caracteres",
        )
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)
):
    """Actualiza parcialmente una tarea existente.

    Solo se modifican los campos incluidos en el cuerpo de la
    petición; los campos no enviados conservan su valor actual.

    Args:
        task_id (int): Identificador único de la tarea a
            actualizar.
        payload (TaskUpdate): Esquema con los campos a
            modificar (título, descripción, categoría o
            estado, todos opcionales).
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.

    Returns:
        Task: Instancia de la tarea con los campos
            actualizados.

    Raises:
        HTTPException: Error 404 si no existe una tarea con
            el ``task_id`` indicado.
        ValidationError: Error 422 si el título proporcionado
            tiene menos de 3 caracteres.
    """
    stmt = select(Task).where(Task.id == task_id)
    task = db.scalars(stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.status == TaskStatus.done:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede modificar una tarea en estado done",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_tasks(db: Session = Depends(get_db)):
    """Elimina todas las tareas de la base de datos.

    Args:
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.
    """
    db.execute(delete(Task))
    db.commit()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos.

    Args:
        task_id (int): Identificador único de la tarea a
            eliminar.
        db (Session): Sesión de base de datos inyectada por
            la dependencia ``get_db``.

    Raises:
        HTTPException: Error 404 si no existe una tarea con
            el ``task_id`` indicado.
    """
    stmt = select(Task).where(Task.id == task_id)
    task = db.scalars(stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    db.delete(task)
    db.commit()
