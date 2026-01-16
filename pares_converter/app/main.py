from __future__ import annotations

import base64
import gc
import io
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .converter import compile_workbook, write_workbook

# Add storylines to path
storyline1_path = os.path.join(os.path.dirname(__file__), "..", "..", "storyline1_pipeline")
storyline2_path = os.path.join(os.path.dirname(__file__), "..", "..", "storyline2_pipeline")
storyline3_path = os.path.join(os.path.dirname(__file__), "..", "..", "storyline3_pipeline")
storyline4_path = os.path.join(os.path.dirname(__file__), "..", "..", "storyline4_pipeline")
storyline5_path = os.path.join(os.path.dirname(__file__), "..", "..", "storyline5_pipeline")
if storyline1_path not in sys.path:
    sys.path.insert(0, storyline1_path)
if storyline2_path not in sys.path:
    sys.path.insert(0, storyline2_path)
if storyline3_path not in sys.path:
    sys.path.insert(0, storyline3_path)
if storyline4_path not in sys.path:
    sys.path.insert(0, storyline4_path)
if storyline5_path not in sys.path:
    sys.path.insert(0, storyline5_path)

app = FastAPI(title="PARES Excel Converter & Analyzer")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def read_index():
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "index.html")
    return FileResponse(ui_path)

@app.get("/converter")
def read_converter():
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "converter.html")
    return FileResponse(ui_path)

@app.get("/analyzer")
def read_analyzer():
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "analyzer.html")
    return FileResponse(ui_path)

# Mount the ui directory to serve CSS/JS as /ui/style.css etc
ui_dir = os.path.join(os.path.dirname(__file__), "..", "ui")
app.mount("/ui", StaticFiles(directory=ui_dir), name="ui")

# Required sheets for each storyline (from storylines.md spec)
STORYLINE_REQUIREMENTS = {
    1: {
        "required": ["LOOKUP_CONTEXT", "LOOKUP_GEO", "LOOKUP_MDV"],
        "recommended": [
            "TIDY_3_2_PRIORIZACION",  # Importance/priority
            "TIDY_4_1_AMENAZAS",       # Threat severity
            "TIDY_4_2_1_AMENAZA_MDV",  # Impacts on livelihoods
            "TIDY_7_1_RESPONSES",      # Adaptive capacity
            "TIDY_7_1_RESPONDENTS",    # Survey respondents
            "LOOKUP_CA_QUESTIONS",     # Capacity questions
        ],
        "description": "Where to Act First? - Priority Analysis"
    },
    2: {
        "required": ["LOOKUP_CONTEXT", "LOOKUP_GEO", "LOOKUP_MDV", "LOOKUP_SE"],
        "recommended": [
            "TIDY_3_4_ECO_SE",         # Ecosystem ↔ service
            "TIDY_3_4_ECO_MDV",        # Ecosystem ↔ MdV
            "TIDY_3_4_ECOSISTEMAS",    # Ecosystems
            "TIDY_3_5_SE_MDV",         # Service ↔ livelihood dependence
            "TIDY_4_2_2_AMENAZA_SE",   # Threats on services
            "LOOKUP_ECOSISTEMA",       # Ecosystem labels
        ],
        "description": "Ecosystem-Service Lifelines"
    },
    3: {
        "required": ["LOOKUP_CONTEXT", "LOOKUP_GEO"],
        "recommended": [
            "TIDY_4_2_1_DIFERENCIADO", # Differentiated impacts (livelihoods)
            "TIDY_4_2_2_DIFERENCIADO", # Differentiated impacts (services)
            "TIDY_3_5_SE_MDV",         # Service ↔ MdV (for inclusion/barriers)
            "TIDY_3_5_SE_INCLUSION",   # Inclusion/exclusion narratives
            "TIDY_7_1_RESPONSES",      # Capacity disaggregation
            "TIDY_7_1_RESPONDENTS",    # Respondent attributes
        ],
        "description": "Equity & Differentiated Vulnerability"
    },
    4: {
        "required": ["LOOKUP_CONTEXT", "LOOKUP_GEO"],
        "recommended": [
            "TIDY_5_1_ACTORES",         # Actors
            "TIDY_5_1_RELACIONES",      # Actor relationships
            "TIDY_5_2_DIALOGO",         # Dialogue spaces
            "TIDY_5_2_DIALOGO_ACTOR",   # Dialogue participation
            "TIDY_6_1_CONFLICT_EVENTS", # Conflicts timeline
            "TIDY_6_2_CONFLICTO_ACTOR", # Actor roles in conflicts
            "TIDY_4_2_1_MAPEO_CONFLICTO", # Threat ↔ conflict links
            "TIDY_4_2_2_MAPEO_CONFLICTO", # Threat ↔ conflict links
        ],
        "description": "Feasibility, Governance & Conflict Risk"
    },
    5: {
        "required": ["LOOKUP_CONTEXT", "LOOKUP_GEO", "LOOKUP_MDV"],
        "recommended": [
            "TIDY_3_2_PRIORIZACION",     # Priority
            "TIDY_4_2_1_AMENAZA_MDV",    # Threat impacts
            "TIDY_3_5_SE_MDV",           # Service-livelihood
            "TIDY_3_4_ECO_SE",           # Ecosystem-service
            "TIDY_4_2_1_DIFERENCIADO",   # Differentiated impacts
            "TIDY_5_1_RELACIONES",       # Actor relations
            "TIDY_6_1_CONFLICT_EVENTS",  # Conflicts
        ],
        "description": "SbN Portfolio Design + Monitoring Plan"
    }
}

