from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_task_title_too_short_returns_422():
    response = client.post("/tasks/", json={"title": "ab", "category": "general"})
    assert response.status_code == 422
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_patch_done_task_returns_409():
    response = client.post("/tasks/", json={"title": "Tarea completa", "category": "general", "status": "done"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})
    assert response.status_code == 409
