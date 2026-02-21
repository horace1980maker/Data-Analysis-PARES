# Sistema de Análisis de Datos PARES — Resumen Ejecutivo

## ¿Qué es este sistema?

El **Sistema PARES** es una plataforma de procesamiento de datos que toma **información cruda de encuestas y talleres de campo** recolectada en paisajes vulnerables de Centroamérica y la transforma en **recomendaciones estratégicas claras y basadas en evidencia** para inversiones en **Soluciones basadas en la Naturaleza (SbN)** y **Adaptación basada en Ecosistemas (AbE)**.

En términos prácticos: los equipos de campo completan libros Excel estandarizados durante talleres y entrevistas. Este sistema ingiere esos libros, limpia y estructura los datos, y luego ejecuta cinco líneas de análisis ("Storylines") que responden a las preguntas críticas que los tomadores de decisión necesitan resolver antes de comprometer recursos.

---

## Cómo Funciona (Flujo General)

```
  Datos crudos de campo (Excel)
        │
        ▼
  ┌──────────────────────────┐
  │  1. CONVERSIÓN DE DATOS  │  Limpia, valida y reestructura las
  │     (Convertidor)        │  hojas de cálculo crudas en una base
  └──────────┬───────────────┘  de datos analítica estandarizada
             │                  (tablas LOOKUP + TIDY)
             ▼
  ┌──────────────────────────┐
  │  2. MOTOR DE ANÁLISIS    │  Cinco líneas temáticas (Storylines)
  │   (5 Storylines)         │  calculan índices, rankings y alertas
  └──────────┬───────────────┘
             │
             ▼
  ┌──────────────────────────┐
  │   3. ENTREGABLES         │  Reportes HTML interactivos, resúmenes
  │   (Reportes y Datos)     │  en Excel, visualizaciones y paquetes
  └──────────────────────────┘  ZIP descargables
```

---

## Los 5 Storylines en resumen

| #   | Storyline                        | Preguntas Clave que Responde                                                                                                                                                                | Producto Principal                                                                                                                |
| --- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Priorización**                 | **¿Dónde debemos actuar primero?**<br>_También:_ ¿Qué medios de vida están en mayor riesgo de colapso?<br>¿Dónde están las mayores brechas de capacidad?                                    | Ranking de medios de vida y zonas geográficas por urgencia, severidad de amenazas y brechas de capacidad adaptativa.              |
| 2   | **Líneas de Vida Ecosistémicas** | **¿Qué servicios ecosistémicos son más críticos?**<br>_También:_ ¿Qué amenazas específicas están rompiendo estas líneas de vida?<br>¿Qué ecosistemas actúan como "infraestructura crítica"? | Mapa de dependencias (Ecosistema → Servicio → Medio de Vida) identificando puntos de apalancamiento para máximo impacto.          |
| 3   | **Equidad y Vulnerabilidad**     | **¿A quién no debemos dejar atrás?**<br>_También:_ ¿Existen barreras de acceso para mujeres o jóvenes?<br>¿Qué grupos sufrirán desproporcionadamente si no actuamos?                        | Alertas de "No Acción con Daño" identificando grupos diferenciadamente afectados (género, etnia, edad) y barreras de acceso.      |
| 4   | **Gobernanza y Conflicto**       | **¿Es viable la intervención?**<br>_También:_ ¿Quiénes son los actores clave (campeones) para liderar el cambio?<br>¿Qué conflictos actuales podrían bloquear la implementación?            | Análisis de redes de actores, cobertura de espacios de diálogo y mapeo de riesgos de conflicto.                                   |
| 5   | **Portafolio SbN y Monitoreo**   | **¿Qué debemos financiar y cómo lo medimos?**<br>_También:_ ¿Qué acciones son "para hacer ya" vs "para hacer después"?<br>¿Qué indicadores mínimos nos dirán si estamos teniendo éxito?     | Portafolio integrado de acciones ("Hacer ahora / Hacer después / Hacer más adelante") con plan de monitoreo (MEAL) auto-generado. |

> **El Storyline 5** sintetiza los resultados de los cuatro anteriores en una recomendación lista para inversión.

---

## ¿Por qué es importante para quienes toman decisiones?

| Beneficio              | Descripción                                                                                                                                                                                                                |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Reproducibilidad**   | Cada recomendación es trazable hasta los datos de campo; los resultados pueden regenerarse con un solo clic.                                                                                                               |
| **Comparabilidad**     | La estructura de datos estandarizada permite comparaciones entre paisajes y entre países.                                                                                                                                  |
| **Velocidad**          | Lo que antes requería semanas de análisis manual en hojas de cálculo ahora se ejecuta en minutos.                                                                                                                          |
| **Transparencia**      | Reportes de aseguramiento de calidad integrados señalan problemas en los datos (duplicados, IDs faltantes), y el análisis de sensibilidad verifica si los rankings se mantienen bajo diferentes escenarios de ponderación. |
| **No Acción con Daño** | Las dimensiones de equidad y conflicto están incorporadas en el análisis desde el inicio, no añadidas como un paso posterior.                                                                                              |

