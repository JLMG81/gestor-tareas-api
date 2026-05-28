# ADR-001: Elección de SQLite como base de datos

## Estado
Aceptado

## Contexto
La API de Gestión de Tareas requiere persistencia de datos para almacenar las tareas creadas por los usuarios. Se necesita una solución de base de datos que sea:
- Simple de configurar y mantener
- Adecuada para el volumen de datos esperado (aplicación de gestión de tareas personal)
- Compatible con SQLAlchemy 2.0.49
- Fácil de usar en entornos de desarrollo y pruebas

## Decisión
Se ha seleccionado **SQLite** como sistema de base de datos para la aplicación.

La configuración actual utiliza un archivo local `tareas.db` con la URL de conexión `sqlite:///./tareas.db` [1-cite-0](#1-cite-0) .

## Razones de la decisión
1. **Cero configuración**: SQLite no requiere instalación ni configuración de servidor. El archivo de base de datos se crea automáticamente.
2. **Portabilidad**: La base de datos es un archivo único que puede ser versionado, movido o copiado fácilmente.
3. **Ideal para desarrollo**: Perfecto para entornos de desarrollo y prototipado rápido.
4. **Compatibilidad con tests**: Los tests pueden usar SQLite en memoria para aislamiento total, como ya se implementa en el proyecto [1-cite-1](#1-cite-1) .
5. **Bajo overhead**: No hay proceso de servidor separado, lo que reduce el consumo de recursos.
6. **Suficiente para el caso de uso**: Una API de gestión de tareas personal no requiere las capacidades de escalabilidad de bases de datos cliente-servidor.

## Alternativas consideradas

### PostgreSQL
**Ventajas:**
- Base de datos relacional robusta y madura
- Soporte avanzado para consultas complejas, JSON, índices especializados
- Mejor rendimiento en concurrencia alta
- Escalabilidad horizontal y vertical
- Transacciones ACID completas con mejor aislamiento

**Inconvenientes:**
- Requiere instalación y configuración de servidor
- Mayor complejidad de despliegue y mantenimiento
- Sobredimensionado para una aplicación de gestión de tareas simple
- Necesita gestión de usuarios, permisos y backups separados

### MySQL
**Ventajas:**
- Ampliamente utilizado y documentado
- Buen rendimiento para aplicaciones web
- Ecosistema de herramientas maduro
- Soporte para replicación y clustering

**Inconvenientes:**
- Requiere instalación y configuración de servidor
- Licenciamiento más complejo (edición community vs enterprise)
- Menos características avanzadas que PostgreSQL
- Sobredimensionado para el caso de uso actual

## Consecuencias a largo plazo

### Positivas
- **Mantenimiento simplificado**: No hay servidor de base de datos que administrar
- **Facilidad de onboarding**: Nuevos desarrolladores pueden empezar a trabajar sin configurar infraestructura adicional
- **Costos reducidos**: No hay costos de infraestructura o licencias
- **Backup trivial**: Basta con copiar el archivo `tareas.db`

### Negativas / Riesgos
- **Escalabilidad limitada**: SQLite no está diseñado para alta concurrencia de escritura. Si la aplicación crece significativamente en usuarios o volumen de datos, será necesario migrar a PostgreSQL o MySQL.
- **Limitaciones de características**: No soporta procedimientos almacenados complejos, vistas materializadas, o algunas funciones avanzadas de SQL.
- **Single-writer**: SQLite permite múltiples lectores pero solo un escritor a la vez, lo que puede ser un cuello de botella en escenarios de alta concurrencia.
- **Migración futura**: Si se requiere migrar a PostgreSQL o MySQL, será necesario:
  - Actualizar la URL de conexión en `base_de_datos.py`
  - Instalar el driver correspondiente (psycopg2 para PostgreSQL, mysqlclient para MySQL)
  - Posiblemente ajustar algunas consultas SQL específicas de SQLite
  - Migrar los datos existentes

### Plan de mitigación
Si el proyecto crece y se identifica que SQLite es insuficiente, la migración a PostgreSQL será straightforward gracias al uso de SQLAlchemy ORM, que abstrae la mayoría de las diferencias entre motores de base de datos.