@app.post("/validate")
async def validate_file(
    file: UploadFile = File(...),
    storyline: int = Form(1),
):
    """
    Validate an uploaded file for a specific storyline.
    Returns which required and recommended sheets are present/missing.
    """
    content = await file.read()
    
    try:
        xl = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
        available_sheets = set(xl.sheet_names)
    except Exception as e:
        return JSONResponse(content={
            "valid": False,
            "error": f"Cannot read Excel file: {str(e)}",
            "available_sheets": [],
            "missing_required": [],
            "missing_recommended": [],
        })
    
    reqs = STORYLINE_REQUIREMENTS.get(storyline, STORYLINE_REQUIREMENTS[1])
    
    missing_required = [s for s in reqs["required"] if s not in available_sheets]
    missing_recommended = [s for s in reqs["recommended"] if s not in available_sheets]
    present_required = [s for s in reqs["required"] if s in available_sheets]
    present_recommended = [s for s in reqs["recommended"] if s in available_sheets]
    
    is_valid = len(missing_required) == 0
    
    # Check if this looks like a raw database vs converted file
    is_raw_database = "LOOKUP_CONTEXT" not in available_sheets and any(
        s.startswith("1.") or s.startswith("2.") or s.startswith("3.") 
        for s in available_sheets
    )
    
    message = ""
    if is_raw_database:
        message = "This appears to be a raw database file. Please convert it first using the Converter before analyzing."
    elif not is_valid:
        message = f"Missing required sheets: {', '.join(missing_required)}"
    elif missing_recommended:
        message = f"Ready to analyze! Some optional sheets missing: {', '.join(missing_recommended[:3])}"
    else:
        message = "All required and recommended sheets present. Ready to analyze!"
    
    return JSONResponse(content={
        "valid": is_valid,
        "is_raw_database": is_raw_database,
        "storyline": storyline,
        "storyline_name": reqs["description"],
        "message": message,
        "available_sheets": list(available_sheets),
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "present_required": present_required,
        "present_recommended": present_recommended,
    })

