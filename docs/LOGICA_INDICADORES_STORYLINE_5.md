# Lógica de Generación de Indicadores - Storyline 5

Este documento explica cómo se generan y seleccionan los indicadores para el plan de monitoreo en el Storyline 5.

## 1. Origen de los Indicadores (La Fuente)

A diferencia de otros componentes que pueden ser dinámicos, los indicadores en el Storyline 5 **no se generan desde cero** en cada ejecución. En su lugar, provienen de una **librería de mejores prácticas predefinida**.

*   **Ubicación del Código**: `storyline5_pipeline/storyline5/monitoring.py`
*   **Variable Principal**: `INDICATOR_TEMPLATES` (Líneas 21-142 aprox.)

Esta variable es una lista estática en Python que contiene 12 indicadores estándar basados en guías de la UICN y AbE (Adaptación basada en Ecosistemas). Cada plantilla define:
*   Nombre del indicador
*   Tipo (OUTPUT, OUTCOME, GOVERNANCE, EQUITY, CAPACITY, RISK)
*   Definición
*   Unidad de medida
*   Frecuencia sugerida
*   Fuentes de datos sugeridas

Si se desea modificar el texto, agregar nuevos indicadores o cambiar las definiciones, se debe editar directamente esta lista en el archivo `monitoring.py`.

## 2. El Disparador: Paquetes de Acción (Bundles)

El sistema primero construye "Paquetes de Acción" (Bundles), que son combinaciones de:
*   Un Medio de Vida (MdV) prioritario.
*   Servicios Ecosistémicos críticos asociados.
*   Ecosistemas de soporte.

Cada paquete recibe puntuaciones de **Viabilidad**, **Urgencia de Equidad (EVI)** y **Riesgo de Conflicto**.

## 3. Lógica de Selección (El Algoritmo)

Una vez que existen los paquetes, la función `get_priority_indicators_for_bundle` (en `monitoring.py`) asigna automáticamente los indicadores más relevantes para cada paquete basándose en sus características específicas.

La lógica de asignación es la siguiente:

| Condición del Paquete | Indicador Asignado | Tipo | Razón |
| :--- | :--- | :--- | :--- |
| **Siempre** | *Participants engaged in bundle actions* | OUTPUT | Toda acción requiere rastrear la participación básica. |
| **Tiene Servicios Vinculados** | *Perceived availability of critical service* | OUTCOME | Para medir si la acción realmente mejora la disponibilidad del servicio. |
| **Hay datos de Viabilidad** | *Active dialogue spaces* | GOVERNANCE | Para asegurar que las estructuras de gobernanza están activas. |
| **Puntaje EVI > 0.4** | *Participation from prioritized groups* | EQUITY | Una alta vulnerabilidad diferenciada exige un monitoreo estricto de la equidad. |
| **Riesgo de Conflicto > 0.5** | *Conflict dynamics evolution* | RISK | Un alto riesgo requiere monitorear la sensibilidad al conflicto (Do No Harm). |
| **Hay datos de Capacidad** | *Capacity survey score change* | CAPACITY | Para rastrear si el desarrollo de capacidades está siendo efectivo. |

## 4. El Resultado Final

El producto final es la tabla `MONITORING_PLAN` que aparece en los reportes. Esta tabla presenta los indicadores seleccionados para cada acción recomendada ("Do Now" / "Do Next"), listos para ser utilizados en un marco MEAL (Monitoreo, Evaluación, Rendición de Cuentas y Aprendizaje).
