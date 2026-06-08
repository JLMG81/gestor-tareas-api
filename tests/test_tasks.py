# Tests del endpoint GET /tasks/status/{status}

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
    client.post("/tasks/", json={"title": "Tarea pendiente", "category": "general"})
    client.post("/tasks/", json={"title": "Tarea en progreso", "category": "general", "status": "in_progress"})
    client.post("/tasks/", json={"title": "Tarea hecha", "category": "general", "status": "done"})

    response = client.get("/tasks/status/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tarea pendiente"
    assert data[0]["status"] == "pending"


def test_list_tasks_by_status_returns_empty_when_no_match(client):
    client.post("/tasks/", json={"title": "Tarea pendiente", "category": "general"})

    response = client.get("/tasks/status/done")
    assert response.status_code == 200
    assert response.json() == []


# — Caso de error: estado inválido devuelve 422 —

def test_list_tasks_by_status_invalid_status_returns_422(client):
    response = client.get("/tasks/status/invalid_value")
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


# — Tests de categoría —

def test_create_without_category_returns_422(client):
    resp = client.post("/tasks/", json={"title": "Tarea sin cat"})
    assert resp.status_code == 422


def test_create_with_null_category_returns_422(client):
    resp = client.post("/tasks/", json={"title": "Tarea null cat", "category": None})
    assert resp.status_code == 422


def test_create_task_with_category(client):
    resp = client.post("/tasks/", json={"title": "Tarea trabajo", "category": "trabajo"})
    assert resp.status_code == 201
    assert resp.json()["category"] == "trabajo"


def test_create_minimal_task_includes_category(client):
    resp = client.post(
        "/tasks/", json={"title": "Tarea mínima", "category": "general"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["category"] == "general"


def test_update_only_category(client):
    resp = client.post(
        "/tasks/", json={"title": "Tarea para actualizar", "category": "general"}
    )
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    resp = client.patch(
        f"/tasks/{task_id}", json={"category": "personal"}
    )
    assert resp.status_code == 200
    assert resp.json()["category"] == "personal"


def test_task_create_schema_requires_category():
    from aplicacion.esquemas import TaskCreate
    task = TaskCreate(title="test", category="general")
    assert task.category == "general"
