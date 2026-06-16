-- =============================================================================
-- Proyecto ETL RSN — Script de Inicialización DDL (Fase 3)
-- Data Warehouse: Esquema Estrella para Eventos Sísmicos
-- =============================================================================
-- Este script se ejecuta automáticamente cuando el contenedor PostgreSQL
-- arranca por primera vez (directorio /docker-entrypoint-initdb.d/).
-- =============================================================================
-- Crear esquema dedicado para aislar las tablas del DW
CREATE SCHEMA IF NOT EXISTS dw;
-- Establecer el esquema por defecto para este script
SET search_path TO dw;
-- =============================================================================
-- DIMENSIONES
-- =============================================================================
-- -----------------------------------------------------------------------------
-- dim_tiempo: Dimensión temporal con granularidad de hora
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_tiempo (
    id_tiempo UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    anio SMALLINT NOT NULL CHECK (
        anio BETWEEN 1900 AND 2100
    ),
    mes SMALLINT NOT NULL CHECK (
        mes BETWEEN 1 AND 12
    ),
    dia SMALLINT NOT NULL CHECK (
        dia BETWEEN 1 AND 31
    ),
    hora SMALLINT NOT NULL CHECK (
        hora BETWEEN 0 AND 23
    ),
    dia_semana SMALLINT NOT NULL CHECK (
        dia_semana BETWEEN 1 AND 7
    ),
    -- Columna calculada para facilitar consultas de rango
    fecha_completa DATE GENERATED ALWAYS AS (
        MAKE_DATE(anio::INT, mes::INT, dia::INT)
    ) STORED
);
COMMENT ON TABLE dw.dim_tiempo IS 'Dimensión temporal con granularidad de hora para el esquema estrella sísmico.';
COMMENT ON COLUMN dw.dim_tiempo.dia_semana IS '1=Lunes … 7=Domingo (ISO 8601)';
-- Índice para consultas por fecha
CREATE INDEX IF NOT EXISTS idx_dim_tiempo_fecha ON dw.dim_tiempo(fecha_completa);
CREATE INDEX IF NOT EXISTS idx_dim_tiempo_anio_mes ON dw.dim_tiempo(anio, mes);
-- -----------------------------------------------------------------------------
-- dim_ubicacion: Dimensión geográfica
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_ubicacion (
    id_ubicacion UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    latitud NUMERIC(9, 6) NOT NULL CHECK (
        latitud BETWEEN -90 AND 90
    ),
    longitud NUMERIC(9, 6) NOT NULL CHECK (
        longitud BETWEEN -180 AND 180
    ),
    zona_geografica VARCHAR(150) NOT NULL DEFAULT 'Sin clasificar'
);
COMMENT ON TABLE dw.dim_ubicacion IS 'Dimensión de ubicación geográfica del epicentro del evento sísmico.';
CREATE INDEX IF NOT EXISTS idx_dim_ubicacion_zona ON dw.dim_ubicacion(zona_geografica);
-- -----------------------------------------------------------------------------
-- dim_estacion: Dimensión de la estación sísmica que registró el evento
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_estacion (
    id_estacion UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_red VARCHAR(2) NOT NULL,
    codigo_estacion VARCHAR(5) NOT NULL,
    descripcion_sensor VARCHAR(100) NOT NULL DEFAULT 'Desconocido',
    canal VARCHAR(3) NOT NULL,
    latitud NUMERIC(9, 6) NOT NULL CHECK (
        latitud BETWEEN -90 AND 90
    ),
    longitud NUMERIC(9, 6) NOT NULL CHECK (
        longitud BETWEEN -180 AND 180
    ),
    estado_operativo VARCHAR(50) NOT NULL DEFAULT 'Activo' CHECK (
        estado_operativo IN (
            'Activo',
            'Inactivo',
            'Mantenimiento',
            'Desconocido'
        )
    )
);
COMMENT ON TABLE dw.dim_estacion IS 'Dimensión de estaciones de la Red Sismológica Nacional (RSN).';
-- =============================================================================
-- TABLA DE HECHOS
-- =============================================================================
-- -----------------------------------------------------------------------------
-- fact_evento_sismico: Tabla de hechos central del esquema estrella
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fact_evento_sismico (
    id_hecho UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    -- Claves foráneas hacia las dimensiones
    id_ubicacion UUID NOT NULL REFERENCES dw.dim_ubicacion(id_ubicacion) ON DELETE RESTRICT,
    id_tiempo UUID NOT NULL REFERENCES dw.dim_tiempo(id_tiempo) ON DELETE RESTRICT,
    id_estacion UUID REFERENCES dw.dim_estacion(id_estacion) ON DELETE
    SET NULL,
        -- Métricas del evento
        magnitud NUMERIC(4, 2) NOT NULL CHECK (magnitud >= 0),
        profundidad_km NUMERIC(7, 3) CHECK (profundidad_km >= 0),
        error_rms NUMERIC(6, 4) CHECK (error_rms >= 0),
        -- Auditoría
        fecha_carga TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE dw.fact_evento_sismico IS 'Tabla de hechos: cada fila representa un evento sísmico registrado por la RSN.';
COMMENT ON COLUMN dw.fact_evento_sismico.magnitud IS 'Magnitud en escala Richter o equivalente.';
COMMENT ON COLUMN dw.fact_evento_sismico.profundidad_km IS 'Profundidad del hipocentro en kilómetros.';
COMMENT ON COLUMN dw.fact_evento_sismico.error_rms IS 'Error RMS del ajuste de la localización (segundos).';
-- Índices para los patrones de consulta más comunes
CREATE INDEX IF NOT EXISTS idx_fact_id_tiempo ON dw.fact_evento_sismico(id_tiempo);
CREATE INDEX IF NOT EXISTS idx_fact_id_ubicacion ON dw.fact_evento_sismico(id_ubicacion);
CREATE INDEX IF NOT EXISTS idx_fact_magnitud ON dw.fact_evento_sismico(magnitud);
CREATE INDEX IF NOT EXISTS idx_fact_fecha_carga ON dw.fact_evento_sismico(fecha_carga);
-- =============================================================================
-- USUARIO DE APLICACIÓN (Principio de mínimo privilegio)
-- =============================================================================
-- El usuario de la aplicación ETL recibe solo los permisos necesarios.
-- El superusuario postgres/DW_DB_USER ya existe; aquí se crea el rol ETL.
-- TODO(security): En producción, separar el rol de lectura del de escritura
--   y usar mTLS para la autenticación de la conexión a la base de datos.
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = 'etl_loader'
) THEN CREATE ROLE etl_loader LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
END IF;
END $$;
-- Permisos exclusivos sobre el esquema dw
GRANT USAGE ON SCHEMA dw TO etl_loader;
GRANT SELECT,
    INSERT,
    UPDATE ON ALL TABLES IN SCHEMA dw TO etl_loader;
GRANT USAGE,
    SELECT ON ALL SEQUENCES IN SCHEMA dw TO etl_loader;
-- Permisos para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA dw
GRANT SELECT,
    INSERT,
    UPDATE ON TABLES TO etl_loader;
ALTER DEFAULT PRIVILEGES IN SCHEMA dw
GRANT USAGE,
    SELECT ON SEQUENCES TO etl_loader;
-- =============================================================================
-- DATOS DE REFERENCIA INICIALES
-- =============================================================================
-- Zonas geográficas frecuentes en Costa Rica (RSN)
INSERT INTO dw.dim_ubicacion (latitud, longitud, zona_geografica)
VALUES (9.9281, -84.0907, 'Valle Central'),
    (10.4634, -85.1396, 'Guanacaste'),
    (9.0000, -83.3500, 'Zona Sur'),
    (10.0000, -83.0000, 'Caribe'),
    (9.6500, -84.6500, 'Pacífico Central') ON CONFLICT DO NOTHING;
-- Mensaje de confirmación en los logs del contenedor
DO $$ BEGIN RAISE NOTICE '✅ Esquema estrella RSN Data Warehouse inicializado correctamente.';
END $$;