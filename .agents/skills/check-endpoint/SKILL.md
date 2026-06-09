---
name: check-endpoint
description: Verifica que un endpoint específico de la API responde correctamente.
triggers: ["user"]
argument-hint: <ruta del endpoint>
---

## Contexto actual
- Rama: !`git branch --show-current`
- Servidor: http://localhost:8000

## Verificación

1. Arranca la API: uvicorn aplicacion.principal:app --port 8000 &
2. Espera 3 segundos a que arranque
3. Ejecuta: curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$0
4. Verifica que la respuesta tiene código 200
5. Muestra el body completo: curl -s http://localhost:8000$0
6. Para el servidor: kill $(lsof -t -i:8000)

## Resultado esperado
- Código HTTP: 200
- Endpoint verificado: $0
