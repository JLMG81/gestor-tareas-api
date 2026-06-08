# Tests de la API de gestión de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app


# Motor en memoria compartido para que las tablas persistan durante cada test
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine_test)

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


# — Happy path: filtra correctamente por estado —

def test_list_tasks_by_status_returns_matching_tasks(client):
    client.post("/tasks/", json={"title": "Tarea pendiente", "category": "trabajo"})
    client.post(
        "/tasks/",
        json={"title": "Tarea en progreso", "category": "personal", "status": "in_progress"},
    )
    client.post(
        "/tasks/",
        json={"title": "Tarea hecha", "category": "estudio", "status": "done"},
    )

    response = client.get("/tasks/status/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tarea pendiente"
    assert data[0]["status"] == "pending"


def test_list_tasks_by_status_returns_empty_when_no_match(client):
    client.post("/tasks/", json={"title": "Tarea pendiente", "category": "trabajo"})

    response = client.get("/tasks/status/done")
    assert response.status_code == 200
    assert response.json() == []


# — Caso de error: estado inválido devuelve 422 —

def test_list_tasks_by_status_invalid_status_returns_422(client):
    response = client.get("/tasks/status/invalid_value")
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


# — Tests del campo obligatorio 'category' —

def test_create_task_with_category(client):
    response = client.post(
        "/tasks/",
        json={"title": "Nueva tarea", "category": "trabajo"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "trabajo"


def test_create_task_without_category_returns_422(client):
    response = client.post("/tasks/", json={"title": "Sin categoría"})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


def test_update_task_category(client):
    create = client.post(
        "/tasks/",
        json={"title": "Tarea original", "category": "trabajo"},
    )
    task_id = create.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"category": "personal"},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "personal"


def test_category_present_in_task_response(client):
    client.post(
        "/tasks/",
        json={"title": "Tarea completa", "category": "estudio"},
    )

    response = client.get("/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "category" in data[0]
    assert data[0]["category"] == "estudio"


# — Regresión: títulos de solo espacios o con espacios de relleno —

def test_create_task_whitespace_only_title_returns_422(client):
    response = client.post(
        "/tasks/",
        json={"title": "     ", "category": "trabajo"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_task_short_padded_title_returns_422(client):
    response = client.post(
        "/tasks/",
        json={"title": "  ab  ", "category": "trabajo"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_task_strips_title_whitespace(client):
    response = client.post(
        "/tasks/",
        json={"title": "  Tarea válida  ", "category": "trabajo"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Tarea válida"


def test_update_task_whitespace_only_title_returns_422(client):
    create = client.post(
        "/tasks/",
        json={"title": "Tarea original", "category": "trabajo"},
    )
    task_id = create.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "     "},
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_update_task_strips_title_whitespace(client):
    create = client.post(
        "/tasks/",
        json={"title": "Tarea original", "category": "trabajo"},
    )
    task_id = create.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "  Nuevo título  "},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Nuevo título"
