# API de Gestión de Tareas

API REST para gestionar tareas construida con **FastAPI** y **SQLAlchemy**. Permite crear, consultar, actualizar y eliminar tareas. Cada tarea cuenta con un identificador único, título, descripción opcional, categoría (obligatoria), estado (`pending`, `in_progress`, `done`) y fecha de creación automática.

---

## Requisitos previos

| Requisito | Versión mínima |
|---|---|
| Python | 3.12+ |

### Dependencias principales

| Paquete | Versión | Descripción |
|---|---|---|
| FastAPI | 0.136.1 | Framework web asíncrono |
| SQLAlchemy | 2.0.49 | ORM para acceso a base de datos |
| Pydantic | 2.13.4 | Validación de datos y serialización |
| Uvicorn | 0.46.0 | Servidor ASGI |
| pytest | 9.0.3 | Framework de tests |
| httpx | 0.28.1 | Cliente HTTP para tests |

---

## Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/JLMG81/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. Crear y activar el entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   # venv\Scripts\activate          # Windows
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

---

## Arrancar la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.

La documentación interactiva (Swagger UI) se genera automáticamente en `http://127.0.0.1:8000/docs`.

---

## Endpoints

Todos los endpoints se sirven bajo el prefijo `/tasks`.

### 1. Listar todas las tareas

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/` |
| **Parámetros** | Ninguno |

**Ejemplo de petición:**

```bash
curl http://127.0.0.1:8000/tasks/
```

**Ejemplo de respuesta** (`200 OK`):

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Actualizar el README del proyecto",
    "category": "docs",
    "status": "pending",
    "created_at": "2026-05-28T10:30:00"
  }
]
```

---

### 2. Obtener una tarea por id

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo de petición:**

```bash
curl http://127.0.0.1:8000/tasks/1
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "category": "docs",
  "status": "pending",
  "created_at": "2026-05-28T10:30:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 3. Crear una nueva tarea

| | |
|---|---|
| **Método** | `POST` |
| **Ruta** | `/tasks/` |
| **Cuerpo (JSON)** | `title` (str, obligatorio), `description` (str, opcional, máx 200 caracteres), `category` (str, obligatorio), `status` (str, opcional — por defecto `"pending"`) |

Valores válidos para `status`: `"pending"`, `"in_progress"`, `"done"`.

**Ejemplo de petición:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Implementar login", "description": "Añadir autenticación JWT", "category": "backend"}'
```

**Ejemplo de respuesta** (`201 Created`):

```json
{
  "id": 2,
  "title": "Implementar login",
  "description": "Añadir autenticación JWT",
  "category": "backend",
  "status": "pending",
  "created_at": "2026-05-28T11:00:00"
}
```

---

### 4. Actualizar parcialmente una tarea

| | |
|---|---|
| **Método** | `PATCH` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |
| **Cuerpo (JSON)** | `title` (str, opcional), `description` (str, opcional, máx 200 caracteres), `category` (str, opcional), `status` (str, opcional) |

Solo se actualizan los campos incluidos en el cuerpo de la petición.

**Ejemplo de petición:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/2 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 2,
  "title": "Implementar login",
  "description": "Añadir autenticación JWT",
  "category": "backend",
  "status": "in_progress",
  "created_at": "2026-05-28T11:00:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 5. Eliminar una tarea

| | |
|---|---|
| **Método** | `DELETE` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo de petición:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/2
```

**Respuesta exitosa:** `204 No Content` (sin cuerpo).

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 6. Eliminar todas las tareas

| | |
|---|---|
| **Método** | `DELETE` |
| **Ruta** | `/tasks/` |
| **Parámetros** | Ninguno |

**Ejemplo de petición:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/
```

**Respuesta exitosa:** `204 No Content` (sin cuerpo).

---

## Tests

Los tests utilizan una base de datos SQLite en memoria para garantizar aislamiento total; no afectan al archivo `tareas.db` de producción.

```bash
pytest tests/ -v
```

---

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/                # Paquete principal de la aplicación
│   ├── principal.py           # Punto de entrada: instancia FastAPI y registro de routers
│   ├── base_de_datos.py       # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py             # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py            # Esquemas Pydantic de entrada y respuesta
│   └── rutas/                 # Directorio de endpoints
│       └── tareas.py          # Endpoints REST de tareas
├── tests/                     # Suite de tests funcionales
│   └── test_tasks.py          # Tests con pytest y SQLite en memoria
├── requirements.txt           # Dependencias del proyecto
├── AGENTS.md                  # Instrucciones para Devin
└── README.md                  # Documentación del proyecto
```
