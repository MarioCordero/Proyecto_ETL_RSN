Aquí tienes el documento formateado en Markdown, limpio y bien estructurado para que sea fácil de leer y navegar:

```markdown
# CI-0141 – Bases de Datos Avanzadas
## Proyecto Programado 2: Desarrollo de ETL y Visualización de Datos

**Universidad de Costa Rica**  
**Escuela de Ciencias de la Computación e Informática (ECCI)**

| Detalle | Información |
| :--- | :--- |
| **Curso** | CI-0141 Bases de Datos Avanzadas |
| **Universidad** | Universidad de Costa Rica (UCR) |
| **Escuela** | Escuela de Ciencias de la Computación e Informática (ECCI) |
| **Proyecto** | Proyecto Programado 2 – ETL y Visualización de Datos |
| **Peso** | 20% de la nota final |
| **Fecha de entrega** | Lunes 22 de junio de 2026 |
| **Cliente** | Oficina institucional a elección del grupo (ver sección 2) |

---

## 1. Información General

Este documento define la especificación del Proyecto Programado 2 del curso CI-0141 Bases de Datos Avanzadas de la Universidad de Costa Rica. El proyecto consiste en el diseño e implementación de un proceso completo de ETL (Extract, Transform, Load) utilizando datos reales de una oficina institucional, culminando en la creación de dashboards y reportes para la toma de decisiones.

---

## 2. Selección del Cliente (Oficina Institucional)

Cada grupo debe seleccionar una oficina institucional como cliente para el proyecto. La oficina debe generar datos en al menos 3 formatos distintos (por ejemplo: CSV, base de datos relacional y API) y estar dispuesta a facilitar acceso a sus datos para fines académicos.

### 2.1 Ejemplos de oficinas institucionales
A continuación se listan algunos ejemplos de oficinas que podrían servir como cliente. Los grupos no están limitados a estas opciones:
* **Red Sismológica Nacional (RSN) UCR-ICE:** datos sísmicos y vulcanológicos, catálogos históricos, estaciones de monitoreo, datos en tiempo real.
* **Oficina de Registro e Información (ORI) UCR:** datos de matrícula, rendimiento académico, oferta de cursos, estadísticas estudiantiles.
* **Centro Nacional de Alta Tecnología (CeNAT):** datos de investigación, sensores ambientales, información geoespacial.
* **Instituto Meteorológico Nacional (IMN):** datos climáticos, estaciones meteorológicas, pronósticos, registros históricos.
* **Caja Costarricense de Seguro Social (CCSS):** datos de atención médica, estadísticas epidemiológicas, indicadores de gestión.
* **Municipalidades:** permisos de construcción, recaudación tributaria, gestión de servicios públicos, catastro.

### 2.2 Criterios de selección
* La oficina debe contar con datos en al menos 3 formatos diferentes (requisito del proyecto).
* Los datos deben tener volumen suficiente para justificar un proceso de ETL.
* Debe existir disposición de la oficina para facilitar el acceso a los datos.
* Se valorará la complejidad y riqueza de los datos seleccionados.

### 2.3 Justificación
Cada grupo debe incluir en su documentación una justificación de por qué eligieron esa oficina institucional, describiendo el valor que un Data Warehouse y los dashboards/reportes aportarían a la toma de decisiones de dicha oficina.

---

## 3. Objetivos del Proyecto

### 3.1 Objetivo General
Diseñar e implementar un sistema ETL que integre datos de la oficina institucional seleccionada desde múltiples fuentes y formatos, los transforme y cargue en un Data Warehouse, y los presente mediante dashboards interactivos y reportes analíticos.

### 3.2 Objetivos Específicos
1. Identificar y conectar al menos 3 fuentes de datos en formatos distintos (CSV, base de datos relacional, API REST).
2. Diseñar un modelo dimensional (estrella o copo de nieve) para el Data Warehouse.
3. Implementar pipelines de ETL con procesos de limpieza, validación y transformación de datos.
4. Desarrollar al menos 5 dashboards interactivos para visualización de datos.
5. Crear al menos 5 reportes analíticos con métricas e indicadores clave.
6. Documentar la arquitectura, decisiones técnicas y manual de usuario.

---

## 4. Alcance del Proyecto

### 4.1 Dentro del alcance
* Recolección de datos desde al menos 3 fuentes con formatos diferentes.
* Diseño de arquitectura de datos y modelado dimensional del Data Warehouse.
* Desarrollo de procesos ETL automatizados o semi-automatizados.
* Creación de 5 dashboards interactivos y 5 reportes estáticos/dinámicos.
* Documentación técnica completa del proyecto.
* Validación y control de calidad de los datos procesados.

### 4.2 Fuera del alcance
* Implementación en producción o despliegue para usuarios finales de la oficina.
* Procesamiento de datos en tiempo real (streaming).
* Desarrollo de modelos predictivos o de machine learning.
* Integración con sistemas operacionales internos de la oficina.

---

## 5. Fuentes de Datos

El proyecto debe integrar datos de al menos 3 fuentes con formatos distintos. Los formatos requeridos son: archivos planos (CSV, JSON), base de datos relacional y al menos una API. 

*(Nota: La siguiente tabla es un ejemplo ilustrativo basado en la RSN. Cada grupo debe identificar fuentes equivalentes según la oficina institucional que seleccione).*

| Formato | Fuente | Descripción |
| :--- | :--- | :--- |
| **CSV** | Catálogo de sismos históricos | Archivos descargables del catálogo sísmico de la RSN con campos: fecha, hora, latitud, longitud, profundidad, magnitud. |
| **Base de Datos** | Registros de estaciones sismológicas | Base de datos relacional (PostgreSQL/MySQL) con información de las 175+ estaciones: ubicación, tipo de sensor, estado operativo, registros de mantenimiento. |
| **API REST** | Datos en tiempo real / USGS | API de la RSN (`rsnapiusr.ucr.ac.cr`) o del USGS (`earthquake.usgs.gov`) para consultar sismos recientes en formato JSON/GeoJSON. |

### 5.1 Consideraciones sobre los datos
* Los estudiantes deben gestionar el acceso a los datos directamente con la oficina institucional seleccionada.
* Se deben documentar los acuerdos de confidencialidad o restricciones de uso, si aplican.
* Se permite complementar con datos públicos relacionados al dominio si la oficina no puede proporcionar todos los formatos requeridos.
* Se debe documentar el diccionario de datos de cada fuente.

---

## 6. Arquitectura del Sistema

### 6.1 Arquitectura general
El sistema debe seguir una arquitectura de Data Warehouse clásica con las siguientes capas:
1. **Capa de Extracción (Extract):** Conectores a las fuentes de datos (lectores CSV, conectores de BD, clientes HTTP para APIs).
2. **Capa de Transformación (Transform):** Limpieza, validación, normalización, enriquecimiento y conformado de datos.
3. **Capa de Carga (Load):** Inserción de datos transformados en el modelo dimensional del Data Warehouse.
4. **Capa de Presentación:** Dashboards interactivos y reportes conectados al Data Warehouse.

### 6.2 Modelo dimensional
Se debe diseñar un modelo dimensional (esquema estrella o copo de nieve) adecuado al dominio de la oficina seleccionada. El modelo debe incluir al menos:
* Una o más tablas de hechos con las métricas principales del dominio.
* **Dimensión Tiempo:** Año, mes, día, hora, día de la semana *(obligatoria)*.
* Al menos 3 dimensiones adicionales relevantes al dominio (ej: ubicación, categoría, entidad, estado).
* Claves subrogadas en todas las dimensiones.
* *Ejemplo RSN:* Hechos = eventos sísmicos; Dimensiones = tiempo, ubicación, estación, clasificación de magnitud.

### 6.3 Selección de herramientas
Los estudiantes deben seleccionar las herramientas tecnológicas basados en las necesidades del cliente y la infraestructura disponible. Se debe justificar la elección en la documentación. Algunas opciones incluyen:
* **ETL:** Python (pandas, SQLAlchemy), Pentaho Data Integration, Apache NiFi, Talend, SSIS.
* **Base de datos / DW:** PostgreSQL, MySQL, SQL Server, Snowflake.
* **Visualización:** Power BI, Tableau, Apache Superset, Metabase, Grafana.
* **Orquestación (opcional):** Apache Airflow, Prefect, Luigi.

---

## 7. Especificación del Proceso ETL

### 7.1 Extracción
* Implementar conectores específicos para cada formato de fuente (CSV parser, DB connector, HTTP client).
* Manejar paginación en APIs y archivos grandes.
* Registrar metadatos de cada extracción: timestamp, cantidad de registros, estado.
* Implementar manejo de errores y reintentos.

### 7.2 Transformación
* **Limpieza:** eliminación de duplicados, manejo de valores nulos, corrección de formatos.
* **Validación:** reglas de negocio específicas del dominio (ej: rangos válidos, consistencia entre campos, integridad de relaciones).
* **Normalización:** unificación de formatos de fecha/hora, codificaciones, unidades de medida y nomenclaturas entre fuentes.
* **Enriquecimiento:** derivación de campos calculados, clasificaciones automáticas, agregaciones relevantes al dominio.
* **Conformado:** mapeo a dimensiones del modelo estrella, generación de claves subrogadas.

### 7.3 Carga
* Estrategia de carga inicial (full load) y cargas incrementales.
* Manejo de Slowly Changing Dimensions (SCD) según corresponda.
* Validación post-carga: conteos, sumas de control, integridad referencial.
* Registro de auditoría: qué se cargó, cuándo, cuántos registros.

---

## 8. Dashboards (mínimo 5)

Cada dashboard debe ser interactivo, con filtros dinámicos y visualizaciones claras, siendo relevantes al dominio de la oficina seleccionada. 

*(Ejemplo basado en la RSN como referencia)*:

| # | Dashboard | Descripción |
| :--- | :--- | :--- |
| 1 | **Mapa de Actividad Sísmica** | Mapa interactivo de Costa Rica con epicentros geolocalizados, filtrable por magnitud, profundidad y rango de fechas. |
| 2 | **Tendencias Temporales** | Gráficos de línea y barras mostrando frecuencia sísmica por mes/año, con líneas de tendencia y promedios móviles. |
| 3 | **Distribución por Magnitud y Profundidad** | Histogramas y scatter plots de magnitud vs. profundidad, con segmentación por zona geográfica. |
| 4 | **Monitor de Actividad Volcánica** | Panel con estado de los volcanes activos, conteo de eventos asociados, nivel de alerta y última actividad registrada. |
| 5 | **KPIs y Resumen Ejecutivo** | Indicadores clave: total de sismos del periodo, magnitud máxima, promedio de profundidad, comparación con periodo anterior. |

### 8.1 Requisitos generales de dashboards
* Cada dashboard debe incluir al menos 3 visualizaciones diferentes (gráficos, mapas, tablas, KPIs).
* Deben contar con filtros interactivos (por fecha, magnitud, región, etc.).
* Diseño responsivo y con paleta de colores consistente.
* Títulos descriptivos y etiquetas claras en ejes y leyendas.

---

## 9. Reportes (mínimo 5)

Los reportes deben ser documentos estructurados que presenten análisis detallados. Pueden ser estáticos (PDF/Word) o dinámicos (generados bajo demanda desde la herramienta de BI).

*(Ejemplo basado en la RSN)*:

| # | Reporte | Descripción |
| :--- | :--- | :--- |
| 1 | **Reporte Mensual de Sismicidad** | Resumen estadístico mensual: cantidad de sismos, magnitud promedio/máxima, distribución geográfica, comparación con meses anteriores. |
| 2 | **Análisis por Zona Geográfica** | Desglose de actividad sísmica por provincia/región, con ranking de zonas más activas y mapas de calor. |
| 3 | **Reporte de Eventos Significativos** | Detalle de sismos con magnitud >= 4.0: ubicación, profundidad, intensidad percibida, poblaciones afectadas. |
| 4 | **Correlación Sísmica-Volcánica** | Análisis cruzado entre actividad sísmica y volcánica, patrones temporales y espaciales de correlación. |
| 5 | **Reporte de Calidad de Datos** | Métricas de completitud, consistencia y validez de las fuentes de datos: registros procesados, descartados, duplicados y anomalías detectadas. |

### 9.1 Requisitos generales de reportes
* Cada reporte debe incluir: título, fecha de generación, periodo analizado, fuentes de datos utilizadas.
* Incluir tanto visualizaciones como tablas de datos de respaldo.
* Agregar interpretaciones textuales de los hallazgos principales.
* Los reportes deben poder generarse para diferentes periodos de tiempo.

---

## 10. Cronograma

El siguiente cronograma sugiere la distribución de actividades para las 3 semanas disponibles antes de la fecha de entrega:

| Fase | Actividad | Periodo | Detalle |
| :--- | :--- | :--- | :--- |
| **Fase 1** | Análisis y recolección de datos | Semana 1 (2–8 jun) | Contactar oficina institucional, identificar fuentes, obtener acceso a datos |
| **Fase 2** | Diseño de arquitectura | Semana 1–2 (5–12 jun) | Modelado dimensional, diseño del Data Warehouse |
| **Fase 3** | Desarrollo del ETL | Semana 2–3 (9–18 jun) | Implementar extracción, transformación y carga |
| **Fase 4** | Dashboards y reportes | Semana 3 (15–20 jun) | Crear al menos 5 dashboards y 5 reportes |
| **Fase 5** | Pruebas y documentación | Semana 3–4 (18–22 jun) | Validación de datos, documentación técnica |
| **Entrega** | Entrega final | Lunes 22 jun | Entrega de todos los artefactos |

---

## 11. Entregables

1. **Código fuente:** Repositorio con todo el código del ETL, scripts de creación de la BD y archivos de configuración.
2. **Data Warehouse:** Base de datos poblada con los datos transformados, incluyendo scripts DDL.
3. **Dashboards:** Mínimo 5 dashboards funcionales e interactivos.
4. **Reportes:** Mínimo 5 reportes analíticos generados desde el DW.
5. **Documentación técnica:** Arquitectura del sistema, modelo dimensional, diccionario de datos, decisiones de diseño, manual de ejecución.
6. **Presentación:** Presentación oral del proyecto (si el profesor lo requiere).

---

## 12. Rúbrica de Evaluación

La evaluación del proyecto se distribuirá de la siguiente manera:

| Criterio | Peso |
| :--- | :--- |
| Fuentes de datos (3+ formatos) | 15% |
| Diseño de arquitectura y Data Warehouse | 20% |
| Desarrollo del ETL (calidad, documentación) | 25% |
| Dashboards (mínimo 5) | 15% |
| Reportes (mínimo 5) | 15% |
| Documentación y presentación | 10% |

---

## 13. Consideraciones Adicionales

* El trabajo es grupal. Todos los miembros deben contribuir de forma equitativa y documentar su participación.
* Se valorará la justificación de las herramientas seleccionadas con base en las necesidades del cliente y la infraestructura disponible.
* Los datos sensibles o confidenciales deben tratarse conforme a los acuerdos establecidos con la oficina institucional.
* Se recomienda utilizar control de versiones (Git) para el código fuente y la documentación.
* Las entregas tardías estarán sujetas a las políticas del curso.
* Se espera que los estudiantes demuestren comprensión de los conceptos de Data Warehousing y ETL vistos en clase.
```
