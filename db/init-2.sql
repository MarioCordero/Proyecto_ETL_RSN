-- Crear esquema dedicado para la base relacional
CREATE SCHEMA IF NOT EXISTS relationaldb;
-- Establecer el esquema por defecto para este script
SET search_path TO relationaldb;


-- Exportar la informacion de las estaciones
-- 1. Crear tabla temporal para cargar los datos del archivo txt.
CREATE TABLE IF NOT EXISTS relationaldb.estaciones_staging (
    network      VARCHAR(5),
    station      VARCHAR(5),
    latitude     DECIMAL(9,6),
    longitude    DECIMAL(9,6),
    elevation    DECIMAL(8,2),
    site_name    VARCHAR(100),
    start_time   timestamp,
    end_time     timestamp
);

-- 2. Crear tabla para guardar la informacion de las estaciones
CREATE TABLE IF NOT EXISTS relationaldb.estaciones (
    codigo_red          VARCHAR(5) NOT NULL,
    codigo_estacion     VARCHAR(5),
    latitud             DECIMAL(9,6) NOT NULL,
    longitud            DECIMAL(9,6) NOT NULL,
    elevacion_metros    DECIMAL(8,2) NOT NULL,
    nombre_sitio        VARCHAR(100) DEFAULT 'Desconocido',

    CONSTRAINT estaciones_codigo_PK
        PRIMARY KEY (codigo_estacion)
);

-- 3. Copiar los datos del archivo txt a estaciones_staging
COPY relationaldb.estaciones_staging
FROM '/import/stations_sites.txt'
WITH (
    FORMAT csv,
    DELIMITER '|',
    HEADER true
);

-- 4. pasar a estaciones unicamente las columnas relevantes
INSERT INTO relationaldb.estaciones (
    codigo_red,
    codigo_estacion,
    latitud,
    longitud,
    elevacion_metros,
    nombre_sitio
)
SELECT DISTINCT
    TRIM(network),
    TRIM(station),
    latitude,
    longitude,
    elevation,
    TRIM(site_name)
FROM relationaldb.estaciones_staging
ON CONFLICT (codigo_estacion)
DO NOTHING;

-- 5. Borrar la tabla temporal estaciones_staging
DROP TABLE relationaldb.estaciones_staging;

DO $$ BEGIN RAISE NOTICE '✅ Import de estaciones completado';
END $$;


-- Exportar la informacion de los instrumetos de las estaciones
-- 1. Crear tabla temporal para cargar los datos del archivo txt.
CREATE TABLE IF NOT EXISTS relationaldb.instrumentos_staging (
    network              VARCHAR(5),
    station              VARCHAR(5),
    location             VARCHAR(100),
    channel              VARCHAR(3),
    latitude             DECIMAL(9,6),
    longitude            DECIMAL(9,6),
    elevation            DECIMAL(8,2),
    depth                DECIMAL(8,2),
    azimuth              DECIMAL(8,2),
    dip                  DECIMAL(8,2),
    sensor_description   VARCHAR(100),
    scale                DOUBLE PRECISION,
    scale_freq           DECIMAL(10,4),
    scale_units          VARCHAR(20),
    sample_rate          DECIMAL(10,4),
    start_time           TIMESTAMP,
    end_time             TIMESTAMP
);

-- 2. Crear tabla para guardar la informacion de las estaciones
CREATE TABLE IF NOT EXISTS relationaldb.instrumentos (
    id                      UUID DEFAULT gen_random_uuid(),
    codigo_estacion         VARCHAR(5) NOT NULL,
    canal                   VARCHAR(3) NOT NULL,
    latitud                 DECIMAL(9,6) NOT NULL,
    longitud                DECIMAL(9,6) NOT NULL,
    profundidad_metros      DECIMAL(8,2) NOT NULL,
    elevacion_metros        DECIMAL(8,2) NOT NULL,
    acimut                  DECIMAL(8,2),
    inclinacion             DECIMAL(8,2),
    descripcion             VARCHAR(100) DEFAULT 'Sin descripcion',
    escala                  DOUBLE PRECISION,
    frecuencia_escala_Hz    DECIMAL(10,4),
    unidades_escala         VARCHAR(20),
    frecuencia_muestreo     DECIMAL(10,4),
    inicio_mediciones       TIMESTAMP NOT NULL,
    fin_mediciones          TIMESTAMP,

    CONSTRAINT instrumentos_id_PK
        PRIMARY KEY (id),
    CONSTRAINT instrumentos_codigo_estacion_estaciones_FK
        FOREIGN KEY(codigo_estacion)
        REFERENCES relationaldb.estaciones(codigo_estacion)
);

-- 3. Copiar los datos del archivo txt a instrumentos_staging
COPY relationaldb.instrumentos_staging
FROM '/import/stations_channel.txt'
WITH (
    FORMAT csv,
    DELIMITER '|',
    HEADER true
);

-- 4. pasar a estaciones unicamente las columnas relevantes
INSERT INTO relationaldb.instrumentos (
    codigo_estacion,
    canal,
    latitud,
    longitud,
    profundidad_metros,
    elevacion_metros,
    acimut,
    inclinacion,
    descripcion,
    escala,
    frecuencia_escala_Hz,
    unidades_escala,
    frecuencia_muestreo,
    inicio_mediciones,
    fin_mediciones
)
SELECT DISTINCT
    TRIM(station),
    TRIM(channel),
    latitude,
    longitude,
    depth,
    elevation,
    azimuth,
    dip,
    sensor_description,
    scale,
    scale_freq,
    scale_units,
    sample_rate,
    start_time,
    end_time
FROM relationaldb.instrumentos_staging;

-- 5. Borrar la tabla temporal instrumentos_staging
DROP TABLE relationaldb.instrumentos_staging;

DO $$ BEGIN RAISE NOTICE '✅ Import de instrumentos completado';
END $$;