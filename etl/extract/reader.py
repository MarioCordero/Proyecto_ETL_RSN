"""
=============================================================================
Proyecto ETL RSN — Extract Layer (Fase 3)
=============================================================================
Responsabilidad: Leer el archivo fuente Catalogo_RSN_v2022.txt (TSV) y
retornar los registros crudos como una lista de diccionarios.

Seguridad:
  - El path del archivo se recibe como parámetro, nunca desde input del usuario.
  - Se valida que el path resuelto esté dentro del directorio permitido para
    prevenir ataques de path traversal (CWE-22).
  - No se usan funciones de ejecución de sistema operativo.
=============================================================================
"""