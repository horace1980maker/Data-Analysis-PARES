# Lógica de Generación de Recomendaciones (Storyline)

Este documento explica **cómo el sistema genera las recomendaciones** para el reporte final.

El motor de recomendaciones se divide en dos partes distintas:

1.  **Storyline 1 (Priorización)**: Identifica _dónde_ actuar (qué Medios de Vida).
2.  **Storyline 5 (Portafolio)**: Identifica _qué_ hacer (Intervenciones) y asigna un nivel de "Hacer Ahora / Hacer Después".

---

## Parte 1: Priorización (Storyline 1)

**Objetivo:** Clasificar los medios de vida (MdV) por urgencia.

El sistema calcula un **Índice de Prioridad de Acción (IPA / API)** para cada medio de vida en cada comunidad.
Fórmula:

```python
Puntaje IPA = (w1 * Prioridad) + (w2 * Riesgo) + (w3 * Brecha_Capacidad)
```

- **Prioridad (40%)**: ¿Qué tan importante es este medio de vida para la comunidad? (Fuente: Votación en talleres)
- **Riesgo (40%)**: ¿Qué tan amenazado está por peligros climáticos/no climáticos? (Fuente: Matriz de Amenazas)
- **Brecha de Capacidad (20%)**: ¿Qué tan poco preparada está la comunidad para adaptarse? (Fuente: Encuesta de Resiliencia)

_Resultado:_ Una lista ordenada de medios de vida. Los Top 10 pasan a Storyline 5.

---

## Parte 2: Construcción del Portafolio (Storyline 5)

**Objetivo:** Convertir los medios de vida priorizados en un plan de acción concreto con intervenciones específicas.

Aquí es donde reside la lógica compleja (`storyline5/portfolio.py`).

### Paso A: Construcción del "Paquete" (Bundle)

Para cada Medio de Vida Prioritario, el sistema construye un "paquete" de datos relacionados:

1.  **Servicios Ecosistémicos**: ¿De qué servicios depende este medio de vida? (ej. Provisión de agua)
2.  **Ecosistemas**: ¿Qué ecosistemas proveen esos servicios? (ej. Bosque Nuboso)
3.  **Amenazas**: ¿Qué está destruyendo esos ecosistemas? (ej. Deforestación, Sequía)

### Paso B: Puntuación de la Intervención

El sistema luego califica la intervención potencial basada en 4 criterios:

1.  **Potencial de Impacto**: (Heredado del Puntaje IPA de Storyline 1).
2.  **Apalancamiento (ELI)**: ¿Este ecosistema apoya a _muchos_ otros medios de vida? (Alto apalancamiento = mejor inversión).
3.  **Equidad (EVI)**: ¿Esta intervención ayuda a grupos vulnerables (mujeres, jóvenes, indígenas)?
4.  **Factibilidad**: ¿Existe alto conflicto o baja gobernanza en esta área? (Actúa como penalización).

### Paso C: Lógica "Hacer Ahora / Hacer Después" (Asignación de Niveles)

Esta es la matriz de decisión central utilizada para asignar el "tier" (nivel) de recomendación:

| Nivel      | Nombre                          | Criterio Lógico                                                                                                        |
| :--------- | :------------------------------ | :--------------------------------------------------------------------------------------------------------------------- |
| **Tier 1** | **HACER AHORA (Inmediato)**     | Alta Urgencia Y Alta Factibilidad.<br>`(API > 0.7) Y (Factibilidad > 0.6)`                                             |
| **Tier 2** | **HACER DESPUÉS (Corto Plazo)** | Alta Urgencia PERO Baja Factibilidad (necesita trabajo de gobernanza primero).<br>`(API > 0.7) Y (Factibilidad < 0.6)` |
| **Tier 3** | **A LARGO PLAZO**               | Menor Urgencia, bueno para planificación estratégica.<br>`(API < 0.7)`                                                 |

### Paso D: El Filtro de Conflicto (Conflict Gate)

