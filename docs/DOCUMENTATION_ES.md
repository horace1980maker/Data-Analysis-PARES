# Convertidor Excel PARES

## Documentación (Español)

### ¿Qué es este convertidor?
El **Convertidor Excel PARES** es una herramienta especializada diseñada para cerrar la brecha entre la recolección de datos brutos y el análisis estructurado en el contexto del marco PARES SES (Sistemas Socio-Ecológicos). Automatiza la transformación de libros de trabajo de Excel desde un formato de origen (específicamente aquellos estructurados como la base de datos **TIERRAVIVA**) hacia una plantilla estandarizada y lista para el análisis (**FINAL_SES**).

### ¿Por qué lo necesitamos?
1.  **Estandarización**: Los datos de campo a menudo se recolectan en formatos que son fáciles para el ingreso de datos pero difíciles de procesar para motores de análisis automatizados o herramientas de visualización. Esta herramienta asegura que cada conjunto de datos siga una estructura rigurosa y uniforme.
2.  **Mapeo de Datos Complejo**: El convertidor maneja reglas de traducción complejas, tales como:
    *   **Relaciones Uno-a-Muchos**: Expandir una sola fila de datos de encuesta en múltiples registros organizados basados en categorías específicas como "Medios de Vida".
    *   **Generación de IDs Determinísticos**: Crear identificadores únicos y estables (UIDs) para ecosistemas, actores y amenazas para asegurar la consistencia entre diferentes versiones de los datos.
    *   **Vinculación entre Módulos**: Relacionar automáticamente a los actores con medios de vida o amenazas específicos basados en coincidencias de palabras clave y lógica predefinida.
3.  **Eficiencia y Precisión**: La conversión manual de estos libros de trabajo consume mucho tiempo y es propensa a errores humanos. La automatización asegura que se mantenga la integridad de los datos y que los problemas de Garantía de Calidad (QA) se identifiquen de inmediato (por ejemplo, hojas faltantes o referencias inconsistentes).
4.  **Flujo de Trabajo Premium**: Al proporcionar tanto una interfaz web moderna como una API robusta, la herramienta se integra perfectamente en la suite de análisis SES, permitiendo a los investigadores preparar rápidamente sus datos para tableros e informes de alta fidelidad.

### Características Clave
*   **Transformación de Módulos**: Soporta la conversión para Medios de Vida (MdV), Ecosistemas (SE), Amenazas, Actores y espacios de Diálogo.
*   **Generación de Tablas "Tidy"**: Produce conjuntos de datos optimizados para el análisis estadístico y la visualización.
*   **Registro de QA**: Incluye metadatos en la salida (GeoId, recuento de problemas de QA) para rastrear la salud de los datos convertidos.
