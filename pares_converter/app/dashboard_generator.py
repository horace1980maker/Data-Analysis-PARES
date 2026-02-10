"""
Dashboard Generator Module
Generates an interactive SES dashboard from an analysis-ready Excel workbook.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)


def extract_meta(xl: pd.ExcelFile, file_name: str, org_name: str = "Organización") -> Dict[str, Any]:
    """Extract metadata from workbook."""
    # Try to get geo info
    geo_df = pd.read_excel(xl, "LOOKUP_GEO") if "LOOKUP_GEO" in xl.sheet_names else pd.DataFrame()
    ctx_df = pd.read_excel(xl, "LOOKUP_CONTEXT") if "LOOKUP_CONTEXT" in xl.sheet_names else pd.DataFrame()
    
    # Get first paisaje and admin0
    paisaje = geo_df["paisaje"].iloc[0] if len(geo_df) > 0 and "paisaje" in geo_df.columns else "Paisaje"
    admin0 = geo_df["admin0"].iloc[0] if len(geo_df) > 0 and "admin0" in geo_df.columns else ""
    
    return {
        "title": f"Análisis Interactivo del Paisaje de {paisaje}",
        "subtitle": "Una exploración visual de las dinámicas socioecológicas y la capacidad adaptativa.",
        "org": org_name,
        "landscape": paisaje,
        "admin0": admin0,
        "export_date": datetime.now().strftime("%Y-%m-%d"),
        "workbook_name": file_name
    }


def normalize_grupo(grupo: str) -> str:
    """Normalize grupo/zona labels."""
    if not grupo or pd.isna(grupo):
        return "Sin especificar"
    g = str(grupo).lower().strip()
    if "alta" in g:
        return "Zona Alta"
    elif "media" in g:
        return "Zona Media"
    elif "baja" in g:
        return "Zona Baja"
    return str(grupo).strip()


def extract_contexts(xl: pd.ExcelFile) -> List[Dict[str, Any]]:
    """Extract context options for dropdown."""
    contexts = []
    
    if "LOOKUP_CONTEXT" not in xl.sheet_names or "LOOKUP_GEO" not in xl.sheet_names:
        # Try to find a context_id from common data sheets if lookup is missing
        first_ctx_id = ""
        for s in ["TIDY_3_5_SE_MDV", "TIDY_4_1_AMENAZAS", "TIDY_3_3_CAR_A"]:
            if s in xl.sheet_names:
                df_tmp = pd.read_excel(xl, s)
                if "context_id" in df_tmp.columns and not df_tmp["context_id"].empty:
                    first_ctx_id = str(df_tmp["context_id"].iloc[0])
                    if first_ctx_id.lower() == "nan": first_ctx_id = ""
                    break
        
        return [{
            "context_id": first_ctx_id,
            "geo_id": "",
            "fecha_iso": "",
            "admin0": "",
            "paisaje": "Paisaje",
            "grupo": "General",
            "grupo_normalized": "General",
            "label": "Vista General"
        }]
    
    ctx_df = pd.read_excel(xl, "LOOKUP_CONTEXT")
    geo_df = pd.read_excel(xl, "LOOKUP_GEO")
    
    # Merge to get full context info
    if "geo_id" in ctx_df.columns and "geo_id" in geo_df.columns:
        merged = ctx_df.merge(geo_df, on="geo_id", how="left")
    else:
        merged = ctx_df
    
    for _, row in merged.iterrows():
        paisaje = row.get("paisaje", "Paisaje")
        grupo = row.get("grupo", "")
        fecha = row.get("fecha_iso", "")
        grupo_norm = normalize_grupo(grupo)
        
        # Format date for display
        if fecha and not pd.isna(fecha):
            if isinstance(fecha, str):
                fecha_display = fecha[:7]  # YYYY-MM
            else:
                fecha_display = str(fecha)[:10]
        else:
            fecha_display = ""
        
        ctx_id = str(row.get("context_id", "")) if not pd.isna(row.get("context_id")) else ""
        if ctx_id.lower() == "nan": ctx_id = ""
        
        contexts.append({
            "context_id": ctx_id,
            "geo_id": str(row.get("geo_id", "")) if not pd.isna(row.get("geo_id")) else "",
            "fecha_iso": str(fecha) if fecha and not pd.isna(fecha) else "",
            "admin0": str(row.get("admin0", "")),
            "paisaje": str(paisaje) if paisaje else "Paisaje",
            "grupo": str(grupo) if grupo and not pd.isna(grupo) else "",
            "grupo_normalized": grupo_norm,
            "label": f"{paisaje} — {grupo_norm} — {fecha_display}".strip(" —")
        })
    
    if not contexts:
        contexts = [{
            "context_id": "",
            "geo_id": "",
            "fecha_iso": "",
            "admin0": "",
            "paisaje": "Paisaje",
            "grupo": "General",
            "grupo_normalized": "General",
            "label": "Vista General"
        }]
    
    return contexts


def compute_kpis(xl: pd.ExcelFile, contexts: List[Dict]) -> Dict[str, Dict[str, int]]:
    """Compute KPI counts per context."""
    kpis = {}
    
    for ctx in contexts:
        ctx_id = ctx["context_id"]
        kpis[ctx_id] = {
            "n_services": 0,
            "n_livelihoods": 0,
            "n_threats": 0,
            "n_actors": 0
        }
    
    # Count services from TIDY_3_5_SE_MDV
    if "TIDY_3_5_SE_MDV" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_3_5_SE_MDV")
        for ctx in contexts:
            ctx_id = ctx["context_id"]
            subset = df[df["context_id"].astype(str) == ctx_id]
            if not subset.empty:
                if "elemento_se" in subset.columns:
                    kpis[ctx_id]["n_services"] = subset["elemento_se"].nunique()
                if "mdv_name" in subset.columns:
                    kpis[ctx_id]["n_livelihoods"] = subset["mdv_name"].nunique()
    
    # Count threats from TIDY_4_1_AMENAZAS
    if "TIDY_4_1_AMENAZAS" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_4_1_AMENAZAS")
        for ctx in contexts:
            ctx_id = ctx["context_id"]
            if "context_id" in df.columns:
                subset = df[df["context_id"].astype(str).fillna("") == ctx_id]
                if not subset.empty and "amenaza" in subset.columns:
                    kpis[ctx_id]["n_threats"] = subset["amenaza"].nunique()
    
    # Count actors from TIDY_5_1_ACTORES
    if "TIDY_5_1_ACTORES" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_5_1_ACTORES")
        for ctx in contexts:
            ctx_id = ctx["context_id"]
            subset = df[df["context_id"].astype(str) == ctx_id]
            if not subset.empty and "nombre_actor" in subset.columns:
                kpis[ctx_id]["n_actors"] = subset["nombre_actor"].nunique()
    
    return kpis


def extract_lifelines(xl: pd.ExcelFile) -> Dict[str, Any]:
    """Extract SE→MdV relationships and seasonality data."""
    lifelines = {"se_mdv": [], "se_months": []}
    
    if "TIDY_3_5_SE_MDV" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_3_5_SE_MDV")
        cols = ["se_mdv_id", "context_id", "elemento_se", "mdv_name", "nr_usuarios", "accesso", "barreras"]
        available_cols = [c for c in cols if c in df.columns]
        lifelines["se_mdv"] = df[available_cols].fillna("").to_dict("records")
    
    if "TIDY_3_5_SE_MONTHS" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_3_5_SE_MONTHS")
        cols = ["se_mdv_id", "month_num", "month_type"]
        available_cols = [c for c in cols if c in df.columns]
        if available_cols:
            lifelines["se_months"] = df[available_cols].fillna("").to_dict("records")
    
    return lifelines


def extract_threats(xl: pd.ExcelFile) -> Dict[str, Any]:
    """Extract threat data and compute scores."""
    threats = {"amenazas": [], "threat_scores": []}
    
    impact_cols = ["i_economia", "i_alimentaria", "i_sanitaria", "i_ambiental", 
                   "i_personal", "i_comunitaria", "i_politica"]
    
    # Try TIDY_4_2_1_AMENAZA_MDV first, then TIDY_4_2_2_AMENAZA_SE
    sheet = None
    if "TIDY_4_2_1_AMENAZA_MDV" in xl.sheet_names:
        sheet = "TIDY_4_2_1_AMENAZA_MDV"
    elif "TIDY_4_2_2_AMENAZA_SE" in xl.sheet_names:
        sheet = "TIDY_4_2_2_AMENAZA_SE"
    
    if sheet:
        df = pd.read_excel(xl, sheet)
        # Get relevant columns
        base_cols = ["context_id", "amenaza", "tipo_amenaza", "nr_familias"]
        available_cols = [c for c in base_cols + impact_cols if c in df.columns]
        
        # Add impact column names for reference
        available_impacts = [c for c in impact_cols if c in df.columns]
        
        for _, row in df.iterrows():
            record = {c: row[c] if not pd.isna(row.get(c)) else 0 for c in available_cols}
            record["context_id"] = str(record.get("context_id", ""))
            
            # Compute threat score (mean of impact values)
            impact_values = [row.get(c, 0) for c in available_impacts if not pd.isna(row.get(c, 0))]
            record["threat_score"] = sum(impact_values) / len(impact_values) if impact_values else 0
            
            threats["amenazas"].append(record)
        
        # Aggregate scores by threat
        if threats["amenazas"]:
            by_threat = {}
            for rec in threats["amenazas"]:
                key = (rec.get("context_id"), rec.get("amenaza"))
                if key not in by_threat:
                    by_threat[key] = {"scores": [], "nr_familias": 0}
                by_threat[key]["scores"].append(rec["threat_score"])
                by_threat[key]["nr_familias"] += rec.get("nr_familias", 0) or 0
            
            for (ctx_id, amenaza), data in by_threat.items():
                threats["threat_scores"].append({
                    "context_id": ctx_id,
                    "amenaza": amenaza,
                    "mean_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0,
                    "total_familias": data["nr_familias"]
                })
    
    # Also get threat metadata from TIDY_4_1_AMENAZAS
    if "TIDY_4_1_AMENAZAS" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_4_1_AMENAZAS")
        meta_cols = ["context_id", "amenaza", "tipo_amenaza", "magnitud", "frequencia", "tendencia"]
        available_cols = [c for c in meta_cols if c in df.columns]
        threats["amenazas_meta"] = df[available_cols].fillna("").to_dict("records")
    
    return threats


def extract_actors(xl: pd.ExcelFile) -> List[Dict[str, Any]]:
    """Extract actor data for power-interest scatter."""
    actors = []
    
    sheet_name = next((s for s in xl.sheet_names if "5_1_ACTORES" in s), None)
    if not sheet_name:
        return actors
    
    df = pd.read_excel(xl, sheet_name)
    cols = ["context_id", "actor_id", "nombre_actor", "tipo_actor", "rol_paisaje", "poder", "interes"]
    available_cols = [c for c in cols if c in df.columns]
    
    for _, row in df.iterrows():
        record = {}
        for c in available_cols:
            val = row.get(c)
            if pd.isna(val):
                record[c] = "" if c in ["nombre_actor", "tipo_actor", "rol_paisaje"] else 0
            else:
                record[c] = str(val) if c in ["context_id", "actor_id", "nombre_actor", "tipo_actor", "rol_paisaje"] else val
        actors.append(record)
    
    return actors


def extract_ecosystems(xl: pd.ExcelFile) -> List[Dict[str, Any]]:
    """Extract ecosystem health data."""
    ecosystems = []
    
    if "TIDY_3_4_ECOSISTEMAS" not in xl.sheet_names:
        return ecosystems
    
    df = pd.read_excel(xl, "TIDY_3_4_ECOSISTEMAS")
    cols = ["context_id", "ecosistema", "tipo", "es_salud", "causas_deg"]
    available_cols = [c for c in cols if c in df.columns]
    
    for _, row in df.iterrows():
        record = {c: str(row[c]) if not pd.isna(row.get(c)) else "" for c in available_cols}
        record["context_id"] = str(row.get("context_id", "")) if not pd.isna(row.get("context_id")) else ""
        ecosystems.append(record)
    
    return ecosystems


def extract_conflicts(xl: pd.ExcelFile) -> Dict[str, Any]:
    """Extract conflict events for timeline."""
    conflicts = {"events": [], "actors": []}
    
    # Try finding the events sheet
    events_sheet = next((s for s in xl.sheet_names if "6_1_CONFLICT_EVENTS" in s), None)
    if events_sheet:
        df = pd.read_excel(xl, events_sheet)
        cols = ["event_id", "context_id", "cod_conflict", "evento", "ano_evento", 
                "diferencias", "dif_factor", "cooperacion", "coop_factor", "suma"]
        available_cols = [c for c in cols if c in df.columns]
        
        for _, row in df.iterrows():
            record = {}
            for c in available_cols:
                val = row.get(c)
                if pd.isna(val):
                    record[c] = "" if c in ["evento", "diferencias", "dif_factor", "cooperacion", "coop_factor"] else 0
                else:
                    record[c] = str(val) if c in ["event_id", "context_id", "cod_conflict", "evento", 
                                                   "diferencias", "dif_factor", "cooperacion", "coop_factor"] else val
            conflicts["events"].append(record)
    
    # Try finding the actors sheet
    actors_sheet = next((s for s in xl.sheet_names if "6_2_CONFLICTO_ACTOR" in s), None)
    if actors_sheet:
        df = pd.read_excel(xl, actors_sheet)
        cols = ["context_id", "cod_conflict", "actor", "i_en_actor", "i_en_conflicto"]
        available_cols = [c for c in cols if c in df.columns]
        conflicts["actors"] = df[available_cols].fillna("").to_dict("records")
    
    return conflicts


def extract_dialogue(xl: pd.ExcelFile) -> Dict[str, Any]:
    """Extract dialogue spaces data."""
    dialogue = {"spaces": [], "actors": []}
    
    if "TIDY_5_2_DIALOGO" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_5_2_DIALOGO")
        cols = ["dialogo_id", "context_id", "nombre_espacio", "tipo", "alcance", 
                "funcion", "incidencia", "fortalezas", "debilidades"]
        available_cols = [c for c in cols if c in df.columns]
        
        for _, row in df.iterrows():
            record = {c: str(row[c]) if not pd.isna(row.get(c)) else "" for c in available_cols}
            dialogue["spaces"].append(record)
    
    if "TIDY_5_2_DIALOGO_ACTOR" in xl.sheet_names:
        df = pd.read_excel(xl, "TIDY_5_2_DIALOGO_ACTOR")
        cols = ["dialogo_id", "actor_id", "actor_name"]
        available_cols = [c for c in cols if c in df.columns]
        dialogue["actors"] = df[available_cols].fillna("").to_dict("records")
    
    return dialogue


def extract_livelihoods(xl: pd.ExcelFile) -> List[Dict[str, Any]]:
    """Extract livelihood details from characterization and prioritization tables."""
    livelihoods = []
    
    # Get unique livelihoods from LOOKUP_MDV
    if "LOOKUP_MDV" in xl.sheet_names:
        df = pd.read_excel(xl, "LOOKUP_MDV")
        for _, row in df.iterrows():
            livelihoods.append({
                "mdv_id": str(row.get("mdv_id", "")),
                "mdv_name": str(row.get("mdv_name", "")),
                "context_id": "",
                "i_total": 0,
                "rank": 999
            })
    
    # Add prioritization data if available (TIDY_3_2_PRIORIZACION)
    prio_map = {}
    if "TIDY_3_2_PRIORIZACION" in xl.sheet_names:
        prio_df = pd.read_excel(xl, "TIDY_3_2_PRIORIZACION")
        for _, row in prio_df.iterrows():
            key = (str(row.get("context_id", "")), str(row.get("mdv_id", "")))
            prio_map[key] = {
                "i_total": row.get("i_total", 0),
                "rank": row.get("rank_in_zona", 999)
            }
    
    # Enrich with characterization data if available
    car_a_sheet = next((s for s in xl.sheet_names if "3_3_CAR_A" in s), None)
    if car_a_sheet:
        car_a = pd.read_excel(xl, car_a_sheet)
        for liv in livelihoods:
            subset = car_a[car_a["mdv_id"].astype(str) == liv["mdv_id"]]
            if len(subset) > 0:
                row = subset.iloc[0]
                ctx_id = str(row.get("context_id", ""))
                liv.update({
                    "context_id": ctx_id,
                    "sistema": str(row.get("sistema", "")),
                    "uso_final": str(row.get("uso_final", "")),
                    "cv_importancia": row.get("cv_importancia"),
                    "cv_producto": str(row.get("cv_producto", "")),
                    "cv_mercado": str(row.get("cv_mercado", ""))
                })
                
                # Add priority info
                prio = prio_map.get((ctx_id, liv["mdv_id"]))
                if prio:
                    liv["i_total"] = prio["i_total"]
                    liv["rank"] = prio["rank"]
                else:
                    liv["i_total"] = 0
                    liv["rank"] = 999
    
    return livelihoods


def build_qa_summary(xl: pd.ExcelFile) -> Dict[str, Any]:
    """Build QA summary from available data."""
    qa = {
        "missing_optional": [],
        "available_sheets": [],
        "data_quality_notes": []
    }
    
    required_sheets = ["LOOKUP_CONTEXT", "LOOKUP_GEO"]
    recommended_sheets = [
        "TIDY_3_5_SE_MDV", "TIDY_3_5_SE_MONTHS", "TIDY_4_1_AMENAZAS",
        "TIDY_4_2_1_AMENAZA_MDV", "TIDY_5_1_ACTORES"
    ]
    optional_sheets = [
        "TIDY_3_4_ECOSISTEMAS", "TIDY_6_1_CONFLICT_EVENTS", "TIDY_5_2_DIALOGO",
        "TIDY_7_1_RESPONDENTS", "TIDY_7_1_RESPONSES"
    ]
    
    for sheet in required_sheets:
        if sheet in xl.sheet_names:
            qa["available_sheets"].append(sheet)
        else:
            qa["data_quality_notes"].append(f"CRITICAL: Missing required sheet {sheet}")
    
    for sheet in recommended_sheets:
        if sheet in xl.sheet_names:
            qa["available_sheets"].append(sheet)
        else:
            qa["missing_optional"].append(sheet)
    
    for sheet in optional_sheets:
        if sheet in xl.sheet_names:
            qa["available_sheets"].append(sheet)
        else:
            qa["missing_optional"].append(sheet)
    
    return qa


def build_bundle(xl: pd.ExcelFile, file_name: str, org_name: str = "Organización") -> Dict[str, Any]:
    """Build the complete dashboard data bundle."""
    meta = extract_meta(xl, file_name, org_name)
    contexts = extract_contexts(xl)
    
    bundle = {
        "meta": meta,
        "contexts": contexts,
        "kpis": compute_kpis(xl, contexts),
        "lifelines": extract_lifelines(xl),
        "threats": extract_threats(xl),
        "actors": extract_actors(xl),
        "ecosystems": extract_ecosystems(xl),
        "livelihoods": extract_livelihoods(xl),
        "conflicts": extract_conflicts(xl),
        "dialogue": extract_dialogue(xl),
        "qa": build_qa_summary(xl)
    }
    
    return bundle


def generate_dashboard_html(bundle: Dict[str, Any]) -> str:
    """Generate the dashboard HTML from bundle data."""
    # Read the template
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard_template.html")
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Embed the bundle as JSON
    bundle_json = json.dumps(bundle, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    # Replace placeholder in template
    html = template.replace("/* __BUNDLE_DATA__ */", f"const BUNDLE = {bundle_json};")
    
    return html


def generate_dashboard(
    excel_path: str,
    output_dir: str,
    org_name: str = "Organización"
) -> Tuple[str, str, str]:
    """
    Generate dashboard from Excel workbook.
    
    Args:
        excel_path: Path to analysis-ready Excel workbook
        output_dir: Directory to write output files
        org_name: Organization name for display
    
    Returns:
        Tuple of (html_path, bundle_path, qa_path)
    """
    # Read workbook
    file_name = os.path.basename(excel_path)
    xl = pd.ExcelFile(excel_path)
    
    # Build bundle
    bundle = build_bundle(xl, file_name, org_name)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Write bundle JSON
    bundle_path = os.path.join(output_dir, "bundle.json")
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    # Write QA JSON
    qa_path = os.path.join(output_dir, "qa_dashboard.json")
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump(bundle["qa"], f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    # Generate and write HTML
    html = generate_dashboard_html(bundle)
    html_path = os.path.join(output_dir, "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return html_path, bundle_path, qa_path
