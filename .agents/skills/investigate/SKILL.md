---
name: investigate
description: Investiga en profundidad una parte del código y produce un informe con referencias exactas a archivos y líneas.
allowed-tools: Read, Grep, ListDir
triggers: ["user"]
argument-hint: <tema o área a investigar>
--- 

## Investigación

1. Busca en el repositorio los archivos relacionados con: $ARGUMENTS
2. Lee los archivos más relevantes en profundidad
3. Traza el flujo de llamadas y el flujo de datos entre módulos

## Informe

1. Escribe un resumen de cómo funciona $ARGUMENTS
2. Incluye rutas de archivo y número de línea concretos para cada afirmación
3. Señala cualquier riesgo, caso límite o área que necesite atención
