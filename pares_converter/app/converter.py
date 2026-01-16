#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZA TIERRA VIVA — Fully complete deterministic compiler
Input:  database_general_ZA_TIERRA_VIVA.xlsx
Output: analysis-ready workbook with:
  - RAW sheets copied as-is
  - LOOKUP_* normalized dimensions
  - TIDY_* normalized fact/bridge tables
  - QA_* validation sheets

Design goals
- Deterministic IDs (sha1 over canonicalized strings)
- Safe list explosion (comma/semicolon/newline)
- Zero manual cleanup: output can be consumed by notebooks/pipelines
"""

from __future__ import annotations
import argparse
import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


# ---------------------------
# CONFIG (exact sheet names)
# ---------------------------

SHEETS = [
    "variables",
    "3.1. Lluvia MdV&SE",
    "3.2. Priorización",
    "3.3. Car_A",
    "3.3. Car_B",
    "3.3. Car_C",
    "3.3. Car_D",
    "3.4. Ecosistemas",
    "3.5. SE y MdV",
    "4.1. Amenazas",
    "4.2.1. Amenazas_MdV",
    "4.2.2. Amenazas_SE",
    "5.1. Actores",
    "5.2. Diálogo",
    "6.1. Evolución_conflict",
    "6.2. Actores_conflict",
    "7.1. Encuesta CA",
]

REQUIRED_COLUMNS = {
    "variables": ["Herramienta/variable"],
    "3.1. Lluvia MdV&SE": ["fecha","admin0","paisaje","grupo","elemento_SES","nombre","uso_fin_mdv"],
    "3.2. Priorización": ["fecha","admin0","paisaje","grupo","mdv ","producto_principal","i_seg_alim","i_area","i_des_loc","i_ambiente","i_inclusion","i_total"],

    "3.3. Car_A": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","sistema","uso_final","cv_importancia","cv_producto","cv_mercado"],
    "3.3. Car_B": ["fecha","admin0","paisaje","grupo","mdv","codigo_mapa","tenencia","tenencia_descripcion"],
    "3.3. Car_C": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","tamano","unidad","rango","porcentaje"],
    "3.3. Car_D": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","tenencia","tamano","porcentaje"],

    "3.4. Ecosistemas": ["fecha","admin0","paisaje","grupo","ecosistema","tipo","mdv_relacionado","es_salud","servicio_ecosistemico","causas_deg","cod_es"],
    "3.5. SE y MdV": ["fecha","admin0","paisaje","grupo","cod_es_se","mdv_relacionado","elemento_se","accesso","barreras","nr_usuarios","mes_contrib","mes_falta","inclusion","incl_descripcion"],

    "4.1. Amenazas": ["fecha","admin0","paisaje","grupo","tipo_amenaza","amenaza","magnitud","frequencia","tendencia","suma","sitios_afect","cod_mapa"],

    "4.2.1. Amenazas_MdV": ["fecha","admin0","paisaje","grupo","tipo_amenaza","amenaza","mdv",
                             "i_economia","i_econ_coment","i_alimentaria","i_aliment_coment","i_sanitaria","i_sanit_coment",
                             "i_ambiental","i_amb_coment","i_personal","i_pers_coment","i_comunitaria","i_comun_coment",
                             "i_politica","i_polit_coment","nr_familias","i_diferenciado","tipo_conflicto","nivel_conflicto","mapeo_conflicto"],

    "4.2.2. Amenazas_SE": ["fecha","admin0","paisaje","grupo","tipo_amenaza","amenaza","cod_se",
                            "i_economia","i_econ_coment","i_alimentaria","i_aliment_coment","i_sanitaria","i_sanit_coment",
                            "i_ambiental","i_amb_coment","i_personal","i_pers_coment","i_comunitaria","i_comun_coment",
                            "i_politica","i_polit_coment","nr_familias","i_diferenciado","tipo_conflicto","nivel_conflicto","mapeo_conflicto"],

    "5.1. Actores": ["fecha","admin0","paisaje","grupo","nombre_actor","tipo_actor","rol_paisaje","conflicto_con","colabor_con","poder","interes"],
    "5.2. Diálogo": ["fecha","admin0","paisaje","grupo","nombre_espacio","tipo","alcance","actores_invol","funcion","incidencia","fortalezas","debilidades"],

    "6.1. Evolución_conflict": ["fecha","admin0","paisaje","grupo","cod_conflict","evento","ano_evento","diferencias","dif_factor","cooperacion","coop_factor","suma"],
    "6.2. Actores_conflict": ["fecha","admin0","paisaje","grupo","cod_conflict","actor","i_en_actor","iea_factor","i_en_conflicto","iec_factor"],

    "7.1. Encuesta CA": ["País","Grupo","Medio de vida","Tamaño de propiedad"],
}


# ---------------------------
# UTILITIES
# ---------------------------

def canonical_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and np.isnan(x):
        return ""
    s = unicodedata.normalize("NFKC", str(x))
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()

def sha1_short(*parts: Any, n: int = 16) -> str:
    joined = "|".join(canonical_text(p) for p in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:n]

def coerce_date_iso(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    ts = pd.to_datetime(x, errors="coerce")
    if pd.notna(ts):
        return ts.date().isoformat()
    return canonical_text(x)

def split_list(value: Any) -> List[str]:
    """Split comma/semicolon/newline lists, return de-duplicated tokens preserving first-seen order."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return []
    # common separators: comma, semicolon, newline; keep also " / " as separator occasionally
    tokens = re.split(r"[,;\n]+", s)
    out, seen = [], set()
    for t in tokens:
        t2 = t.strip()
        if not t2:
            continue
        k = canonical_text(t2)
        if k in seen:
            continue
        seen.add(k)
        out.append(t2)
    return out

def explode_list_column(df: pd.DataFrame, col: str, out_col: str) -> pd.DataFrame:
    tmp = df.copy()
    tmp[col] = tmp[col].apply(split_list)
    tmp = tmp.explode(col, ignore_index=True)
    tmp = tmp.rename(columns={col: out_col})
    tmp = tmp[tmp[out_col].notna() & (tmp[out_col].astype(str).str.strip() != "")]
    return tmp

MONTH_MAP = {
    "ene": 1, "enero": 1,
    "feb": 2, "febrero": 2,
    "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6,
    "jul": 7, "julio": 7,
    "ago": 8, "agosto": 8,
    "sep": 9, "sept": 9, "septiembre": 9,
    "oct": 10, "octubre": 10,
    "nov": 11, "noviembre": 11,
    "dic": 12, "diciembre": 12
}

def parse_month_tokens(value: Any) -> List[Tuple[str,int]]:
    toks = split_list(value)
    out = []
    for t in toks:
        k = canonical_text(t).replace(".", "")
        num = MONTH_MAP.get(k)
        out.append((t, num if num is not None else np.nan))
    return out


# ---------------------------
# IO
# ---------------------------

# Column name mappings: long form (sample file) -> short form (V2 expected)
# Note: Some mappings are sheet-specific and handled in normalize_columns
COLUMN_ALIASES = {
    # 3.1
    "uso_fin_medio_de_vida": "uso_fin_mdv",
    # 3.2 indices
    "indice_seguridad_alimentaria": "i_seg_alim",
    "imdice_area": "i_area",  # Note: typo in source 'imdice'
    "indice_area": "i_area",
    "indice_desarrollo_local": "i_des_loc",
    "indice_ambiente": "i_ambiente",
    "indice_inlcusion": "i_inclusion",  # Note: typo in source 'inlcusion'
    "indice_inclusion": "i_inclusion",
    "indice_total": "i_total",
    # 3.3
    "codigo_medio_de_vida": "codigo_mdv",
    # 3.4 / 3.5
    "medio_de_vida_relacionado": "mdv_relacionado",
}

# Sheet-specific column mappings
SHEET_COLUMN_ALIASES = {
    "3.2. Priorización": {
        "medio_de_vida": "mdv ",  # V2 expects "mdv " with trailing space in 3.2
    },
    "3.3. Car_A": {"medio_de_vida": "mdv"},
    "3.3. Car_B": {"medio_de_vida": "mdv"},
    "3.3. Car_C": {"medio_de_vida": "mdv"},
    "3.3. Car_D": {"medio_de_vida": "mdv"},
    "4.2.1. Amenazas_MdV": {"medio_de_vida": "mdv"},
}

def normalize_columns(df: pd.DataFrame, sheet_name: str = "") -> pd.DataFrame:
    """Apply column name aliases to normalize input data."""
    rename_map = {}
    
    # First apply sheet-specific mappings
    sheet_aliases = SHEET_COLUMN_ALIASES.get(sheet_name, {})
    
    for col in df.columns:
        col_str = str(col).strip()
        # Check sheet-specific alias first
        if col_str in sheet_aliases:
            rename_map[col] = sheet_aliases[col_str]
        # Then check global aliases
        elif col_str in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col_str]
    
    if rename_map:
        # Only rename if target column doesn't already exist to avoid collision
        safe_map = {}
        existing = set(df.columns)
        for old, new in rename_map.items():
            if new not in existing:
                safe_map[old] = new
        if safe_map:
            df = df.rename(columns=safe_map)
    return df

def read_workbook(path: str) -> Dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path, engine="openpyxl")
    raw: Dict[str, pd.DataFrame] = {}
    for sh in SHEETS:
        if sh in xls.sheet_names:
            df = pd.read_excel(xls, sh, dtype=object)
            # Deduplicate columns (keep first)
            df = df.loc[:, ~df.columns.duplicated()]
            # Normalize column names (sheet-aware)
            df = normalize_columns(df, sheet_name=sh)
            # Deduplicate again in case normalization caused collisions
            df = df.loc[:, ~df.columns.duplicated()]
            raw[sh] = df
    return raw
    return raw

