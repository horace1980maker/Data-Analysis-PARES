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


def _read_table(xl: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """Read a sheet and force a single global context to aggregate all data."""
    if sheet_name not in xl.sheet_names:
        return pd.DataFrame()
    df = pd.read_excel(xl, sheet_name)
    # Force aggregation by standardizing context_id
    if "context_id" in df.columns:
        df["context_id"] = "CTX_GLOBAL"
    return df


def extract_meta(xl: pd.ExcelFile, file_name: str, org_name: str = "Organización") -> Dict[str, Any]:
    """Extract metadata from workbook."""
    # Try to get geo info
    geo_df = _read_table(xl, "LOOKUP_GEO")
    ctx_df = _read_table(xl, "LOOKUP_CONTEXT")
    
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
    """Extract context options for dropdown. Returns STRICTLY one context."""
    # Force single context for entire landscape
    
    # Try to get landscape name
    paisaje_name = "Paisaje"
    if "LOOKUP_GEO" in xl.sheet_names:
        geo_df = _read_table(xl, "LOOKUP_GEO")
        if not geo_df.empty and "paisaje" in geo_df.columns:
            paisaje_name = str(geo_df["paisaje"].iloc[0])
            
    # Return single global context
    return [{
        "context_id": "CTX_GLOBAL",
        "geo_id": "",
        "fecha_iso": datetime.now().strftime("%Y-%m-%d"),
        "admin0": "",
        "paisaje": paisaje_name,
        "grupo": "Global",
        "grupo_normalized": "Global",
        "label": f"{paisaje_name}"  # Simple label
    }]


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
        df = _read_table(xl, "TIDY_3_5_SE_MDV")
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
        df = _read_table(xl, "TIDY_4_1_AMENAZAS")
        for ctx in contexts:
            ctx_id = ctx["context_id"]
            if "context_id" in df.columns:
                subset = df[df["context_id"].astype(str).fillna("") == ctx_id]
                if not subset.empty and "amenaza" in subset.columns:
                    kpis[ctx_id]["n_threats"] = subset["amenaza"].nunique()
    
    # Count actors from TIDY_5_1_ACTORES
    if "TIDY_5_1_ACTORES" in xl.sheet_names:
        df = _read_table(xl, "TIDY_5_1_ACTORES")
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
        df = _read_table(xl, "TIDY_3_5_SE_MDV")
        # Join ecosystem names from lookup table
        if "LOOKUP_ECOSISTEMA" in xl.sheet_names:
            eco_lookup = _read_table(xl, "LOOKUP_ECOSISTEMA")
            if "ecosistema_id" in df.columns and "ecosistema_id" in eco_lookup.columns:
                # Primary join on ecosistema_id (filter out NaN ids)
                eco_id_map = eco_lookup.dropna(subset=["ecosistema_id"]).set_index("ecosistema_id")
                if "ecosistema" in eco_id_map.columns:
                    df["ecosistema"] = df["ecosistema_id"].map(eco_id_map["ecosistema"])
                # Fallback: fill gaps using cod_es -> ecosistema mapping
                if "cod_es" in df.columns and "cod_es" in eco_lookup.columns:
                    eco_code_map = eco_lookup.dropna(subset=["cod_es"]).drop_duplicates("cod_es").set_index("cod_es")
                    if "ecosistema" in eco_code_map.columns:
                        mask = df["ecosistema"].isna() | (df["ecosistema"] == "")
                        df.loc[mask, "ecosistema"] = df.loc[mask, "cod_es"].map(eco_code_map["ecosistema"])
                # Final fallback: use cod_es code as label if still empty
                if "cod_es" in df.columns:
                    still_empty = df["ecosistema"].isna() | (df["ecosistema"] == "")
                    df.loc[still_empty, "ecosistema"] = df.loc[still_empty, "cod_es"]
        cols = ["se_mdv_id", "context_id", "elemento_se", "mdv_name", "nr_usuarios", "accesso", "barreras", "ecosistema", "cod_es"]
        available_cols = [c for c in cols if c in df.columns]
        lifelines["se_mdv"] = df[available_cols].fillna("").to_dict("records")
    
    if "TIDY_3_5_SE_MONTHS" in xl.sheet_names:
        df = _read_table(xl, "TIDY_3_5_SE_MONTHS")
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
        df = _read_table(xl, sheet)
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
    
    df = _read_table(xl, sheet_name)
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
    
    df = _read_table(xl, "TIDY_3_4_ECOSISTEMAS")
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
        df = _read_table(xl, events_sheet)
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
        df = _read_table(xl, actors_sheet)
        cols = ["context_id", "cod_conflict", "actor", "i_en_actor", "i_en_conflicto"]
        available_cols = [c for c in cols if c in df.columns]
        conflicts["actors"] = df[available_cols].fillna("").to_dict("records")
    
    return conflicts


def extract_dialogue(xl: pd.ExcelFile) -> Dict[str, Any]:
    """Extract dialogue spaces data."""
    dialogue = {"spaces": [], "actors": []}
    
    if "TIDY_5_2_DIALOGO" in xl.sheet_names:
        df = _read_table(xl, "TIDY_5_2_DIALOGO")
        cols = ["dialogo_id", "context_id", "nombre_espacio", "tipo", "alcance", 
                "funcion", "incidencia", "fortalezas", "debilidades"]
        available_cols = [c for c in cols if c in df.columns]
        
        for _, row in df.iterrows():
            record = {c: str(row[c]) if not pd.isna(row.get(c)) else "" for c in available_cols}
            dialogue["spaces"].append(record)
    
    if "TIDY_5_2_DIALOGO_ACTOR" in xl.sheet_names:
        df = _read_table(xl, "TIDY_5_2_DIALOGO_ACTOR")
        cols = ["dialogo_id", "actor_id", "actor_name"]
        available_cols = [c for c in cols if c in df.columns]
        dialogue["actors"] = df[available_cols].fillna("").to_dict("records")
    
    return dialogue



INTERVENTION_MAP = {
    "Sequía": "Cosecha de Agua y Sistemas Agroforestales",
    "Inundación": "Restauración de Riberas y Drenaje Sostenible",
    "Incendios": "Manejo Integrado del Fuego y Barreras Vivas",
    "Plagas": "Manejo Integrado de Plagas y Diversificación",
    "Deslizamientos": "Estabilización de Laderas y Reforestación",
    "Deforestación": "Restauración Ecológica y Agroforestería",
    "Contaminación": "Biofiltros y Gestión de Cuencas",
    "Huracanes": "Barreras de Viento y Diversificación de Cultivos",
    "Vientos fuertes": "Cortinas Rompevientos",
    "Temperaturas extremas": "Sombra en Cafetales y Cultivos",
    "Erosión": "Prácticas de Conservación de Suelos"
}

def extract_livelihoods(xl: pd.ExcelFile) -> List[Dict[str, Any]]:
    """Extract livelihood details from characterization and prioritization tables."""
    livelihoods = []
    
    # Get unique livelihoods from LOOKUP_MDV
    if "LOOKUP_MDV" in xl.sheet_names:
        df = _read_table(xl, "LOOKUP_MDV")
        for _, row in df.iterrows():
            livelihoods.append({
                "mdv_id": str(row.get("mdv_id", "")),
                "mdv_name": str(row.get("mdv_name", "")),
                "context_id": "",
                "i_total": 0,
                "rank": 999,
                "intervention_type": "SbN General",  # Default
                "top_threat": ""
            })
    
    # Map threats to livelihoods to find the top threat
    threat_map = {}
    if "TIDY_4_2_1_AMENAZA_MDV" in xl.sheet_names:
        threat_df = _read_table(xl, "TIDY_4_2_1_AMENAZA_MDV")
        # Ensure we have numeric impact columns to calculate score
        impact_cols = [c for c in threat_df.columns if c.startswith("i_")]
        
        for _, row in threat_df.iterrows():
            ctx_id = str(row.get("context_id", ""))
            mdv_name = str(row.get("mdv_name", "")) # Note: using name as ID link is fragile but common in this project's excel structure
            threat = str(row.get("amenaza", ""))
            
            # Calculate simple impact score
            if impact_cols:
                vals = [row[c] for c in impact_cols if pd.notna(row[c])]
                score = sum(vals) / len(vals) if vals else 0
            else:
                score = 0
            
            key = (ctx_id, mdv_name)
            if key not in threat_map or score > threat_map[key]["score"]:
                threat_map[key] = {
                    "threat": threat,
                    "score": score
                }
    
    # Add prioritization data if available (TIDY_3_2_PRIORIZACION)
    prio_map = {}
    if "TIDY_3_2_PRIORIZACION" in xl.sheet_names:
        prio_df = _read_table(xl, "TIDY_3_2_PRIORIZACION")
        for _, row in prio_df.iterrows():
            key = (str(row.get("context_id", "")), str(row.get("mdv_id", "")))
            prio_map[key] = {
                "i_total": row.get("i_total", 0),
                "rank": row.get("rank_in_zona", 999)
            }
    
    # Enrich with characterization data if available
    car_a_sheet = next((s for s in xl.sheet_names if "3_3_CAR_A" in s), None)
    if car_a_sheet:
        car_a = _read_table(xl, car_a_sheet)
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
                    liv["i_total"] = 0
                    liv["rank"] = 999
                
                
                    liv["intervention_type"] = "SbN General" # Reset/Default if re-assigning? No, let's leave it to the final pass or specific logic data.
                    # Actually, let's remove the logic from here and put it below to ensure it runs for everyone.
    
    # Final pass: Assign interventions based on threats (Runs for ALL livelihoods, regardless of CAR_A presence)
    for liv in livelihoods:
        ctx_id = liv.get("context_id", "")
        # Try matching by (ctx, name)
        t_data = threat_map.get((ctx_id, liv["mdv_name"]))
        
        # Fallback: Try matching just by MDV name 
        if not t_data:
             for (t_ctx, t_mdv), data in threat_map.items():
                 if t_mdv == liv["mdv_name"]:
                     t_data = data
                     break

        if t_data:
            threat_name = t_data["threat"]
            liv["top_threat"] = threat_name
            
            found_intervention = "SbN General"
            for k, v in INTERVENTION_MAP.items():
                if k.lower() in threat_name.lower():
                    found_intervention = v
                    break
            
            if found_intervention == "SbN General" and threat_name:
                 found_intervention = f"Gestión de {threat_name}"
            
            liv["intervention_type"] = found_intervention
    
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
        "capacity": analyze_capacity(extract_capacity(xl)),
        "qa": build_qa_summary(xl)
    }
    
    return bundle


