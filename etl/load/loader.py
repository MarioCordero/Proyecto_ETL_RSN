"""
=============================================================================
Proyecto ETL RSN — Load Layer (Fase 3)
=============================================================================
Responsabilidad: Insertar los registros transformados en el Data Warehouse
PostgreSQL respetando las relaciones del esquema estrella.

Seguridad:
  - TODAS las consultas usan parámetros (psycopg2 parameterized queries).
  - Nunca se construyen queries con concatenación de strings (CWE-89).
  - La conexión se configura desde variables de entorno, no desde código.
  - Los errores de BD se loguean internamente; no se exponen al cliente.
=============================================================================
"""