def write_workbook(path: str, tables: Dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in tables.items():
            sheet_name = name if len(name) <= 31 else (name[:27] + "...")
            df.to_excel(writer, sheet_name=sheet_name, index=False)


# ---------------------------
# VALIDATION
# ---------------------------

class ValidationError(ValueError):
    def __init__(self, message, df):
        super().__init__(message)
        self.df = df

def validate_input(raw: Dict[str, pd.DataFrame], strict: bool = True) -> pd.DataFrame:
    rows = []
    for sh, req in REQUIRED_COLUMNS.items():
        if sh not in raw:
            rows.append({"sheet": sh, "status": "missing_sheet", "missing_cols": ",".join(req)})
            continue
        cols = set(raw[sh].columns)
        missing = [c for c in req if c not in cols]
        status = "ok" if not missing else "missing_columns"
        rows.append({"sheet": sh, "status": status, "missing_cols": ",".join(missing)})
    out = pd.DataFrame(rows)
    if strict and (out["status"] != "ok").any():
        bad = out[out["status"] != "ok"]
        # Convert bad rows to string logic is preserved for CLI msg
        raise ValidationError("Input validation failed:\n" + bad.to_string(index=False), bad)
    return out


# ---------------------------
# LOOKUPS
# ---------------------------

def build_lookup_geo_context(raw: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for sh, df in raw.items():
        if all(c in df.columns for c in ["fecha","admin0","paisaje","grupo"]):
            tmp = df[["fecha","admin0","paisaje","grupo"]].copy()
            tmp["fecha_iso"] = tmp["fecha"].apply(coerce_date_iso)
            frames.append(tmp[["fecha_iso","admin0","paisaje","grupo"]])
    if not frames:
        lookup_geo = pd.DataFrame(columns=["geo_id","admin0","paisaje","grupo"])
        lookup_context = pd.DataFrame(columns=["context_id","geo_id","fecha_iso"])
        return lookup_geo, lookup_context

    ctx = pd.concat(frames, ignore_index=True).drop_duplicates()
    # normalize group/paisaje/admin0 nulls to empty strings for stable IDs
    for c in ["admin0","paisaje","grupo"]:
        ctx[c] = ctx[c].apply(lambda x: "" if (x is None or (isinstance(x,float) and np.isnan(x))) else str(x).strip())
    ctx["geo_id"] = ctx.apply(lambda r: sha1_short(r["admin0"], r["paisaje"], r["grupo"]), axis=1)
    lookup_geo = ctx[["geo_id","admin0","paisaje","grupo"]].drop_duplicates().reset_index(drop=True)

    ctx["context_id"] = ctx.apply(lambda r: sha1_short(r["geo_id"], r["fecha_iso"]), axis=1)
    lookup_context = ctx[["context_id","geo_id","fecha_iso"]].drop_duplicates().reset_index(drop=True)
    return lookup_geo, lookup_context

def build_context_map(lookup_geo: pd.DataFrame, lookup_context: pd.DataFrame) -> Dict[Tuple[str,str,str,str], str]:
    tmp = lookup_context.merge(lookup_geo, on="geo_id", how="left")
    tmp["_k"] = tmp.apply(lambda r: (
        canonical_text(r["admin0"]),
        canonical_text(r["paisaje"]),
        canonical_text(r["grupo"]),
        str(r["fecha_iso"])
    ), axis=1)
    return dict(zip(tmp["_k"], tmp["context_id"]))

def infer_paisaje_for_country_group(raw: Dict[str,pd.DataFrame]) -> Dict[Tuple[str,str], str]:
    """For survey context, infer the most common paisaje for (admin0, grupo) from other sheets."""
    rows = []
    for sh, df in raw.items():
        if all(c in df.columns for c in ["admin0","grupo","paisaje"]):
            tmp = df[["admin0","grupo","paisaje"]].copy()
            tmp["admin0"] = tmp["admin0"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
            tmp["grupo"]  = tmp["grupo"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
            tmp["paisaje"]= tmp["paisaje"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
            rows.append(tmp)
    if not rows:
        return {}
    allx = pd.concat(rows, ignore_index=True)
    allx = allx[allx["admin0"].astype(str).str.strip()!=""]
    # mode paisaje per (admin0, grupo)
    out = {}
    for (a,g), sub in allx.groupby(["admin0","grupo"], dropna=False):
        vals = [v for v in sub["paisaje"].tolist() if str(v).strip()!=""]
        if not vals:
            continue
        # mode:
        mode = pd.Series(vals).mode()
        out[(canonical_text(a), canonical_text(g))] = str(mode.iloc[0])
    return out

def build_lookup_survey_context(raw: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    if "7.1. Encuesta CA" not in raw:
        return pd.DataFrame(columns=["survey_context_id","admin0","grupo","paisaje_inferido"])
    df = raw["7.1. Encuesta CA"][["País","Grupo"]].copy().drop_duplicates()
    df["admin0"] = df["País"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    df["grupo"]  = df["Grupo"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    inf = infer_paisaje_for_country_group(raw)
    df["paisaje_inferido"] = df.apply(lambda r: inf.get((canonical_text(r["admin0"]), canonical_text(r["grupo"])), ""), axis=1)
    df["survey_context_id"] = df.apply(lambda r: sha1_short("survey", r["admin0"], r["grupo"], r["paisaje_inferido"]), axis=1)
    return df[["survey_context_id","admin0","grupo","paisaje_inferido"]].reset_index(drop=True)

def build_lookup_mdv(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: List[str] = []

    # 3.1 brainstorm
    if "3.1. Lluvia MdV&SE" in raw:
        df = raw["3.1. Lluvia MdV&SE"]
        if "elemento_SES" in df.columns and "nombre" in df.columns:
            mdv_names = df.loc[df["elemento_SES"].astype(str).str.lower().str.contains("medio", na=False), "nombre"]
            rows.extend(mdv_names.dropna().astype(str).tolist())

    # 3.2
    if "3.2. Priorización" in raw and "mdv " in raw["3.2. Priorización"].columns:
        rows.extend(raw["3.2. Priorización"]["mdv "].dropna().astype(str).tolist())

    # 3.3
    for sh in ["3.3. Car_A","3.3. Car_B","3.3. Car_C","3.3. Car_D"]:
        if sh in raw and "mdv" in raw[sh].columns:
            rows.extend(raw[sh]["mdv"].dropna().astype(str).tolist())

    # 3.4 + 3.5
    for sh in ["3.4. Ecosistemas","3.5. SE y MdV"]:
        if sh in raw and "mdv_relacionado" in raw[sh].columns:
            for v in raw[sh]["mdv_relacionado"].tolist():
                rows.extend(split_list(v))

    # 4.2.1 mdv lists
    if "4.2.1. Amenazas_MdV" in raw and "mdv" in raw["4.2.1. Amenazas_MdV"].columns:
        for v in raw["4.2.1. Amenazas_MdV"]["mdv"].tolist():
            rows.extend(split_list(v))

    # survey CA
    if "7.1. Encuesta CA" in raw and "Medio de vida" in raw["7.1. Encuesta CA"].columns:
        rows.extend(raw["7.1. Encuesta CA"]["Medio de vida"].dropna().astype(str).tolist())

    cleaned, seen = [], set()
    for x in rows:
        s = str(x).strip()
        if not s or s.lower() == "nan":
            continue
        k = canonical_text(s)
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(s)

    out = pd.DataFrame({"mdv_name": cleaned})
    out["mdv_id"] = out["mdv_name"].apply(lambda x: sha1_short("mdv", x))
    return out[["mdv_id","mdv_name"]].reset_index(drop=True)

def build_lookup_ecosistema(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    # 3.1 brainstorm ecosystems
    if "3.1. Lluvia MdV&SE" in raw:
        df = raw["3.1. Lluvia MdV&SE"]
        if "elemento_SES" in df.columns and "nombre" in df.columns:
            eco = df.loc[df["elemento_SES"].astype(str).str.lower().str.contains("ecosistema", na=False), "nombre"]
            for v in eco.dropna().astype(str).tolist():
                rows.append({"cod_es": np.nan, "ecosistema": v.strip()})
    # 3.4
    if "3.4. Ecosistemas" in raw:
        df = raw["3.4. Ecosistemas"]
        for _, r in df[["cod_es","ecosistema"]].dropna(subset=["ecosistema"]).drop_duplicates().iterrows():
            rows.append({"cod_es": r.get("cod_es"), "ecosistema": str(r.get("ecosistema")).strip()})

    if not rows:
        return pd.DataFrame(columns=["ecosistema_id","cod_es","ecosistema"])

    out = pd.DataFrame(rows)
    out["cod_es"] = out["cod_es"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    out["ecosistema"] = out["ecosistema"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    # prefer cod_es when present for ID stability, else use ecosistema name
    out["ecosistema_id"] = out.apply(lambda r: sha1_short("eco", r["cod_es"] if r["cod_es"] else r["ecosistema"]), axis=1)
    out = out.drop_duplicates(subset=["ecosistema_id"]).reset_index(drop=True)
    return out[["ecosistema_id","cod_es","ecosistema"]]

def build_lookup_se(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    codes: List[str] = []

    # 3.4 service_ecosistemico (strings like P1, P2 etc)
    if "3.4. Ecosistemas" in raw and "servicio_ecosistemico" in raw["3.4. Ecosistemas"].columns:
        for v in raw["3.4. Ecosistemas"]["servicio_ecosistemico"].tolist():
            codes.extend(split_list(v))

    # 3.5 cod_es_se: split ecosistema + cod_se if possible
    if "3.5. SE y MdV" in raw and "cod_es_se" in raw["3.5. SE y MdV"].columns:
        for v in raw["3.5. SE y MdV"]["cod_es_se"].tolist():
            if v is None or (isinstance(v,float) and np.isnan(v)):
                continue
            s = str(v).strip()
            if "_" in s:
                _, cod = s.split("_", 1)
                codes.append(cod.strip())
            else:
                codes.append(s)

    # 4.2.2 cod_se
    if "4.2.2. Amenazas_SE" in raw and "cod_se" in raw["4.2.2. Amenazas_SE"].columns:
        codes.extend(raw["4.2.2. Amenazas_SE"]["cod_se"].dropna().astype(str).tolist())

    cleaned, seen = [], set()
    for c in codes:
        s = str(c).strip()
        if not s or s.lower() == "nan":
            continue
        k = canonical_text(s)
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(s)

    out = pd.DataFrame({"cod_se": cleaned})
    out["se_id"] = out["cod_se"].apply(lambda x: sha1_short("se", x))
    return out[["se_id","cod_se"]].reset_index(drop=True)

def build_lookup_elemento_se(raw: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    vals = []
    if "3.5. SE y MdV" in raw and "elemento_se" in raw["3.5. SE y MdV"].columns:
        vals.extend(raw["3.5. SE y MdV"]["elemento_se"].dropna().astype(str).tolist())
    cleaned, seen = [], set()
    for v in vals:
        s = str(v).strip()
        if not s or s.lower()=="nan":
            continue
        k = canonical_text(s)
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(s)
    out = pd.DataFrame({"elemento_se": cleaned})
    out["elemento_se_id"] = out["elemento_se"].apply(lambda x: sha1_short("elemento_se", x))
    return out[["elemento_se_id","elemento_se"]].reset_index(drop=True)

def build_lookup_amenaza(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for sh in ["4.1. Amenazas","4.2.1. Amenazas_MdV","4.2.2. Amenazas_SE"]:
        if sh in raw and all(c in raw[sh].columns for c in ["tipo_amenaza","amenaza"]):
            frames.append(raw[sh][["tipo_amenaza","amenaza"]].dropna().drop_duplicates())
    if not frames:
        return pd.DataFrame(columns=["amenaza_id","tipo_amenaza","amenaza"])
    out = pd.concat(frames, ignore_index=True).drop_duplicates()
    out["amenaza_id"] = out.apply(lambda r: sha1_short("amenaza", r["tipo_amenaza"], r["amenaza"]), axis=1)
    return out[["amenaza_id","tipo_amenaza","amenaza"]].reset_index(drop=True)

def build_lookup_actor(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    if "5.1. Actores" in raw:
        df = raw["5.1. Actores"]
        if "nombre_actor" in df.columns:
            rows.extend(df["nombre_actor"].dropna().astype(str).tolist())
        for col in ["colabor_con","conflicto_con"]:
            if col in df.columns:
                for v in df[col].tolist():
                    rows.extend(split_list(v))
    if "5.2. Diálogo" in raw and "actores_invol" in raw["5.2. Diálogo"].columns:
        for v in raw["5.2. Diálogo"]["actores_invol"].tolist():
            rows.extend(split_list(v))
    if "6.2. Actores_conflict" in raw and "actor" in raw["6.2. Actores_conflict"].columns:
        rows.extend(raw["6.2. Actores_conflict"]["actor"].dropna().astype(str).tolist())

    cleaned, seen = [], set()
    for x in rows:
        s = str(x).strip()
        if not s or s.lower()=="nan":
            continue
        k = canonical_text(s)
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(s)

    out = pd.DataFrame({"nombre_actor": cleaned})
    out["actor_id"] = out["nombre_actor"].apply(lambda x: sha1_short("actor", x))
    return out[["actor_id","nombre_actor"]].reset_index(drop=True)

def build_lookup_espacio(raw: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    if "5.2. Diálogo" not in raw:
        return pd.DataFrame(columns=["espacio_id","nombre_espacio"])
    df = raw["5.2. Diálogo"]
    if "nombre_espacio" not in df.columns:
        return pd.DataFrame(columns=["espacio_id","nombre_espacio"])
    names = df["nombre_espacio"].dropna().astype(str).map(str.strip).drop_duplicates().tolist()
    out = pd.DataFrame({"nombre_espacio": names})
    out["espacio_id"] = out["nombre_espacio"].apply(lambda x: sha1_short("espacio", x))
    return out[["espacio_id","nombre_espacio"]].reset_index(drop=True)

def build_lookup_conflicto(raw: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    codes = []
    for sh in ["6.1. Evolución_conflict","6.2. Actores_conflict"]:
        if sh in raw and "cod_conflict" in raw[sh].columns:
            for v in raw[sh]["cod_conflict"].tolist():
                codes.extend(split_list(v))
    # also parse mapeo_conflicto tokens (underscores) but keep as codes too
    for sh in ["4.2.1. Amenazas_MdV","4.2.2. Amenazas_SE"]:
        if sh in raw and "mapeo_conflicto" in raw[sh].columns:
            for v in raw[sh]["mapeo_conflicto"].tolist():
                if v is None or (isinstance(v,float) and np.isnan(v)):
                    continue
                s = str(v).strip()
                if not s:
                    continue
                toks = re.split(r"[_\s,;]+", s)
                for t in toks:
                    t2 = t.strip()
                    if t2:
                        codes.append(t2)

    cleaned, seen = [], set()
    for c in codes:
        s = str(c).strip()
        if not s or s.lower()=="nan":
            continue
        k = canonical_text(s)
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(s)

    out = pd.DataFrame({"cod_conflict": cleaned})
    out["conflicto_id"] = out["cod_conflict"].apply(lambda x: sha1_short("conflict", x))
    return out[["conflicto_id","cod_conflict"]].reset_index(drop=True)

def build_lookup_ca_questions(raw: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    if "7.1. Encuesta CA" not in raw:
        return pd.DataFrame(columns=["question_id","question_order","question_text","column_name"])
    df = raw["7.1. Encuesta CA"]
    fixed = ["País","Grupo","Medio de vida","Tamaño de propiedad"]
    qcols = [c for c in df.columns if c not in fixed]
    rows = []
    for c in qcols:
        text = str(c).strip()
        m = re.match(r"^\s*(\d+)\s*[.)]?\s*(.*)$", text)
        if m:
            order = int(m.group(1))
            qtext = m.group(2).strip() if m.group(2).strip() else text
        else:
            order = np.nan
            qtext = text
        qid = sha1_short("ca_q", order if order==order else "", qtext)
        rows.append({"question_id": qid, "question_order": order, "question_text": qtext, "column_name": text})
    if not rows:
        out = pd.DataFrame(columns=["question_id","question_order","question_text","column_name"])
    else:
        out = pd.DataFrame(rows)
    # stable order: numeric then others
    out = out.sort_values(by=["question_order","question_text"], na_position="last").reset_index(drop=True)
    return out[["question_id","question_order","question_text","column_name"]]


# ---------------------------
# TIDY HELPERS
# ---------------------------

def attach_context_id(df: pd.DataFrame, cmap: Dict[Tuple[str,str,str,str], str]) -> pd.DataFrame:
    tmp = df.copy()
    tmp["fecha_iso"] = tmp["fecha"].apply(coerce_date_iso)
    def key(r):
        return (canonical_text(r.get("admin0")), canonical_text(r.get("paisaje")), canonical_text(r.get("grupo")), str(r.get("fecha_iso")))
    tmp["context_id"] = tmp.apply(lambda r: cmap.get(key(r), np.nan), axis=1)
    return tmp

def mdv_id_map(lookup_mdv: pd.DataFrame) -> Dict[str,str]:
    return dict(zip(lookup_mdv["mdv_name"].map(canonical_text), lookup_mdv["mdv_id"]))

def actor_id_map(lookup_actor: pd.DataFrame) -> Dict[str,str]:
    return dict(zip(lookup_actor["nombre_actor"].map(canonical_text), lookup_actor["actor_id"]))

def se_id_map(lookup_se: pd.DataFrame) -> Dict[str,str]:
    return dict(zip(lookup_se["cod_se"].map(canonical_text), lookup_se["se_id"]))

def ecosistema_id_map(lookup_eco: pd.DataFrame) -> Dict[str,str]:
    # map by cod_es if present else by name
    m = {}
    for _, r in lookup_eco.iterrows():
        if str(r.get("cod_es","")).strip():
            m[canonical_text(r["cod_es"])] = r["ecosistema_id"]
        if str(r.get("ecosistema","")).strip():
            m[canonical_text(r["ecosistema"])] = r["ecosistema_id"]
    return m


# ---------------------------
# TIDY TRANSFORMS
# ---------------------------

def tidy_3_1_brainstorm(raw, geo, ctx, mdv_lk, eco_lk) -> pd.DataFrame:
    sh = "3.1. Lluvia MdV&SE"
    if sh not in raw:
        return pd.DataFrame(columns=["brainstorm_id","context_id","elemento_SES","nombre","uso_fin_mdv","mdv_id","ecosistema_id"])
    cmap = build_context_map(geo, ctx)
    df = attach_context_id(raw[sh], cmap)

    # Normalize column name variants
    if "uso_fin_medio_de_vida" in df.columns and "uso_fin_mdv" not in df.columns:
        df = df.rename(columns={"uso_fin_medio_de_vida": "uso_fin_mdv"})
    if "uso_fin_mdv" not in df.columns:
        df["uso_fin_mdv"] = np.nan

    mdvmap = mdv_id_map(mdv_lk)
    ecomap = ecosistema_id_map(eco_lk)

    df["elemento_SES_norm"] = df["elemento_SES"].apply(canonical_text)
    df["mdv_id"] = np.where(df["elemento_SES_norm"].str.contains("medio", na=False),
                            df["nombre"].map(lambda x: mdvmap.get(canonical_text(x), np.nan)),
                            np.nan)
    df["ecosistema_id"] = np.where(df["elemento_SES_norm"].str.contains("ecosistema", na=False),
                                   df["nombre"].map(lambda x: ecomap.get(canonical_text(x), np.nan)),
                                   np.nan)
    df["brainstorm_id"] = df.apply(lambda r: sha1_short("bs", r["context_id"], r["elemento_SES"], r["nombre"], r.get("uso_fin_mdv","")), axis=1)
    out = df[["brainstorm_id","context_id","elemento_SES","nombre","uso_fin_mdv","mdv_id","ecosistema_id"]].copy()
    return out

def tidy_3_2_priorizacion(raw, geo, ctx, mdv_lk) -> pd.DataFrame:
    sh = "3.2. Priorización"
    if sh not in raw:
        return pd.DataFrame(columns=["priorizacion_id","context_id","mdv_id","mdv_name","producto_principal","i_seg_alim","i_area","i_des_loc","i_ambiente","i_inclusion","i_total"])
    cmap = build_context_map(geo, ctx)
    df = raw[sh].copy().rename(columns={"mdv ":"mdv_name"})
    df = attach_context_id(df, cmap)

    mdvmap = mdv_id_map(mdv_lk)
    df["mdv_id"] = df["mdv_name"].map(lambda x: mdvmap.get(canonical_text(x), np.nan))

    num_cols = ["i_seg_alim","i_area","i_des_loc","i_ambiente","i_inclusion","i_total"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["priorizacion_id"] = df.apply(lambda r: sha1_short("prio", r["context_id"], r["mdv_id"]), axis=1)
    keep = ["priorizacion_id","context_id","mdv_id","mdv_name","producto_principal"] + num_cols
    return df[keep].copy()

def tidy_3_3_car(raw, geo, ctx, mdv_lk) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    cmap = build_context_map(geo, ctx)
    mdvmap = mdv_id_map(mdv_lk)

    def base(sheet):
        if sheet not in raw:
            return pd.DataFrame()
        df = attach_context_id(raw[sheet], cmap)
        df["mdv_id"] = df["mdv"].map(lambda x: mdvmap.get(canonical_text(x), np.nan))
        return df

    # A
    dfA = base("3.3. Car_A")
    if dfA.empty:
        tidyA = pd.DataFrame(columns=["car_a_id","context_id","mdv_id","mdv","codigo_mdv","codigo_mapa","sistema","uso_final","cv_importancia","cv_producto","cv_mercado"])
    else:
        tidyA = dfA.copy()
        for c in ["cv_importancia","cv_producto","cv_mercado"]:
            tidyA[c] = pd.to_numeric(tidyA[c], errors="coerce")
        tidyA["car_a_id"] = tidyA.apply(lambda r: sha1_short("carA", r["context_id"], r["mdv_id"], r["codigo_mapa"], r["codigo_mdv"]), axis=1)
        tidyA = tidyA[["car_a_id","context_id","mdv_id","mdv","codigo_mdv","codigo_mapa","sistema","uso_final","cv_importancia","cv_producto","cv_mercado"]].copy()

    # B
    dfB = base("3.3. Car_B")
    if dfB.empty:
        tidyB = pd.DataFrame(columns=["car_b_id","context_id","mdv_id","mdv","codigo_mapa","tenencia","tenencia_descripcion"])
    else:
        tidyB = dfB.copy()
        tidyB["car_b_id"] = tidyB.apply(lambda r: sha1_short("carB", r["context_id"], r["mdv_id"], r["codigo_mapa"], r["tenencia"]), axis=1)
        tidyB = tidyB[["car_b_id","context_id","mdv_id","mdv","codigo_mapa","tenencia","tenencia_descripcion"]].copy()

    # C
    dfC = base("3.3. Car_C")
    if dfC.empty:
        tidyC = pd.DataFrame(columns=["car_c_id","context_id","mdv_id","mdv","codigo_mdv","codigo_mapa","tamano","unidad","rango","porcentaje"])
    else:
        tidyC = dfC.copy()
        tidyC["porcentaje"] = pd.to_numeric(tidyC["porcentaje"], errors="coerce")
        tidyC["car_c_id"] = tidyC.apply(lambda r: sha1_short("carC", r["context_id"], r["mdv_id"], r["codigo_mapa"], r["tamano"], r["unidad"], r["rango"]), axis=1)
        tidyC = tidyC[["car_c_id","context_id","mdv_id","mdv","codigo_mdv","codigo_mapa","tamano","unidad","rango","porcentaje"]].copy()

    # D
    dfD = base("3.3. Car_D")
    if dfD.empty:
        tidyD = pd.DataFrame(columns=["car_d_id","context_id","mdv_id","mdv","codigo_mdv","codigo_mapa","tenencia","tamano","porcentaje"])
    else:
        tidyD = dfD.copy()
        tidyD["porcentaje"] = pd.to_numeric(tidyD["porcentaje"], errors="coerce")
        tidyD["car_d_id"] = tidyD.apply(lambda r: sha1_short("carD", r["context_id"], r["mdv_id"], r["codigo_mapa"], r["tenencia"], r["tamano"]), axis=1)
        tidyD = tidyD[["car_d_id","context_id","mdv_id","mdv","codigo_mdv","codigo_mapa","tenencia","tamano","porcentaje"]].copy()

    # LONG union (fully normalized key-value)
    long_rows = []
    def melt_table(df, pk, module):
        if df.empty:
            return
        nonlocal long_rows
        for _, r in df.iterrows():
            rid = r[pk]
            base = {
                "car_long_id": sha1_short("carL", module, rid),
                "module": module,
                "record_id": rid,
                "context_id": r.get("context_id"),
                "mdv_id": r.get("mdv_id"),
                "mdv": r.get("mdv"),
                "codigo_mapa": r.get("codigo_mapa"),
                "codigo_mdv": r.get("codigo_mdv") if "codigo_mdv" in df.columns else np.nan
            }
            for c in df.columns:
                if c in [pk,"context_id","mdv_id","mdv","codigo_mapa","codigo_mdv"]:
                    continue
                long_rows.append({**base, "field": c, "value": r.get(c)})
    melt_table(tidyA, "car_a_id", "A")
    melt_table(tidyB, "car_b_id", "B")
    melt_table(tidyC, "car_c_id", "C")
    melt_table(tidyD, "car_d_id", "D")

    tidyLong = pd.DataFrame(long_rows) if long_rows else pd.DataFrame(columns=["car_long_id","module","record_id","context_id","mdv_id","mdv","codigo_mapa","codigo_mdv","field","value"])
    return tidyA, tidyB, tidyC, tidyD, tidyLong

def tidy_3_4_ecosistemas(raw, geo, ctx, eco_lk, se_lk, mdv_lk) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    sh = "3.4. Ecosistemas"
    cmap = build_context_map(geo, ctx)
    ecomap = ecosistema_id_map(eco_lk)
    semap = se_id_map(se_lk)
    mdvmap = mdv_id_map(mdv_lk)

    if sh not in raw:
        return (
            pd.DataFrame(columns=["ecosistema_obs_id","context_id","ecosistema_id","cod_es","ecosistema","tipo","es_salud","causas_deg"]),
            pd.DataFrame(columns=["eco_se_id","ecosistema_obs_id","se_id","cod_se"]),
            pd.DataFrame(columns=["eco_mdv_id","ecosistema_obs_id","mdv_id","mdv_name"]),
        )
    df = attach_context_id(raw[sh], cmap).copy()
    df["ecosistema_id"] = df.apply(lambda r: ecomap.get(canonical_text(r.get("cod_es",""))) or ecomap.get(canonical_text(r.get("ecosistema",""))), axis=1)

    df["ecosistema_obs_id"] = df.apply(lambda r: sha1_short("eco_obs", r["context_id"], r.get("cod_es",""), r.get("ecosistema","")), axis=1)
    main = df[["ecosistema_obs_id","context_id","ecosistema_id","cod_es","ecosistema","tipo","es_salud","causas_deg"]].copy()

    se_df = explode_list_column(df[["ecosistema_obs_id","servicio_ecosistemico"]], "servicio_ecosistemico", "cod_se")
    se_df["se_id"] = se_df["cod_se"].map(lambda x: semap.get(canonical_text(x), np.nan))
    se_df["eco_se_id"] = se_df.apply(lambda r: sha1_short("eco_se", r["ecosistema_obs_id"], r["se_id"], r["cod_se"]), axis=1)
    se_df = se_df[["eco_se_id","ecosistema_obs_id","se_id","cod_se"]].copy()

    mdv_df = explode_list_column(df[["ecosistema_obs_id","mdv_relacionado"]], "mdv_relacionado", "mdv_name")
    mdv_df["mdv_id"] = mdv_df["mdv_name"].map(lambda x: mdvmap.get(canonical_text(x), np.nan))
    mdv_df["eco_mdv_id"] = mdv_df.apply(lambda r: sha1_short("eco_mdv", r["ecosistema_obs_id"], r["mdv_id"], r["mdv_name"]), axis=1)
    mdv_df = mdv_df[["eco_mdv_id","ecosistema_obs_id","mdv_id","mdv_name"]].copy()

    return main, se_df, mdv_df

def tidy_3_5_se_mdv(raw, geo, ctx, eco_lk, se_lk, elemento_se_lk, mdv_lk) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    sh = "3.5. SE y MdV"
    cmap = build_context_map(geo, ctx)
    ecomap = ecosistema_id_map(eco_lk)
    semap = se_id_map(se_lk)
    elem_map = dict(zip(elemento_se_lk["elemento_se"].map(canonical_text), elemento_se_lk["elemento_se_id"]))
    mdvmap = mdv_id_map(mdv_lk)

    if sh not in raw:
        return (
            pd.DataFrame(columns=["se_mdv_id","context_id","ecosistema_id","se_id","cod_es_se","cod_es","cod_se","elemento_se_id","elemento_se",
                                  "mdv_id","mdv_name","accesso","barreras","nr_usuarios","impactos_cruzados","incl_descripcion"]),
            pd.DataFrame(columns=["se_month_id","se_mdv_id","month_label","month_num","month_type"]),
            pd.DataFrame(columns=["se_inclusion_id","se_mdv_id","group_label"]),
        )
    df = attach_context_id(raw[sh], cmap).copy()

    # parse cod_es_se => cod_es + cod_se
    def parse_cod(x):
        if x is None or (isinstance(x,float) and np.isnan(x)):
            return ("","")
        s = str(x).strip()
        if "_" in s:
            a,b = s.split("_",1)
            return (a.strip(), b.strip())
        return ("", s)
    parsed = df["cod_es_se"].apply(parse_cod)
    df["cod_es"] = [p[0] for p in parsed]
    df["cod_se"] = [p[1] for p in parsed]

    df["ecosistema_id"] = df["cod_es"].map(lambda x: ecomap.get(canonical_text(x), np.nan))
    df["se_id"] = df["cod_se"].map(lambda x: semap.get(canonical_text(x), np.nan))
    df["elemento_se_id"] = df["elemento_se"].map(lambda x: elem_map.get(canonical_text(x), np.nan))

    # explode MdV
    base = explode_list_column(df, "mdv_relacionado", "mdv_name")
    base["mdv_id"] = base["mdv_name"].map(lambda x: mdvmap.get(canonical_text(x), np.nan))

    base["nr_usuarios"] = pd.to_numeric(base["nr_usuarios"], errors="coerce")

    base["se_mdv_id"] = base.apply(lambda r: sha1_short("semdv", r["context_id"], r["cod_es_se"], r["elemento_se"], r["mdv_id"]), axis=1)
    main_cols = ["se_mdv_id","context_id","ecosistema_id","se_id","cod_es_se","cod_es","cod_se","elemento_se_id","elemento_se",
                 "mdv_id","mdv_name","accesso","barreras","nr_usuarios","impactos_cruzados","incl_descripcion"]
    for c in main_cols:
        if c not in base.columns:
            base[c] = np.nan
    main = base[main_cols].copy()

    # months bridges
    month_rows = []
    for _, r in main.merge(df[["cod_es_se","mes_contrib","mes_falta","inclusion"]], on="cod_es_se", how="left").iterrows():
        sid = r["se_mdv_id"]
        for typ, col in [("contrib","mes_contrib"), ("falta","mes_falta")]:
            for label,num in parse_month_tokens(r.get(col)):
                month_rows.append({
                    "se_month_id": sha1_short("se_month", sid, typ, label),
                    "se_mdv_id": sid,
                    "month_label": label,
                    "month_num": num,
                    "month_type": typ,
                })
    months = pd.DataFrame(month_rows) if month_rows else pd.DataFrame(columns=["se_month_id","se_mdv_id","month_label","month_num","month_type"])

    # inclusion bridge
    incl_rows = []
    for _, r in main.merge(df[["cod_es_se","inclusion"]], on="cod_es_se", how="left").iterrows():
        sid = r["se_mdv_id"]
        for g in split_list(r.get("inclusion")):
            incl_rows.append({
                "se_inclusion_id": sha1_short("se_incl", sid, g),
                "se_mdv_id": sid,
                "group_label": g
            })
    inclusion = pd.DataFrame(incl_rows) if incl_rows else pd.DataFrame(columns=["se_inclusion_id","se_mdv_id","group_label"])

    return main, months, inclusion

def tidy_4_1_amenazas(raw, geo, ctx, amen_lk) -> pd.DataFrame:
    sh = "4.1. Amenazas"
    cmap = build_context_map(geo, ctx)
    if sh not in raw:
        return pd.DataFrame(columns=["amenaza_obs_id","context_id","amenaza_id","tipo_amenaza","amenaza","magnitud","frequencia","tendencia","suma","sitios_afect","cod_mapa"])
    df = attach_context_id(raw[sh], cmap).copy()
    amen_map = dict(zip(amen_lk.apply(lambda r: canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), axis=1), amen_lk["amenaza_id"]))
    df["amenaza_id"] = df.apply(lambda r: amen_map.get(canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), np.nan), axis=1)
    for c in ["magnitud","frequencia","tendencia","suma"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["amenaza_obs_id"] = df.apply(lambda r: sha1_short("amen_obs", r["context_id"], r["amenaza_id"], r.get("cod_mapa",""), r.get("sitios_afect","")), axis=1)
    return df[["amenaza_obs_id","context_id","amenaza_id","tipo_amenaza","amenaza","magnitud","frequencia","tendencia","suma","sitios_afect","cod_mapa"]].copy()

def tidy_4_2_amenaza_mdv(raw, geo, ctx, amen_lk, mdv_lk, conf_lk) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    sh = "4.2.1. Amenazas_MdV"
    cmap = build_context_map(geo, ctx)
    mdvmap = mdv_id_map(mdv_lk)
    amen_map = dict(zip(amen_lk.apply(lambda r: canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), axis=1), amen_lk["amenaza_id"]))
    conf_map = dict(zip(conf_lk["cod_conflict"].map(canonical_text), conf_lk["conflicto_id"]))

    if sh not in raw:
        empty_main = pd.DataFrame(columns=["amenaza_mdv_id","context_id","amenaza_id","tipo_amenaza","amenaza","mdv_id","mdv_name",
                                           "i_economia","i_econ_coment","i_alimentaria","i_aliment_coment","i_sanitaria","i_sanit_coment",
                                           "i_ambiental","i_amb_coment","i_personal","i_pers_coment","i_comunitaria","i_comun_coment",
                                           "i_politica","i_polit_coment","nr_familias","tipo_conflicto","nivel_conflicto","mapeo_conflicto"])
        return empty_main, pd.DataFrame(columns=["dif_id","amenaza_mdv_id","group_label"]), pd.DataFrame(columns=["map_id","amenaza_mdv_id","cod_conflict","conflicto_id"])

    df = attach_context_id(raw[sh], cmap).copy()
    df["amenaza_id"] = df.apply(lambda r: amen_map.get(canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), np.nan), axis=1)

    base = explode_list_column(df, "mdv", "mdv_name")
    base["mdv_id"] = base["mdv_name"].map(lambda x: mdvmap.get(canonical_text(x), np.nan))

    score_cols = ["i_economia","i_alimentaria","i_sanitaria","i_ambiental","i_personal","i_comunitaria","i_politica"]
    for c in score_cols + ["nr_familias"]:
        base[c] = pd.to_numeric(base[c], errors="coerce")

    base["amenaza_mdv_id"] = base.apply(lambda r: sha1_short("am_mdv", r["context_id"], r["amenaza_id"], r["mdv_id"], r.get("tipo_conflicto",""), r.get("nivel_conflicto","")), axis=1)

    main_cols = ["amenaza_mdv_id","context_id","amenaza_id","tipo_amenaza","amenaza","mdv_id","mdv_name",
                 "i_economia","i_econ_coment","i_alimentaria","i_aliment_coment","i_sanitaria","i_sanit_coment",
                 "i_ambiental","i_amb_coment","i_personal","i_pers_coment","i_comunitaria","i_comun_coment",
                 "i_politica","i_polit_coment","nr_familias","tipo_conflicto","nivel_conflicto","mapeo_conflicto"]
    for c in main_cols:
        if c not in base.columns:
            base[c] = np.nan
    main = base[main_cols].copy()

    # i_diferenciado bridge
    dif_rows = []
    if "i_diferenciado" in base.columns:
        for _, r in base[["amenaza_mdv_id","i_diferenciado"]].iterrows():
            for g in split_list(r.get("i_diferenciado")):
                dif_rows.append({"dif_id": sha1_short("dif", r["amenaza_mdv_id"], g), "amenaza_mdv_id": r["amenaza_mdv_id"], "group_label": g})
    dif = pd.DataFrame(dif_rows) if dif_rows else pd.DataFrame(columns=["dif_id","amenaza_mdv_id","group_label"])

    # mapeo_conflicto bridge (tokens)
    map_rows = []
    if "mapeo_conflicto" in base.columns:
        for _, r in base[["amenaza_mdv_id","mapeo_conflicto"]].iterrows():
            val = r.get("mapeo_conflicto")
            if val is None or (isinstance(val,float) and np.isnan(val)):
                continue
            toks = re.split(r"[_\s,;]+", str(val).strip())
            for t in toks:
                t2 = t.strip()
                if not t2:
                    continue
                map_rows.append({
                    "map_id": sha1_short("map", r["amenaza_mdv_id"], t2),
                    "amenaza_mdv_id": r["amenaza_mdv_id"],
                    "cod_conflict": t2,
                    "conflicto_id": conf_map.get(canonical_text(t2), np.nan)
                })
    mapdf = pd.DataFrame(map_rows) if map_rows else pd.DataFrame(columns=["map_id","amenaza_mdv_id","cod_conflict","conflicto_id"])

    return main, dif, mapdf

def tidy_4_2_amenaza_se(raw, geo, ctx, amen_lk, se_lk, conf_lk) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    sh = "4.2.2. Amenazas_SE"
    cmap = build_context_map(geo, ctx)
    semap = se_id_map(se_lk)
    amen_map = dict(zip(amen_lk.apply(lambda r: canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), axis=1), amen_lk["amenaza_id"]))
    conf_map = dict(zip(conf_lk["cod_conflict"].map(canonical_text), conf_lk["conflicto_id"]))

    if sh not in raw:
        empty_main = pd.DataFrame(columns=["amenaza_se_id","context_id","amenaza_id","tipo_amenaza","amenaza","se_id","cod_se",
                                           "i_economia","i_econ_coment","i_alimentaria","i_aliment_coment","i_sanitaria","i_sanit_coment",
                                           "i_ambiental","i_amb_coment","i_personal","i_pers_coment","i_comunitaria","i_comun_coment",
                                           "i_politica","i_polit_coment","nr_familias","tipo_conflicto","nivel_conflicto","mapeo_conflicto"])
        return empty_main, pd.DataFrame(columns=["dif_id","amenaza_se_id","group_label"]), pd.DataFrame(columns=["map_id","amenaza_se_id","cod_conflict","conflicto_id"])

    df = attach_context_id(raw[sh], cmap).copy()
    df["amenaza_id"] = df.apply(lambda r: amen_map.get(canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), np.nan), axis=1)
    df["se_id"] = df["cod_se"].map(lambda x: semap.get(canonical_text(x), np.nan))

    score_cols = ["i_economia","i_alimentaria","i_sanitaria","i_ambiental","i_personal","i_comunitaria","i_politica"]
    for c in score_cols + ["nr_familias"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["amenaza_se_id"] = df.apply(lambda r: sha1_short("am_se", r["context_id"], r["amenaza_id"], r["se_id"], r.get("tipo_conflicto",""), r.get("nivel_conflicto","")), axis=1)

    main_cols = ["amenaza_se_id","context_id","amenaza_id","tipo_amenaza","amenaza","se_id","cod_se",
                 "i_economia","i_econ_coment","i_alimentaria","i_aliment_coment","i_sanitaria","i_sanit_coment",
                 "i_ambiental","i_amb_coment","i_personal","i_pers_coment","i_comunitaria","i_comun_coment",
                 "i_politica","i_polit_coment","nr_familias","tipo_conflicto","nivel_conflicto","mapeo_conflicto"]
    for c in main_cols:
        if c not in df.columns:
            df[c] = np.nan
    main = df[main_cols].copy()

    # i_diferenciado bridge
    dif_rows = []
    if "i_diferenciado" in df.columns:
        for _, r in df[["amenaza_se_id","i_diferenciado"]].iterrows():
            for g in split_list(r.get("i_diferenciado")):
                dif_rows.append({"dif_id": sha1_short("dif", r["amenaza_se_id"], g), "amenaza_se_id": r["amenaza_se_id"], "group_label": g})
    dif = pd.DataFrame(dif_rows) if dif_rows else pd.DataFrame(columns=["dif_id","amenaza_se_id","group_label"])

    # mapeo_conflicto bridge
    map_rows = []
    if "mapeo_conflicto" in df.columns:
        for _, r in df[["amenaza_se_id","mapeo_conflicto"]].iterrows():
            val = r.get("mapeo_conflicto")
            if val is None or (isinstance(val,float) and np.isnan(val)):
                continue
            toks = re.split(r"[_\s,;]+", str(val).strip())
            for t in toks:
                t2 = t.strip()
                if not t2:
                    continue
                map_rows.append({
                    "map_id": sha1_short("map", r["amenaza_se_id"], t2),
                    "amenaza_se_id": r["amenaza_se_id"],
                    "cod_conflict": t2,
                    "conflicto_id": conf_map.get(canonical_text(t2), np.nan)
                })
    mapdf = pd.DataFrame(map_rows) if map_rows else pd.DataFrame(columns=["map_id","amenaza_se_id","cod_conflict","conflicto_id"])

    return main, dif, mapdf

def tidy_5_1_actores(raw, geo, ctx, actor_lk) -> Tuple[pd.DataFrame,pd.DataFrame]:
    sh = "5.1. Actores"
    cmap = build_context_map(geo, ctx)
    amap = actor_id_map(actor_lk)

    if sh not in raw:
        return (
            pd.DataFrame(columns=["actor_obs_id","context_id","actor_id","nombre_actor","tipo_actor","rol_paisaje","poder","interes"]),
            pd.DataFrame(columns=["rel_id","context_id","actor_id","other_actor_id","other_actor_name","rel_type"]),
        )

    df = attach_context_id(raw[sh], cmap).copy()
    df["actor_id"] = df["nombre_actor"].map(lambda x: amap.get(canonical_text(x), np.nan))
    df["actor_obs_id"] = df.apply(lambda r: sha1_short("actor_obs", r["context_id"], r["actor_id"]), axis=1)

    main = df[["actor_obs_id","context_id","actor_id","nombre_actor","tipo_actor","rol_paisaje","poder","interes"]].copy()

    rel_rows = []
    for _, r in df.iterrows():
        a_id = r.get("actor_id")
        if a_id is None or (isinstance(a_id,float) and np.isnan(a_id)):
            continue
        for rel_type, col in [("conflicto","conflicto_con"), ("colabora","colabor_con")]:
            for name in split_list(r.get(col)):
                other_id = amap.get(canonical_text(name), np.nan)
                rel_rows.append({
                    "rel_id": sha1_short("rel", r.get("context_id"), a_id, other_id, rel_type),
                    "context_id": r.get("context_id"),
                    "actor_id": a_id,
                    "other_actor_id": other_id,
                    "other_actor_name": name,
                    "rel_type": rel_type
                })
    rel = pd.DataFrame(rel_rows) if rel_rows else pd.DataFrame(columns=["rel_id","context_id","actor_id","other_actor_id","other_actor_name","rel_type"])
    return main, rel

def tidy_5_2_dialogo(raw, geo, ctx, espacio_lk, actor_lk) -> Tuple[pd.DataFrame,pd.DataFrame]:
    sh = "5.2. Diálogo"
    cmap = build_context_map(geo, ctx)
    esp_map = dict(zip(espacio_lk["nombre_espacio"].map(canonical_text), espacio_lk["espacio_id"]))
    act_map = actor_id_map(actor_lk)

    if sh not in raw:
        return (
            pd.DataFrame(columns=["dialogo_id","context_id","espacio_id","nombre_espacio","tipo","alcance","funcion","incidencia","fortalezas","debilidades"]),
            pd.DataFrame(columns=["bridge_id","dialogo_id","actor_id","actor_name"]),
        )

    df = attach_context_id(raw[sh], cmap).copy()
    df["espacio_id"] = df["nombre_espacio"].map(lambda x: esp_map.get(canonical_text(x), np.nan))
    df["dialogo_id"] = df.apply(lambda r: sha1_short("dialogo", r["context_id"], r["espacio_id"], r.get("tipo",""), r.get("alcance","")), axis=1)

    main = df[["dialogo_id","context_id","espacio_id","nombre_espacio","tipo","alcance","funcion","incidencia","fortalezas","debilidades"]].copy()

    bridges = explode_list_column(df[["dialogo_id","actores_invol"]].copy(), "actores_invol", "actor_name")
    bridges["actor_id"] = bridges["actor_name"].map(lambda x: act_map.get(canonical_text(x), np.nan))
    bridges["bridge_id"] = bridges.apply(lambda r: sha1_short("dlg_act", r["dialogo_id"], r["actor_id"], r["actor_name"]), axis=1)
    bridges = bridges[["bridge_id","dialogo_id","actor_id","actor_name"]].copy()
    return main, bridges

def tidy_6_1_conflict_events(raw, geo, ctx, conf_lk) -> pd.DataFrame:
    sh = "6.1. Evolución_conflict"
    cmap = build_context_map(geo, ctx)
    conf_map = dict(zip(conf_lk["cod_conflict"].map(canonical_text), conf_lk["conflicto_id"]))

    if sh not in raw:
        return pd.DataFrame(columns=["event_id","context_id","conflicto_id","cod_conflict","evento","ano_evento","diferencias","dif_factor","cooperacion","coop_factor","suma"])

    df = attach_context_id(raw[sh], cmap).copy()
    # explode cod_conflict lists
    base = explode_list_column(df, "cod_conflict", "cod_conflict_item")
    base["conflicto_id"] = base["cod_conflict_item"].map(lambda x: conf_map.get(canonical_text(x), np.nan))

    # numeric conversions
    for c in ["ano_evento","diferencias","cooperacion","suma"]:
        base[c] = pd.to_numeric(base[c], errors="coerce")

    base["event_id"] = base.apply(lambda r: sha1_short("ev", r["context_id"], r.get("evento",""), r.get("ano_evento",""), r.get("cod_conflict_item","")), axis=1)
    out = base.rename(columns={"cod_conflict_item":"cod_conflict"})
    return out[["event_id","context_id","conflicto_id","cod_conflict","evento","ano_evento","diferencias","dif_factor","cooperacion","coop_factor","suma"]].copy()

def tidy_6_2_conflict_actor(raw, geo, ctx, conf_lk, actor_lk) -> pd.DataFrame:
    sh = "6.2. Actores_conflict"
    cmap = build_context_map(geo, ctx)
    conf_map = dict(zip(conf_lk["cod_conflict"].map(canonical_text), conf_lk["conflicto_id"]))
    act_map = actor_id_map(actor_lk)

    if sh not in raw:
        return pd.DataFrame(columns=["conflict_actor_id","context_id","conflicto_id","cod_conflict","actor_id","actor","i_en_actor","iea_factor","i_en_conflicto","iec_factor"])

    df = attach_context_id(raw[sh], cmap).copy()
    df["conflicto_id"] = df["cod_conflict"].map(lambda x: conf_map.get(canonical_text(x), np.nan))
    df["actor_id"] = df["actor"].map(lambda x: act_map.get(canonical_text(x), np.nan))
    df["conflict_actor_id"] = df.apply(lambda r: sha1_short("cact", r["context_id"], r["conflicto_id"], r["actor_id"]), axis=1)
    return df[["conflict_actor_id","context_id","conflicto_id","cod_conflict","actor_id","actor","i_en_actor","iea_factor","i_en_conflicto","iec_factor"]].copy()

def tidy_7_1_ca(raw, survey_ctx_lk, mdv_lk, ca_q_lk) -> Tuple[pd.DataFrame,pd.DataFrame]:
    sh = "7.1. Encuesta CA"
    if sh not in raw:
        return (
            pd.DataFrame(columns=["respondent_id","survey_context_id","admin0","grupo","paisaje_inferido","mdv_id","mdv_name","tamano_propiedad"]),
            pd.DataFrame(columns=["response_id","respondent_id","question_id","question_order","response_raw","response_numeric"]),
        )
    df = raw[sh].copy()
    fixed = ["País","Grupo","Medio de vida","Tamaño de propiedad"]
    qcols = [c for c in df.columns if c not in fixed]

    # maps
    mdvmap = mdv_id_map(mdv_lk)
    sc_map = dict(zip(
        survey_ctx_lk.apply(lambda r: canonical_text(r["admin0"])+"|"+canonical_text(r["grupo"]), axis=1),
        survey_ctx_lk["survey_context_id"]
    ))
    paisaje_map = dict(zip(
        survey_ctx_lk["survey_context_id"], survey_ctx_lk["paisaje_inferido"]
    ))
    qmap = dict(zip(ca_q_lk["column_name"], ca_q_lk["question_id"]))
    qorder = dict(zip(ca_q_lk["question_id"], ca_q_lk["question_order"]))

    # respondents
    df["admin0"] = df["País"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    df["grupo"]  = df["Grupo"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    df["survey_context_id"] = df.apply(lambda r: sc_map.get(canonical_text(r["admin0"])+"|"+canonical_text(r["grupo"]), np.nan), axis=1)
    df["paisaje_inferido"] = df["survey_context_id"].map(lambda x: paisaje_map.get(x, ""))

    df["mdv_name"] = df["Medio de vida"].apply(lambda x: "" if x is None or (isinstance(x,float) and np.isnan(x)) else str(x).strip())
    df["mdv_id"] = df["mdv_name"].map(lambda x: mdvmap.get(canonical_text(x), np.nan))
    df["tamano_propiedad"] = df["Tamaño de propiedad"]
    df["respondent_id"] = df.apply(lambda r: sha1_short("resp", r["survey_context_id"], r["mdv_id"], r["mdv_name"], r.get("tamano_propiedad","")), axis=1)

    respondents = df[["respondent_id","survey_context_id","admin0","grupo","paisaje_inferido","mdv_id","mdv_name","tamano_propiedad"]].copy()

    # responses long
    rows = []
    for idx, r in df.iterrows():
        rid = r["respondent_id"]
        for c in qcols:
            qid = qmap.get(str(c).strip())
            if not qid:
                continue
            val = r.get(c)
            rawv = "" if val is None or (isinstance(val,float) and np.isnan(val)) else str(val).strip()
            numv = pd.to_numeric(rawv, errors="coerce")
            rows.append({
                "response_id": sha1_short("respq", rid, qid),
                "respondent_id": rid,
                "question_id": qid,
                "question_order": qorder.get(qid, np.nan),
                "response_raw": rawv,
                "response_numeric": numv if numv==numv else np.nan,
            })
    responses = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["response_id","respondent_id","question_id","question_order","response_raw","response_numeric"])
    return respondents, responses


# ---------------------------
# QA
# ---------------------------

def qa_table_summary(tables: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame([{"table":k,"rows":int(v.shape[0]),"cols":int(v.shape[1])} for k,v in tables.items()]).sort_values("table")

def qa_pk_duplicates(tables: Dict[str,pd.DataFrame], pk_map: Dict[str,List[str]]) -> pd.DataFrame:
    rows = []
    for t, pk in pk_map.items():
        if t not in tables:
            continue
        df = tables[t]
        if any(c not in df.columns for c in pk):
            rows.append({"table":t,"pk":",".join(pk),"duplicate_rows":np.nan,"note":"missing_pk_columns"})
            continue
        rows.append({"table":t,"pk":",".join(pk),"duplicate_rows":int(df.duplicated(pk, keep=False).sum()),"note":""})
    return pd.DataFrame(rows).sort_values("table")

def qa_missing_ids(tables: Dict[str,pd.DataFrame], id_cols: Dict[str,List[str]]) -> pd.DataFrame:
    rows = []
    for t, cols in id_cols.items():
        if t not in tables:
            continue
        df = tables[t]
        for c in cols:
            if c not in df.columns:
                rows.append({"table":t,"col":c,"missing":np.nan,"note":"col_missing"})
                continue
            miss = int(df[c].isna().sum() + (df[c].astype(str).str.strip()=="").sum())
            rows.append({"table":t,"col":c,"missing":miss,"note":""})
    return pd.DataFrame(rows).sort_values(["table","col"])

def qa_fk(tables: Dict[str,pd.DataFrame], specs: List[Tuple[str,str,str,str]]) -> pd.DataFrame:
    out = []
    for tbl,fk,lk,lkpk in specs:
        if tbl not in tables or lk not in tables:
            continue
        df, lkdf = tables[tbl], tables[lk]
        if fk not in df.columns or lkpk not in lkdf.columns:
            out.append({"table":tbl,"fk":fk,"lookup":lk,"missing_fk":np.nan,"note":"missing_columns"})
            continue
        valid = set(lkdf[lkpk].dropna().astype(str))
        vals = df[fk].dropna().astype(str)
        out.append({"table":tbl,"fk":fk,"lookup":lk,"missing_fk":int((~vals.isin(valid)).sum()),"note":""})
    return pd.DataFrame(out).sort_values(["table","fk"])


# ---------------------------
# COMPILER
# ---------------------------

def compile_workbook(input_path: str, strict: bool=True, copy_raw: bool=True) -> Dict[str,pd.DataFrame]:
    raw = read_workbook(input_path)
    qa_schema = validate_input(raw, strict=strict)

    # lookups
    geo, ctx = build_lookup_geo_context(raw)
    survey_ctx = build_lookup_survey_context(raw)
    mdv = build_lookup_mdv(raw)
    eco = build_lookup_ecosistema(raw)
    se  = build_lookup_se(raw)
    elemento_se = build_lookup_elemento_se(raw)
    amen = build_lookup_amenaza(raw)
    actor = build_lookup_actor(raw)
    espacio = build_lookup_espacio(raw)
    conflicto = build_lookup_conflicto(raw)
    ca_q = build_lookup_ca_questions(raw)

    # tidy
    t31 = tidy_3_1_brainstorm(raw, geo, ctx, mdv, eco)
    t32 = tidy_3_2_priorizacion(raw, geo, ctx, mdv)
    tA, tB, tC, tD, tL = tidy_3_3_car(raw, geo, ctx, mdv)
    t34_main, t34_se, t34_mdv = tidy_3_4_ecosistemas(raw, geo, ctx, eco, se, mdv)
    t35_main, t35_months, t35_incl = tidy_3_5_se_mdv(raw, geo, ctx, eco, se, elemento_se, mdv)
    t41 = tidy_4_1_amenazas(raw, geo, ctx, amen)
    t421_main, t421_dif, t421_map = tidy_4_2_amenaza_mdv(raw, geo, ctx, amen, mdv, conflicto)
    t422_main, t422_dif, t422_map = tidy_4_2_amenaza_se(raw, geo, ctx, amen, se, conflicto)
    t51_main, t51_rel = tidy_5_1_actores(raw, geo, ctx, actor)
    t52_main, t52_bridge = tidy_5_2_dialogo(raw, geo, ctx, espacio, actor)
    t61 = tidy_6_1_conflict_events(raw, geo, ctx, conflicto)
    t62 = tidy_6_2_conflict_actor(raw, geo, ctx, conflicto, actor)
    t71_resp, t71_ans = tidy_7_1_ca(raw, survey_ctx, mdv, ca_q)

    tables: Dict[str,pd.DataFrame] = {}

    if copy_raw:
        for sh, df in raw.items():
            tables[sh] = df

    # LOOKUPS
    tables["LOOKUP_GEO"] = geo
    tables["LOOKUP_CONTEXT"] = ctx
    tables["LOOKUP_SURVEY_CONTEXT"] = survey_ctx
    tables["LOOKUP_MDV"] = mdv
    tables["LOOKUP_ECOSISTEMA"] = eco
    tables["LOOKUP_SE"] = se
    tables["LOOKUP_ELEMENTO_SE"] = elemento_se
    tables["LOOKUP_AMENAZA"] = amen
    tables["LOOKUP_ACTOR"] = actor
    tables["LOOKUP_ESPACIO"] = espacio
    tables["LOOKUP_CONFLICTO"] = conflicto
    tables["LOOKUP_CA_QUESTIONS"] = ca_q

    # TIDY
    tables["TIDY_3_1_BRAINSTORM"] = t31
    tables["TIDY_3_2_PRIORIZACION"] = t32
    tables["TIDY_3_3_CAR_A"] = tA
    tables["TIDY_3_3_CAR_B"] = tB
    tables["TIDY_3_3_CAR_C"] = tC
    tables["TIDY_3_3_CAR_D"] = tD
    tables["TIDY_3_3_CAR_LONG"] = tL
    tables["TIDY_3_4_ECOSISTEMAS"] = t34_main
    tables["TIDY_3_4_ECO_SE"] = t34_se
    tables["TIDY_3_4_ECO_MDV"] = t34_mdv
    tables["TIDY_3_5_SE_MDV"] = t35_main
    tables["TIDY_3_5_SE_MONTHS"] = t35_months
    tables["TIDY_3_5_SE_INCLUSION"] = t35_incl
    tables["TIDY_4_1_AMENAZAS"] = t41
    tables["TIDY_4_2_1_AMENAZA_MDV"] = t421_main
    tables["TIDY_4_2_1_DIFERENCIADO"] = t421_dif
    tables["TIDY_4_2_1_MAPEO_CONFLICTO"] = t421_map
    tables["TIDY_4_2_2_AMENAZA_SE"] = t422_main
    tables["TIDY_4_2_2_DIFERENCIADO"] = t422_dif
    tables["TIDY_4_2_2_MAPEO_CONFLICTO"] = t422_map
    tables["TIDY_5_1_ACTORES"] = t51_main
    tables["TIDY_5_1_RELACIONES"] = t51_rel
    tables["TIDY_5_2_DIALOGO"] = t52_main
    tables["TIDY_5_2_DIALOGO_ACTOR"] = t52_bridge
    tables["TIDY_6_1_CONFLICT_EVENTS"] = t61
    tables["TIDY_6_2_CONFLICTO_ACTOR"] = t62
    tables["TIDY_7_1_RESPONDENTS"] = t71_resp
    tables["TIDY_7_1_RESPONSES"] = t71_ans

    # QA config
    pk_map = {
        "LOOKUP_GEO": ["geo_id"],
        "LOOKUP_CONTEXT": ["context_id"],
        "LOOKUP_SURVEY_CONTEXT": ["survey_context_id"],
        "LOOKUP_MDV": ["mdv_id"],
        "LOOKUP_ECOSISTEMA": ["ecosistema_id"],
        "LOOKUP_SE": ["se_id"],
        "LOOKUP_ELEMENTO_SE": ["elemento_se_id"],
        "LOOKUP_AMENAZA": ["amenaza_id"],
        "LOOKUP_ACTOR": ["actor_id"],
        "LOOKUP_ESPACIO": ["espacio_id"],
        "LOOKUP_CONFLICTO": ["conflicto_id"],
        "LOOKUP_CA_QUESTIONS": ["question_id"],

        "TIDY_3_1_BRAINSTORM": ["brainstorm_id"],
        "TIDY_3_2_PRIORIZACION": ["priorizacion_id"],
        "TIDY_3_3_CAR_A": ["car_a_id"],
        "TIDY_3_3_CAR_B": ["car_b_id"],
        "TIDY_3_3_CAR_C": ["car_c_id"],
        "TIDY_3_3_CAR_D": ["car_d_id"],
        "TIDY_3_3_CAR_LONG": ["car_long_id"],
        "TIDY_3_4_ECOSISTEMAS": ["ecosistema_obs_id"],
        "TIDY_3_4_ECO_SE": ["eco_se_id"],
        "TIDY_3_4_ECO_MDV": ["eco_mdv_id"],
        "TIDY_3_5_SE_MDV": ["se_mdv_id"],
        "TIDY_3_5_SE_MONTHS": ["se_month_id"],
        "TIDY_3_5_SE_INCLUSION": ["se_inclusion_id"],
        "TIDY_4_1_AMENAZAS": ["amenaza_obs_id"],
        "TIDY_4_2_1_AMENAZA_MDV": ["amenaza_mdv_id"],
        "TIDY_4_2_1_DIFERENCIADO": ["dif_id"],
        "TIDY_4_2_1_MAPEO_CONFLICTO": ["map_id"],
        "TIDY_4_2_2_AMENAZA_SE": ["amenaza_se_id"],
        "TIDY_4_2_2_DIFERENCIADO": ["dif_id"],
        "TIDY_4_2_2_MAPEO_CONFLICTO": ["map_id"],
        "TIDY_5_1_ACTORES": ["actor_obs_id"],
        "TIDY_5_1_RELACIONES": ["rel_id"],
        "TIDY_5_2_DIALOGO": ["dialogo_id"],
        "TIDY_5_2_DIALOGO_ACTOR": ["bridge_id"],
        "TIDY_6_1_CONFLICT_EVENTS": ["event_id"],
        "TIDY_6_2_CONFLICTO_ACTOR": ["conflict_actor_id"],
        "TIDY_7_1_RESPONDENTS": ["respondent_id"],
        "TIDY_7_1_RESPONSES": ["response_id"],
    }

    id_cols = {
        "TIDY_3_1_BRAINSTORM": ["context_id"],
        "TIDY_3_2_PRIORIZACION": ["context_id","mdv_id"],
        "TIDY_3_3_CAR_A": ["context_id","mdv_id"],
        "TIDY_3_3_CAR_B": ["context_id","mdv_id"],
        "TIDY_3_3_CAR_C": ["context_id","mdv_id"],
        "TIDY_3_3_CAR_D": ["context_id","mdv_id"],
        "TIDY_3_4_ECOSISTEMAS": ["context_id","ecosistema_id"],
        "TIDY_3_4_ECO_SE": ["ecosistema_obs_id","se_id"],
        "TIDY_3_4_ECO_MDV": ["ecosistema_obs_id","mdv_id"],
        "TIDY_3_5_SE_MDV": ["context_id","ecosistema_id","se_id","elemento_se_id","mdv_id"],
        "TIDY_4_1_AMENAZAS": ["context_id","amenaza_id"],
        "TIDY_4_2_1_AMENAZA_MDV": ["context_id","amenaza_id","mdv_id"],
        "TIDY_4_2_2_AMENAZA_SE": ["context_id","amenaza_id","se_id"],
        "TIDY_5_1_ACTORES": ["context_id","actor_id"],
        "TIDY_5_2_DIALOGO": ["context_id","espacio_id"],
        "TIDY_5_2_DIALOGO_ACTOR": ["dialogo_id","actor_id"],
        "TIDY_6_1_CONFLICT_EVENTS": ["context_id","conflicto_id"],
        "TIDY_6_2_CONFLICTO_ACTOR": ["context_id","conflicto_id","actor_id"],
        "TIDY_7_1_RESPONDENTS": ["survey_context_id","mdv_id"],
        "TIDY_7_1_RESPONSES": ["respondent_id","question_id"],
    }

    fk_specs = [
        ("LOOKUP_CONTEXT","geo_id","LOOKUP_GEO","geo_id"),

        ("TIDY_3_1_BRAINSTORM","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_1_BRAINSTORM","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_3_1_BRAINSTORM","ecosistema_id","LOOKUP_ECOSISTEMA","ecosistema_id"),

        ("TIDY_3_2_PRIORIZACION","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_2_PRIORIZACION","mdv_id","LOOKUP_MDV","mdv_id"),

        ("TIDY_3_3_CAR_A","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_3_CAR_A","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_3_3_CAR_B","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_3_CAR_B","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_3_3_CAR_C","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_3_CAR_C","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_3_3_CAR_D","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_3_CAR_D","mdv_id","LOOKUP_MDV","mdv_id"),

        ("TIDY_3_4_ECOSISTEMAS","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_4_ECOSISTEMAS","ecosistema_id","LOOKUP_ECOSISTEMA","ecosistema_id"),
        ("TIDY_3_4_ECO_SE","se_id","LOOKUP_SE","se_id"),
        ("TIDY_3_4_ECO_MDV","mdv_id","LOOKUP_MDV","mdv_id"),

        ("TIDY_3_5_SE_MDV","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_5_SE_MDV","ecosistema_id","LOOKUP_ECOSISTEMA","ecosistema_id"),
        ("TIDY_3_5_SE_MDV","se_id","LOOKUP_SE","se_id"),
        ("TIDY_3_5_SE_MDV","elemento_se_id","LOOKUP_ELEMENTO_SE","elemento_se_id"),
        ("TIDY_3_5_SE_MDV","mdv_id","LOOKUP_MDV","mdv_id"),

        ("TIDY_4_1_AMENAZAS","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_4_1_AMENAZAS","amenaza_id","LOOKUP_AMENAZA","amenaza_id"),

        ("TIDY_4_2_1_AMENAZA_MDV","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_4_2_1_AMENAZA_MDV","amenaza_id","LOOKUP_AMENAZA","amenaza_id"),
        ("TIDY_4_2_1_AMENAZA_MDV","mdv_id","LOOKUP_MDV","mdv_id"),

        ("TIDY_4_2_2_AMENAZA_SE","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_4_2_2_AMENAZA_SE","amenaza_id","LOOKUP_AMENAZA","amenaza_id"),
        ("TIDY_4_2_2_AMENAZA_SE","se_id","LOOKUP_SE","se_id"),

        ("TIDY_5_1_ACTORES","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_5_1_ACTORES","actor_id","LOOKUP_ACTOR","actor_id"),
        ("TIDY_5_1_RELACIONES","actor_id","LOOKUP_ACTOR","actor_id"),

        ("TIDY_5_2_DIALOGO","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_5_2_DIALOGO","espacio_id","LOOKUP_ESPACIO","espacio_id"),
        ("TIDY_5_2_DIALOGO_ACTOR","actor_id","LOOKUP_ACTOR","actor_id"),

        ("TIDY_6_1_CONFLICT_EVENTS","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_6_1_CONFLICT_EVENTS","conflicto_id","LOOKUP_CONFLICTO","conflicto_id"),

        ("TIDY_6_2_CONFLICTO_ACTOR","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_6_2_CONFLICTO_ACTOR","conflicto_id","LOOKUP_CONFLICTO","conflicto_id"),
        ("TIDY_6_2_CONFLICTO_ACTOR","actor_id","LOOKUP_ACTOR","actor_id"),

        ("TIDY_7_1_RESPONDENTS","survey_context_id","LOOKUP_SURVEY_CONTEXT","survey_context_id"),
        ("TIDY_7_1_RESPONDENTS","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_7_1_RESPONSES","respondent_id","TIDY_7_1_RESPONDENTS","respondent_id"),
        ("TIDY_7_1_RESPONSES","question_id","LOOKUP_CA_QUESTIONS","question_id"),
    ]

    # QA sheets
    tables["QA_INPUT_SCHEMA"] = qa_schema
    tables["QA_TABLE_SUMMARY"] = qa_table_summary(tables)
    tables["QA_PK_DUPLICATES"] = qa_pk_duplicates(tables, pk_map)
    tables["QA_MISSING_IDS"] = qa_missing_ids(tables, id_cols)
    tables["QA_FOREIGN_KEYS"] = qa_fk(tables, fk_specs)

    return tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--no-strict", action="store_true")
    ap.add_argument("--no-raw", action="store_true", help="Do not copy RAW sheets to output")
    args = ap.parse_args()

    tables = compile_workbook(args.input, strict=not args.no_strict, copy_raw=not args.no_raw)
    write_workbook(args.output, tables)
    print(f"Wrote analysis-ready workbook: {args.output}")

if __name__ == "__main__":
    main()
