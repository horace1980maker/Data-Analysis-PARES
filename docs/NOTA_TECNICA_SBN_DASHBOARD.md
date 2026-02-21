# Nota Técnica: Lógica del Dashboard Interactivo

Este documento explica las diferencias técnicas entre el **Dashboard Interactivo** (visualizador rápido) y el **Reporte de Storyline 5** (análisis profundo), y detalla los cambios recientes para mejorar la precisión de las recomendaciones.

## 1. Diferencia de Arquitectura

El sistema PARES tiene dos componentes principales que operan de forma separada:

| Componente                                                | Función                                                                                                                          | Lógica                                                                                                                        |
| :-------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------- |
| **Pipeline de Análisis**<br>(`storyline5_pipeline`)       | Genera los **Reportes PDF**. Ejecuta modelos complejos de priorización, análisis de redes, y cálculo de portafolios (Tiers 1-3). | **Completa**: Utiliza pesos, matrices de impacto cruzado, y filtros de gobernanza.                                            |
| **Generador del Dashboard**<br>(`dashboard_generator.py`) | Genera el **Dashboard HTML**. Diseñado para ser un visualizador "ligero" y rápido que lee directamente del Excel de entrada.     | **Simplificada**: Utiliza promedios simples y asignaciones directas para permitir una exploración rápida de los datos crudos. |

### ¿Por qué existen diferencias en los resultados?

Debido a esta separación, el Dashboard **no ejecuta** el pipeline completo de Storyline 5. Por lo tanto:

- **Priorización**: El dashboard ordena los medios de vida basándose únicamente en el puntaje crudo de importancia (`i_total`), sin los ajustes de ponderación fina del reporte.
- **Actores**: El dashboard asigna actores de "Alto Poder" (>7) de forma rotativa a las tarjetas para ilustrar el concepto de liderazgo, mientras que el reporte hace un análisis de redes más profundo.

---

## 2. Solución Nature-based (SbN)

### El Problema Anterior (Texto "Hardcoded")

Anteriormente, todas las tarjetas de priorización en el dashboard mostraban el texto estático:

> _"Acción: SbN / Restauración"_

**Causa Técnica**: Como el generador del dashboard no tenía acceso a la columna de "Tipo de Intervención" calculada por el pipeline complejo de Storyline 5, se usó un marcador de posición genérico durante el desarrollo.

**¿Por qué "Restauración"?**
Este término no salió de los datos del proyecto. Fue un texto **"placeholder" (marcador de posición)** colocado directamente en el código HTML de la plantilla (`dashboard_template.html`) por los desarrolladores originales para visualizar cómo se vería la tarjeta. La "Restauración" es la acción de SbN más genérica y común, por lo que se usó como ejemplo predeterminado a falta de una conexión real con los datos.

### La Nueva Solución (Lógica Dinámica)

Hemos implementado una nueva lógica dentro del generador del dashboard para inferir el tipo de intervención basándose en la **Amenaza Principal** identificada para cada medio de vida.

**Lógica de Asignación:**
El sistema busca la amenaza con mayor impacto para el medio de vida y asigna una acción específica:

| Amenaza Detectada       | Acción SbN Asignada                          |
| :---------------------- | :------------------------------------------- |
| **Sequía**              | Cosecha de Agua y Sistemas Agroforestales    |
| **Inundación**          | Restauración de Riberas y Drenaje Sostenible |
| **Incendios**           | Manejo Integrado del Fuego y Barreras Vivas  |
| **Plagas**              | Manejo Integrado de Plagas y Diversificación |
| **Deslizamientos**      | Estabilización de Laderas y Reforestación    |
| **Deforestación**       | Restauración Ecológica y Agroforestería      |
| **Contaminación**       | Biofiltros y Gestión de Cuencas              |
| **Huracanes / Vientos** | Barreras de Viento y Diversificación         |
| _Otra_                  | Gestión de [Nombre de la Amenaza]            |

### Origen del Mapeo (Justificación Técnica)

**¿De dónde sale esta lista?**
Esta tabla de mapeo fue creada **específicamente para esta actualización del dashboard** basada en estándares internacionales de Soluciones Basadas en Naturaleza (SbN), como los definidos por la UICN.

**No proviene de un archivo existente en el proyecto.**

- **La Brecha**: El proyecto original no tenía una tabla de búsqueda para esto; solo tenía el texto "SbN / Restauración" hardcoded.
- **La Razón**: El reporte complejo de Storyline 5 calcula estos paquetes dinámicamente con datos a los que el dashboard simplificado no tiene acceso.
- **La Solución**: Se creó esta lista heurística estandarizada para asegurar que el dashboard muestre acciones significativas y lógicas en lugar de un texto genérico.

**Personalización**:
Dado que esta lista ahora está definida explícitamente en el código (`dashboard_generator.py`), puede ser fácilmente ajustada para coincidir con la terminología específica de la organización si así se desea.

---

## 3. Asignación de Actores (Liderazgo)

El campo de "Liderazgo" en las tarjetas del dashboard sigue una lógica simplificada para propósitos de visualización:

1.  El sistema filtra la lista de actores del Excel (`TIDY_5_1_ACTORES`).
2.  Identifica aquellos con un puntaje de **Poder > 7**.
3.  Asigna estos actores de alto poder de manera rotativa a las 6 tarjetas principales.

**Nota Importante**: Esta asignación es ilustrativa. Para una planificación estratégica de gobernanza, se debe referir siempre al **Reporte PDF de Storyline 5**, el cual contiene el análisis detallado de la red de actores y sus roles específicos.
