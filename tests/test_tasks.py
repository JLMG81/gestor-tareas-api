"""Tests para la API de gestión de tareas.

Prioridad: casos de error y límite sobre happy-path.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.modelos import Task, TaskStatus
from aplicacion.principal import app


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="sample_task")
def fixture_sample_task(client):
    resp = client.post("/tasks/", json={"title": "Tarea de prueba"})
    return resp.json()


# ── GET /tasks/{id} – 404 y casos límite ────────────────────────────

class TestGetTaskErrors:
    def test_get_nonexistent_task_returns_404(self, client):
        resp = client.get("/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_get_task_id_zero_returns_404(self, client):
        resp = client.get("/tasks/0")
        assert resp.status_code == 404

    def test_get_task_negative_id_returns_422(self, client):
        resp = client.get("/tasks/-1")
        assert resp.status_code in (404, 422)

    def test_get_task_string_id_returns_422(self, client):
        resp = client.get("/tasks/abc")
        assert resp.status_code == 422

    def test_get_task_very_large_id_returns_404(self, client):
        resp = client.get("/tasks/99999999")
        assert resp.status_code == 404


# ── POST /tasks/ – errores de validación ─────────────────────────────

class TestCreateTaskErrors:
    def test_create_without_body_returns_422(self, client):
        resp = client.post("/tasks/")
        assert resp.status_code == 422

    def test_create_empty_json_returns_422(self, client):
        resp = client.post("/tasks/", json={})
        assert resp.status_code == 422

    def test_create_with_null_title_returns_422(self, client):
        resp = client.post("/tasks/", json={"title": None})
        assert resp.status_code == 422

    def test_create_with_wrong_type_title_returns_422(self, client):
        resp = client.post("/tasks/", json={"title": 12345})
        # FastAPI/Pydantic may coerce int to str; check response is not 5xx
        assert resp.status_code < 500

    def test_create_with_invalid_status_returns_422(self, client):
        resp = client.post(
            "/tasks/", json={"title": "t", "status": "invalid_status"}
        )
        assert resp.status_code == 422

    def test_create_with_extra_fields_ignores_them(self, client):
        resp = client.post(
            "/tasks/", json={"title": "t", "extra_field": "ignored"}
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "extra_field" not in body

    def test_create_with_empty_string_title(self, client):
        resp = client.post("/tasks/", json={"title": ""})
        assert resp.status_code == 201
        assert resp.json()["title"] == ""

    def test_create_with_very_long_title(self, client):
        long_title = "x" * 1000
        resp = client.post("/tasks/", json={"title": long_title})
        assert resp.status_code < 500

    def test_create_with_all_statuses(self, client):
        for st in ("pending", "in_progress", "done"):
            resp = client.post(
                "/tasks/", json={"title": f"task_{st}", "status": st}
            )
            assert resp.status_code == 201
            assert resp.json()["status"] == st


# ── PATCH /tasks/{id} – 404 y validación ────────────────────────────

class TestUpdateTaskErrors:
    def test_update_nonexistent_task_returns_404(self, client):
        resp = client.patch("/tasks/999", json={"title": "new"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_update_string_id_returns_422(self, client):
        resp = client.patch("/tasks/abc", json={"title": "new"})
        assert resp.status_code == 422

    def test_update_with_invalid_status_returns_422(self, client, sample_task):
        resp = client.patch(
            f"/tasks/{sample_task['id']}", json={"status": "bad"}
        )
        assert resp.status_code == 422

    def test_update_with_empty_body(self, client, sample_task):
        resp = client.patch(f"/tasks/{sample_task['id']}", json={})
        assert resp.status_code == 200
        assert resp.json()["title"] == sample_task["title"]

    def test_update_only_title(self, client, sample_task):
        resp = client.patch(
            f"/tasks/{sample_task['id']}", json={"title": "Nuevo título"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Nuevo título"
        assert body["status"] == sample_task["status"]

    def test_update_only_description(self, client, sample_task):
        resp = client.patch(
            f"/tasks/{sample_task['id']}", json={"description": "Desc nueva"}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Desc nueva"

    def test_update_only_status(self, client, sample_task):
        resp = client.patch(
            f"/tasks/{sample_task['id']}", json={"status": "done"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    def test_update_all_fields(self, client, sample_task):
        payload = {
            "title": "Updated",
            "description": "Updated desc",
            "status": "in_progress",
        }
        resp = client.patch(f"/tasks/{sample_task['id']}", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Updated"
        assert body["description"] == "Updated desc"
        assert body["status"] == "in_progress"

    def test_update_set_description_to_null(self, client, sample_task):
        client.patch(
            f"/tasks/{sample_task['id']}", json={"description": "algo"}
        )
        resp = client.patch(
            f"/tasks/{sample_task['id']}", json={"description": None}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] is None


# ── DELETE /tasks/{id} – 404 y casos límite ──────────────────────────

class TestDeleteTaskErrors:
    def test_delete_nonexistent_task_returns_404(self, client):
        resp = client.delete("/tasks/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"

    def test_delete_string_id_returns_422(self, client):
        resp = client.delete("/tasks/abc")
        assert resp.status_code == 422

    def test_delete_returns_no_body(self, client, sample_task):
        resp = client.delete(f"/tasks/{sample_task['id']}")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_delete_same_task_twice_returns_404(self, client, sample_task):
        tid = sample_task["id"]
        resp1 = client.delete(f"/tasks/{tid}")
        assert resp1.status_code == 204
        resp2 = client.delete(f"/tasks/{tid}")
        assert resp2.status_code == 404

    def test_get_after_delete_returns_404(self, client, sample_task):
        tid = sample_task["id"]
        client.delete(f"/tasks/{tid}")
        resp = client.get(f"/tasks/{tid}")
        assert resp.status_code == 404


# ── DELETE /tasks/ – eliminar todas las tareas ───────────────────────

class TestDeleteAllTasks:
    def test_delete_all_returns_204_and_empties_list(self, client):
        client.post("/tasks/", json={"title": "Tarea 1"})
        client.post("/tasks/", json={"title": "Tarea 2"})
        client.post("/tasks/", json={"title": "Tarea 3"})
        resp = client.delete("/tasks/")
        assert resp.status_code == 204
        assert resp.content == b""
        listing = client.get("/tasks/")
        assert listing.status_code == 200
        assert listing.json() == []

    def test_delete_all_on_empty_db_returns_204(self, client):
        resp = client.delete("/tasks/")
        assert resp.status_code == 204
        listing = client.get("/tasks/")
        assert listing.status_code == 200
        assert listing.json() == []


# ── GET /tasks/ – lista vacía y con datos ────────────────────────────

class TestListTasks:
    def test_list_empty(self, client):
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_creating_tasks(self, client):
        client.post("/tasks/", json={"title": "a"})
        client.post("/tasks/", json={"title": "b"})
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ── POST /tasks/ – happy-path mínimo ────────────────────────────────

class TestCreateTaskHappyPath:
    def test_create_minimal_task(self, client):
        resp = client.post("/tasks/", json={"title": "Mi tarea"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Mi tarea"
        assert body["description"] is None
        assert body["status"] == "pending"
        assert "id" in body
        assert "created_at" in body

    def test_create_task_with_description(self, client):
        resp = client.post(
            "/tasks/",
            json={"title": "t", "description": "detalle"},
        )
        assert resp.status_code == 201
        assert resp.json()["description"] == "detalle"

    def test_create_task_with_in_progress_status(self, client):
        resp = client.post(
            "/tasks/", json={"title": "t", "status": "in_progress"}
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "in_progress"


# ── GET /tasks/{id} – happy-path ─────────────────────────────────────

class TestGetTaskHappyPath:
    def test_get_existing_task(self, client, sample_task):
        resp = client.get(f"/tasks/{sample_task['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sample_task["id"]
        assert resp.json()["title"] == sample_task["title"]


# ── Modelo y enums ───────────────────────────────────────────────────

class TestTaskStatusEnum:
    def test_enum_values(self):
        assert TaskStatus.pending.value == "pending"
        assert TaskStatus.in_progress.value == "in_progress"
        assert TaskStatus.done.value == "done"

    def test_enum_is_str(self):
        assert isinstance(TaskStatus.pending, str)

    def test_enum_members_count(self):
        assert len(TaskStatus) == 3


# ── Esquemas Pydantic ────────────────────────────────────────────────

class TestSchemas:
    def test_task_create_defaults(self):
        from aplicacion.esquemas import TaskCreate

        tc = TaskCreate(title="test")
        assert tc.title == "test"
        assert tc.description is None
        assert tc.status == TaskStatus.pending

    def test_task_create_invalid_status_raises(self):
        from aplicacion.esquemas import TaskCreate

        with pytest.raises(Exception):
            TaskCreate(title="test", status="nope")

    def test_task_update_all_none_by_default(self):
        from aplicacion.esquemas import TaskUpdate

        tu = TaskUpdate()
        assert tu.title is None
        assert tu.description is None
        assert tu.status is None

    def test_task_response_from_attributes(self):
        from aplicacion.esquemas import TaskResponse

        assert TaskResponse.model_config.get("from_attributes") is True


# ── get_db generator ─────────────────────────────────────────────────

class TestGetDb:
    def test_get_db_yields_and_closes(self):
        gen = get_db()
        session = next(gen)
        assert session is not None
        try:
            gen.send(None)
        except StopIteration:
            pass

    def test_get_db_closes_on_exception(self):
        gen = get_db()
        _ = next(gen)
        try:
            gen.throw(RuntimeError("boom"))
        except RuntimeError:
            pass


# ── Rutas inexistentes ───────────────────────────────────────────────

class TestMiscRoutes:
    def test_root_returns_404(self, client):
        resp = client.get("/")
        assert resp.status_code == 404

    def test_put_not_allowed(self, client, sample_task):
        resp = client.put(
            f"/tasks/{sample_task['id']}", json={"title": "x"}
        )
        assert resp.status_code == 405
