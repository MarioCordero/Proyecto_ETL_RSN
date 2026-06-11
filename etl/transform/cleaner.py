"""
=============================================================================
Proyecto ETL RSN — Transform Layer (Fase 3)
=============================================================================
Responsabilidad: Limpiar, validar y transformar los registros crudos en
objetos listos para ser insertados en el Data Warehouse (esquema estrella).

Reglas de transformación:
  1. Eliminar filas donde 'magnitud' sea nula, vacía o no numérica.
  2. Eliminar filas con latitud/longitud inválidas.
  3. Convertir tipos de datos al tipo Python correcto.
  4. Construir los sub-objetos para cada tabla del esquema estrella.

Seguridad:
  - Todos los valores se validan antes de ser usados (inputs no confiables).
  - No se usa eval() ni exec() para parsear datos.
  - Los errores de validación se registran en el logger, no se exponen al usuario.
=============================================================================
"""