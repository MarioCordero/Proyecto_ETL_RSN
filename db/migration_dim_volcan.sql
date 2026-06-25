-- =============================================================================
-- Migración: Enriquecimiento volcánico (dim_volcan + FK en la tabla de hechos)
-- =============================================================================
-- Aplica los cambios sobre un Data Warehouse YA EXISTENTE sin romper lo actual.
-- Es idempotente (IF NOT EXISTS), así que se puede correr varias veces.
--
-- Uso:
--   docker exec -i rsn_postgres_dw psql -U etl_user -d rsn_dw < db/migration_dim_volcan.sql
--
-- (En una instalación nueva no hace falta: db/init.sql ya incluye estos cambios.)
-- =============================================================================

-- 1. Nueva dimensión de volcanes -------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_volcan (
    id_volcan UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_volcan VARCHAR(10) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    latitud NUMERIC(9, 6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9, 6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    radio_influencia_km NUMERIC(5, 2) NOT NULL DEFAULT 10 CHECK (radio_influencia_km > 0),
    tipo_manifestacion VARCHAR(100) NOT NULL DEFAULT 'Desconocido',
    CONSTRAINT uq_dim_volcan UNIQUE (codigo_volcan)
);

-- 2. Llave foránea al volcán cercano en la tabla de hechos (NULLABLE) ------------
ALTER TABLE dw.fact_evento_sismico
    ADD COLUMN IF NOT EXISTS id_volcan_cercano UUID
    REFERENCES dw.dim_volcan(id_volcan) ON DELETE SET NULL;

-- 3. Índice para consultas por volcán -------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_id_volcan
    ON dw.fact_evento_sismico(id_volcan_cercano);