@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    org_slug: str = Form("tierraviva"),
    strict: bool = Form(False),
    copy_raw: bool = Form(True),
):
    """
    Convert an Excel workbook using the V2 deterministic compiler.
    
    - **file**: The input Excel file (TIERRAVIVA format)
    - **org_slug**: Organization identifier (used in output filename)
    - **strict**: If True, fail on missing columns. If False, continue with warnings.
    - **copy_raw**: If True, include RAW sheets in output.
    """
    content = await file.read()
    input_buffer = io.BytesIO(content)
    
    try:
        tables = compile_workbook(
            input_path=input_buffer,
            strict=strict,
            copy_raw=copy_raw,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )

    output_buffer = io.BytesIO()
    write_workbook(output_buffer, tables)
    data = output_buffer.getvalue()

    qa_summary = tables.get("QA_TABLE_SUMMARY")
    total_tables = len(tables)
    qa_issues = 0
    if "QA_MISSING_IDS" in tables:
        qa_issues += int(tables["QA_MISSING_IDS"]["missing"].sum()) if not tables["QA_MISSING_IDS"].empty else 0
    if "QA_PK_DUPLICATES" in tables:
        qa_issues += int(tables["QA_PK_DUPLICATES"]["duplicate_rows"].sum()) if not tables["QA_PK_DUPLICATES"].empty else 0
    if "QA_FOREIGN_KEYS" in tables:
        qa_issues += int(tables["QA_FOREIGN_KEYS"]["missing_fk"].sum()) if not tables["QA_FOREIGN_KEYS"].empty else 0

    geo_id = ""
    if "LOOKUP_GEO" in tables and not tables["LOOKUP_GEO"].empty:
        geo_id = str(tables["LOOKUP_GEO"]["geo_id"].iloc[0])

    filename = f"FINAL_{org_slug}_analysis_ready.xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Converter-GeoId": geo_id,
            "X-Converter-QAIssues": str(qa_issues),
            "X-Converter-TotalTables": str(total_tables),
        },
    )


