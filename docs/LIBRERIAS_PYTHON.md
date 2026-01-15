# Librerías Python Utilizadas en el Proyecto

Este documento detalla las bibliotecas de Python empleadas en la aplicación `pares_excel_converter_app`, explicando su función específica y la razón de su elección.

## 1. Backend y Servidor API

### **FastAPI**
*   **Uso**: Es el framework principal de la aplicación web. Gestiona los endpoints (`/validate`, `/analyze/storylineX`), la validación de archivos cargados y sirve la interfaz de usuario estática.
*   **Por qué**: Se eligió por su alto rendimiento (asíncrono), facilidad de uso para crear APIs RESTful y validación automática de datos. Es ideal para conectar la lógica de procesamiento de datos con una interfaz web moderna.

### **Uvicorn**
*   **Uso**: Servidor web ASGI que ejecuta la aplicación FastAPI.
*   **Por qué**: FastAPI requiere un servidor ASGI para funcionar. Uvicorn es el estándar de facto por su velocidad y ligereza.

### **Python-Multipart**
*   **Uso**: Permite a FastAPI procesar cargas de archivos (upload de Excel).
*   **Por qué**: Necesario para el endpoint `/validate` y `/analyze` que reciben archivos `multipart/form-data`.

## 2. Procesamiento de Datos

### **Pandas**
*   **Uso**: Es el motor central del proyecto. Se utiliza para:
    *   Leer y escribir archivos Excel (`read_excel`, `to_excel`).
    *   Limpieza y transformación de datos (TIDY tables).
    *   Cálculo de métricas complejas (agrupaciones, joins, pivotes).
    *   Análisis de grafos "manual" (cálculo de *degree centrality* mediante joins).
*   **Por qué**: Es la herramienta estándar en ciencia de datos por su potencia y flexibilidad para manipular datos tabulares, esencial para convertir los datos crudos de Excel en insights estructurados.

### **NumPy**
*   **Uso**: Soporte para operaciones numéricas de bajo nivel, usado internamente por Pandas y para conversiones de tipos (e.g., manejo de `NaN`).
*   **Por qué**: Dependencia fundamental de Pandas y necesaria para cálculos vectorizados eficientes.

### **OpenPyXL**
*   **Uso**: Motor subyacente que permite a Pandas leer y escribir archivos en formato `.xlsx`.
*   **Por qué**: Soporta el formato moderno de Excel, necesario para interactuar con los archivos de entrada (cuestionarios) y generar los reportes de salida.

### **PyYAML**
*   **Uso**: Carga archivos de configuración (`params.yaml`, `config/*.yaml`) que definen parámetros de análisis y mapeos.
*   **Por qué**: Permite separar la configuración del código, facilitando ajustes en los parámetros de los storylines sin modificar el software.

## 3. Visualización y Reportes

### **Matplotlib**
*   **Uso**: Generación de gráficos estáticos (PNG) para los reportes de los Storylines (e.g., gráficos de barras de actores, líneas de tiempo de conflictos, matrices de adyacencia).
*   **Por qué**: Biblioteca robusta y madura para generar visualizaciones programáticas de alta calidad. Aunque existen opciones interactivas, Matplotlib es excelente para generar imágenes estáticas incrustables en reportes HTML y Excel.

## 4. Librerías Estándar (Built-in)

El proyecto también hace uso extensivo de la biblioteca estándar de Python:

*   **`hashlib`**: Generación de IDs estables (hash MD5) para entidades (actores, conflictos) basados en sus nombres/textos.
*   **`re` (Regular Expressions)**: Limpieza avanzada de texto y normalización de nombres de columnas.
*   **`unicodedata`**: Normalización de texto (remoción de acentos/tildes) para asegurar consistencia en los cruces de datos.
*   **`base64`**: Codificación de imágenes para incrustarlas directamente en los reportes HTML (standalone).
*   **`zipfile`**: Empaquetado de los múltiples archivos de salida (Excel, HTML, Figuras) en un solo archivo ZIP descargable.
*   **`dataclasses`**: Definición de estructuras de datos claras y tipadas para la configuración de los pipelines.

---
**Nota sobre Dependencias**: Todas las librerías externas mencionadas en las secciones 1, 2 y 3 deben estar listadas en el archivo `requirements.txt` para asegurar el correcto funcionamiento en el despliegue (Docker/Coolify).
