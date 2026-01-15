#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZA TIERRA VIVA — Modular Excel Compiler (single-file)
- Tailored to the exact sheet/column names in database_general_ZA_TIERRA_VIVA.xlsx
- Deterministic IDs (sha1 over canonicalized strings)
- List explosion (comma / semicolon / newline)
- QA sheets (schema, PK duplicates, missing IDs, FK checks)
"""

from __future__ import annotations
import argparse
import hashlib
import re
import unicodedata
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


# ============================================================
# 0) CONFIG — exact sheet names + minimal required columns
# ============================================================

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
    "3.1. Lluvia MdV&SE": ["fecha","admin0","paisaje","grupo","elemento_SES","nombre","uso_fin_mdv"],
    "3.2. Priorización": ["fecha","admin0","paisaje","grupo","mdv ","rank","pre_se","pre_mdv"],

    "3.3. Car_A": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","sistema","uso_final","tamaño","cv_producto","cv_importancia_text"],
    "3.3. Car_B": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","elem_mdv","cv_elem_mdv","descripcion_elem_mdv"],
    "3.3. Car_C": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","elem_se","cv_elem_se","descripcion_elem_se"],
    "3.3. Car_D": ["fecha","admin0","paisaje","grupo","mdv","codigo_mdv","codigo_mapa","tenencia","cv_proposicion_text","tenencia_text"],

    "3.4. Ecosistemas": ["fecha","admin0","paisaje","grupo","ecosistema","tipo","es_salud","servicio_ecosistemico","mdv_relacionado","causas_deg","cod_es"],
    "3.5. SE y MdV": ["fecha","admin0","paisaje","grupo","cod_es_se","elemento_se","mdv_relacionado","accesso","barreras","nr_usuarios","mes_contrib","mes_falta","inclusion","impactos_cruzados"],

    "4.1. Amenazas": ["fecha","admin0","paisaje","grupo","tipo_amenaza","amenaza","sitios_afect","cod_mapa"],
    "4.2.1. Amenazas_MdV": ["fecha","admin0","paisaje","grupo","tipo_amenaza","amenaza","mdv","codigo_mdv","cod_mapa","nr_familias",
                            "i_economia","i_sociedad","i_salud","i_educacion","i_ambiental","i_politico","i_conflictos","i_migracion",
                            "impactos","soluciones","maladapt","nr_familias_text"],
    "4.2.2. Amenazas_SE": ["fecha","admin0","paisaje","grupo","tipo_amenaza","amenaza","cod_se","nr_usuarios",
                           "i_economia","i_sociedad","i_salud","i_educacion","i_ambiental","i_politico","i_conflictos","i_migracion",
                           "impactos","soluciones","maladapt","nr_usuarios_text"],

    "5.1. Actores": ["fecha","admin0","paisaje","grupo","nombre_actor","tipo_actor","colabor_con","conflicto_con"],
    "5.2. Diálogo": ["fecha","admin0","paisaje","grupo","nombre_espacio","tipo","alcance","actores_invol"],

    "6.1. Evolución_conflict": ["fecha","admin0","paisaje","grupo","cod_conflict","descripcion","tipo_conflicto","nivel_conflicto","incidencia"],
    "6.2. Actores_conflict": ["fecha","admin0","paisaje","grupo","cod_conflict","actor","i_en_actor","iea_factor","i_en_conflicto","iec_factor"],

    "7.1. Encuesta CA": ["País","Grupo","Medio de vida","Tamaño de propiedad"],
}


# ============================================================
# 1) UTILITIES — deterministic IDs, text canon, list explosion
# ============================================================

def canonical_text(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
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
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return []
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


# ============================================================
# 2) IO — read + write workbook
# ============================================================

def read_workbook(path: str) -> Dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path, engine="openpyxl")
    raw = {}
    for sh in SHEETS:
        if sh in xls.sheet_names:
            raw[sh] = pd.read_excel(xls, sh, dtype=object)
    return raw

def write_workbook(path: str, tables: Dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in tables.items():
            sheet_name = name if len(name) <= 31 else (name[:27] + "...")
            df.to_excel(writer, sheet_name=sheet_name, index=False)


# ============================================================
# 3) VALIDATION — schema QA
# ============================================================

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
        raise ValueError("Input validation failed:\n" + bad.to_string(index=False))
    return out


# ============================================================
# 4) LOOKUPS — GEO, CONTEXT, MDV, SE, AMENAZA, ACTOR, etc.
# ============================================================

def build_lookup_geo_context(raw: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for sh, df in raw.items():
        if all(c in df.columns for c in ["fecha","admin0","paisaje","grupo"]):
            tmp = df[["fecha","admin0","paisaje","grupo"]].copy()
            tmp["fecha_iso"] = tmp["fecha"].apply(coerce_date_iso)
            frames.append(tmp[["fecha_iso","admin0","paisaje","grupo"]])
    if not frames:
        return (
            pd.DataFrame(columns=["geo_id","admin0","paisaje","grupo"]),
            pd.DataFrame(columns=["context_id","geo_id","fecha_iso"]),
        )
    ctx = pd.concat(frames, ignore_index=True).drop_duplicates()
    ctx["geo_id"] = ctx.apply(lambda r: sha1_short(r["admin0"], r["paisaje"], r["grupo"]), axis=1)
    lookup_geo = ctx[["geo_id","admin0","paisaje","grupo"]].drop_duplicates().reset_index(drop=True)
    ctx["context_id"] = ctx.apply(lambda r: sha1_short(r["geo_id"], r["fecha_iso"]), axis=1)
    lookup_context = ctx[["context_id","geo_id","fecha_iso"]].drop_duplicates().reset_index(drop=True)
    return lookup_geo, lookup_context

def context_map(lookup_geo: pd.DataFrame, lookup_context: pd.DataFrame) -> Dict[Tuple[str,str,str,str], str]:
    tmp = lookup_context.merge(lookup_geo, on="geo_id", how="left")
    tmp["_k"] = tmp.apply(lambda r: (
        canonical_text(r["admin0"]),
        canonical_text(r["paisaje"]),
        canonical_text(r["grupo"]),
        str(r["fecha_iso"])
    ), axis=1)
    return dict(zip(tmp["_k"], tmp["context_id"]))

def build_lookup_mdv(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    if "3.2. Priorización" in raw and "mdv " in raw["3.2. Priorización"].columns:
        rows.extend(raw["3.2. Priorización"]["mdv "].dropna().astype(str).tolist())
    for sh in ["3.3. Car_A","3.3. Car_B","3.3. Car_C","3.3. Car_D"]:
        if sh in raw and "mdv" in raw[sh].columns:
            rows.extend(raw[sh]["mdv"].dropna().astype(str).tolist())
    for sh in ["3.4. Ecosistemas","3.5. SE y MdV","4.2.1. Amenazas_MdV"]:
        if sh in raw and "mdv_relacionado" in raw[sh].columns:
            for v in raw[sh]["mdv_relacionado"].tolist():
                rows.extend(split_list(v))
        if sh in raw and "mdv" in raw[sh].columns:
            for v in raw[sh]["mdv"].tolist():
                rows.extend(split_list(v))
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
    out["mdv_id"] = out["mdv_name"].apply(lambda x: sha1_short(x))
    return out[["mdv_id","mdv_name"]].reset_index(drop=True)

def build_lookup_se(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    codes = []
    if "3.4. Ecosistemas" in raw and "servicio_ecosistemico" in raw["3.4. Ecosistemas"].columns:
        for v in raw["3.4. Ecosistemas"]["servicio_ecosistemico"].tolist():
            codes.extend(split_list(v))
    if "3.5. SE y MdV" in raw and "cod_es_se" in raw["3.5. SE y MdV"].columns:
        for v in raw["3.5. SE y MdV"]["cod_es_se"].tolist():
            if v is None or (isinstance(v,float) and np.isnan(v)): 
                continue
            s = str(v).strip()
            if "_" in s:
                _, cod = s.split("_", 1)
                codes.append(cod.strip())
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
    out["se_id"] = out["cod_se"].apply(lambda x: sha1_short(x))
    return out[["se_id","cod_se"]].reset_index(drop=True)

def build_lookup_amenaza(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for sh in ["4.1. Amenazas","4.2.1. Amenazas_MdV","4.2.2. Amenazas_SE"]:
        if sh in raw and all(c in raw[sh].columns for c in ["tipo_amenaza","amenaza"]):
            frames.append(raw[sh][["tipo_amenaza","amenaza"]].dropna().drop_duplicates())
    if not frames:
        return pd.DataFrame(columns=["amenaza_id","tipo_amenaza","amenaza"])
    out = pd.concat(frames, ignore_index=True).drop_duplicates()
    out["amenaza_id"] = out.apply(lambda r: sha1_short(r["tipo_amenaza"], r["amenaza"]), axis=1)
    return out[["amenaza_id","tipo_amenaza","amenaza"]].reset_index(drop=True)

def build_lookup_actor(raw: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    if "5.1. Actores" in raw:
        df = raw["5.1. Actores"]
        if "nombre_actor" in df.columns:
            for v in df["nombre_actor"].dropna().astype(str).tolist():
                rows.append(v.strip())
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
    out["actor_id"] = out["nombre_actor"].apply(lambda x: sha1_short(x))
    return out[["actor_id","nombre_actor"]].reset_index(drop=True)


# ============================================================
# 5) TIDY — core transformations (including list explosions)
# ============================================================

def tidy_3_2_priorizacion(raw, geo, ctx, mdv) -> pd.DataFrame:
    sh = "3.2. Priorización"
    if sh not in raw:
        return pd.DataFrame(columns=["priorizacion_id","context_id","mdv_id","mdv_name","rank","pre_se","pre_mdv"])
    df = raw[sh].copy().rename(columns={"mdv ":"mdv_name"})
    df["fecha_iso"] = df["fecha"].apply(coerce_date_iso)
    cmap = context_map(geo, ctx)
    df["context_id"] = df.apply(lambda r: cmap.get((canonical_text(r["admin0"]),canonical_text(r["paisaje"]),canonical_text(r["grupo"]),str(r["fecha_iso"])), np.nan), axis=1)

    mdv_map = dict(zip(mdv["mdv_name"].map(canonical_text), mdv["mdv_id"]))
    df["mdv_id"] = df["mdv_name"].map(lambda x: mdv_map.get(canonical_text(x), np.nan))

    for c in ["rank","pre_se","pre_mdv"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["priorizacion_id"] = df.apply(lambda r: sha1_short(r["context_id"], r["mdv_id"]), axis=1)
    return df[["priorizacion_id","context_id","mdv_id","mdv_name","rank","pre_se","pre_mdv"]]

def tidy_3_4_ecosistemas(raw, geo, ctx, se, mdv) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    sh = "3.4. Ecosistemas"
    if sh not in raw:
        return (
            pd.DataFrame(columns=["ecosistema_obs_id","context_id","ecosistema","cod_es","tipo","es_salud","causas_deg"]),
            pd.DataFrame(columns=["ecosistema_obs_id","se_id","cod_se"]),
            pd.DataFrame(columns=["ecosistema_obs_id","mdv_id","mdv_name"]),
        )
    df = raw[sh].copy()
    df["fecha_iso"] = df["fecha"].apply(coerce_date_iso)
    cmap = context_map(geo, ctx)
    df["context_id"] = df.apply(lambda r: cmap.get((canonical_text(r["admin0"]),canonical_text(r["paisaje"]),canonical_text(r["grupo"]),str(r["fecha_iso"])), np.nan), axis=1)

    df["ecosistema_obs_id"] = df.apply(lambda r: sha1_short(r["context_id"], r["cod_es"], r["ecosistema"]), axis=1)
    main = df[["ecosistema_obs_id","context_id","ecosistema","cod_es","tipo","es_salud","causas_deg"]].copy()

    se_map = dict(zip(se["cod_se"].map(canonical_text), se["se_id"]))
    se_df = explode_list_column(df[["ecosistema_obs_id","servicio_ecosistemico"]], "servicio_ecosistemico", "cod_se")
    se_df["se_id"] = se_df["cod_se"].map(lambda x: se_map.get(canonical_text(x), np.nan))
    se_df = se_df[["ecosistema_obs_id","se_id","cod_se"]]

    mdv_map = dict(zip(mdv["mdv_name"].map(canonical_text), mdv["mdv_id"]))
    mdv_df = explode_list_column(df[["ecosistema_obs_id","mdv_relacionado"]], "mdv_relacionado", "mdv_name")
    mdv_df["mdv_id"] = mdv_df["mdv_name"].map(lambda x: mdv_map.get(canonical_text(x), np.nan))
    mdv_df = mdv_df[["ecosistema_obs_id","mdv_id","mdv_name"]]

    return main, se_df, mdv_df

def tidy_4_2_1_amenaza_mdv(raw, geo, ctx, amen, mdv) -> pd.DataFrame:
    sh = "4.2.1. Amenazas_MdV"
    if sh not in raw:
        return pd.DataFrame()
    df = raw[sh].copy()
    df["fecha_iso"] = df["fecha"].apply(coerce_date_iso)
    cmap = context_map(geo, ctx)
    df["context_id"] = df.apply(lambda r: cmap.get((canonical_text(r["admin0"]),canonical_text(r["paisaje"]),canonical_text(r["grupo"]),str(r["fecha_iso"])), np.nan), axis=1)

    amen_map = dict(zip(amen.apply(lambda r: canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), axis=1), amen["amenaza_id"]))
    df["amenaza_id"] = df.apply(lambda r: amen_map.get(canonical_text(r["tipo_amenaza"])+"|"+canonical_text(r["amenaza"]), np.nan), axis=1)

    base = explode_list_column(df, "mdv", "mdv_name")
    mdv_map = dict(zip(mdv["mdv_name"].map(canonical_text), mdv["mdv_id"]))
    base["mdv_id"] = base["mdv_name"].map(lambda x: mdv_map.get(canonical_text(x), np.nan))

    impacts = ["i_economia","i_sociedad","i_salud","i_educacion","i_ambiental","i_politico","i_conflictos","i_migracion"]
    for c in impacts:
        if c in base.columns:
            base[c] = pd.to_numeric(base[c], errors="coerce")

    base["amenaza_mdv_id"] = base.apply(lambda r: sha1_short(r["context_id"], r["amenaza_id"], r["mdv_id"]), axis=1)
    keep = ["amenaza_mdv_id","context_id","amenaza_id","tipo_amenaza","amenaza","mdv_id","mdv_name","nr_familias","nr_familias_text"] + impacts + ["impactos","soluciones","maladapt"]
    for c in keep:
        if c not in base.columns:
            base[c] = np.nan
    return base[keep]

def tidy_5_1_actores(raw, geo, ctx, actor_lk) -> Tuple[pd.DataFrame,pd.DataFrame]:
    sh = "5.1. Actores"
    if sh not in raw:
        return pd.DataFrame(), pd.DataFrame()
    df = raw[sh].copy()
    df["fecha_iso"] = df["fecha"].apply(coerce_date_iso)
    cmap = context_map(geo, ctx)
    df["context_id"] = df.apply(lambda r: cmap.get((canonical_text(r["admin0"]),canonical_text(r["paisaje"]),canonical_text(r["grupo"]),str(r["fecha_iso"])), np.nan), axis=1)

    actor_map = dict(zip(actor_lk["nombre_actor"].map(canonical_text), actor_lk["actor_id"]))
    df["actor_id"] = df["nombre_actor"].map(lambda x: actor_map.get(canonical_text(x), np.nan))
    df["actor_obs_id"] = df.apply(lambda r: sha1_short(r["context_id"], r["actor_id"]), axis=1)

    main = df[["actor_obs_id","context_id","actor_id","nombre_actor","tipo_actor"]].copy()

    rel_rows = []
    for _, r in df.iterrows():
        a_id = r.get("actor_id")
        if pd.isna(a_id):
            continue
        for rel_type, col in [("colabora","colabor_con"), ("conflicto","conflicto_con")]:
            if col not in df.columns:
                continue
            for name in split_list(r.get(col)):
                other_id = actor_map.get(canonical_text(name), np.nan)
                rel_rows.append({
                    "rel_id": sha1_short(a_id, other_id, rel_type),
                    "context_id": r.get("context_id"),
                    "actor_id": a_id,
                    "other_actor_id": other_id,
                    "other_actor_name": name,
                    "rel_type": rel_type
                })
    rel = pd.DataFrame(rel_rows) if rel_rows else pd.DataFrame(columns=["rel_id","context_id","actor_id","other_actor_id","other_actor_name","rel_type"])
    return main, rel


# ============================================================
# 6) QA — duplicates, missing IDs, FK checks
# ============================================================

def qa_table_summary(tables: Dict[str,pd.DataFrame]) -> pd.DataFrame:
    return pd.DataFrame([{"table":k,"rows":v.shape[0],"cols":v.shape[1]} for k,v in tables.items()]).sort_values("table")

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


# ============================================================
# 7) COMPILER — orchestrate everything
# ============================================================

def compile_workbook(input_path: str, strict: bool=True) -> Dict[str,pd.DataFrame]:
    raw = read_workbook(input_path)
    qa_schema = validate_input(raw, strict=strict)

    geo, ctx = build_lookup_geo_context(raw)
    mdv = build_lookup_mdv(raw)
    se  = build_lookup_se(raw)
    amen = build_lookup_amenaza(raw)
    actors = build_lookup_actor(raw)

    # TIDY examples (extend similarly for remaining sheets if needed)
    t32 = tidy_3_2_priorizacion(raw, geo, ctx, mdv)
    t34_main, t34_se, t34_mdv = tidy_3_4_ecosistemas(raw, geo, ctx, se, mdv)
    t421 = tidy_4_2_1_amenaza_mdv(raw, geo, ctx, amen, mdv)
    t51_main, t51_rel = tidy_5_1_actores(raw, geo, ctx, actors)

    tables: Dict[str,pd.DataFrame] = {}

    # keep RAW (values)
    for sh, df in raw.items():
        tables[sh] = df

    # lookups
    tables["LOOKUP_GEO"] = geo
    tables["LOOKUP_CONTEXT"] = ctx
    tables["LOOKUP_MDV"] = mdv
    tables["LOOKUP_SE"] = se
    tables["LOOKUP_AMENAZA"] = amen
    tables["LOOKUP_ACTOR"] = actors

    # tidies
    tables["TIDY_3_2_PRIORIZACION"] = t32
    tables["TIDY_3_4_ECOSISTEMAS"] = t34_main
    tables["TIDY_3_4_ECO_SE"] = t34_se
    tables["TIDY_3_4_ECO_MDV"] = t34_mdv
    tables["TIDY_4_2_1_AMENAZA_MDV"] = t421
    tables["TIDY_5_1_ACTORES"] = t51_main
    tables["TIDY_5_1_RELACIONES"] = t51_rel

    # QA
    pk_map = {
        "LOOKUP_GEO":["geo_id"],
        "LOOKUP_CONTEXT":["context_id"],
        "LOOKUP_MDV":["mdv_id"],
        "LOOKUP_SE":["se_id"],
        "LOOKUP_AMENAZA":["amenaza_id"],
        "LOOKUP_ACTOR":["actor_id"],
        "TIDY_3_2_PRIORIZACION":["priorizacion_id"],
        "TIDY_3_4_ECOSISTEMAS":["ecosistema_obs_id"],
        "TIDY_4_2_1_AMENAZA_MDV":["amenaza_mdv_id"],
        "TIDY_5_1_ACTORES":["actor_obs_id"],
        "TIDY_5_1_RELACIONES":["rel_id"],
    }
    id_cols = {
        "TIDY_3_2_PRIORIZACION":["context_id","mdv_id"],
        "TIDY_3_4_ECO_SE":["ecosistema_obs_id","se_id"],
        "TIDY_3_4_ECO_MDV":["ecosistema_obs_id","mdv_id"],
        "TIDY_4_2_1_AMENAZA_MDV":["context_id","amenaza_id","mdv_id"],
        "TIDY_5_1_ACTORES":["context_id","actor_id"],
    }
    fk_specs = [
        ("TIDY_3_2_PRIORIZACION","context_id","LOOKUP_CONTEXT","context_id"),
        ("TIDY_3_2_PRIORIZACION","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_3_4_ECO_SE","se_id","LOOKUP_SE","se_id"),
        ("TIDY_3_4_ECO_MDV","mdv_id","LOOKUP_MDV","mdv_id"),
        ("TIDY_4_2_1_AMENAZA_MDV","amenaza_id","LOOKUP_AMENAZA","amenaza_id"),
        ("TIDY_5_1_ACTORES","actor_id","LOOKUP_ACTOR","actor_id"),
    ]

    tables["QA_INPUT_SCHEMA"] = qa_schema
    tables["QA_TABLE_SUMMARY"] = qa_table_summary(tables)
    tables["QA_PK_DUPLICATES"] = qa_pk_duplicates(tables, pk_map)
    tables["QA_MISSING_IDS"] = qa_missing_ids(tables, id_cols)
    tables["QA_FOREIGN_KEYS"] = qa_fk(tables, fk_specs)

    return tables


# ============================================================
# 8) CLI
# ============================================================

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--no-strict", action="store_true")
    args = p.parse_args()

    tables = compile_workbook(args.input, strict=not args.no_strict)
    write_workbook(args.output, tables)
    print(f"✅ Wrote analysis-ready workbook: {args.output}")

if __name__ == "__main__":
    main()