_Regla Especial:_ Si el **Riesgo de Conflicto** es "Crítico" (Puntaje > 0.8), la recomendación es **automáticamente degradada** o marcada con una advertencia de "Go/No-Go", independientemente de su prioridad. Esto asegura el principio de "No Hacer Daño".

---

## 3. El Dashboard Interactivo (Lógica Simplificada)

**Distinción Importante:** El Dashboard HTML interactivo utiliza una **lógica simplificada** comparada con el reporte PDF completo.

- **Lógica del Reporte**: Utiliza el algoritmo completo descrito arriba (Tiers 1-3, Filtros de Conflicto).
- **Lógica del Dashboard**:
  1.  Toma los **Top 6 Medios de Vida** ordenados por `i_total` (Importancia).
  2.  Para cada uno, busca el **Servicio Ecosistémico Principal**.
  3.  Identifica la **Amenaza Principal** para ese servicio.
  4.  Vincula esto a una solución genérica (SbN).

### Representación Visual en el Dashboard

En el dashboard (`dashboard_template.html`), las tarjetas se generan vía JavaScript:

```javascript
// Lógica Simplificada del Dashboard (pseudo-código)
const top_mdvs = livelihoods.sort((a, b) => b.i_total - a.i_total).slice(0, 6);

top_mdvs.forEach((mdv) => {
  DisplayCard({
    title: mdv.nombre,
    badge: "Prioridad Alta",
    icon: GetIcon(mdv.sector),
    // Lógica Dinámica implementada:
    action: mdv.intervention_type || "SbN / Restauración",
  });
});
```

_Nota: El dashboard está diseñado para exploración rápida, mientras que el Reporte de Storyline 5 es para planificación detallada de inversiones._

### ¿Por qué esto era "hardcoded"? (Desconexión Técnica)

El Generador del Dashboard (`dashboard_generator.py`) fue diseñado como un visor ligero de pre-cómputo. Lee directamente del **Excel de Entrada** (Pre-Análisis) para generar la visualización.

Sin embargo, la lógica específica de recomendación (ej. asignar "Restauración" vs "Agroforestería") ocurre en el **Pipeline de Storyline 5** (`storyline5/portfolio.py`), el cual genera los **Reportes de Salida** (Post-Análisis).

Debido a que el Generador del Dashboard no ejecuta el pipeline de Storyline 5, no tiene acceso a la columna calculada "Tipo de Intervención". Por lo tanto, `"SbN / Restauración"` se usó probablemente como un **marcador de posición estático** durante el desarrollo.

## 7. Referencias Clave de Literatura

Aunque el proyecto no contiene una base de datos bibliográfica o archivos PDF, la lógica central está explícitamente construida sobre tres marcos internacionales (como se documenta en `docs/RESUMEN_EJECUTIVO.md`):

1.  **Estándar Global de la UICN para Soluciones Basadas en la Naturaleza (v2.0)**
    - _Uso:_ Guía la priorización de co-beneficios en Storylines 1 & 2.
    - _Fuente:_ [IUCN Global Standard](https://iucn.org/our-work/topic/iucn-global-standard-nature-based-solutions)

2.  **IPCC AR6 Grupo de Trabajo II (Impactos, Adaptación y Vulnerabilidad)**
    - _Uso:_ Define el marco de vulnerabilidad (Exposición, Sensibilidad, Capacidad Adaptativa) usado en Storyline 1.
    - _Fuente:_ [IPCC AR6 WGII](https://www.ipcc.ch/report/ar6/wg2/)

3.  **Análisis de Decisión Multicriterio (MCDA) del Gobierno del Reino Unido**
    - _Uso:_ Provee la base matemática para el "Índice de Prioridad de Acción" (IPA) y el análisis de sensibilidad.
    - _Fuente:_ [UK Gov MCDA Guide](https://analysisfunction.civilservice.gov.uk/policy-store/an-introductory-guide-to-mcda/)
