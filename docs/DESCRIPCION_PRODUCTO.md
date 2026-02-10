# Sistema de Análisis y Conversión PARES

## Visión General del Producto
El **Sistema PARES** es una plataforma integral de inteligencia de datos diseñada para transformar la complejidad de los territorios vulnerables en hojas de ruta claras para la inversión en **Soluciones basadas en la Naturaleza (SbN)** y Adaptación basada en Ecosistemas (AbE).

Actúa como un puente tecnológico que estandariza datos crudos recolectados en campo y los procesa mediante algoritmos avanzados para generar **5 Storylines Estratégicos**, respondiendo preguntas críticas sobre dónde, cómo y con quién actuar para maximizar el impacto social y ecológico.

---

## Propuesta de Valor

### 1. De la Intuición a la Evidencia
Reemplaza la toma de decisiones basada en anécdotas por un análisis riguroso y reproducible. Cada recomendación está respaldada por índices cuantitativos (vulnerabilidad, criticidad de servicios ecosistémicos, riesgo de conflicto).

### 2. Estandarización Total
Elimina el caos de las hojas de cálculo dispares. El módulo **Convertidor** normaliza automáticamente bases de datos heterogéneas (formato TIERRAVIVA) en una estructura maestra ("Tidy Data"), garantizando que los análisis sean comparables entre diferentes paisajes y países.

### 3. Enfoque "Do No Harm" (No Acción con Daño)
Integra explícitamente variables de equidad y conflicto. El sistema alerta sobre posibles impactos negativos en grupos vulnerables o riesgos de exacerbar conflictos existentes, asegurando que las inversiones sean socialmente viables y justas.

---

## Módulos del Sistema

### Módulo 1: El Convertidor
*El motor de limpieza y estandarización.*
*   **Función**: Ingesta archivos Excel crudos, detecta errores de calidad (QA), normaliza nombres y estructuras, y genera una base de datos maestra lista para análisis.
*   **Características Clave**:
    *   Detección automática de duplicados y columnas faltantes.
    *   Interfaz visual para reporte de errores.
    *   Generación de identificadores únicos (UIDs) para trazabilidad.

### Módulo 2: El Analizador (5 Storylines)
*El cerebro estratégico que interpreta los datos.*

| Storyline | Pregunta que Responde | Producto Entregable |
| :--- | :--- | :--- |
| **1. Priorización** | *¿Dónde actuar primero?* | Ranking de medios de vida y grupos geográficos con mayor urgencia y menor capacidad adaptativa. |
| **2. Líneas de Vida** | *¿Qué servicios ecosistémicos son vitales?* | Modelado de dependencias críticas entre ecosistemas y bienestar humano (Índice SCI/ELI). |
| **3. Equidad** | *¿A quién no debemos dejar atrás?* | Análisis de vulnerabilidad diferenciada por género, etnia y grupo etario. |
| **4. Gobernanza** | *¿Es viable intervenir?* | Mapa de actores, redes de influencia y evaluación de riesgos de conflicto social. |
| **5. Portafolio SbN** | *¿Qué vamos a financiar?* | Selección final de intervenciones (SbN) optimizada por impacto, viabilidad y urgencia, con su plan de monitoreo (MEAL). |

---

## Especificaciones Técnicas
*   **Entrada**: Archivos Excel (formato TIERRAVIVA/PARES) con múltiples hojas de encuestas y talleres.
*   **Motor de Procesamiento**: Python (Pandas + NumPy) con algoritmos determinísticos para reproducibilidad.
*   **Salidas**:
    *   Reportes interactivos HTML (visualización de datos).
    *   Tablas Excel "Análisis-Listas" (para investigadores).
    *   Archivos ZIP con todos los activos generados.
*   **Despliegue**: Contenerizado con Docker, accesible vía interfaz web moderna.
