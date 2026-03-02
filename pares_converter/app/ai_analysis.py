import json
import os
import io
import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

try:
    from dotenv import load_dotenv
    # Load .env file from the project root if it exists
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass


# We will import the storylines modules to process the data
import sys
storyline1_path = os.path.join(os.path.dirname(__file__), "..", "..", "storyline1_pipeline")
if storyline1_path not in sys.path:
    sys.path.insert(0, storyline1_path)

try:
    from storyline1.io import load_tables
    from storyline1.metrics import compute_all_metrics
except ImportError as e:
    load_tables = None
    compute_all_metrics = None

try:
    from pares_converter.ai.scientific_prompts import SYSTEM_PROMPT, build_user_prompt
except ImportError:
    # Fallback if module path issues occur
    SYSTEM_PROMPT = "Eres un científico experto analizando datos PARES. No alucines, mantén rigor científico."
    def build_user_prompt(data): return f"Datos: {data}"

router = APIRouter()

@router.post("/analyze/ai_report")
async def generate_ai_report(
    file: UploadFile = File(...),
    storyline: int = Form(...),
    model_name: str = Form(...)
):
    if storyline != 1:
        raise HTTPException(status_code=400, detail="Solo Storyline 1 está soportada para la generación de reportes IA.")
    
    if load_tables is None or compute_all_metrics is None:
        raise HTTPException(status_code=500, detail="No se pudieron importar los módulos de Storyline 1.")

    # 1. Save uploaded file to temp dir
    content = await file.read()
    tmpdir = tempfile.mkdtemp()
    
    try:
        input_path = Path(tmpdir) / file.filename
        input_path.write_bytes(content)
        
        # 2. Extract Data
        tables, warnings = load_tables(str(input_path))
        metrics_tables = compute_all_metrics(tables, top_n=5, top_n_drivers=3)
        
        # 3. Format Data into Compact Text/JSON for the Prompt
        # We only send essential tables to save tokens and maintain focus
        essential_keys = [
            "rankings_overall_balanced", 
            "threats_overall", 
            "capacity_overall_by_mdv"
        ]
        
        compact_data = {}
        for key in essential_keys:
            if key in metrics_tables and not metrics_tables[key].empty:
                # Convert DataFrame to list of dicts, excluding complex/heavy columns
                df = metrics_tables[key]
                # Drop unnamed or index columns if needed
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                # Convert to dict
                compact_data[key] = df.to_dict(orient="records")
        
        data_json = json.dumps(compact_data, ensure_ascii=False, indent=2)
        
        # 4. Build Prompt
        user_prompt = build_user_prompt(data_json)
        
        # 5. Route to selected AI Model
        report_markdown = ""
        
        if model_name == "gpt-4o-mini" or model_name == "gpt-4o":
            report_markdown = await call_openai(model_name, SYSTEM_PROMPT, user_prompt)
        elif model_name == "glm-4":
            report_markdown = await call_zhipu("GLM-4.7", SYSTEM_PROMPT, user_prompt)
        elif model_name in ["gemma2:27b", "qwen2.5:32b"]:
            report_markdown = await call_ollama(model_name, SYSTEM_PROMPT, user_prompt)
        else:
            raise HTTPException(status_code=400, detail=f"Modelo {model_name} no soportado.")
            
        return JSONResponse(content={
            "success": True,
            "model_name": model_name,
            "report_markdown": report_markdown
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500, 
            content={"error": str(e), "traceback": traceback.format_exc()}
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

async def call_openai(model: str, system_prompt: str, user_prompt: str) -> str:
    try:
        import openai
    except ImportError:
        raise Exception("El paquete 'openai' no está instalado. Ejecuta 'pip install openai'.")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise Exception("Falta la variable de entorno OPENAI_API_KEY")
    
    client = openai.AsyncOpenAI(api_key=api_key)
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
        max_tokens=2000
    )
    return response.choices[0].message.content

async def call_zhipu(model: str, system_prompt: str, user_prompt: str) -> str:
    try:
        from zhipuai import ZhipuAI
    except ImportError:
        raise Exception("El paquete 'zhipuai' no está instalado. Ejecuta 'pip install zhipuai'.")
    
    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        raise Exception("Falta la variable de entorno ZHIPUAI_API_KEY")
    
    client = ZhipuAI(api_key=api_key)
    
    # Zhipu API is synchronous by default in the python SDK so we wrap it
    import asyncio
    
    def fetch():
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        if not response.choices:
            return "Error: Zhipu no devolvió 'choices' en la respuesta."
            
        content = response.choices[0].message.content
        if content is None or content.strip() == "":
            return f"Alerta: Zhipu devolvió un mensaje vacío."
            
        return content
        
    return await asyncio.to_thread(fetch)

async def call_ollama(model: str, system_prompt: str, user_prompt: str) -> str:
    try:
        import httpx
    except ImportError:
        raise Exception("El paquete 'httpx' no está instalado. Ejecuta 'pip install httpx'.")
    
    # Check if a custom Ollama host is defined
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    url = f"{ollama_host}/api/chat"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
        except httpx.ConnectError:
            raise Exception(f"No se pudo conectar a Ollama en {ollama_host}. Asegúrate de que la aplicación Ollama esté corriendo.")
        except httpx.HTTPStatusError as e:
            error_details = e.response.text
            raise Exception(f"Error HTTP Ollama (Status {e.response.status_code}): {error_details}")
        except Exception as e:
            raise Exception(f"Contexto fallo Ollama: {type(e).__name__} - {str(e)}")