---

## ¿Qué Entra / Qué Sale?

| Entrada                                                                                        | Salida                                                                           |
| ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Libros Excel crudos de la recolección de datos PARES (talleres, encuestas, mapeos de actores). | **Reportes HTML interactivos** con gráficos y tablas por cada Storyline.         |
|                                                                                                | **Libros Excel de análisis** con tablas LOOKUP y TIDY estructuradas.             |
|                                                                                                | **Visualizaciones** (gráficos PNG: cuadrantes, mapas de calor, grafos de redes). |
|                                                                                                | **Paquetes ZIP descargables** con todos los activos generados.                   |

---

## Despliegue Técnico (resumen)

- **Tecnología**: Python (Pandas, NumPy, Matplotlib), servido mediante una aplicación web **FastAPI**.
- **Interfaz**: Los usuarios interactúan a través de una **interfaz web moderna** (subir archivo → elegir análisis → descargar resultados).
- **Contenerizado**: Se distribuye con Docker para despliegue consistente en cualquier entorno.
- **Listo para integración**: Toda la funcionalidad también está disponible a través de endpoints REST para integración con otros sistemas.

---

## Alineación con Estándares Internacionales

El marco analítico se fundamenta en tres referencias internacionales clave:

### 1. Estándar Global de la UICN para Soluciones basadas en la Naturaleza (v2.0)

La [Unión Internacional para la Conservación de la Naturaleza (UICN)](https://iucn.org/our-work/topic/iucn-global-standard-nature-based-solutions) establece ocho criterios para el diseño y verificación de SbN. El sistema PARES los incorpora de la siguiente manera:

- **Criterios de priorización**: Los Storylines 1 y 2 evalúan la relación ecosistema → servicio → medio de vida para identificar puntos de apalancamiento, alineándose con el criterio de la UICN que exige que las SbN generen beneficios simultáneos para la biodiversidad y el bienestar humano.
- **Salvaguardas sociales y ambientales**: El Storyline 3 (Equidad) y el Storyline 4 (Gobernanza y Conflicto) operan como salvaguardas integradas de "No Acción con Daño", verificando la inclusión de grupos vulnerables y la viabilidad de gobernanza antes de recomendar intervenciones.
- **Indicadores de monitoreo**: El Storyline 5 utiliza una librería de 12 plantillas de indicadores estándar basados en guías de la UICN y Adaptación basada en Ecosistemas (AbE) para generar planes MEAL automáticos.

### 2. IPCC AR6 Grupo de Trabajo II — Impactos, Adaptación y Vulnerabilidad

El [Sexto Informe de Evaluación del IPCC, Grupo de Trabajo II](https://www.ipcc.ch/report/ar6/wg2/) provee la base conceptual para evaluar vulnerabilidad climática y opciones de adaptación. Su influencia en PARES incluye:

- **Marco de vulnerabilidad**: La estructura de análisis del Storyline 1 (amenazas → impactos → brecha de capacidad adaptativa) refleja el marco del IPCC que define la vulnerabilidad como función de la exposición, la sensibilidad y la capacidad adaptativa.
- **Dimensiones de impacto**: Las ocho dimensiones de impacto evaluadas (económico, social, salud, educación, ambiental, político, conflicto y migración) se alinean con las categorías de riesgo identificadas por el IPCC para América Central.
- **Evidencia para la adaptación**: Las recomendaciones del portafolio SbN (Storyline 5) se enmarcan dentro de las opciones de adaptación basada en ecosistemas validadas por el IPCC.

### 3. Análisis de Decisión Multicriterio (MCDA)

Siguiendo las mejores prácticas establecidas por la [Guía del Gobierno del Reino Unido](https://analysisfunction.civilservice.gov.uk/policy-store/an-introductory-guide-to-mcda/), el sistema implementa MCDA como mecanismo de priorización transparente y reproducible:

- **Índice de Prioridad de Acción (API)**: Combina tres métricas normalizadas (prioridad comunitaria, riesgo de impacto y brecha de capacidad) mediante ponderación aditiva: `API = w₁·Prioridad + w₂·Riesgo + w₃·Brecha`.
- **Análisis de sensibilidad**: Se ejecutan tres escenarios de ponderación ("Balanceado", "Prioridad MdV" y "Prioridad Riesgo") para verificar la estabilidad de los rankings, asegurando que las recomendaciones no dependan de una sola configuración de pesos.
- **Trazabilidad**: Cada entrada del índice compuesto es rastreable hasta los datos de campo originales, cumpliendo con el principio de transparencia del MCDA.

---

_Para detalles técnicos de implementación, consulte `README.md` y la carpeta `docs/` dentro del repositorio._
