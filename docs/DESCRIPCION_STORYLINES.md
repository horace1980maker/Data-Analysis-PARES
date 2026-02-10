# Sistema PARES de Análisis para Soluciones basadas en la Naturaleza (SbN)

## Visión General

El sistema PARES es una plataforma de análisis de datos que transforma información territorial compleja en recomendaciones estratégicas para inversiones en Adaptación basada en Ecosistemas (AbE) y Soluciones basadas en la Naturaleza (SbN).

A partir de datos recolectados en campo sobre medios de vida, servicios ecosistémicos, amenazas climáticas, actores y conflictos, el sistema genera automáticamente **5 reportes temáticos** (Storylines) que responden a las preguntas clave para la toma de decisiones de inversión en paisajes vulnerables.

---

## Arquitectura de Datos

El sistema funciona con dos capas de datos:

1.  **Tablas LOOKUP (Dimensiones)**: Catálogos de referencia (territorios, medios de vida, servicios ecosistémicos, actores, etc.).
2.  **Tablas TIDY (Hechos)**: Registros de relaciones y valoraciones entre elementos (prioridades, impactos de amenazas, vínculos servicio-medio de vida, etc.).

A partir de estas tablas, cada Storyline calcula métricas específicas y genera visualizaciones y tablas resumen.

---

## Los 5 Storylines: De los Datos a la Decisión

### Storyline 1: "¿Dónde actuar primero?"
**Pregunta Clave**: *¿Qué medios de vida y grupos deben priorizarse para las acciones de SbN/adaptación, y por qué?*

| Análisis | Fuente de Datos |
| :--- | :--- |
| Puntaje de prioridad por medio de vida | Priorización comunitaria (TIDY_3_2) |
| Impacto de amenazas | Mapeo de amenazas-MdV (TIDY_4_2_1) |
| Brecha de capacidad adaptativa | Encuesta de capacidades (TIDY_7_1) |
| **Índice Compuesto de Prioridad de Acción (API)** | Combinación ponderada de los tres anteriores |

**Producto Principal**: Ranking de los "Top 10 Medios de Vida Prioritarios" con evidencia de riesgo y brechas.

---

### Storyline 2: "Líneas de vida ecosistémicas"
**Pregunta Clave**: *¿Qué servicios ecosistémicos son más críticos para los medios de vida, y qué amenazas los debilitan?*

| Análisis | Fuente de Datos |
| :--- | :--- |
| Índice de Criticidad del Servicio (SCI) | Usuarios, dependencia, estacionalidad (TIDY_3_5) |
| Índice de Apalancamiento Ecosistémico (ELI) | Conexiones Ecosistema→Servicio→MdV (TIDY_3_4) |
| Amenazas sobre servicios | Mapeo amenazas-servicios (TIDY_4_2_2) |

**Producto Principal**: Diagrama de dependencias Ecosistema → Servicio → Medio de Vida, identificando los "puntos críticos" donde una inversión tendría mayor efecto multiplicador.

---

### Storyline 3: "Equidad y vulnerabilidad diferenciada"
**Pregunta Clave**: *¿Quiénes son los más afectados y excluidos, y cómo evitar profundizar inequidades?*

| Análisis | Fuente de Datos |
| :--- | :--- |
| Índice de Vulnerabilidad de Equidad (EVI) | Grupos diferenciados y sus impactos (TIDY_4_2_1_DIF) |
| Barreras de acceso | Narrativas de exclusión (TIDY_3_5) |
| Perfiles de impacto diferenciado | Dimensiones de impacto por subgrupo |

**Producto Principal**: Identificación de "señales de alerta" (Do-No-Harm flags) para que las inversiones no excluyan a grupos vulnerables.

---

### Storyline 4: "Viabilidad, gobernanza y riesgo de conflicto"
**Pregunta Clave**: *¿Qué acciones son implementables y qué dinámicas de conflicto podrían bloquearlas?*

| Análisis | Fuente de Datos |
| :--- | :--- |
| Centralidad de actores | Red de relaciones de actores (TIDY_5_1_REL) |
| Cobertura de espacios de diálogo | Participación en espacios (TIDY_5_2) |
| Índice de Riesgo de Conflicto | Eventos de conflicto y actores (TIDY_6_1, TIDY_6_2) |
| Mapeo Amenaza-Conflicto | Vínculos entre riesgos climáticos y conflictos (TIDY_4_2_X_MAPEO) |

**Producto Principal**: "Mapa de implementación" con campeones, coaliciones necesarias y notas de mitigación de conflictos.

---

### Storyline 5: "Portafolio de SbN y Plan de Monitoreo"
**Pregunta Clave**: *¿Cuál es el portafolio recomendado de SbN/adaptación, y cómo se medirán los resultados?*

Este Storyline **integra los resultados de los 4 anteriores** para construir un portafolio priorizado de acciones.

| Dimensión Integrada | Fuente |
| :--- | :--- |
| Potencial de Impacto | Storyline 1 |
| Apalancamiento Ecosistémico | Storyline 2 |
| Urgencia de Equidad | Storyline 3 |
| Viabilidad de Implementación | Storyline 4 |

**Productos Principales**:
1.  **Tabla de Portafolio de Acciones**: Clasificada en "Hacer ahora" / "Hacer después" / "Hacer más adelante".
2.  **Plan de Monitoreo (MEAL)**: Indicadores específicos seleccionados automáticamente para cada acción recomendada.

---

## Diferenciador Clave: Robustez y Transparencia

Para que la priorización sea defendible ante financiadores, el sistema incluye:

*   **Análisis de Sensibilidad**: Cada clasificación se ejecuta bajo 3 escenarios de pesos (ej. "primero equidad", "primero viabilidad") para mostrar la estabilidad de las recomendaciones.
*   **Apéndice de Calidad de Datos (QA)**: Resumen de posibles problemas en los datos originales (duplicados, IDs faltantes) para generar confianza en el proceso.

---

## Resumen de Flujo

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Datos de Campo (Excel PARES)                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│    Conversión a Modelo LOOKUP + TIDY (Datos Estructurados)          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   Storyline 1            Storyline 2             Storyline 3
   (Prioridad)            (Líneas de Vida)        (Equidad)
        │                       │                       │
        ▼                       ▼                       ▼
   Storyline 4            Storyline 5 ◄────────────────┘
   (Viabilidad)          (Portafolio + MEAL)
        │                       
        └──────────────────────►┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│   Reportes HTML Interactivos + Tablas Excel para Decisión          │
└─────────────────────────────────────────────────────────────────────┘
```