def extract_capacity(xl: pd.ExcelFile) -> List[Dict[str, Any]]:
    """Extract capacity data from TIDY_7_1_CAPACITY."""
    capacity_data = []
    
    if "TIDY_7_1_CAPACITY" in xl.sheet_names:
        df = _read_table(xl, "TIDY_7_1_CAPACITY")
        cols = ["mdv_id", "mdv_name", "dimension", "indicator", "score"]
        available_cols = [c for c in cols if c in df.columns]
        
        for _, row in df.iterrows():
            record = {}
            for c in available_cols:
                val = row.get(c)
                if pd.isna(val):
                    record[c] = "" if c in ["mdv_id", "mdv_name", "dimension", "indicator"] else 0
                else:
                    record[c] = float(val) if c == "score" else str(val).strip()
            
            # Normalize Dimension Names (handle potential typos)
            dim = record.get("dimension", "").lower()
            if "innov" in dim: record["dimension"] = "Innovación"
            elif "necesid" in dim: record["dimension"] = "Necesidades Básicas"
            elif "acci" in dim: record["dimension"] = "Acción"
            
            capacity_data.append(record)
            
    return capacity_data


def analyze_capacity(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform analytical processing on capacity data.
    Returns structured data for visualization and narrative generation.
    """
    if not data:
        return {"profiles": [], "narrative": {}}

    # 1. Group by Livelihood
    profiles = {}
    for row in data:
        mdv = row.get("mdv_name", "Unknown")
        if mdv not in profiles:
            profiles[mdv] = {
                "mdv_name": mdv,
                "scores": {},      # Map of indicator -> score
                "dimensions": {    # Aggregate scores per dimension
                    "Innovación": [],
                    "Necesidades Básicas": [],
                    "Acción": []
                }
            }
        
        # Store individual score
        ind = row.get("indicator")
        score = row.get("score", 0)
        profiles[mdv]["scores"][ind] = score
        
        # Add to dimension list for aggregation
        dim = row.get("dimension")
        if dim in profiles[mdv]["dimensions"]:
            profiles[mdv]["dimensions"][dim].append(score)
            
            # Store detailed mapping for frontend
            if "dimension_detail" not in profiles[mdv]:
                profiles[mdv]["dimension_detail"] = {k: {} for k in profiles[mdv]["dimensions"]}
            profiles[mdv]["dimension_detail"][dim][ind] = score

    # 2. Compute Aggregates & Resilience Index
    result_profiles = []
    for mdv, p in profiles.items():
        # Compute dimension means
        dim_scores = {}
        for dim, scores in p["dimensions"].items():
            dim_scores[dim] = sum(scores) / len(scores) if scores else 0
        
        # Resilience Index (Simple Average of Dimensions)
        res_index = sum(dim_scores.values()) / 3
        
        # Resilience Classification
        if res_index < 2.0: status = "Sobrevivencia"
        elif res_index < 3.5: status = "Adaptación"
        else: status = "Transformación"

        result_profiles.append({
            "mdv_name": mdv,
            "dimension_scores": dim_scores,
            "dimension_detail": p.get("dimension_detail", {}),
            "indicators": p["scores"],
            "resilience_index": res_index,
            "resilience_status": status
        })

    # 3. Compute Group Average
    group_avg = {
        "mdv_name": "Promedio del Grupo",
        "dimension_scores": {},
        "dimension_detail": {},
        "indicators": {},
        "resilience_index": 0,
        "resilience_status": "Promedio"
    }
    
    all_indicators = {}
    all_dimensions = {"Innovación": [], "Necesidades Básicas": [], "Acción": []}
    
    for p in result_profiles:
        for ind, score in p["indicators"].items():
            if ind not in all_indicators: all_indicators[ind] = []
            all_indicators[ind].append(score)
        for dim, score in p["dimension_scores"].items():
            all_dimensions[dim].append(score)
            
    for ind, scores in all_indicators.items():
        group_avg["indicators"][ind] = sum(scores) / len(scores) if scores else 0
        
    for dim, scores in all_dimensions.items():
        group_avg["dimension_scores"][dim] = sum(scores) / len(scores) if scores else 0
        
    group_avg["resilience_index"] = sum(group_avg["dimension_scores"].values()) / 3
    
    # Organize dimension_detail for group_avg
    for row in data:
        dim = row.get("dimension")
        ind = row.get("indicator")
        if dim not in group_avg["dimension_detail"]:
            group_avg["dimension_detail"][dim] = {}
        group_avg["dimension_detail"][dim][ind] = group_avg["indicators"].get(ind, 0)

    # 4. Generate Narratives (Automated Insights)
    narrative = generate_capacity_narrative(result_profiles)

    return {
        "profiles": result_profiles,
        "group_avg": group_avg,
        "narrative": narrative
    }


def generate_capacity_narrative(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate text-based insights based on the analysis.
    """
    nar = {
        "general_status": "",
        "vulnerability_alert": [],
        "equity_insight": "",
        "strategic_recommendation": ""
    }

    if not profiles:
        return nar

    # Sort profiles by resilience index
    sorted_profiles = sorted(profiles, key=lambda x: x["resilience_index"], reverse=True)
    best = sorted_profiles[0]
    worst = sorted_profiles[-1]

    nar["general_status"] = (
        f"El panorama de resiliencia muestra una disparidad significativa. "
        f"Mientras que **{best['mdv_name']}** lidera con un índice de {best['resilience_index']:.1f} ({best['resilience_status']}), "
        f"el grupo de **{worst['mdv_name']}** se encuentra en estado de {worst['resilience_status']} ({worst['resilience_index']:.1f})."
    )

    # 1. Vulnerability Check
    for p in profiles:
        fs = p["indicators"].get("Seguridad alimentaria", 0)
        ps = p["indicators"].get("Seguridad personal", 0)
        if fs < 2.5:
            nar["vulnerability_alert"].append(f"🔴 **{p['mdv_name']}** enfrenta inseguridad alimentaria crítica ({fs}).")
        if ps < 2.5:
            nar["vulnerability_alert"].append(f"⚠️ **{p['mdv_name']}** reporta riesgos de seguridad personal ({ps}).")

    # 2. Equity Insight
    equity_scores = []
    for p in profiles:
        eq_vals = [v for k,v in p["indicators"].items() if 'quidad' in k] 
        if eq_vals:
            avg_eq = sum(eq_vals)/len(eq_vals)
            equity_scores.append((p['mdv_name'], avg_eq))
    
    if equity_scores:
        equity_scores.sort(key=lambda x: x[1])
        low_eq_mdv = equity_scores[0]
        nar["equity_insight"] = (
            f"El análisis transversal de género indica que **{low_eq_mdv[0]}** tiene las brechas de equidad más marcadas ({low_eq_mdv[1]:.1f}), "
            "lo que sugiere que las intervenciones en este sector deben priorizar la inclusión de mujeres en la toma de decisiones."
        )

    # 3. Strategic Recommendation
    rec_mdv = worst
    org = rec_mdv["indicators"].get("Organización", 0)
    assets = rec_mdv["indicators"].get("Insumos", 0)
    
    if org > assets + 1:
        nar["strategic_recommendation"] = (
            f"Para **{rec_mdv['mdv_name']}**, existe un fuerte capital social (Organización {org}), pero faltan recursos tangibles. "
            "La estrategia debe enfocarse en **inversión de activos y tecnología** aprovechando la estructura comunitaria existente."
        )
    elif assets > org + 1:
        nar["strategic_recommendation"] = (
            f"Para **{rec_mdv['mdv_name']}**, existen recursos (Insumos {assets}), pero la organización es débil ({org}). "
            "Se recomienda priorizar el **fortalecimiento de cooperativas y gobernanza local** antes de aumentar la inversión física."
        )
    else:
        nar["strategic_recommendation"] = (
            f"Para **{rec_mdv['mdv_name']}**, se requiere un enfoque integral de 'Big Push', "
            "abordando simultáneamente las necesidades básicas y la capacidad de agencia."
        )

    return nar


def generate_dashboard_html(bundle: Dict[str, Any]) -> str:
    """Generate the dashboard HTML from bundle data."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    bundle_json = json.dumps(bundle, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    return template.replace("/* __BUNDLE_DATA__ */", f"const BUNDLE = {bundle_json};")


def generate_capacity_html(bundle: Dict[str, Any]) -> str:
    """Generate the capacity HTML from bundle data."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "capacity_template.html")
    if not os.path.exists(template_path):
        return ""
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    bundle_json = json.dumps(bundle, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    return template.replace("/* __BUNDLE_DATA__ */", f"const BUNDLE = {bundle_json};")


def generate_dashboard(
    excel_path: str,
    output_dir: str,
    org_name: str = "Organización"
) -> Tuple[str, str, str]:
    """Generate dashboard files."""
    file_name = os.path.basename(excel_path)
    xl = pd.ExcelFile(excel_path)
    bundle = build_bundle(xl, file_name, org_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # JSONs
    bundle_path = os.path.join(output_dir, "bundle.json")
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    qa_path = os.path.join(output_dir, "qa_dashboard.json")
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump(bundle["qa"], f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    # HTMLs
    html = generate_dashboard_html(bundle)
    html_path = os.path.join(output_dir, "dashboard.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    # Capacity Page
    cap_html = generate_capacity_html(bundle)
    if cap_html:
        cap_path = os.path.join(output_dir, "capacity.html")
        with open(cap_path, "w", encoding="utf-8") as f:
            f.write(cap_html)
    
    return html_path, bundle_path, qa_path
