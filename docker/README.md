# Guía de Uso Rápido: pgAdmin 4 y Superset (Entorno ETL RSN)

Esta guía detalla el flujo de trabajo dentro de pgAdmin para navegar, consultar y auditar los datos extraídos durante el proceso ETL, utilizando las conexiones previamente configuradas para el Data Warehouse y la base de datos relacional fuente. Además, incluye la configuración y uso inicial de Apache Superset para la visualización de datos.

## 1. Navegación en el Árbol de Objetos (Object Browser)

<dd>

El panel izquierdo de pgAdmin permite visualizar toda la infraestructura de bases de datos. Siga estas rutas para encontrar las tablas relevantes:

### A. Explorando el Data Warehouse (Destino)

1. Despliegue la conexión **Data Warehouse RSN**.
2. Expanda **Databases** > **rsn_datawarehouse**.
3. Expanda **Schemas** (Esquemas).
4. Despliegue el esquema **`dw`** (ignore el esquema `public`).
5. Expanda **Tables**. Aquí encontrará las tablas del modelo estrella (`fact_evento_sismico`, `dim_tiempo`, `dim_ubicacion`, `dim_estacion`, `etl_auditoria`).

### B. Explorando la Base Relacional (Fuente)

1. Despliegue la conexión **Fuente Relacional (OVSICORI/RSN)**.
2. Expanda **Databases** > *(Su base de datos de origen)* > **Schemas** > **public**.
3. Expanda **Tables**. Aquí encontrará las tablas de origen, como `estacion` e `instrumento`.

> **Nota:** Puede hacer clic derecho sobre cualquier tabla y seleccionar **View/Edit Data** > **First 100 Rows**. Esto ejecutará automáticamente un `SELECT * LIMIT 100` y mostrará los datos en formato tabular en la pestaña inferior.

</dd>

## 2. Herramienta de Consultas (Query Tool)

<dd>

La consola SQL es la herramienta principal para auditar las transformaciones, como la generación de UUIDs y la granularidad de los datos.

### Apertura de la consola SQL

1. Seleccione la base de datos a consultar con un clic sobre su nombre (ej. `rsn_datawarehouse`).
2. En el menú superior izquierdo, haga clic en el ícono de **Query Tool** (o vaya a **Tools** > **Query Tool**).
3. Se abrirá una nueva pestaña en el panel derecho.

### Consultas de Auditoría (Ejemplos)

Ejecute las siguientes consultas en el Query Tool para verificar los resultados del proceso ETL. Utilice el botón **Execute/Refresh** o presione `F5`.

**Auditoría 1: Verificar el grano de la tabla de hechos (múltiples canales por sismo)**

```sql
-- Establecemos el esquema 'dw' por defecto
SET search_path TO dw;

-- Verificamos un sismo específico cruzado con la dimensión de estaciones
SELECT 
    t.fecha_completa,
    u.zona_geografica,
    f.magnitud,
    e.codigo_red,
    e.codigo_estacion,
    e.canal,
    f.id_hecho
FROM fact_evento_sismico f
JOIN dim_tiempo t ON f.id_tiempo = t.id_tiempo
JOIN dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
JOIN dim_estacion e ON f.id_estacion = e.id_estacion
ORDER BY t.fecha_completa DESC
LIMIT 50;
```

**Auditoría 2: Validar el conteo general del ETL**

```sql
SET search_path TO dw;

SELECT 'Hechos' AS tabla, count(*) AS total_registros FROM fact_evento_sismico
UNION ALL
SELECT 'Dimensión Tiempo', count(*) FROM dim_tiempo
UNION ALL
SELECT 'Dimensión Ubicación', count(*) FROM dim_ubicacion;
```

</dd>

## 3. Generación del Diagrama Entidad-Relación (ERD)

<dd>

pgAdmin permite generar visualmente el esquema de la base de datos a partir de su definición, lo cual es útil para la documentación del proyecto.

1. Haga clic derecho sobre el nombre de la base de datos (`rsn_datawarehouse`).
2. Seleccione **ERD For Database**.
3. pgAdmin analizará las tablas y llaves foráneas para dibujar el esquema en pantalla.
4. Puede acomodar los elementos gráficos y utilizar el botón **Download Image** en la esquina superior izquierda para exportar el diagrama.

</dd>

## 4. Exportación de Resultados

<dd>

En caso de encontrar anomalías de calidad de datos durante las consultas (por ejemplo, sismos con un `error_rms` inusual), puede exportar los resultados:

1. Ejecute la consulta en el Query Tool.
2. Sobre la cuadrícula de resultados (Data Output), ubique el botón de descarga.
3. Haga clic en **Save results to file** para exportar la salida en formato `.csv`.

Con estas herramientas podrá administrar y auditar el entorno de datos. La información persistirá de manera segura en los volúmenes de Docker.

</dd>

## 5. Configuración Inicial de Superset

<dd>

Una vez finalizada la revisión en pgAdmin, el siguiente paso es configurar Apache Superset para la creación de dashboards. Asegúrese de que los contenedores de Docker estén en ejecución.

**Paso 1: Inicializar y migrar la base de datos interna de Superset**

```bash
docker exec -it rsn_superset superset db upgrade
```

**Paso 2: Crear el usuario administrador**
El sistema solicitará interactuar en la consola para ingresar un nombre de usuario, nombre, apellido, correo electrónico y contraseña.

