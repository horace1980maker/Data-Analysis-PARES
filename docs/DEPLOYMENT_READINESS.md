# Evaluación de Preparación para Despliegue (Coolify)

Fecha: 2026-01-15
Estado: **NO LISTO / ERROR CRÍTICO**

## 1. Hallazgos Críticos (Bloqueantes)

### 🔴 Dockerfile Incompleto
El `Dockerfile` actual **no funcionará**. La aplicación depende de las carpetas de los pipelines (`storyline1_pipeline`, `storyline2_pipeline`, etc.) para realizar los análisis, pero estas **no se están copiando** a la imagen Docker.

*   **Problema**: Faltan instrucciones `COPY` para las carpetas `storyline*_pipeline`.
*   **Consecuencia**: La aplicación iniciará, pero fallará inmediatamente al intentar ejecutar cualquier análisis (Error 500: `ImportError`).

```dockerfile
# Faltan estas líneas (ejemplo):
COPY storyline1_pipeline ./storyline1_pipeline
COPY storyline2_pipeline ./storyline2_pipeline
...
```

## 2. Hallazgos Importantes

### 🟠 Falta `docker-compose.yaml`
Aunque Coolify puede desplegar desde un Dockerfile, se recomienda encarecidamente incluir un archivo `docker-compose.yaml` para definir explícitamente:
*   El nombre del servicio.
*   El puerto expuesto (8000).
*   La política de reinicio (`restart: always`).
*   Variables de entorno (si fueran necesarias en el futuro).

### 🟠 Dependencias Innecesarias (`requirements.txt`)
El archivo incluye `streamlit>=1.31`.
*   El análisis del código confirmó que la interfaz de usuario antigua (`streamlit_app.py.deprecated`) está deprecada y la nueva UI es HTML/JS estático servido por FastAPI.
*   Mantener `streamlit` aumenta innecesariamente el tamaño de la imagen Docker (~100MB+).

## 3. Estado de la Aplicación

*   **Framework**: FastAPI (Correcto).
*   **Servidor**: Uvicorn (Correcto).
*   **Puerto**: 8000 (Correcto).
*   **Variables de Entorno**: No se detectaron dependencias críticas (`os.getenv` no encontrado en código activo). La configuración es autocontenida.

## 4. Recomendaciones de Acción

1.  **Corregir `Dockerfile`**: Agregar los `COPY` faltantes para los 5 storylines y la carpeta `ui` (si no está incluida dentro de `pares_converter`, verificar estructura).
    *   *Nota: `pares_converter/app/main.py` monta `../ui`. Si `ui` está fuera de `pares_converter`, también debe copiarse.*
    *   Verificado: `ui` está dentro de `pares_converter`? -> *Revisión necesaria: En el `list_dir` anterior, `ui` estaba dentro de `pares_converter`. Entonces `COPY pares_converter ./pares_converter` incluye la UI. Correcto.*
2.  **Crear `docker-compose.yaml`**: Para estandarizar el despliegue.
3.  **Limpiar `requirements.txt`**: Eliminar `streamlit`.

---
**Conclusión**: No despliegue todavía. Se requieren correcciones en el `Dockerfile` para asegurar que el análisis funcione.
