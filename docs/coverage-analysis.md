# Análisis de cobertura de tests — `pytest --cov`

**Fecha:** 2026-06-23  
**Cobertura total:** 85 % (107 sentencias, 16 sin cubrir) — 9 tests pasaron

## Resumen por módulo

| Módulo | Sentencias | Faltan | Cobertura | Líneas sin cubrir |
|---|---|---|---|---|
| `aplicacion/__init__.py` | 0 | 0 | 100 % | — |
| `aplicacion/base_de_datos.py` | 12 | 4 | **67 %** | 24-28 |
| `aplicacion/esquemas.py` | 22 | 0 | 100 % | — |
| `aplicacion/modelos.py` | 16 | 0 | 100 % | — |
| `aplicacion/principal.py` | 6 | 0 | 100 % | — |
| `aplicacion/rutas/__init__.py` | 0 | 0 | 100 % | — |
| `aplicacion/rutas/tareas.py` | 51 | 12 | **76 %** | 55-58, 123, 144-145, 162-166 |

---

## Los 3 módulos con menor cobertura

### 1. `aplicacion/base_de_datos.py` — 67 % (4 sentencias sin cubrir)

**Líneas sin cubrir:** 24-28 (función `get_db()` completa)

**Qué no está cubierto:**

La función generadora `get_db()` de producción nunca se ejecuta durante los
tests porque estos sobreescriben la dependencia con
`app.dependency_overrides[get_db]`, que usa una sesión en memoria. Esto
significa que:

- La creación de la sesión de producción (`db = SessionLocal()`) no se prueba.
- El `yield db` del generador no se ejecuta.
- El bloque `finally: db.close()` (limpieza de la sesión) no se verifica.

**Casos a cubrir:**

1. Verificar que `get_db()` produce (`yield`) una sesión SQLAlchemy válida.
2. Verificar que la sesión se cierra correctamente al consumir el generador
   (bloque `finally`).
3. Verificar que `db.close()` se ejecuta incluso si ocurre una excepción
   durante el uso de la sesión.

**Esfuerzo estimado: Bajo**

Un único test unitario que invoque `next()` sobre el generador, valide el tipo
de la sesión, y luego llame a `.close()` cubriría las 4 líneas faltantes. No
requiere infraestructura adicional.

---

### 2. `aplicacion/rutas/tareas.py` — 76 % (12 sentencias sin cubrir)

**Líneas sin cubrir:** 55-58, 123, 144-145, 162-166

**Qué no está cubierto:**

| Líneas | Endpoint | Descripción |
|---|---|---|
| 55-58 | `GET /tasks/{task_id}` | Endpoint completo: ni el happy path (obtener tarea por ID) ni el caso de error (404 tarea no encontrada) están probados. |
| 123 | `PATCH /tasks/{task_id}` | Rama de error 404: no se prueba el caso de actualizar una tarea inexistente. (El happy path y el 409 de tarea `done` sí están cubiertos.) |
| 144-145 | `DELETE /tasks/` | Endpoint completo: no hay test para eliminar todas las tareas. |
| 162-166 | `DELETE /tasks/{task_id}` | Endpoint completo: ni el happy path (eliminar tarea por ID) ni el caso de error (404) están probados. |

**Casos a cubrir:**

1. `GET /tasks/{id}` — happy path: crear tarea y recuperarla por ID.
2. `GET /tasks/{id}` — error: solicitar ID inexistente → 404 con `detail`.
3. `PATCH /tasks/{id}` — error: actualizar ID inexistente → 404 con `detail`.
4. `DELETE /tasks/` — happy path: crear varias tareas, eliminar todas,
   verificar que `GET /tasks/` devuelve lista vacía.
5. `DELETE /tasks/{id}` — happy path: crear tarea, eliminarla, verificar que ya
   no existe.
6. `DELETE /tasks/{id}` — error: eliminar ID inexistente → 404 con `detail`.

**Esfuerzo estimado: Medio**

Son 6 casos de test repartidos en 3 endpoints. Cada test es sencillo (llamada
HTTP + aserción sobre status code y body), pero el volumen de trabajo es mayor
al seguir la convención del proyecto de probar tanto el happy path como el caso
de error por endpoint.

---

### 3. `aplicacion/principal.py` — 100 % (6 sentencias, 0 sin cubrir)

**Nota:** Este módulo ya tiene cobertura completa (es el tercer módulo con más
código entre los que no son rutas). Las 6 sentencias (imports,
`Base.metadata.create_all()`, instanciación de `FastAPI`, `include_router`) se
ejecutan como efecto secundario al importar `app` desde los tests.

**Por qué se incluye:** Los 5 módulos restantes están al 100 %, por lo que
`principal.py` es el tercero con "menor" cobertura por tener la mayor cantidad
de lógica de inicialización entre los módulos completos. Aunque las líneas están
cubiertas, **no existen tests dedicados** que verifiquen el comportamiento de
arranque.

**Posibles mejoras:**

1. Test *smoke* que verifique que `GET /docs` responde 200 (confirma que Swagger
   UI se sirve).
2. Test que valide que el router de tareas está registrado (`/tasks/` en
   `app.routes`).

**Esfuerzo estimado: Bajo**

Un par de aserciones rápidas sobre la instancia `app`. No aportarían cobertura
numérica nueva, pero sí confianza en el arranque.

---

## Resumen de esfuerzo

| Módulo | Cobertura actual | Tests nuevos | Esfuerzo |
|---|---|---|---|
| `base_de_datos.py` | 67 % → ~100 % | 1-2 tests | Bajo |
| `rutas/tareas.py` | 76 % → ~100 % | 6 tests | Medio |
| `principal.py` | 100 % (mejorar confianza) | 1-2 tests | Bajo |

Cubrir los módulos 1 y 3 llevaría la cobertura total a ~90 %. Añadir los 6
tests del módulo 2 la llevaría a ~100 %.