```bash
docker exec -it rsn_superset superset fab create-admin
```

**Paso 3: Crear los roles por defecto y asignar los permisos necesarios**

```bash
docker exec -it rsn_superset superset init
```

**Paso 4: Instalar el driver de PostgreSQL en el entorno virtual**
Dado que la imagen oficial de Superset restringe la instalación de dependencias, es necesario instalar el driver `psycopg2` en el entorno virtual, asignar los permisos correctos y reiniciar el servicio:

```bash
docker exec -it -u root rsn_superset pip install psycopg2-binary --target /app/.venv/lib/python3.10/site-packages

docker exec -it -u root rsn_superset chown -R superset:superset /app/.venv/lib/python3.10/site-packages

docker restart rsn_superset
```

**Paso 5: Conectar el Data Warehouse en la interfaz**

1. Ingrese a `http://localhost:8088/` e inicie sesión con las credenciales creadas en el Paso 2.
2. Navegue a **Settings** > **Database Connections** > **+ Database** > **PostgreSQL**.
3. Seleccione la opción **"Connect this database with a SQLAlchemy URI string instead"**.
4. Ingrese la siguiente cadena de conexión para enlazar Superset con el Data Warehouse:

```text
postgresql://etl_loader:CHANGE_IN_PRODUCTION@rsn_postgres_dw:5432/rsn_dw
```

*(Nota: Si el nombre de la base de datos en su archivo .env es distinto, ajuste el final de la URI).*

</dd>

## 6. Uso de Superset

<dd>

A continuación, se detalla el proceso para crear el primer dashboard conectando los datos y utilizando consultas SQL directamente.

### Paso 1: Configurar la conexión al Data Warehouse

1. Ingrese a `http://localhost:8088` e inicie sesión.
2. En la esquina superior derecha, diríjase a **Settings** > **Database Connections**.
3. Haga clic en **+ Database** y seleccione **PostgreSQL**.
4. Complete la información de la conexión:
    * **Display Name:** `DW RSN`
    * **SQLAlchemy URI:** `postgresql://rsn_admin:super_password_seguro_123@postgres_dw:5432/rsn_datawarehouse`
    *(Superset se comunica a través de la red interna de Docker, por lo que el host corresponde al nombre del servicio `postgres_dw` definido en el `docker-compose.yml`).*
5. Presione **Test Connection** para verificar la comunicación y, si es exitosa, haga clic en **Connect**.

---

### Paso 2: SQL Lab para la preparación de datos

Superset permite crear conjuntos de datos (Datasets) directamente desde consultas SQL. El siguiente ejemplo prepara los datos para un mapa de actividad sísmica.

1. En el menú superior, seleccione **SQL Lab** > **SQL Editor**.
2. En el panel izquierdo, elija la base de datos (`DW RSN`) y el esquema (`dw`).
3. Ingrese la consulta SQL para cruzar la tabla de hechos con las dimensiones de ubicación y tiempo:

    ```sql
    SELECT 
        f.id_hecho,
        t.fecha_completa,
        f.magnitud,
        f.profundidad_km,
        u.latitud,
        u.longitud,
        e.canal
    FROM dw.fact_evento_sismico f
    JOIN dw.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
    JOIN dw.dim_tiempo t ON f.id_tiempo = t.id_tiempo
    JOIN dw.dim_estacion e ON f.id_estacion = e.id_estacion;
    ```

4. Ejecute la consulta mediante el botón **Run** para previsualizar los resultados.
5. Haga clic en **Save Dataset** (o *Explore*), y asigne el nombre `dataset_mapa_sismico`.

---

### Paso 3: Creación del gráfico geoespacial (deck.gl)

Con el dataset guardado, proceda a configurar la visualización en el mapa.

1. Al guardar el dataset, Superset abrirá la pantalla de exploración gráfica.
2. En el panel izquierdo, bajo **Chart Type**, seleccione **deck.gl Scatterplot**.
3. Configure los parámetros obligatorios:
    * **Longitude & Latitude:** Seleccione las columnas `longitud` y `latitud`.
    * **Point Size:** Utilice `magnitud` para que el tamaño de los puntos sea proporcional a la intensidad del sismo.
    * **Point Color:** Seleccione `profundidad_km` para aplicar una escala de colores basada en la profundidad.
4. Presione **Update Chart** para renderizar el mapa interactivo.
5. Haga clic en **Save**, asigne el nombre "Mapa de Epicentros" y guarde el gráfico.

---

### Paso 4: Armado del Dashboard

1. En el menú principal, diríjase a **Dashboards** > **+ Dashboard**.
2. En el panel derecho, bajo la pestaña **Charts**, arrastre el gráfico "Mapa de Epicentros" hacia el lienzo central y ajuste su tamaño.
3. Para incluir capacidades de filtrado por fechas o magnitud, añada componentes de tipo **Filter Box** desde el panel izquierdo, vinculándolos a su dataset.
4. Finalmente, guarde el dashboard con el nombre "Dashboard 1: Actividad Sísmica".

Este flujo de trabajo es aplicable para crear visualizaciones adicionales, como gráficos de series de tiempo para tendencias históricas o gráficos de dispersión para analizar la relación entre profundidad y magnitud.

</dd>