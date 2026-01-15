#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 Metrics Module
Computes priority, risk, capacity, and Action Priority Index metrics.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from .config import (
    IMPACT_COLS,
    PRIORITY_COMPONENT_COLS,
    PRIORITY_TOTAL_COL,
    THREAT_SEVERITY_COLS,
    get_weights_yaml_path,
)
from .transforms import (
    attach_geo,
    coerce_numeric_columns,
    compute_response_numeric,
    minmax,
    safe_group_agg,
    safe_merge,
)

logger = logging.getLogger(__name__)


def load_weight_scenarios(yaml_path: Optional[Path] = None) -> Dict[str, Dict[str, float]]:
    """
    Load weight scenarios from YAML configuration.
    
    Args:
        yaml_path: Path to weights.yaml file (default: config/weights.yaml)
        
    Returns:
        Dict mapping scenario name to weight dict with keys:
        w_priority, w_risk, w_capacity_gap
    """
    if yaml_path is None:
        yaml_path = get_weights_yaml_path()
    
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        scenarios = config.get("scenarios", {})
        return {
            name: {
                "w_priority": s.get("w_priority", 0.33),
                "w_risk": s.get("w_risk", 0.33),
                "w_capacity_gap": s.get("w_capacity_gap", 0.34),
            }
            for name, s in scenarios.items()
        }
    except Exception as e:
        logger.warning(f"Failed to load weights.yaml: {e}. Using defaults.")
        return {
            "balanced": {"w_priority": 0.4, "w_risk": 0.4, "w_capacity_gap": 0.2},
            "livelihood_first": {"w_priority": 0.5, "w_risk": 0.3, "w_capacity_gap": 0.2},
            "risk_first": {"w_priority": 0.3, "w_risk": 0.5, "w_capacity_gap": 0.2},
        }


