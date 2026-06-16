# Proyecto ETL RSN — Fase 3: Data Warehouse Local 🌋

Pipeline ETL para la carga del **Catálogo Sísmico de la Red Sismológica Nacional (RSN)** a un Data Warehouse PostgreSQL con esquema estrella.

---

## 📁 Estructura del Proyecto

```
Proyecto_ETL_RSN/
├── docker/
│   └── docker-compose.yml      # Stack: PostgreSQL DW + pgAdmin
├── .env.example                # Plantilla de variables de entorno
├── .env                        # Variables reales (NO METER EN EL GIT)
├── .gitignore
│
├── db/
│   └── init.sql                # DDL: esquema estrella (se ejecuta al iniciar)
│
├── data/
│   └── raw/
│       └── Catalogo_RSN_v2022.txt  # Archivo fuente (TSV separado por tabs)
│
├── etl/
│   ├── pipeline.py             # Orquestador principal (CLI)
│   ├── requirements.txt        # Dependencias Python
│   │
│   ├── extract/
│   │   └── reader.py           # Capa E: lee el TSV con validación de path
│   │
│   ├── transform/
│   │   └── cleaner.py          # Capa T: limpia y estructura los datos
│   │
│   └── load/
│       └── loader.py           # Capa L: inserta al DW con queries parametrizados
│
└── doc/
    └── Especificacion_Proyecto_ETL_CI0141.pdf
```

---

## 🚀 Levantar el Entorno Docker

### 1. Configurar variables de entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Si quieren pueden editar el archivo .env con las credenciales deseadas
```

### 2. Levantar los contenedores

```bash
# Levantar en segundo plano
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f postgres_dw

# Verificar estado de los servicios
docker compose ps
```

### 3. Verificar la inicialización de la base de datos

```bash
# Conectarse directamente al contenedor PostgreSQL
docker exec -it rsn_postgres_dw psql -U etl_user -d rsn_dw

# Dentro de psql, verificar las tablas del esquema estrella:
# \dt dw.*
# SELECT * FROM dw.dim_ubicacion;
```

### 4. Acceder a pgAdmin (interfaz gráfica)

Abrir en el navegador: **[http://localhost:5050](http://localhost:5050)**

- **Email:** valor de `PGADMIN_EMAIL` en el `.env`
- **Password:** valor de `PGADMIN_PASSWORD` en el `.env`

**Registrar el servidor PostgreSQL del Data Warehouse en pgAdmin:**
1. Click derecho en _Servers_ → _Register_ → _Server_
2. **General → Name:** `RSN Data Warehouse`
3. **Connection → Host:** `rsn_postgres_dw` (nombre del servicio Docker)
4. **Connection → Port:** `5432`
5. **Connection → Database:** valor DW_DB_NAME  del `.env`
6. **Connection → Username / Password:** valores del `.env`

**Registrar el servidor PostgreSQL de datos del fdsn en pgAdmin:**
1. Click derecho en _Servers_ → _Register_ → _Server_
2. **General → Name:** `FDSN Data Base`
3. **Connection → Host:** `fdsn_postgres_db` (nombre del servicio Docker)
4. **Connection → Port:** `5432`
5. **Connection → Database:** valor RDB_DB_NAME  del `.env`
6. **Connection → Username / Password:** valores del `.env`

---

## 🐍 Ejecutar el Pipeline ETL

### Instalar dependencias Python

```bash
cd etl/
pip install -r requirements.txt
```

### Preparar el archivo fuente

```bash
mkdir -p data/raw
cp /ruta/a/tu/Catalogo_RSN_v2022.txt data/raw/
```

### Ejecutar el pipeline completo

```bash
# Desde la raíz del proyecto
python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt
```

### Modo dry-run (sin escribir a la BD)

```bash
python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt --dry-run
```

### Variables de entorno necesarias para la BD

Asegúrar tener en el `.env`

```bash
export DW_DB_HOST=127.0.0.1
export DW_DB_PORT=5432
export DW_DB_NAME=rsn_dw
export DW_DB_USER=etl_user
export DW_DB_PASSWORD=TuPasswordSegura123!
```

---

## 🛑 Detener y Limpiar

```bash
# Detener contenedores (preserva los datos)
docker compose stop

# Detener y eliminar contenedores (preserva los volúmenes)
docker compose down

# Eliminar TODO incluyendo datos persistentes ⚠️
docker compose down -v
```

---

## 🗄️ Esquema Estrella

```
                    ┌─────────────────┐
                    │   dim_tiempo    │
                    │─────────────────│
                    │ id_tiempo  (PK) │
                    │ anio            │
                    │ mes             │
                    │ dia             │
                    │ hora            │
                    │ dia_semana      │
                    └────────┬────────┘
                             │
  ┌──────────────────┐       │       ┌──────────────────────┐
  │  dim_ubicacion   │       │       │    dim_estacion      │
  │──────────────────│       │       │──────────────────────│
  │ id_ubicacion(PK) │       │       │ id_estacion    (PK)  │
  │ latitud          │       │       │ codigo_estacion      │
  │ longitud         │       │       │ tipo_sensor          │
  │ zona_geografica  │       │       │ estado_operativo     │
  └────────┬─────────┘       │       └──────────┬───────────┘
           │                 │                  │
           └────────┐        │        ┌─────────┘
                    ▼        ▼        ▼
              ┌──────────────────────────────┐
              │      fact_evento_sismico     │
              │──────────────────────────────│
              │ id_hecho       (PK)          │
              │ id_ubicacion   (FK)          │
              │ id_tiempo      (FK)          │
              │ id_estacion    (FK)          │
              │ magnitud                     │
              │ profundidad_km               │
              │ error_rms                    │
              │ fecha_carga                  │
              └──────────────────────────────┘
```

---

## 📋 Requisitos

| Herramienta | Versión mínima |
|-------------|----------------|
| Docker      | 24.x           |
| Docker Compose | 2.x (plugin) |
| Python      | 3.11+          |
| psycopg2-binary | 2.9.9     |
| python-dotenv | 1.0.1        |