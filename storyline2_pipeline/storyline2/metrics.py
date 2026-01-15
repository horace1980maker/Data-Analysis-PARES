#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 Metrics Module
Computes SCI, ELI, TPS, and IVL metrics.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from .config import (
    ADMIN0_COL,
    AMENAZA_COL,
    AMENAZA_ID_COL,
    BARRERAS_COL,
    CAUSAS_DEG_COL,
    CONTEXT_ID_COL,
    ECOSISTEMA_ID_CANDIDATES,
    ECOSISTEMA_NAME_CANDIDATES,
    ES_SALUD_COL,
    FECHA_COL,
    GEO_ID_COL,
    GRUPO_COL,
    IMPACT_COLS_ALL,
    INCLUSION_COL,
    MDV_ID_COL,
    MDV_NAME_COL,
    MES_FALTA_COL,
    NR_USUARIOS_COL,
    PAISAJE_COL,
    PRIORITY_TOTAL_COL,
    SE_CODE_CANDIDATES,
    SUMA_COL,
    TIPO_AMENAZA_COL,
    get_params_yaml_path,
    get_weights_yaml_path,
)
from .transforms import (
    attach_geo,
    coerce_numeric,
    compute_seasonality_fragility,
    extract_numeric_from_text,
    minmax,
    pick_first_existing_col,
    safe_group_agg,
    safe_merge,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION LOADERS
# =============================================================================

def load_weight_scenarios(yaml_path: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    """Load SCI weight scenarios from YAML."""
    if yaml_path is None:
        yaml_path = get_weights_yaml_path()
    
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        scenarios = config.get("scenarios", {})
        return {
            name: {
                "w_links_mdv": s.get("w_links_mdv", 0.40),
                "w_users": s.get("w_users", 0.25),
                "w_priority": s.get("w_priority", 0.20),
                "w_seasonality": s.get("w_seasonality", 0.15),
            }
            for name, s in scenarios.items()
        }
    except Exception as e:
        logger.warning(f"Failed to load weights.yaml: {e}. Using defaults.")
        return {
            "balanced": {"w_links_mdv": 0.40, "w_users": 0.25, "w_priority": 0.20, "w_seasonality": 0.15},
        }


def load_eli_weights(yaml_path: Optional[Path] = None) -> Dict[str, float]:
    """Load ELI weights from YAML."""
    if yaml_path is None:
        yaml_path = get_weights_yaml_path()
    
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("eli_weights", {
            "w_connectivity": 0.60,
            "w_critical_services": 0.40,
        })
    except Exception:
        return {"w_connectivity": 0.60, "w_critical_services": 0.40}


def load_params(yaml_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load pipeline parameters from YAML."""
    if yaml_path is None:
        yaml_path = get_params_yaml_path()
    
    defaults = {
        "top_n": 10,
        "min_records_for_rank": 1,
        "use_threat_severity_weight": True,
        "threat_weight_fallback": 1.0,
        "max_heatmap_items": 15,
        "fill_missing_numeric": 0.0,
        "fill_missing_norm": 0.5,
    }
    
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        defaults.update(config or {})
    except Exception as e:
        logger.warning(f"Failed to load params.yaml: {e}. Using defaults.")
    
    return defaults


# =============================================================================
# DIMENSION BUILDERS
# =============================================================================

def build_dim_context_geo(
    lookup_context: pd.DataFrame,
    lookup_geo: pd.DataFrame,
) -> pd.DataFrame:
    """Build dimensional context-geo table."""
    if lookup_context.empty or lookup_geo.empty:
        logger.warning("Empty LOOKUP tables, returning empty dim_context_geo")
        return pd.DataFrame(columns=[
            CONTEXT_ID_COL, GEO_ID_COL, ADMIN0_COL, PAISAJE_COL, GRUPO_COL, FECHA_COL
        ])
    
    dim = lookup_context.merge(lookup_geo, on=GEO_ID_COL, how="left")
    logger.info(f"Built dim_context_geo with {len(dim)} rows")
    return dim


def build_dim_entities(
    tables: Dict[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Build dimension tables for MDV, SE, and Ecosistema.
    
    Returns:
        Tuple of (dim_mdv, dim_se, dim_ecosistema)
    """
    # DIM_MDV
    lookup_mdv = tables.get("LOOKUP_MDV", pd.DataFrame())
    if not lookup_mdv.empty:
        dim_mdv = lookup_mdv[[c for c in [MDV_ID_COL, MDV_NAME_COL] if c in lookup_mdv.columns]].drop_duplicates()
    else:
        dim_mdv = pd.DataFrame(columns=[MDV_ID_COL, MDV_NAME_COL])
    
    # DIM_SE
    lookup_se = tables.get("LOOKUP_SE", pd.DataFrame())
    if not lookup_se.empty:
        se_code_col = pick_first_existing_col(lookup_se, SE_CODE_CANDIDATES)
        if se_code_col:
            dim_se = lookup_se.copy()
            if "se_id" not in dim_se.columns:
                dim_se["se_id"] = dim_se[se_code_col]
            dim_se["se_label"] = dim_se[se_code_col]
        else:
            dim_se = lookup_se.copy()
    else:
        dim_se = pd.DataFrame(columns=["se_id", "se_label"])
    
    # DIM_ECOSISTEMA
    lookup_eco = tables.get("LOOKUP_ECOSISTEMA", pd.DataFrame())
    if not lookup_eco.empty:
        eco_id_col = pick_first_existing_col(lookup_eco, ECOSISTEMA_ID_CANDIDATES)
        eco_name_col = pick_first_existing_col(lookup_eco, ECOSISTEMA_NAME_CANDIDATES)
        dim_eco = lookup_eco.copy()
        if eco_id_col and "ecosistema_id" not in dim_eco.columns:
            dim_eco["ecosistema_id"] = dim_eco[eco_id_col]
        if eco_name_col:
            dim_eco["ecosistema_label"] = dim_eco[eco_name_col]
    else:
        # Derive from TIDY_3_4_ECOSISTEMAS
        tidy_eco = tables.get("TIDY_3_4_ECOSISTEMAS", pd.DataFrame())
        if not tidy_eco.empty:
            eco_name_col = pick_first_existing_col(tidy_eco, ECOSISTEMA_NAME_CANDIDATES)
            if eco_name_col:
                dim_eco = tidy_eco[[eco_name_col]].drop_duplicates()
                dim_eco["ecosistema_id"] = range(1, len(dim_eco) + 1)
                dim_eco["ecosistema_label"] = dim_eco[eco_name_col]
            else:
                dim_eco = pd.DataFrame(columns=["ecosistema_id", "ecosistema_label"])
        else:
            dim_eco = pd.DataFrame(columns=["ecosistema_id", "ecosistema_label"])
    
    logger.info(f"Dimensions: {len(dim_mdv)} MDV, {len(dim_se)} SE, {len(dim_eco)} Ecosistema")
    return dim_mdv, dim_se, dim_eco


def get_se_key_col(df: pd.DataFrame) -> Optional[str]:
    """Get the service key column from a DataFrame."""
    return pick_first_existing_col(df, SE_CODE_CANDIDATES)


def get_eco_key_col(df: pd.DataFrame) -> Optional[str]:
    """Get the ecosystem key column from a DataFrame."""
    eco_id = pick_first_existing_col(df, ECOSISTEMA_ID_CANDIDATES)
    if eco_id:
        return eco_id
    return pick_first_existing_col(df, ECOSISTEMA_NAME_CANDIDATES)


# =============================================================================
# ECOSYSTEM CONNECTIVITY
# =============================================================================

def ecosystem_connectivity(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute ecosystem connectivity metrics.
    
    Returns:
        Tuple of (ecosystem_summary_overall, ecosystem_summary_by_grupo)
    """
    tidy_eco = tables.get("TIDY_3_4_ECOSISTEMAS", pd.DataFrame())
    eco_se = tables.get("TIDY_3_4_ECO_SE", pd.DataFrame())
    eco_mdv = tables.get("TIDY_3_4_ECO_MDV", pd.DataFrame())
    
    empty_cols = ["ecosistema", "n_obs", "n_services", "n_livelihoods", "n_causes_deg", "connectivity_norm"]
    
    if tidy_eco.empty:
        logger.warning("TIDY_3_4_ECOSISTEMAS is empty, skipping ecosystem connectivity")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Attach geo to ecosystems
    tidy_eco = attach_geo(tidy_eco, dim_context_geo)
    
    # Get ecosystem key column
    eco_key = get_eco_key_col(tidy_eco)
    if not eco_key:
        eco_key = "ecosistema"
        if eco_key not in tidy_eco.columns:
            logger.warning("No ecosystem identifier found")
            return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Build ecosystem -> services mapping
    services_per_eco = pd.DataFrame()
    if not eco_se.empty:
        se_key = get_se_key_col(eco_se)
        if se_key and "ecosistema_obs_id" in eco_se.columns:
            # Join through ecosistema_obs_id
            eco_se_joined = eco_se.merge(
                tidy_eco[[col for col in ["ecosistema_obs_id", eco_key, GRUPO_COL] if col in tidy_eco.columns]],
                on="ecosistema_obs_id",
                how="left"
            )
            services_per_eco = eco_se_joined.groupby(eco_key)[se_key].nunique().reset_index()
            services_per_eco.columns = [eco_key, "n_services"]
    
    # Build ecosystem -> livelihoods mapping
    livelihoods_per_eco = pd.DataFrame()
    if not eco_mdv.empty and MDV_ID_COL in eco_mdv.columns:
        if "ecosistema_obs_id" in eco_mdv.columns:
            eco_mdv_joined = eco_mdv.merge(
                tidy_eco[[col for col in ["ecosistema_obs_id", eco_key, GRUPO_COL] if col in tidy_eco.columns]],
                on="ecosistema_obs_id",
                how="left"
            )
            livelihoods_per_eco = eco_mdv_joined.groupby(eco_key)[MDV_ID_COL].nunique().reset_index()
            livelihoods_per_eco.columns = [eco_key, "n_livelihoods"]
    
    # OVERALL aggregation
    agg_spec = {
        "ecosistema_obs_id": "nunique" if "ecosistema_obs_id" in tidy_eco.columns else "count",
    }
    if CAUSAS_DEG_COL in tidy_eco.columns:
        tidy_eco["_has_causas"] = tidy_eco[CAUSAS_DEG_COL].notna() & (tidy_eco[CAUSAS_DEG_COL] != "")
        agg_spec["_has_causas"] = "sum"
    
    overall = tidy_eco.groupby(eco_key, dropna=False).agg(agg_spec).reset_index()
    overall.columns = [eco_key, "n_obs"] + (["n_causes_deg"] if "_has_causas" in agg_spec else [])
    
    # Join service and livelihood counts
    if not services_per_eco.empty:
        overall = overall.merge(services_per_eco, on=eco_key, how="left")
    else:
        overall["n_services"] = 0
    
    if not livelihoods_per_eco.empty:
        overall = overall.merge(livelihoods_per_eco, on=eco_key, how="left")
    else:
        overall["n_livelihoods"] = 0
    
    overall = overall.fillna(0)
    
    # Compute connectivity norm
    overall["connectivity_raw"] = overall["n_services"] + overall["n_livelihoods"]
    overall["connectivity_norm"] = minmax(overall["connectivity_raw"])
    
    # Add ecosystem name from LOOKUP_ECOSISTEMA if available
    lookup_eco = tables.get("LOOKUP_ECOSISTEMA", pd.DataFrame())
    if not lookup_eco.empty and eco_key:
        eco_id_col = pick_first_existing_col(lookup_eco, ECOSISTEMA_ID_CANDIDATES)
        eco_name_col = pick_first_existing_col(lookup_eco, ECOSISTEMA_NAME_CANDIDATES)
        if eco_id_col and eco_name_col and eco_key == eco_id_col:
            eco_lookup = lookup_eco[[eco_id_col, eco_name_col]].drop_duplicates()
            eco_lookup = eco_lookup.rename(columns={eco_name_col: "ecosistema"})
            if "ecosistema" not in overall.columns:
                overall = overall.merge(eco_lookup, left_on=eco_key, right_on=eco_id_col, how="left")
                if eco_id_col != eco_key:
                    overall.drop(columns=[eco_id_col], errors='ignore', inplace=True)
    
    # BY GRUPO aggregation
    by_grupo = pd.DataFrame(columns=["grupo"] + empty_cols)
    if GRUPO_COL in tidy_eco.columns:
        grupo_agg = tidy_eco.groupby([GRUPO_COL, eco_key], dropna=False).agg({
            "ecosistema_obs_id": "nunique" if "ecosistema_obs_id" in tidy_eco.columns else "count",
        }).reset_index()
        grupo_agg.columns = [GRUPO_COL, eco_key, "n_obs"]
        
        # For by_grupo, we need service/livelihood counts per group
        # Simplified: use overall counts (could be refined with group-specific joins)
        by_grupo = grupo_agg.merge(services_per_eco, on=eco_key, how="left") if not services_per_eco.empty else grupo_agg
        if "n_services" not in by_grupo.columns:
            by_grupo["n_services"] = 0
        by_grupo = by_grupo.merge(livelihoods_per_eco, on=eco_key, how="left") if not livelihoods_per_eco.empty else by_grupo
        if "n_livelihoods" not in by_grupo.columns:
            by_grupo["n_livelihoods"] = 0
        
        by_grupo = by_grupo.fillna(0)
        by_grupo["connectivity_raw"] = by_grupo["n_services"] + by_grupo["n_livelihoods"]
        by_grupo["connectivity_norm"] = by_grupo.groupby(GRUPO_COL)["connectivity_raw"].transform(
            lambda x: minmax(x)
        )
        
        # Add ecosystem name to by_grupo
        if not lookup_eco.empty and eco_key:
            eco_id_col = pick_first_existing_col(lookup_eco, ECOSISTEMA_ID_CANDIDATES)
            eco_name_col = pick_first_existing_col(lookup_eco, ECOSISTEMA_NAME_CANDIDATES)
            if eco_id_col and eco_name_col and eco_key == eco_id_col:
                eco_lookup = lookup_eco[[eco_id_col, eco_name_col]].drop_duplicates()
                eco_lookup = eco_lookup.rename(columns={eco_name_col: "ecosistema"})
                if "ecosistema" not in by_grupo.columns:
                    by_grupo = by_grupo.merge(eco_lookup, left_on=eco_key, right_on=eco_id_col, how="left")
                    if eco_id_col != eco_key:
                        by_grupo.drop(columns=[eco_id_col], errors='ignore', inplace=True)
    
    logger.info(f"Ecosystem connectivity: {len(overall)} overall, {len(by_grupo)} by grupo")
    return overall, by_grupo



# =============================================================================
# SERVICE SCI COMPONENTS
# =============================================================================

def service_sci_components(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute Service Criticality Index (SCI) components.
    
    Returns:
        Tuple of (sci_components_overall, sci_components_by_grupo)
    """
    tidy_se_mdv = tables.get("TIDY_3_5_SE_MDV", pd.DataFrame())
    tidy_priority = tables.get("TIDY_3_2_PRIORIZACION", pd.DataFrame())
    
    empty_cols = ["se_key", "links_mdv", "users", "seasonality_fragility", "priority_weight"]
    
    if tidy_se_mdv.empty:
        logger.warning("TIDY_3_5_SE_MDV is empty, skipping SCI components")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Attach geo
    df = attach_geo(tidy_se_mdv, dim_context_geo)
    
    # Get SE key column
    se_key = get_se_key_col(df)
    if not se_key:
        logger.warning("No SE key column found in TIDY_3_5_SE_MDV")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    df["se_key"] = df[se_key]
    
    # Parse numeric users
    if NR_USUARIOS_COL in df.columns:
        df["users_numeric"] = df[NR_USUARIOS_COL].apply(extract_numeric_from_text)
    else:
        df["users_numeric"] = 0
    
    # Compute seasonality fragility
    if MES_FALTA_COL in df.columns:
        df["seasonality_fragility"] = df[MES_FALTA_COL].apply(compute_seasonality_fragility)
    else:
        df["seasonality_fragility"] = 0
    
    # Get priority weights
    priority_by_mdv = pd.DataFrame()
    if not tidy_priority.empty and MDV_ID_COL in tidy_priority.columns:
        priority_df = attach_geo(tidy_priority, dim_context_geo)
        if PRIORITY_TOTAL_COL in priority_df.columns:
            priority_df = coerce_numeric(priority_df, [PRIORITY_TOTAL_COL])
            priority_by_mdv = priority_df.groupby(MDV_ID_COL)[PRIORITY_TOTAL_COL].mean().reset_index()
            priority_by_mdv.columns = [MDV_ID_COL, "mdv_priority"]
            priority_by_mdv["mdv_priority_norm"] = minmax(priority_by_mdv["mdv_priority"])
    
    # Join priority to SE-MDV data
    if not priority_by_mdv.empty and MDV_ID_COL in df.columns:
        df = df.merge(priority_by_mdv[[MDV_ID_COL, "mdv_priority_norm"]], on=MDV_ID_COL, how="left")
        df["mdv_priority_norm"] = df["mdv_priority_norm"].fillna(0.5)
    else:
        df["mdv_priority_norm"] = 0.5
    
    # OVERALL aggregation
    overall_agg = df.groupby("se_key", dropna=False).agg({
        MDV_ID_COL: "nunique",
        "users_numeric": "sum",
        "seasonality_fragility": "mean",
        "mdv_priority_norm": "mean",
    }).reset_index()
    overall_agg.columns = ["se_key", "links_mdv", "users", "seasonality_fragility", "priority_weight"]
    
    # Normalize components
    overall_agg["links_mdv_norm"] = minmax(overall_agg["links_mdv"])
    overall_agg["users_norm"] = minmax(overall_agg["users"])
    overall_agg["seasonality_norm"] = minmax(overall_agg["seasonality_fragility"])
    overall_agg["priority_norm"] = minmax(overall_agg["priority_weight"])
    
    # BY GRUPO aggregation
    by_grupo = pd.DataFrame(columns=["grupo"] + empty_cols)
    if GRUPO_COL in df.columns:
        by_grupo = df.groupby([GRUPO_COL, "se_key"], dropna=False).agg({
            MDV_ID_COL: "nunique",
            "users_numeric": "sum",
            "seasonality_fragility": "mean",
            "mdv_priority_norm": "mean",
        }).reset_index()
        by_grupo.columns = ["grupo", "se_key", "links_mdv", "users", "seasonality_fragility", "priority_weight"]
        
        # Normalize within each grupo
        for col, norm_col in [
            ("links_mdv", "links_mdv_norm"),
            ("users", "users_norm"),
            ("seasonality_fragility", "seasonality_norm"),
            ("priority_weight", "priority_norm"),
        ]:
            by_grupo[norm_col] = by_grupo.groupby("grupo")[col].transform(lambda x: minmax(x))
    
    logger.info(f"SCI components: {len(overall_agg)} overall, {len(by_grupo)} by grupo")
    return overall_agg, by_grupo


# =============================================================================
# COMPUTE SCI RANKINGS
# =============================================================================

def compute_sci_rankings(
    sci_overall: pd.DataFrame,
    sci_by_grupo: pd.DataFrame,
    weight_scenarios: Optional[Dict[str, Dict[str, float]]] = None,
    top_n: int = 10,
) -> Dict[str, pd.DataFrame]:
    """
    Compute SCI rankings for each weight scenario.
    
    Returns:
        Dict of ranking table names -> DataFrames
    """
    if weight_scenarios is None:
        weight_scenarios = load_weight_scenarios()
    
    results: Dict[str, pd.DataFrame] = {}
    
    # OVERALL rankings
    if not sci_overall.empty:
        for scenario_name, weights in weight_scenarios.items():
            df = sci_overall.copy()
            
            # Compute SCI
            df["sci"] = (
                weights["w_links_mdv"] * df.get("links_mdv_norm", 0.5) +
                weights["w_users"] * df.get("users_norm", 0.5) +
                weights["w_priority"] * df.get("priority_norm", 0.5) +
                weights["w_seasonality"] * df.get("seasonality_norm", 0.5)
            )
            
            # Rank and select top N
            ranking = df.sort_values("sci", ascending=False).head(top_n).copy()
            ranking["rank"] = range(1, len(ranking) + 1)
            ranking["scenario"] = scenario_name
            
            results[f"service_ranking_overall_{scenario_name}"] = ranking
    
    # BY GRUPO rankings
    if not sci_by_grupo.empty and "grupo" in sci_by_grupo.columns:
        for scenario_name, weights in weight_scenarios.items():
            df = sci_by_grupo.copy()
            
            # Compute SCI
            df["sci"] = (
                weights["w_links_mdv"] * df.get("links_mdv_norm", 0.5) +
                weights["w_users"] * df.get("users_norm", 0.5) +
                weights["w_priority"] * df.get("priority_norm", 0.5) +
                weights["w_seasonality"] * df.get("seasonality_norm", 0.5)
            )
            
            # Rank within each grupo
            df["rank"] = df.groupby("grupo")["sci"].rank(ascending=False, method="first")
            ranking = df[df["rank"] <= top_n].sort_values(["grupo", "rank"]).copy()
            ranking["scenario"] = scenario_name
            
            results[f"service_ranking_by_grupo_{scenario_name}"] = ranking
    
    logger.info(f"Generated SCI rankings for {len(weight_scenarios)} scenarios")
    return results


# =============================================================================
# ECOSYSTEM LEVERAGE INDEX (ELI)
# =============================================================================

def ecosystem_leverage_index(
    eco_overall: pd.DataFrame,
    eco_by_grupo: pd.DataFrame,
    sci_overall: pd.DataFrame,
    tables: Dict[str, pd.DataFrame],
    eli_weights: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute Ecosystem Leverage Index (ELI).
    
    Returns:
        Tuple of (eli_overall, eli_by_grupo)
    """
    if eli_weights is None:
        eli_weights = load_eli_weights()
    
    w_conn = eli_weights.get("w_connectivity", 0.60)
    w_crit = eli_weights.get("w_critical_services", 0.40)
    
    eco_se = tables.get("TIDY_3_4_ECO_SE", pd.DataFrame())
    
    # Get mean SCI per ecosystem (via ECO_SE linkage)
    eco_key = get_eco_key_col(eco_overall) if not eco_overall.empty else None
    se_key = get_se_key_col(eco_se) if not eco_se.empty else None
    
    mean_sci_per_eco = pd.DataFrame()
    if not eco_se.empty and not sci_overall.empty and se_key and "se_key" in sci_overall.columns:
        # Rename to match
        eco_se_copy = eco_se.copy()
        eco_se_copy["se_key"] = eco_se_copy[se_key]
        
        # Get ecosistema key in eco_se
        eco_key_in_eco_se = None
        if eco_key and eco_key in eco_se_copy.columns:
            eco_key_in_eco_se = eco_key
        elif "ecosistema_obs_id" in eco_se_copy.columns:
            # Need to join through TIDY_3_4_ECOSISTEMAS
            tidy_eco = tables.get("TIDY_3_4_ECOSISTEMAS", pd.DataFrame())
            if not tidy_eco.empty and eco_key and eco_key in tidy_eco.columns:
                eco_se_copy = eco_se_copy.merge(
                    tidy_eco[["ecosistema_obs_id", eco_key]].drop_duplicates(),
                    on="ecosistema_obs_id",
                    how="left"
                )
                eco_key_in_eco_se = eco_key
        
        if eco_key_in_eco_se:
            # Join SCI scores
            eco_sci = eco_se_copy.merge(
                sci_overall[["se_key", "links_mdv_norm"]],  # Use links as proxy if no SCI yet
                on="se_key",
                how="left"
            )
            eco_sci["links_mdv_norm"] = eco_sci["links_mdv_norm"].fillna(0.5)
            
            mean_sci_per_eco = eco_sci.groupby(eco_key_in_eco_se)["links_mdv_norm"].mean().reset_index()
            mean_sci_per_eco.columns = [eco_key_in_eco_se, "mean_sci"]
    
    # OVERALL ELI
    eli_overall = eco_overall.copy() if not eco_overall.empty else pd.DataFrame()
    if not eli_overall.empty and eco_key:
        if not mean_sci_per_eco.empty:
            eli_overall = eli_overall.merge(mean_sci_per_eco, on=eco_key, how="left")
        else:
            eli_overall["mean_sci"] = 0.5
        eli_overall["mean_sci"] = eli_overall["mean_sci"].fillna(0.5)
        eli_overall["mean_sci_norm"] = minmax(eli_overall["mean_sci"])
        
        eli_overall["eli"] = (
            w_conn * eli_overall.get("connectivity_norm", 0.5) +
            w_crit * eli_overall["mean_sci_norm"]
        )
        eli_overall["eli_norm"] = minmax(eli_overall["eli"])
    
    # BY GRUPO ELI
    eli_by_grupo = eco_by_grupo.copy() if not eco_by_grupo.empty else pd.DataFrame()
    if not eli_by_grupo.empty and eco_key and "grupo" in eli_by_grupo.columns:
        if not mean_sci_per_eco.empty:
            eli_by_grupo = eli_by_grupo.merge(mean_sci_per_eco, on=eco_key, how="left")
        else:
            eli_by_grupo["mean_sci"] = 0.5
        eli_by_grupo["mean_sci"] = eli_by_grupo["mean_sci"].fillna(0.5)
        eli_by_grupo["mean_sci_norm"] = eli_by_grupo.groupby("grupo")["mean_sci"].transform(lambda x: minmax(x))
        
        eli_by_grupo["eli"] = (
            w_conn * eli_by_grupo.get("connectivity_norm", 0.5) +
            w_crit * eli_by_grupo["mean_sci_norm"]
        )
        eli_by_grupo["eli_norm"] = eli_by_grupo.groupby("grupo")["eli"].transform(lambda x: minmax(x))
    
    logger.info(f"ELI: {len(eli_overall)} overall, {len(eli_by_grupo)} by grupo")
    return eli_overall, eli_by_grupo


# =============================================================================
# THREAT PRESSURE ON SERVICES (TPS)
# =============================================================================

def threat_pressure_on_services(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute Threat Pressure on Services (TPS).
    
    Returns:
        Tuple of (tps_overall, tps_by_grupo)
    """
    if params is None:
        params = load_params()
    
    tidy_amenaza_se = tables.get("TIDY_4_2_2_AMENAZA_SE", pd.DataFrame())
    tidy_amenazas = tables.get("TIDY_4_1_AMENAZAS", pd.DataFrame())
    
    empty_cols = ["amenaza_id", "amenaza", "se_key", "sum_pressure", "mean_pressure", "n_rows"]
    
    if tidy_amenaza_se.empty:
        logger.warning("TIDY_4_2_2_AMENAZA_SE is empty, skipping TPS")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Attach geo
    df = attach_geo(tidy_amenaza_se, dim_context_geo)
    
    # Get SE key
    se_key = get_se_key_col(df)
    if se_key:
        df["se_key"] = df[se_key]
    else:
        df["se_key"] = "unknown"
    
    # Compute impact total
    impact_cols_present = [c for c in IMPACT_COLS_ALL if c in df.columns]
    if impact_cols_present:
        df = coerce_numeric(df, impact_cols_present)
        df["impact_total"] = df[impact_cols_present].sum(axis=1, skipna=True)
    else:
        df["impact_total"] = 1.0  # Count-based fallback
    
    # Get threat severity weights
    if params.get("use_threat_severity_weight", True) and not tidy_amenazas.empty:
        severity_df = attach_geo(tidy_amenazas, dim_context_geo)
        if SUMA_COL in severity_df.columns and AMENAZA_ID_COL in severity_df.columns:
            severity_df = coerce_numeric(severity_df, [SUMA_COL])
            severity_lookup = severity_df.groupby(AMENAZA_ID_COL)[SUMA_COL].mean().reset_index()
            severity_lookup["suma_norm"] = minmax(severity_lookup[SUMA_COL])
            
            if AMENAZA_ID_COL in df.columns:
                df = df.merge(severity_lookup[[AMENAZA_ID_COL, "suma_norm"]], on=AMENAZA_ID_COL, how="left")
                df["severity_weight"] = df["suma_norm"].fillna(params.get("threat_weight_fallback", 1.0))
            else:
                df["severity_weight"] = params.get("threat_weight_fallback", 1.0)
        else:
            df["severity_weight"] = params.get("threat_weight_fallback", 1.0)
    else:
        df["severity_weight"] = params.get("threat_weight_fallback", 1.0)
    
    # Compute pressure
    df["pressure"] = df["impact_total"] * df["severity_weight"]
    
    # Aggregation groups
    group_cols = []
    if AMENAZA_ID_COL in df.columns:
        group_cols.append(AMENAZA_ID_COL)
    if TIPO_AMENAZA_COL in df.columns:
        group_cols.append(TIPO_AMENAZA_COL)
    if AMENAZA_COL in df.columns:
        group_cols.append(AMENAZA_COL)
    group_cols.append("se_key")
    
    # OVERALL aggregation
    overall = df.groupby(group_cols, dropna=False).agg({
        "pressure": ["sum", "mean", "count"],
    }).reset_index()
    overall.columns = group_cols + ["sum_pressure", "mean_pressure", "n_rows"]
    overall["pressure_norm"] = minmax(overall["sum_pressure"])
    
    # BY GRUPO aggregation
    by_grupo = pd.DataFrame(columns=["grupo"] + group_cols + ["sum_pressure", "mean_pressure", "n_rows"])
    if GRUPO_COL in df.columns:
        group_cols_with_grupo = [GRUPO_COL] + group_cols
        by_grupo = df.groupby(group_cols_with_grupo, dropna=False).agg({
            "pressure": ["sum", "mean", "count"],
        }).reset_index()
        by_grupo.columns = group_cols_with_grupo + ["sum_pressure", "mean_pressure", "n_rows"]
        by_grupo["pressure_norm"] = by_grupo.groupby(GRUPO_COL)["sum_pressure"].transform(lambda x: minmax(x))
    
    logger.info(f"TPS: {len(overall)} overall, {len(by_grupo)} by grupo")
    return overall, by_grupo


# =============================================================================
# INDIRECT VULNERABILITY OF LIVELIHOODS (IVL)
# =============================================================================

def indirect_vulnerability_livelihoods(
    tps_overall: pd.DataFrame,
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute Indirect Vulnerability of Livelihoods (IVL).
    Threats -> Services -> Livelihoods
    
    Returns:
        Tuple of (ivl_overall, ivl_by_grupo)
    """
    tidy_se_mdv = tables.get("TIDY_3_5_SE_MDV", pd.DataFrame())
    
    empty_cols = ["mdv_id", "mdv_name", "amenaza_id", "amenaza", "sum_pressure_via_services"]
    
    if tps_overall.empty or tidy_se_mdv.empty:
        logger.warning("Missing TPS or SE-MDV data, skipping IVL")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Get SE-MDV linkages
    se_mdv = attach_geo(tidy_se_mdv, dim_context_geo)
    se_key = get_se_key_col(se_mdv)
    if se_key:
        se_mdv["se_key"] = se_mdv[se_key]
    else:
        logger.warning("No SE key in TIDY_3_5_SE_MDV")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Join TPS to SE-MDV on service key
    if "se_key" not in tps_overall.columns:
        logger.warning("No se_key in TPS")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # Select relevant TPS columns
    tps_cols = ["se_key", "sum_pressure"]
    if AMENAZA_ID_COL in tps_overall.columns:
        tps_cols.append(AMENAZA_ID_COL)
    if AMENAZA_COL in tps_overall.columns:
        tps_cols.append(AMENAZA_COL)
    
    tps_subset = tps_overall[tps_cols].copy()
    
    # Join
    joined = se_mdv.merge(tps_subset, on="se_key", how="inner")
    
    if joined.empty:
        logger.warning("No matches between TPS and SE-MDV")
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=["grupo"] + empty_cols)
    
    # OVERALL aggregation
    group_cols = [MDV_ID_COL]
    if MDV_NAME_COL in joined.columns:
        group_cols.append(MDV_NAME_COL)
    if AMENAZA_ID_COL in joined.columns:
        group_cols.append(AMENAZA_ID_COL)
    if AMENAZA_COL in joined.columns:
        group_cols.append(AMENAZA_COL)
    
    overall = joined.groupby(group_cols, dropna=False).agg({
        "sum_pressure": "sum",
    }).reset_index()
    overall.columns = group_cols + ["sum_pressure_via_services"]
    overall["ivl_norm"] = minmax(overall["sum_pressure_via_services"])
    
    # BY GRUPO
    by_grupo = pd.DataFrame(columns=["grupo"] + group_cols + ["sum_pressure_via_services"])
    if GRUPO_COL in joined.columns:
        group_cols_with_grupo = [GRUPO_COL] + group_cols
        by_grupo = joined.groupby(group_cols_with_grupo, dropna=False).agg({
            "sum_pressure": "sum",
        }).reset_index()
        by_grupo.columns = group_cols_with_grupo + ["sum_pressure_via_services"]
        by_grupo["ivl_norm"] = by_grupo.groupby(GRUPO_COL)["sum_pressure_via_services"].transform(lambda x: minmax(x))
    
    logger.info(f"IVL: {len(overall)} overall, {len(by_grupo)} by grupo")
    return overall, by_grupo


# =============================================================================
# MAIN METRICS PIPELINE
# =============================================================================

def compute_all_metrics(
    tables: Dict[str, pd.DataFrame],
    top_n: int = 10,
) -> Dict[str, pd.DataFrame]:
    """
    Compute all Storyline 2 metrics.
    
    Args:
        tables: Dict of table_name -> DataFrame
        top_n: Number of top items for rankings
        
    Returns:
        Dict of all output tables
    """
    results: Dict[str, pd.DataFrame] = {}
    params = load_params()
    
    # Build dimensional tables
    dim_context_geo = build_dim_context_geo(
        tables.get("LOOKUP_CONTEXT", pd.DataFrame()),
        tables.get("LOOKUP_GEO", pd.DataFrame()),
    )
    results["dim_context_geo"] = dim_context_geo
    
    dim_mdv, dim_se, dim_eco = build_dim_entities(tables)
    results["dim_mdv"] = dim_mdv
    results["dim_se"] = dim_se
    results["dim_ecosistema"] = dim_eco
    
    # Ecosystem connectivity
    eco_overall, eco_by_grupo = ecosystem_connectivity(tables, dim_context_geo)
    results["ecosystem_summary_overall"] = eco_overall
    results["ecosystem_summary_by_grupo"] = eco_by_grupo
    
    # Service SCI components
    sci_overall, sci_by_grupo = service_sci_components(tables, dim_context_geo)
    results["service_sci_components_overall"] = sci_overall
    results["service_sci_components_by_grupo"] = sci_by_grupo
    
    # SCI rankings
    weight_scenarios = load_weight_scenarios()
    sci_rankings = compute_sci_rankings(sci_overall, sci_by_grupo, weight_scenarios, top_n)
    results.update(sci_rankings)
    
    # Ecosystem ELI
    eli_overall, eli_by_grupo = ecosystem_leverage_index(
        eco_overall, eco_by_grupo, sci_overall, tables
    )
    results["ecosystem_eli_overall"] = eli_overall
    results["ecosystem_eli_by_grupo"] = eli_by_grupo
    
    # Threat Pressure on Services
    tps_overall, tps_by_grupo = threat_pressure_on_services(tables, dim_context_geo, params)
    results["tps_overall"] = tps_overall
    results["tps_by_grupo"] = tps_by_grupo
    
    # Indirect Vulnerability of Livelihoods
    ivl_overall, ivl_by_grupo = indirect_vulnerability_livelihoods(
        tps_overall, tables, dim_context_geo
    )
    results["ivl_overall"] = ivl_overall
    results["ivl_by_grupo"] = ivl_by_grupo
    
    logger.info(f"Computed {len(results)} output tables")
    return results
