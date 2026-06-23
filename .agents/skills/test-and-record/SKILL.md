---
name: test-and-record
description: Prueba el flujo principal de la API, graba el resultado en vídeo y lo adjunta al chat.
triggers: ["user"]
---

## Contexto actual
- Rama: !`git branch --show-current`
- Cambios en esta rama: !`git diff main --name-only`

## Configuración
1. Instala dependencias: pip install -r requirements.txt
2. Arranca la API: uvicorn aplicacion.principal:app --port 8000 &
3. Espera a que aparezca "Application startup complete"

## Flujo a probar y grabar
1. Inicia la grabación de pantalla
2. Crea una tarea: POST /tasks/ con title "Tarea de prueba"
3. Lista las tareas: GET /tasks/ y verifica que aparece
4. Obtén la tarea: GET /tasks/{id} y verifica los campos
5. Actualiza la tarea: PATCH /tasks/{id} con status in_progress
6. Elimina la tarea: DELETE /tasks/{id}
7. Verifica que ya no existe: GET /tasks/{id} debe devolver 404
8. Detén la grabación

## Entrega
- Envía el vídeo como adjunto en el chat
- Incluye un resumen de los resultados: qué pasó en cada paso
- Para el servidor: kill $(lsof -t -i:8000)