@app.post("/analyze/storyline1")
async def analyze_storyline1(
    file: UploadFile = File(...),
    top_n: int = Form(10),
    include_figures: bool = Form(True),
    include_report: bool = Form(True),
    lang: str = Form("es"),
):
    """
    Run Storyline 1 analysis: "Where to Act First?"
    
    - **file**: Analysis-ready Excel workbook (with LOOKUP_* and TIDY_* sheets)
    - **top_n**: Number of top items in rankings (default: 10)
    - **include_figures**: Generate visualization figures (default: True)
    - **include_report**: Generate HTML report (default: True)
    
    Returns JSON with base64-encoded outputs.
    """
    try:
        from storyline1.io import create_runlog, load_tables, write_outputs
        from storyline1.metrics import compute_all_metrics
        from storyline1.plots import generate_all_plots
        from storyline1.report import generate_report
    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import storyline1 module: {e}"},
        )
    
    content = await file.read()
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    try:
        # Save uploaded file
        input_path = Path(tmpdir) / file.filename
        input_path.write_bytes(content)
        
        outdir = Path(tmpdir) / "output"
        outdir.mkdir()
        
        start_time = datetime.now()
        
        # Step 1: Load tables
        tables, warnings = load_tables(str(input_path))
        
        # Step 2: Compute metrics
        metrics_tables = compute_all_metrics(tables, top_n=top_n, top_n_drivers=5)
        
        # Step 3: Generate figures
        figures = {}
        if include_figures:
            figures = generate_all_plots(metrics_tables, str(outdir))
        
        # Step 4: Generate report
        report_html = None
        if include_report:
            report_html = generate_report(
                metrics_tables, figures, str(input_path), warnings
            )
        
        # Step 5: Write outputs
        end_time = datetime.now()
        
        qa_summary = {}
        for qa_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
            qa_df = tables.get(qa_name)
            qa_summary[qa_name] = len(qa_df) if qa_df is not None and not qa_df.empty else 0
        
        runlog = create_runlog(
            input_path=str(input_path),
            output_dir=str(outdir),
            warnings=warnings,
            qa_summary=qa_summary,
            tables_generated=list(metrics_tables.keys()),
            figures_generated=list(figures.keys()),
            start_time=start_time,
            end_time=end_time,
        )
        
        output_paths = write_outputs(
            str(outdir), metrics_tables, figures, report_html, runlog
        )
        
        # Read outputs into memory
        xlsx_base64 = None
        xlsx_path = output_paths.get("xlsx")
        if xlsx_path and Path(xlsx_path).exists():
            with open(xlsx_path, "rb") as f:
                xlsx_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(outdir):
                for file_name in files:
                    file_path = Path(root) / file_name
                    arcname = file_path.relative_to(outdir)
                    zf.write(file_path, arcname)
        zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
        
        duration = f"{(end_time - start_time).total_seconds():.1f}s"
        
        return JSONResponse(content={
            "success": True,
            "tables_count": len(metrics_tables),
            "figures_count": len(figures),
            "duration": duration,
            "warnings": warnings,
            "xlsx_base64": xlsx_base64,
            "report_html": report_html,
            "zip_base64": zip_base64,
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )
    finally:
        # Cleanup
        tables = None
        metrics_tables = None
        figures = None
        gc.collect()
        
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@app.post("/analyze/storyline4")
async def analyze_storyline4(
    file: UploadFile = File(...),
    top_n: int = Form(10),
    include_figures: bool = Form(True),
    include_report: bool = Form(True),
    lang: str = Form("es"),
):
    """
    Run Storyline 4 analysis: "Feasibility, Governance & Conflict Risk"
    
    - **file**: Analysis-ready Excel workbook (with LOOKUP_* and TIDY_* sheets)
    - **top_n**: Number of top items in rankings (default: 10)
    - **include_figures**: Generate visualization figures (default: True)
    - **include_report**: Generate HTML report (default: True)
    
    Returns JSON with base64-encoded outputs.
    """
    try:
        from storyline4.io import create_runlog, load_tables, write_outputs, get_sheet_availability, get_row_counts
        from storyline4.metrics import process_metrics
        from storyline4.plots import generate_plots
        from storyline4.report import generate_report
    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import storyline4 module: {e}"},
        )
    
    content = await file.read()
    tmpdir = tempfile.mkdtemp()
    
    try:
        input_path = Path(tmpdir) / file.filename
        input_path.write_bytes(content)
        
        outdir = Path(tmpdir) / "output"
        outdir.mkdir()
        
        start_time = datetime.now()
        
        # Step 1: Load tables
        tables, warnings = load_tables(str(input_path))
        
        # Step 2: Compute metrics
        params = {"top_n": top_n}
        metrics_tables = process_metrics(tables, params)
        
        # DEBUG: Print linkage keys
        linkage_keys = [k for k in metrics_tables.keys() if 'LINK' in k or 'THREAT' in k]
        print(f"[STORYLINE4 DEBUG] Linkage keys in metrics_tables: {linkage_keys}")
        print(f"[STORYLINE4 DEBUG] All metrics keys: {list(metrics_tables.keys())}")
        print(f"[STORYLINE4 DEBUG] TIDY_4_2_1_MAPEO_CONFLICTO in tables: {not tables.get('TIDY_4_2_1_MAPEO_CONFLICTO', None) is None}")
        
        # Step 3: Generate figures
        figures = {}
        if include_figures:
            figures = generate_plots(metrics_tables, str(outdir), params)
        
        # Step 4: Generate report
        report_html = None
        if include_report:
            report_html = generate_report(
                metrics_tables, figures, str(input_path), warnings, tables
            )
        
        # Step 5: Write outputs
        end_time = datetime.now()
        
        qa_summary = {}
        for qa_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
            qa_df = tables.get(qa_name)
            qa_summary[qa_name] = len(qa_df) if qa_df is not None and not qa_df.empty else 0
        
        sheet_availability = get_sheet_availability(tables)
        row_counts = get_row_counts(tables)
        
        runlog = create_runlog(
            input_path=str(input_path),
            output_dir=str(outdir),
            warnings=warnings,
            qa_summary=qa_summary,
            tables_generated=list(metrics_tables.keys()),
            figures_generated=list(figures.keys()),
            params=params,
            sheet_availability=sheet_availability,
            row_counts=row_counts,
            start_time=start_time,
            end_time=end_time,
        )
        
        output_paths = write_outputs(
            str(outdir), metrics_tables, figures, report_html, runlog
        )
        
        # Read outputs into memory
        xlsx_base64 = None
        xlsx_path = output_paths.get("xlsx")
        if xlsx_path and Path(xlsx_path).exists():
            with open(xlsx_path, "rb") as f:
                xlsx_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(outdir):
                for file_name in files:
                    file_path = Path(root) / file_name
                    arcname = file_path.relative_to(outdir)
                    zf.write(file_path, arcname)
        zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
        
        duration = f"{(end_time - start_time).total_seconds():.1f}s"
        
        return JSONResponse(content={
            "success": True,
            "tables_count": len(metrics_tables),
            "figures_count": len(figures),
            "duration": duration,
            "warnings": warnings,
            "xlsx_base64": xlsx_base64,
            "report_html": report_html,
            "zip_base64": zip_base64,
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )
    finally:
        # Cleanup
        tables = None
        metrics_tables = None
        figures = None
        gc.collect()
        
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
@app.post("/analyze/storyline2")
async def analyze_storyline2(
    file: UploadFile = File(...),
    top_n: int = Form(10),
    include_figures: bool = Form(True),
    include_report: bool = Form(True),
    lang: str = Form("es"),
):
    """
    Run Storyline 2 analysis: "Ecosystem-service lifelines"
    """
    try:
        from storyline2.io import create_runlog, load_tables, write_outputs
        from storyline2.metrics import compute_all_metrics, load_params
        from storyline2.plots import generate_all_plots
        from storyline2.report import generate_report
    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import storyline2 module: {e}"},
        )
    
    content = await file.read()
    tmpdir = tempfile.mkdtemp()
    
    try:
        input_path = Path(tmpdir) / file.filename
        input_path.write_bytes(content)
        
        outdir = Path(tmpdir) / "output"
        outdir.mkdir()
        
        start_time = datetime.now()
        
        # Step 1: Load tables
        tables, warnings = load_tables(str(input_path))
        
        # Step 2: Compute metrics
        metrics_tables = compute_all_metrics(tables, top_n=top_n)
        
        # Step 3: Generate figures
        figures = {}
        if include_figures:
            figures = generate_all_plots(metrics_tables, str(outdir), tables=tables)
        
        # Step 4: Generate report
        report_html = None
        if include_report:
            report_html = generate_report(
                metrics_tables, figures, str(input_path), warnings, tables=tables
            )
        
        # Step 5: Write outputs
        end_time = datetime.now()
        
        qa_summary = {}
        for qa_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
            qa_df = tables.get(qa_name)
            qa_summary[qa_name] = len(qa_df) if qa_df is not None and not qa_df.empty else 0
        
        params = load_params()
        params["top_n"] = top_n
        
        runlog = create_runlog(
            input_path=str(input_path),
            output_dir=str(outdir),
            warnings=warnings,
            qa_summary=qa_summary,
            tables_generated=list(metrics_tables.keys()),
            figures_generated=list(figures.keys()),
            params=params,
            scenarios=["balanced", "livelihood_priority", "fragility_first"],
            sheet_availability={name: not tables.get(name, pd.DataFrame()).empty for name in tables},
            row_counts={name: len(df) for name, df in tables.items() if not df.empty},
            start_time=start_time,
            end_time=end_time,
        )
        
        output_paths = write_outputs(
            str(outdir), metrics_tables, figures, report_html, runlog
        )
        
        # Read outputs into memory
        xlsx_base64 = None
        xlsx_path = output_paths.get("xlsx")
        if xlsx_path and Path(xlsx_path).exists():
            with open(xlsx_path, "rb") as f:
                xlsx_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(outdir):
                for file_name in files:
                    file_path = Path(root) / file_name
                    arcname = file_path.relative_to(outdir)
                    zf.write(file_path, arcname)
        zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
        
        duration = f"{(end_time - start_time).total_seconds():.1f}s"
        
        return JSONResponse(content={
            "success": True,
            "tables_count": len(metrics_tables),
            "figures_count": len(figures),
            "duration": duration,
            "warnings": warnings,
            "xlsx_base64": xlsx_base64,
            "report_html": report_html,
            "zip_base64": zip_base64,
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )
    finally:
        # Cleanup
        tables = None
        metrics_tables = None
        figures = None
        gc.collect()
        
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@app.post("/analyze/storyline3")
async def analyze_storyline3(
    file: UploadFile = File(...),
    top_n: int = Form(10),
    include_figures: bool = Form(True),
    include_report: bool = Form(True),
    lang: str = Form("es"),
):
    """
    Run Storyline 3 analysis: "Equity & Differentiated Vulnerability"
    """
    try:
        from storyline3.io import create_runlog, load_tables, write_outputs
        from storyline3.metrics import process_metrics, load_params
        from storyline3.plots import generate_plots
        from storyline3.report import generate_report
    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import storyline3 module: {e}"},
        )
    
    content = await file.read()
    tmpdir = tempfile.mkdtemp()
    
    try:
        input_path = Path(tmpdir) / file.filename
        input_path.write_bytes(content)
        
        outdir = Path(tmpdir) / "output"
        outdir.mkdir()
        
        start_time = datetime.now()
        
        # Step 1: Load tables
        tables, warnings = load_tables(str(input_path))
        
        # Step 2: Compute metrics
        params = load_params()
        params["top_n"] = top_n
        metrics_tables = process_metrics(tables, params)
        
        # Step 3: Generate figures
        figures = {}
        if include_figures:
            figures = generate_plots(metrics_tables, str(outdir), params)
        
        # Step 4: Generate report
        report_html = None
        if include_report:
            report_html = generate_report(metrics_tables, figures, str(input_path), tables)
        
        # Step 5: Write outputs
        end_time = datetime.now()
        
        qa_summary = {}
        for qa_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
            qa_df = tables.get(qa_name)
            qa_summary[qa_name] = len(qa_df) if qa_df is not None and not qa_df.empty else 0
        
        runlog = create_runlog(
            input_path=str(input_path),
            output_dir=str(outdir),
            warnings=warnings,
            qa_summary=qa_summary,
            tables_generated=list(metrics_tables.keys()),
            figures_generated=list(figures.keys()),
            params=params,
            sheet_availability={name: not tables.get(name, pd.DataFrame()).empty for name in tables},
            row_counts={name: len(df) for name, df in tables.items() if not df.empty},
            start_time=start_time,
            end_time=end_time,
        )
        
        output_paths = write_outputs(
            str(outdir), metrics_tables, figures, report_html, runlog
        )
        
        # Read outputs into memory
        xlsx_base64 = None
        xlsx_path = output_paths.get("xlsx")
        if xlsx_path and Path(xlsx_path).exists():
            with open(xlsx_path, "rb") as f:
                xlsx_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(outdir):
                for file_name in files:
                    file_path = Path(root) / file_name
                    arcname = file_path.relative_to(outdir)
                    zf.write(file_path, arcname)
        zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
        
        duration = f"{(end_time - start_time).total_seconds():.1f}s"
        
        return JSONResponse(content={
            "success": True,
            "tables_count": len(metrics_tables),
            "figures_count": len(figures),
            "duration": duration,
            "warnings": warnings,
            "xlsx_base64": xlsx_base64,
            "report_html": report_html,
            "zip_base64": zip_base64,
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )
    finally:
        # Cleanup
        tables = None
        metrics_tables = None
        figures = None
        gc.collect()
        
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@app.post("/analyze/storyline5")
async def analyze_storyline5(
    file: UploadFile = File(...),
    top_n: int = Form(10),
    include_figures: bool = Form(True),
    include_report: bool = Form(True),
    lang: str = Form("es"),
):
    """
    Run Storyline 5 analysis: "SbN Portfolio Design + Monitoring Plan"
    
    - **file**: Analysis-ready Excel workbook (with LOOKUP_* and TIDY_* sheets)
    - **top_n**: Number of top bundles in rankings (default: 10)
    - **include_figures**: Generate visualization figures (default: True)
    - **include_report**: Generate HTML report (default: True)
    
    Returns JSON with base64-encoded outputs.
    """
    try:
        from storyline5.io import create_runlog, load_tables, write_outputs, get_sheet_availability, get_row_counts
        from storyline5.metrics_local import compute_all_local_metrics
        from storyline5.portfolio import build_portfolio
        from storyline5.monitoring import build_monitoring_tables
        from storyline5.plots import generate_plots
        from storyline5.report import generate_report
    except ImportError as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to import storyline5 module: {e}"},
        )
    
    content = await file.read()
    tmpdir = tempfile.mkdtemp()
    
    try:
        input_path = Path(tmpdir) / file.filename
        input_path.write_bytes(content)
        
        outdir = Path(tmpdir) / "output"
        outdir.mkdir()
        
        start_time = datetime.now()
        
        # Step 1: Load tables
        tables, warnings = load_tables(str(input_path))
        
        # Step 2: Compute local metrics
        params = {"top_n": top_n, "bundles_per_grupo": 5}
        metrics = compute_all_local_metrics(tables, params)
        
        # Step 3: Build portfolio
        weight_scenarios = {
            "balanced": {"w_impact_potential": 0.35, "w_leverage": 0.25, "w_equity_urgency": 0.20, "w_feasibility": 0.20},
            "equity_first": {"w_impact_potential": 0.30, "w_leverage": 0.20, "w_equity_urgency": 0.35, "w_feasibility": 0.15},
            "feasibility_first": {"w_impact_potential": 0.30, "w_leverage": 0.20, "w_equity_urgency": 0.15, "w_feasibility": 0.35},
        }
        portfolio_tables, bundle_counts = build_portfolio(tables, metrics, params, weight_scenarios)
        
        # Step 4: Build monitoring plan
        monitoring_tables = build_monitoring_tables(portfolio_tables, params)
        
        # Merge all tables
        all_tables = {**metrics, **portfolio_tables}
        
        # Step 5: Generate figures
        figures = {}
        if include_figures:
            figures = generate_plots(portfolio_tables, str(outdir), params)
        
        # Step 6: Generate report
        report_html = None
        if include_report:
            report_html = generate_report(
                portfolio_tables, monitoring_tables, figures, str(input_path), warnings, tables
            )
        
        # Step 7: Write outputs
        end_time = datetime.now()
        
        qa_summary = {}
        for qa_name in ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]:
            qa_df = tables.get(qa_name)
            qa_summary[qa_name] = len(qa_df) if qa_df is not None and not qa_df.empty else 0
        
        sheet_availability = get_sheet_availability(tables)
        row_counts = get_row_counts(tables)
        
        runlog = create_runlog(
            input_path=str(input_path),
            output_dir=str(outdir),
            optional_storyline_paths={},
            warnings=warnings,
            qa_summary=qa_summary,
            tables_generated=list(all_tables.keys()),
            figures_generated=list(figures.keys()),
            params=params,
            scoring_scenarios=list(weight_scenarios.keys()),
            sheet_availability=sheet_availability,
            row_counts=row_counts,
            bundle_counts=bundle_counts,
            start_time=start_time,
            end_time=end_time,
        )
        
        output_paths = write_outputs(
            str(outdir), all_tables, figures, report_html, runlog, monitoring_tables
        )
        
        # Read outputs into memory
        xlsx_base64 = None
        xlsx_path = output_paths.get("xlsx")
        if xlsx_path and Path(xlsx_path).exists():
            with open(xlsx_path, "rb") as f:
                xlsx_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(outdir):
                for file_name in files:
                    file_path = Path(root) / file_name
                    arcname = file_path.relative_to(outdir)
                    zf.write(file_path, arcname)
        zip_base64 = base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
        
        duration = f"{(end_time - start_time).total_seconds():.1f}s"
        
        return JSONResponse(content={
            "success": True,
            "tables_count": len(all_tables),
            "figures_count": len(figures),
            "duration": duration,
            "warnings": warnings,
            "bundles_overall": bundle_counts.get("overall", 0),
            "bundles_by_grupo": bundle_counts.get("by_grupo", 0),
            "indicators_count": len(monitoring_tables.get("INDICATORS", pd.DataFrame())),
            "xlsx_base64": xlsx_base64,
            "report_html": report_html,
            "zip_base64": zip_base64,
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )
    finally:
        # Cleanup
        tables = None
        metrics = None
        portfolio_tables = None
        monitoring_tables = None
        figures = None
        gc.collect()
        
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