def build_dim_context_geo(
    lookup_context: pd.DataFrame,
    lookup_geo: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build dimensional table joining LOOKUP_CONTEXT to LOOKUP_GEO.
    
    Args:
        lookup_context: LOOKUP_CONTEXT table with context_id, geo_id, fecha_iso
        lookup_geo: LOOKUP_GEO table with geo_id, admin0, paisaje, grupo
        
    Returns:
        Joined dimensional table with all context and geo columns
    """
    if lookup_context.empty or lookup_geo.empty:
        logger.warning("Empty LOOKUP tables, returning empty dim_context_geo")
        return pd.DataFrame(columns=[
            "context_id", "geo_id", "admin0", "paisaje", "grupo", "fecha_iso"
        ])
    
    dim = lookup_context.merge(lookup_geo, on="geo_id", how="left")
    logger.info(f"Built dim_context_geo with {len(dim)} rows")
    return dim


# ---------------------------------------------------------------------------
# PRIORITY METRICS
# ---------------------------------------------------------------------------

def priority_metrics(
    tidy_priorizacion: pd.DataFrame,
    dim_context_geo: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute priority metrics by MDV (overall, by grupo, and field-style ranking).
    
    Args:
        tidy_priorizacion: TIDY_3_2_PRIORIZACION table
        dim_context_geo: Dimensional context/geo table
        
    Returns:
        Tuple of:
        - priority_by_mdv_overall: Mean aggregated across all contexts
        - priority_by_mdv_group: Mean aggregated within each grupo
        - priority_field_ranking: Field-style ranking (i_total ranked within each zona)
    """
    empty = pd.DataFrame(columns=[
        "mdv_id", "mdv_name", "mean_i_total", "n_records", "priority_norm"
    ])
    empty_field = pd.DataFrame(columns=[
        "grupo", "mdv_id", "mdv_name", "i_total", "rank_in_zona"
    ])
    
    if tidy_priorizacion.empty:
        logger.warning("Empty TIDY_3_2_PRIORIZACION, returning empty priority metrics")
        return empty, empty.copy(), empty_field
    
    # Attach geo columns
    df = attach_geo(tidy_priorizacion, dim_context_geo, on="context_id")
    
    # Coerce numeric columns
    numeric_cols = [PRIORITY_TOTAL_COL] + PRIORITY_COMPONENT_COLS
    df = coerce_numeric_columns(df, numeric_cols)
    
    # -------------------------------------------------------------------------
    # FIELD-STYLE RANKING: i_total ranked within each zona (respects field methodology)
    # -------------------------------------------------------------------------
    if "grupo" in df.columns and PRIORITY_TOTAL_COL in df.columns:
        # Use the raw i_total values (as computed in the field)
        field_cols = ["grupo", "mdv_id", "mdv_name", PRIORITY_TOTAL_COL]
        field_cols_present = [c for c in field_cols if c in df.columns]
        field_ranking = df[field_cols_present].copy()
        
        # Rank within each zona (highest i_total = rank 1)
        field_ranking["rank_in_zona"] = field_ranking.groupby("grupo")[PRIORITY_TOTAL_COL].rank(
            ascending=False, method="min"
        )
        field_ranking = field_ranking.rename(columns={PRIORITY_TOTAL_COL: "i_total"})
        field_ranking = field_ranking.sort_values(["grupo", "rank_in_zona"])
        
        # Add component columns if available
        for col in PRIORITY_COMPONENT_COLS:
            if col in df.columns:
                field_ranking[col] = df[col].values
    else:
        field_ranking = empty_field.copy()
    
    # -------------------------------------------------------------------------
    # MEAN AGGREGATED VIEW: Overall (analytical view across all contexts)
    # -------------------------------------------------------------------------
    agg_spec = {
        PRIORITY_TOTAL_COL: "mean",
        **{col: "mean" for col in PRIORITY_COMPONENT_COLS if col in df.columns},
    }
    agg_spec["context_id"] = "count"  # For n_records
    
    # OVERALL: group by mdv only
    overall_groups = ["mdv_id", "mdv_name"]
    priority_overall = safe_group_agg(df, overall_groups, agg_spec)
    
    if not priority_overall.empty:
        priority_overall = priority_overall.rename(columns={
            PRIORITY_TOTAL_COL: "mean_i_total",
            "context_id": "n_records",
        })
        # Rename component means
        for col in PRIORITY_COMPONENT_COLS:
            if col in priority_overall.columns:
                priority_overall = priority_overall.rename(columns={col: f"mean_{col}"})
        
        # Compute normalized priority (minmax within overall)
        priority_overall["priority_norm"] = minmax(priority_overall["mean_i_total"])
    
    # BY GROUP: group by grupo + mdv (mean within each zona)
    group_groups = ["grupo", "mdv_id", "mdv_name"]
    priority_by_group = safe_group_agg(df, group_groups, agg_spec)
    
    if not priority_by_group.empty:
        priority_by_group = priority_by_group.rename(columns={
            PRIORITY_TOTAL_COL: "mean_i_total",
            "context_id": "n_records",
        })
        for col in PRIORITY_COMPONENT_COLS:
            if col in priority_by_group.columns:
                priority_by_group = priority_by_group.rename(columns={col: f"mean_{col}"})
        
        # Compute normalized priority within each grupo
        priority_by_group["priority_norm"] = priority_by_group.groupby("grupo")["mean_i_total"].transform(
            lambda x: minmax(x)
        )
    
    logger.info(f"Priority metrics: {len(priority_overall)} overall, {len(priority_by_group)} by grupo, {len(field_ranking)} field rankings")
    return priority_overall, priority_by_group, field_ranking


# ---------------------------------------------------------------------------
# THREAT METRICS
# ---------------------------------------------------------------------------

def threat_metrics(
    tidy_amenazas: pd.DataFrame,
    dim_context_geo: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute threat severity metrics (overall and by grupo).
    
    Args:
        tidy_amenazas: TIDY_4_1_AMENAZAS table
        dim_context_geo: Dimensional context/geo table
        
    Returns:
        Tuple of (threats_overall, threats_by_group)
    """
    if tidy_amenazas.empty:
        logger.warning("Empty TIDY_4_1_AMENAZAS, returning empty threat metrics")
        empty = pd.DataFrame(columns=[
            "amenaza_id", "tipo_amenaza", "amenaza", "mean_suma", "n", "suma_norm"
        ])
        return empty, empty.copy()
    
    # Attach geo columns
    df = attach_geo(tidy_amenazas, dim_context_geo, on="context_id")
    
    # Coerce numeric columns
    df = coerce_numeric_columns(df, THREAT_SEVERITY_COLS)
    
    # Build aggregation spec
    agg_spec = {
        "suma": "mean",
        "magnitud": "mean",
        "frequencia": "mean",
        "tendencia": "mean",
        "context_id": "count",
    }
    
    # OVERALL: group by threat identity
    overall_groups = ["amenaza_id", "tipo_amenaza", "amenaza"]
    threats_overall = safe_group_agg(df, overall_groups, agg_spec)
    
    if not threats_overall.empty:
        threats_overall = threats_overall.rename(columns={
            "suma": "mean_suma",
            "magnitud": "mean_magnitud",
            "frequencia": "mean_frequencia",
            "tendencia": "mean_tendencia",
            "context_id": "n",
        })
        threats_overall["suma_norm"] = minmax(threats_overall["mean_suma"])
    
    # BY GROUP: add grupo to grouping
    group_groups = ["grupo", "amenaza_id", "tipo_amenaza", "amenaza"]
    threats_by_group = safe_group_agg(df, group_groups, agg_spec)
    
    if not threats_by_group.empty:
        threats_by_group = threats_by_group.rename(columns={
            "suma": "mean_suma",
            "magnitud": "mean_magnitud",
            "frequencia": "mean_frequencia",
            "tendencia": "mean_tendencia",
            "context_id": "n",
        })
        threats_by_group["suma_norm"] = threats_by_group.groupby("grupo")["mean_suma"].transform(
            lambda x: minmax(x)
        )
    
    logger.info(f"Threat metrics: {len(threats_overall)} overall, {len(threats_by_group)} by grupo")
    return threats_overall, threats_by_group


# ---------------------------------------------------------------------------
# IMPACT / RISK METRICS
# ---------------------------------------------------------------------------

def impact_metrics(
    tidy_amenaza_mdv: pd.DataFrame,
    threats_overall: pd.DataFrame,
    threats_by_group: pd.DataFrame,
    dim_context_geo: pd.DataFrame,
    top_n_drivers: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute impact/risk metrics by MDV and threat drivers.
    
    Args:
        tidy_amenaza_mdv: TIDY_4_2_1_AMENAZA_MDV table
        threats_overall: Threat metrics (overall)
        threats_by_group: Threat metrics (by grupo)
        dim_context_geo: Dimensional context/geo table
        top_n_drivers: Number of top drivers to include per MDV
        
    Returns:
        Tuple of:
        - risk_by_mdv_overall
        - risk_by_mdv_group
        - top_threat_drivers_overall
        - top_threat_drivers_by_group
    """
    empty_risk = pd.DataFrame(columns=[
        "mdv_id", "mdv_name", "sum_weighted_impact", "mean_weighted_impact", "n_rows", "risk_norm"
    ])
    empty_drivers = pd.DataFrame(columns=[
        "mdv_id", "mdv_name", "amenaza_id", "amenaza", "sum_weighted_impact", "driver_rank"
    ])
    
    if tidy_amenaza_mdv.empty:
        logger.warning("Empty TIDY_4_2_1_AMENAZA_MDV, returning empty impact metrics")
        return empty_risk, empty_risk.copy(), empty_drivers, empty_drivers.copy()
    
    # Attach geo columns
    df = attach_geo(tidy_amenaza_mdv, dim_context_geo, on="context_id")
    
    # Coerce impact columns to numeric
    df = coerce_numeric_columns(df, IMPACT_COLS)
    
    # Compute total impact (sum of impact dimensions)
    impact_cols_present = [c for c in IMPACT_COLS if c in df.columns]
    df["impact_total"] = df[impact_cols_present].sum(axis=1, skipna=True)
    
    # Join threat severity for weighted impact
    # For overall: join on amenaza_id
    if not threats_overall.empty and "amenaza_id" in threats_overall.columns:
        threat_lookup = threats_overall[["amenaza_id", "suma_norm"]].drop_duplicates()
        df = safe_merge(df, threat_lookup, on="amenaza_id", how="left")
        df["suma_norm"] = df["suma_norm"].fillna(0.5)  # Default to mid if missing
    else:
        df["suma_norm"] = 0.5
    
    # Compute weighted impact
    df["weighted_impact"] = df["impact_total"] * df["suma_norm"]
    
    # -------------------------------------------------------------------------
    # RISK BY MDV - OVERALL
    # -------------------------------------------------------------------------
    risk_agg_spec = {
        "weighted_impact": ["sum", "mean"],
        "impact_total": "count",
    }
    
    risk_overall = df.groupby(["mdv_id", "mdv_name"], dropna=False).agg(risk_agg_spec).reset_index()
    risk_overall.columns = ["mdv_id", "mdv_name", "sum_weighted_impact", "mean_weighted_impact", "n_rows"]
    
    if not risk_overall.empty:
        risk_overall["risk_norm"] = minmax(risk_overall["sum_weighted_impact"])
    
    # -------------------------------------------------------------------------
    # RISK BY MDV - BY GROUP
    # -------------------------------------------------------------------------
    if "grupo" in df.columns:
        risk_by_group = df.groupby(["grupo", "mdv_id", "mdv_name"], dropna=False).agg(risk_agg_spec).reset_index()
        risk_by_group.columns = ["grupo", "mdv_id", "mdv_name", "sum_weighted_impact", "mean_weighted_impact", "n_rows"]
        
        if not risk_by_group.empty:
            risk_by_group["risk_norm"] = risk_by_group.groupby("grupo")["sum_weighted_impact"].transform(
                lambda x: minmax(x)
            )
    else:
        risk_by_group = empty_risk.copy()
    
    # -------------------------------------------------------------------------
    # TOP THREAT DRIVERS - OVERALL
    # -------------------------------------------------------------------------
    driver_agg = df.groupby(["mdv_id", "mdv_name", "amenaza_id", "amenaza"], dropna=False).agg({
        "weighted_impact": "sum"
    }).reset_index()
    driver_agg = driver_agg.rename(columns={"weighted_impact": "sum_weighted_impact"})
    
    # Rank within each MDV
    driver_agg["driver_rank"] = driver_agg.groupby(["mdv_id"])["sum_weighted_impact"].rank(
        ascending=False, method="first"
    )
    
    # Keep top N drivers
    drivers_overall = driver_agg[driver_agg["driver_rank"] <= top_n_drivers].copy()
    drivers_overall = drivers_overall.sort_values(["mdv_id", "driver_rank"])
    
    # -------------------------------------------------------------------------
    # TOP THREAT DRIVERS - BY GROUP
    # -------------------------------------------------------------------------
    if "grupo" in df.columns:
        driver_agg_group = df.groupby(
            ["grupo", "mdv_id", "mdv_name", "amenaza_id", "amenaza"], dropna=False
        ).agg({"weighted_impact": "sum"}).reset_index()
        driver_agg_group = driver_agg_group.rename(columns={"weighted_impact": "sum_weighted_impact"})
        
        driver_agg_group["driver_rank"] = driver_agg_group.groupby(
            ["grupo", "mdv_id"]
        )["sum_weighted_impact"].rank(ascending=False, method="first")
        
        drivers_by_group = driver_agg_group[driver_agg_group["driver_rank"] <= top_n_drivers].copy()
        drivers_by_group = drivers_by_group.sort_values(["grupo", "mdv_id", "driver_rank"])
    else:
        drivers_by_group = empty_drivers.copy()
    
    logger.info(
        f"Impact metrics: {len(risk_overall)} risk overall, {len(risk_by_group)} by grupo, "
        f"{len(drivers_overall)} drivers overall, {len(drivers_by_group)} drivers by grupo"
    )
    
    return risk_overall, risk_by_group, drivers_overall, drivers_by_group


# ---------------------------------------------------------------------------
# CAPACITY METRICS
# ---------------------------------------------------------------------------

def capacity_metrics(
    tidy_respondents: pd.DataFrame,
    tidy_responses: pd.DataFrame,
    lookup_questions: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Compute adaptive capacity metrics from survey responses.
    
    Args:
        tidy_respondents: TIDY_7_1_RESPONDENTS with respondent_id, mdv_id, grupo, etc.
        tidy_responses: TIDY_7_1_RESPONSES with response_id, respondent_id, question_id, response_raw
        lookup_questions: LOOKUP_CA_QUESTIONS with question_id, question_text
        
    Returns:
        Tuple of:
        - capacity_overall_by_mdv
        - capacity_by_group_by_mdv
        - capacity_overall_questions (lowest scoring questions)
        - capacity_by_group_questions
    """
    empty_mdv = pd.DataFrame(columns=[
        "mdv_id", "mdv_name", "mean_response_0_1", "n_responses", "capacity_gap", "cap_gap_norm"
    ])
    empty_questions = pd.DataFrame(columns=[
        "question_id", "question_text", "mean_response_0_1", "n_responses"
    ])
    
    if tidy_responses.empty or tidy_respondents.empty:
        logger.warning("Empty survey data, returning empty capacity metrics")
        return empty_mdv, empty_mdv.copy(), empty_questions, empty_questions.copy()
    
    # Compute numeric responses
    responses = compute_response_numeric(tidy_responses)
    
    # Join respondent info to get mdv_id and grupo
    resp_cols = ["respondent_id", "mdv_id", "mdv_name", "grupo"]
    resp_cols_present = [c for c in resp_cols if c in tidy_respondents.columns]
    
    df = responses.merge(
        tidy_respondents[resp_cols_present].drop_duplicates(),
        on="respondent_id",
        how="left"
    )
    
    # Join question info
    if not lookup_questions.empty and "question_id" in df.columns:
        q_cols = ["question_id", "question_text", "question_order"]
        q_cols_present = [c for c in q_cols if c in lookup_questions.columns]
        df = df.merge(lookup_questions[q_cols_present].drop_duplicates(), on="question_id", how="left")
    
    # -------------------------------------------------------------------------
    # CAPACITY BY MDV - OVERALL
    # -------------------------------------------------------------------------
    cap_by_mdv = df.groupby(["mdv_id", "mdv_name"], dropna=False).agg({
        "response_0_1": ["mean", "count"]
    }).reset_index()
    cap_by_mdv.columns = ["mdv_id", "mdv_name", "mean_response_0_1", "n_responses"]
    
    if not cap_by_mdv.empty:
        cap_by_mdv["capacity_gap"] = 1 - cap_by_mdv["mean_response_0_1"]
        cap_by_mdv["cap_gap_norm"] = minmax(cap_by_mdv["capacity_gap"])
    
    # -------------------------------------------------------------------------
    # CAPACITY BY MDV - BY GROUP
    # -------------------------------------------------------------------------
    if "grupo" in df.columns:
        cap_by_group_mdv = df.groupby(["grupo", "mdv_id", "mdv_name"], dropna=False).agg({
            "response_0_1": ["mean", "count"]
        }).reset_index()
        cap_by_group_mdv.columns = ["grupo", "mdv_id", "mdv_name", "mean_response_0_1", "n_responses"]
        
        if not cap_by_group_mdv.empty:
            cap_by_group_mdv["capacity_gap"] = 1 - cap_by_group_mdv["mean_response_0_1"]
            cap_by_group_mdv["cap_gap_norm"] = cap_by_group_mdv.groupby("grupo")["capacity_gap"].transform(
                lambda x: minmax(x)
            )
    else:
        cap_by_group_mdv = empty_mdv.copy()
    
    # -------------------------------------------------------------------------
    # CAPACITY BY QUESTION - OVERALL (lowest scoring = bottlenecks)
    # -------------------------------------------------------------------------
    q_cols_group = ["question_id"]
    if "question_text" in df.columns:
        q_cols_group.append("question_text")
    if "question_order" in df.columns:
        q_cols_group.append("question_order")
    
    cap_questions = df.groupby(q_cols_group, dropna=False).agg({
        "response_0_1": ["mean", "count"]
    }).reset_index()
    
    # Flatten columns
    new_cols = list(q_cols_group) + ["mean_response_0_1", "n_responses"]
    cap_questions.columns = new_cols
    
    # Sort by lowest score (biggest bottleneck)
    cap_questions = cap_questions.sort_values("mean_response_0_1", ascending=True)
    
    # -------------------------------------------------------------------------
    # CAPACITY BY QUESTION - BY GROUP
    # -------------------------------------------------------------------------
    if "grupo" in df.columns:
        q_cols_group_with_grupo = ["grupo"] + q_cols_group
        cap_questions_group = df.groupby(q_cols_group_with_grupo, dropna=False).agg({
            "response_0_1": ["mean", "count"]
        }).reset_index()
        
        new_cols_group = q_cols_group_with_grupo + ["mean_response_0_1", "n_responses"]
        cap_questions_group.columns = new_cols_group
        cap_questions_group = cap_questions_group.sort_values(
            ["grupo", "mean_response_0_1"], ascending=[True, True]
        )
    else:
        cap_questions_group = empty_questions.copy()
    
    logger.info(
        f"Capacity metrics: {len(cap_by_mdv)} by MDV overall, "
        f"{len(cap_by_group_mdv)} by MDV by grupo, {len(cap_questions)} questions"
    )
    
    return cap_by_mdv, cap_by_group_mdv, cap_questions, cap_questions_group


# ---------------------------------------------------------------------------
# ACTION PRIORITY INDEX (API)
# ---------------------------------------------------------------------------

def action_priority_index(
    priority_overall: pd.DataFrame,
    priority_by_group: pd.DataFrame,
    risk_overall: pd.DataFrame,
    risk_by_group: pd.DataFrame,
    capacity_overall: pd.DataFrame,
    capacity_by_group: pd.DataFrame,
    weight_scenarios: Optional[Dict[str, Dict[str, float]]] = None,
    top_n: int = 10,
) -> Dict[str, pd.DataFrame]:
    """
    Compute Action Priority Index (API) rankings for each weight scenario.
    
    API = w_priority * priority_norm + w_risk * risk_norm + w_capacity_gap * cap_gap_norm
    
    Args:
        priority_overall: Priority metrics (overall)
        priority_by_group: Priority metrics (by grupo)
        risk_overall: Risk metrics (overall)
        risk_by_group: Risk metrics (by grupo)
        capacity_overall: Capacity metrics (overall)
        capacity_by_group: Capacity metrics (by grupo)
        weight_scenarios: Dict of scenario_name -> weight dict
        top_n: Number of top livelihoods to include in rankings
        
    Returns:
        Dict mapping table name to DataFrame:
        - rankings_overall_{scenario}: Overall rankings for each scenario
        - rankings_by_group_{scenario}: By-group rankings for each scenario
    """
    if weight_scenarios is None:
        weight_scenarios = load_weight_scenarios()
    
    results: Dict[str, pd.DataFrame] = {}
    
    # Build master mdv_id -> mdv_name lookup from all sources
    mdv_name_lookup = {}
    for df in [priority_overall, priority_by_group, risk_overall, risk_by_group, 
               capacity_overall, capacity_by_group]:
        if not df.empty and "mdv_id" in df.columns and "mdv_name" in df.columns:
            for _, row in df[["mdv_id", "mdv_name"]].drop_duplicates().iterrows():
                if pd.notna(row["mdv_id"]) and pd.notna(row["mdv_name"]) and row["mdv_name"]:
                    mdv_name_lookup[row["mdv_id"]] = row["mdv_name"]
    
    def fill_missing_names(df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing mdv_name values from the lookup."""
        if "mdv_name" in df.columns and "mdv_id" in df.columns:
            mask = df["mdv_name"].isna() | (df["mdv_name"] == "")
            df.loc[mask, "mdv_name"] = df.loc[mask, "mdv_id"].map(mdv_name_lookup)
            # If still missing, use mdv_id as fallback
            mask = df["mdv_name"].isna() | (df["mdv_name"] == "")
            df.loc[mask, "mdv_name"] = df.loc[mask, "mdv_id"].astype(str)
        return df
    
    # -------------------------------------------------------------------------
    # OVERALL RANKINGS
    # -------------------------------------------------------------------------
    # Merge priority, risk, capacity on mdv_id
    if not priority_overall.empty:
        overall = priority_overall[["mdv_id", "mdv_name", "priority_norm"]].copy()
        
        if not risk_overall.empty:
            # Also include mdv_name from risk table in case priority is missing it
            risk_cols = ["mdv_id", "risk_norm"]
            if "mdv_name" in risk_overall.columns:
                risk_cols.append("mdv_name")
            risk_merge = risk_overall[risk_cols].copy()
            if "mdv_name" in risk_merge.columns:
                risk_merge = risk_merge.rename(columns={"mdv_name": "mdv_name_risk"})
            overall = overall.merge(risk_merge, on="mdv_id", how="outer")
            # Fill missing mdv_name from risk
            if "mdv_name_risk" in overall.columns:
                mask = overall["mdv_name"].isna() | (overall["mdv_name"] == "")
                overall.loc[mask, "mdv_name"] = overall.loc[mask, "mdv_name_risk"]
                overall = overall.drop(columns=["mdv_name_risk"])
        else:
            overall["risk_norm"] = 0.5
        
        if not capacity_overall.empty:
            # Also include mdv_name from capacity table
            cap_cols = ["mdv_id", "cap_gap_norm"]
            if "mdv_name" in capacity_overall.columns:
                cap_cols.append("mdv_name")
            cap_merge = capacity_overall[cap_cols].copy()
            if "mdv_name" in cap_merge.columns:
                cap_merge = cap_merge.rename(columns={"mdv_name": "mdv_name_cap"})
            overall = overall.merge(cap_merge, on="mdv_id", how="outer")
            # Fill missing mdv_name from capacity
            if "mdv_name_cap" in overall.columns:
                mask = overall["mdv_name"].isna() | (overall["mdv_name"] == "")
                overall.loc[mask, "mdv_name"] = overall.loc[mask, "mdv_name_cap"]
                overall = overall.drop(columns=["mdv_name_cap"])
        else:
            overall["cap_gap_norm"] = 0.5
        
        # Fill remaining missing names from master lookup
        overall = fill_missing_names(overall)
        
        # Fill NaN with midpoint
        overall["priority_norm"] = overall["priority_norm"].fillna(0.5)
        overall["risk_norm"] = overall["risk_norm"].fillna(0.5)
        overall["cap_gap_norm"] = overall["cap_gap_norm"].fillna(0.5)
        
        # Compute API for each scenario
        for scenario_name, weights in weight_scenarios.items():
            w_p = weights["w_priority"]
            w_r = weights["w_risk"]
            w_c = weights["w_capacity_gap"]
            
            overall[f"api_{scenario_name}"] = (
                w_p * overall["priority_norm"] +
                w_r * overall["risk_norm"] +
                w_c * overall["cap_gap_norm"]
            )
        
        # Create separate ranking tables for each scenario
        for scenario_name in weight_scenarios.keys():
            api_col = f"api_{scenario_name}"
            ranking = overall.sort_values(api_col, ascending=False).head(top_n).copy()
            ranking["rank"] = range(1, len(ranking) + 1)
            ranking = ranking[["rank", "mdv_id", "mdv_name", "priority_norm", "risk_norm", "cap_gap_norm", api_col]]
            ranking = ranking.rename(columns={api_col: "api_score"})
            ranking["scenario"] = scenario_name
            results[f"rankings_overall_{scenario_name}"] = ranking
    
    # -------------------------------------------------------------------------
    # BY GROUP RANKINGS
    # -------------------------------------------------------------------------
    if not priority_by_group.empty and "grupo" in priority_by_group.columns:
        by_group = priority_by_group[["grupo", "mdv_id", "mdv_name", "priority_norm"]].copy()
        
        if not risk_by_group.empty and "grupo" in risk_by_group.columns:
            # Also include mdv_name from risk table
            risk_cols = ["grupo", "mdv_id", "risk_norm"]
            if "mdv_name" in risk_by_group.columns:
                risk_cols.append("mdv_name")
            risk_merge = risk_by_group[risk_cols].copy()
            if "mdv_name" in risk_merge.columns:
                risk_merge = risk_merge.rename(columns={"mdv_name": "mdv_name_risk"})
            by_group = by_group.merge(risk_merge, on=["grupo", "mdv_id"], how="outer")
            # Fill missing mdv_name from risk
            if "mdv_name_risk" in by_group.columns:
                mask = by_group["mdv_name"].isna() | (by_group["mdv_name"] == "")
                by_group.loc[mask, "mdv_name"] = by_group.loc[mask, "mdv_name_risk"]
                by_group = by_group.drop(columns=["mdv_name_risk"])
        else:
            by_group["risk_norm"] = 0.5
        
        if not capacity_by_group.empty and "grupo" in capacity_by_group.columns:
            # Also include mdv_name from capacity table
            cap_cols = ["grupo", "mdv_id", "cap_gap_norm"]
            if "mdv_name" in capacity_by_group.columns:
                cap_cols.append("mdv_name")
            cap_merge = capacity_by_group[cap_cols].copy()
            if "mdv_name" in cap_merge.columns:
                cap_merge = cap_merge.rename(columns={"mdv_name": "mdv_name_cap"})
            by_group = by_group.merge(cap_merge, on=["grupo", "mdv_id"], how="outer")
            # Fill missing mdv_name from capacity
            if "mdv_name_cap" in by_group.columns:
                mask = by_group["mdv_name"].isna() | (by_group["mdv_name"] == "")
                by_group.loc[mask, "mdv_name"] = by_group.loc[mask, "mdv_name_cap"]
                by_group = by_group.drop(columns=["mdv_name_cap"])
        else:
            by_group["cap_gap_norm"] = 0.5
        
        # Fill remaining missing names from master lookup
        by_group = fill_missing_names(by_group)
        
        # Fill NaN
        by_group["priority_norm"] = by_group["priority_norm"].fillna(0.5)
        by_group["risk_norm"] = by_group["risk_norm"].fillna(0.5)
        by_group["cap_gap_norm"] = by_group["cap_gap_norm"].fillna(0.5)
        
        # Compute API for each scenario
        for scenario_name, weights in weight_scenarios.items():
            w_p = weights["w_priority"]
            w_r = weights["w_risk"]
            w_c = weights["w_capacity_gap"]
            
            by_group[f"api_{scenario_name}"] = (
                w_p * by_group["priority_norm"] +
                w_r * by_group["risk_norm"] +
                w_c * by_group["cap_gap_norm"]
            )
        
        # Create separate ranking tables for each scenario, within each grupo
        for scenario_name in weight_scenarios.keys():
            api_col = f"api_{scenario_name}"
            
            # Rank within each grupo
            by_group["rank"] = by_group.groupby("grupo")[api_col].rank(
                ascending=False, method="first"
            )
            
            ranking = by_group[by_group["rank"] <= top_n].copy()
            ranking = ranking.sort_values(["grupo", "rank"])
            ranking = ranking[["grupo", "rank", "mdv_id", "mdv_name", "priority_norm", "risk_norm", "cap_gap_norm", api_col]]
            ranking = ranking.rename(columns={api_col: "api_score"})
            ranking["scenario"] = scenario_name
            results[f"rankings_by_group_{scenario_name}"] = ranking
    
    logger.info(f"Generated API rankings for {len(weight_scenarios)} scenarios")
    return results


# ---------------------------------------------------------------------------
# MAIN METRICS PIPELINE
# ---------------------------------------------------------------------------

def compute_all_metrics(
    tables: Dict[str, pd.DataFrame],
    top_n: int = 10,
    top_n_drivers: int = 5,
) -> Dict[str, pd.DataFrame]:
    """
    Compute all Storyline 1 metrics from loaded tables.
    
    Args:
        tables: Dict of table_name -> DataFrame (from io.load_tables)
        top_n: Number of top items for rankings
        top_n_drivers: Number of top threat drivers per MDV
        
    Returns:
        Dict of all output tables
    """
    results: Dict[str, pd.DataFrame] = {}
    
    # Build dimensional context-geo table
    dim_context_geo = build_dim_context_geo(
        tables.get("LOOKUP_CONTEXT", pd.DataFrame()),
        tables.get("LOOKUP_GEO", pd.DataFrame()),
    )
    results["dim_context_geo"] = dim_context_geo
    
    # Priority metrics (now returns 3 tables: overall, by_group, field_ranking)
    priority_overall, priority_by_group, priority_field_ranking = priority_metrics(
        tables.get("TIDY_3_2_PRIORIZACION", pd.DataFrame()),
        dim_context_geo,
    )
    results["priority_by_mdv_overall"] = priority_overall
    results["priority_by_mdv_group"] = priority_by_group
    results["priority_field_ranking"] = priority_field_ranking
    
    # Threat metrics
    threats_overall, threats_by_group = threat_metrics(
        tables.get("TIDY_4_1_AMENAZAS", pd.DataFrame()),
        dim_context_geo,
    )
    results["threats_overall"] = threats_overall
    results["threats_by_group"] = threats_by_group
    
    # Impact/Risk metrics
    risk_overall, risk_by_group, drivers_overall, drivers_by_group = impact_metrics(
        tables.get("TIDY_4_2_1_AMENAZA_MDV", pd.DataFrame()),
        threats_overall,
        threats_by_group,
        dim_context_geo,
        top_n_drivers=top_n_drivers,
    )
    results["risk_by_mdv_overall"] = risk_overall
    results["risk_by_mdv_group"] = risk_by_group
    results["top_threat_drivers_overall"] = drivers_overall
    results["top_threat_drivers_by_group"] = drivers_by_group
    
    # Capacity metrics
    cap_overall, cap_by_group, cap_q_overall, cap_q_by_group = capacity_metrics(
        tables.get("TIDY_7_1_RESPONDENTS", pd.DataFrame()),
        tables.get("TIDY_7_1_RESPONSES", pd.DataFrame()),
        tables.get("LOOKUP_CA_QUESTIONS", pd.DataFrame()),
    )
    results["capacity_overall_by_mdv"] = cap_overall
    results["capacity_by_group_by_mdv"] = cap_by_group
    results["capacity_overall_questions"] = cap_q_overall
    results["capacity_by_group_questions"] = cap_q_by_group
    
    # Action Priority Index rankings
    api_results = action_priority_index(
        priority_overall,
        priority_by_group,
        risk_overall,
        risk_by_group,
        cap_overall,
        cap_by_group,
        top_n=top_n,
    )
    results.update(api_results)
    
    logger.info(f"Computed {len(results)} output tables")
    return results
