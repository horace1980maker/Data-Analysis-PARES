"""
Metrics computation module for Storyline 5.
Computes minimal indices locally when storyline outputs are not provided.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import (
    CONTEXT_ID_COL,
    GEO_ID_COL,
    GRUPO_COL,
    IMPACT_COLS_V1,
    IMPACT_COLS_V2,
    MDV_ID_CANDIDATES,
    MDV_NAME_CANDIDATES,
    PRIORITY_CANDIDATES,
    SE_CODE_CANDIDATES,
    SUMA_CANDIDATES,
    THREAT_ID_CANDIDATES,
    THREAT_NAME_CANDIDATES,
    ACTOR_NAME_CANDIDATES,
    DIALOGO_NAME_CANDIDATES,
    DIF_GROUP_CANDIDATES,
    BARRIERS_CANDIDATES,
    INCLUSION_CANDIDATES,
    REL_TYPE_CANDIDATES,
    YEAR_CANDIDATES,
)
from .transforms import (
    attach_geo,
    canonical_text,
    coerce_numeric,
    minmax,
    pick_first_existing_col,
    safe_group_agg,
    frequency_table,
    join_as_text,
    normalize_within_group,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DIM_CONTEXT_GEO BUILDER
# =============================================================================

def build_dim_context_geo(
    lookup_context: pd.DataFrame,
    lookup_geo: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the dimension table joining LOOKUP_CONTEXT to LOOKUP_GEO.
    
    Args:
        lookup_context: LOOKUP_CONTEXT table
        lookup_geo: LOOKUP_GEO table
        
    Returns:
        DIM_CONTEXT_GEO with context_id, geo_id, admin0, paisaje, grupo, fecha_iso
    """
    if lookup_context.empty:
        logger.warning("LOOKUP_CONTEXT is empty, DIM_CONTEXT_GEO will be empty")
        return pd.DataFrame()
    
    context = lookup_context.copy()
    
    # Ensure context_id and geo_id exist
    if CONTEXT_ID_COL not in context.columns:
        logger.warning(f"Column {CONTEXT_ID_COL} not in LOOKUP_CONTEXT")
        return pd.DataFrame()
    
    if lookup_geo.empty:
        logger.warning("LOOKUP_GEO is empty, returning context only")
        return context
    
    geo = lookup_geo.copy()
    
    if GEO_ID_COL not in context.columns or GEO_ID_COL not in geo.columns:
        logger.warning(f"Cannot join: {GEO_ID_COL} missing in one of the tables")
        return context
    
    # Normalize join keys
    context[GEO_ID_COL] = context[GEO_ID_COL].astype(str)
    geo[GEO_ID_COL] = geo[GEO_ID_COL].astype(str)
    
    # Select relevant columns from geo
    geo_cols = [c for c in [GEO_ID_COL, "admin0", "paisaje", GRUPO_COL] if c in geo.columns]
    geo_subset = geo[geo_cols].drop_duplicates(subset=[GEO_ID_COL])
    
    # Join
    result = context.merge(geo_subset, on=GEO_ID_COL, how="left")
    
    logger.info(f"Built DIM_CONTEXT_GEO: {len(result)} rows")
    return result


# =============================================================================
# IMPACT POTENTIAL (API) - from Storyline 1
# =============================================================================

def compute_API_mdv(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute impact potential (API-like) index at MdV level.
    
    Components:
    - Priority: from TIDY_3_2_PRIORIZACION (mean i_total)
    - Risk: from TIDY_4_2_1_AMENAZA_MDV (impact_total, weighted by threat severity)
    - Capacity gap: from survey responses (1 - mean response_0_1)
    
    Args:
        tables: Dict of loaded tables
        dim_context_geo: Dimension table
        params: Pipeline parameters
        
    Returns:
        Dict with:
        - IMPACT_POTENTIAL_BY_MDV: overall by mdv
        - IMPACT_POTENTIAL_BY_GRUPO_BY_MDV: by grupo and mdv
        - DRIVER_THREATS_OVERALL: top threats per mdv
        - DRIVER_THREATS_BY_GRUPO: top threats per mdv per grupo
    """
    result = {}
    local_weights = params.get("local_weights", {})
    w_priority = local_weights.get("w_priority", 0.40)
    w_risk = local_weights.get("w_risk", 0.40)
    w_capacity = local_weights.get("w_capacity_gap", 0.20)
    
    # --- PRIORITY from TIDY_3_2_PRIORIZACION ---
    priority_df = tables.get("TIDY_3_2_PRIORIZACION", pd.DataFrame())
    mdv_id_col = pick_first_existing_col(priority_df, MDV_ID_CANDIDATES)
    mdv_name_col = pick_first_existing_col(priority_df, MDV_NAME_CANDIDATES)
    priority_col = pick_first_existing_col(priority_df, PRIORITY_CANDIDATES)
    
    priority_by_mdv = pd.DataFrame()
    if not priority_df.empty and mdv_id_col:
        priority_df = attach_geo(priority_df, dim_context_geo)
        priority_df = coerce_numeric(priority_df, [priority_col] if priority_col else [])
        
        # Aggregate priority by mdv
        agg_cols = {}
        if priority_col:
            agg_cols[priority_col] = "mean"
        
        priority_by_mdv = safe_group_agg(
            priority_df,
            [mdv_id_col] + ([mdv_name_col] if mdv_name_col else []),
            agg_cols
        )
        if priority_col and priority_col in priority_by_mdv.columns:
            priority_by_mdv = priority_by_mdv.rename(columns={priority_col: "priority_raw"})
        else:
            priority_by_mdv["priority_raw"] = 0.5
        
        logger.info(f"Computed priority for {len(priority_by_mdv)} MdV")
    else:
        logger.warning("Could not compute priority (missing TIDY_3_2_PRIORIZACION or mdv_id column)")
    
    # --- RISK from TIDY_4_2_1_AMENAZA_MDV ---
    threat_mdv_df = tables.get("TIDY_4_2_1_AMENAZA_MDV", pd.DataFrame())
    threats_df = tables.get("TIDY_4_1_AMENAZAS", pd.DataFrame())
    
    risk_by_mdv = pd.DataFrame()
    driver_threats = pd.DataFrame()
    
    if not threat_mdv_df.empty:
        threat_mdv_df = threat_mdv_df.copy()
        threat_mdv_df = attach_geo(threat_mdv_df, dim_context_geo)
        
        mdv_id_col_risk = pick_first_existing_col(threat_mdv_df, MDV_ID_CANDIDATES)
        threat_id_col = pick_first_existing_col(threat_mdv_df, THREAT_ID_CANDIDATES)
        suma_col = pick_first_existing_col(threat_mdv_df, SUMA_CANDIDATES)
        
        # Find impact columns
        impact_cols = [c for c in IMPACT_COLS_V1 + IMPACT_COLS_V2 if c in threat_mdv_df.columns]
        if impact_cols:
            threat_mdv_df = coerce_numeric(threat_mdv_df, impact_cols)
            threat_mdv_df["impact_total"] = threat_mdv_df[impact_cols].sum(axis=1, skipna=True)
        elif suma_col:
            threat_mdv_df = coerce_numeric(threat_mdv_df, [suma_col])
            threat_mdv_df["impact_total"] = threat_mdv_df[suma_col]
        else:
            threat_mdv_df["impact_total"] = 1.0
        
        if mdv_id_col_risk:
            # Risk by mdv = sum of impact_total
            risk_by_mdv = threat_mdv_df.groupby(mdv_id_col_risk, as_index=False).agg(
                risk_raw=("impact_total", "sum"),
                n_threats=("impact_total", "count")
            )
            logger.info(f"Computed risk for {len(risk_by_mdv)} MdV")
            
            # Driver threats: top threats per mdv
            if threat_id_col:
                threat_name_col = pick_first_existing_col(threat_mdv_df, THREAT_NAME_CANDIDATES)
                driver_threats = threat_mdv_df.nlargest(50, "impact_total")[
                    [mdv_id_col_risk, threat_id_col] + 
                    ([threat_name_col] if threat_name_col else []) +
                    ["impact_total"]
                ].copy()
                driver_threats = driver_threats.rename(columns={mdv_id_col_risk: "mdv_id"})
    else:
        logger.warning("Could not compute risk (missing TIDY_4_2_1_AMENAZA_MDV)")
    
    # --- CAPACITY GAP from surveys ---
    responses_df = tables.get("TIDY_7_1_RESPONSES", pd.DataFrame())
    capacity_by_mdv = pd.DataFrame()
    
    if not responses_df.empty:
        responses_df = responses_df.copy()
        mdv_id_col_cap = pick_first_existing_col(responses_df, MDV_ID_CANDIDATES)
        
        if mdv_id_col_cap and "response" in responses_df.columns:
            responses_df["response_numeric"] = pd.to_numeric(responses_df["response"], errors="coerce")
            responses_df["response_0_1"] = minmax(responses_df["response_numeric"])
            
            capacity_by_mdv = responses_df.groupby(mdv_id_col_cap, as_index=False).agg(
                mean_response=("response_0_1", "mean")
            )
            capacity_by_mdv["capacity_gap"] = 1 - capacity_by_mdv["mean_response"].fillna(0.5)
            logger.info(f"Computed capacity gap for {len(capacity_by_mdv)} MdV")
    else:
        logger.debug("Survey responses not available, using default capacity gap")
    
    # --- Combine into impact potential ---
    # Start with priority or risk as base (preference: priority)
    if not priority_by_mdv.empty and mdv_id_col:
        base_df = priority_by_mdv.copy()
        base_df = base_df.rename(columns={mdv_id_col: "mdv_id"})
        if mdv_name_col and mdv_name_col in base_df.columns:
            base_df = base_df.rename(columns={mdv_name_col: "mdv_name"})
    elif not risk_by_mdv.empty:
        base_df = risk_by_mdv.copy()
        base_df["priority_raw"] = 0.5
    else:
        # Create empty result
        logger.warning("No data to compute impact potential")
        result["IMPACT_POTENTIAL_BY_MDV"] = pd.DataFrame()
        result["IMPACT_POTENTIAL_BY_GRUPO_BY_MDV"] = pd.DataFrame()
        result["DRIVER_THREATS_OVERALL"] = pd.DataFrame()
        result["DRIVER_THREATS_BY_GRUPO"] = pd.DataFrame()
        return result
    
    # Merge risk if available
    if not risk_by_mdv.empty and mdv_id_col_risk:
        risk_rename = risk_by_mdv.rename(columns={mdv_id_col_risk: "mdv_id"})
        base_df = base_df.merge(risk_rename[["mdv_id", "risk_raw", "n_threats"]], on="mdv_id", how="left")
    else:
        base_df["risk_raw"] = 0.5
        base_df["n_threats"] = 0
    
    # Merge capacity gap if available
    if not capacity_by_mdv.empty:
        cap_rename = capacity_by_mdv.rename(columns={mdv_id_col_cap: "mdv_id"}) if mdv_id_col_cap else capacity_by_mdv
        base_df = base_df.merge(cap_rename[["mdv_id", "capacity_gap"]], on="mdv_id", how="left")
    else:
        base_df["capacity_gap"] = 0.5
    
    # Normalize components
    base_df["priority_norm"] = minmax(base_df["priority_raw"].fillna(0))
    base_df["risk_norm"] = minmax(base_df["risk_raw"].fillna(0))
    base_df["capacity_gap"] = base_df["capacity_gap"].fillna(0.5)
    
    # Compute composite
    base_df["impact_potential"] = (
        w_priority * base_df["priority_norm"] +
        w_risk * base_df["risk_norm"] +
        w_capacity * base_df["capacity_gap"]
    )
    base_df["impact_potential_norm"] = minmax(base_df["impact_potential"])
    
    result["IMPACT_POTENTIAL_BY_MDV"] = base_df
    result["DRIVER_THREATS_OVERALL"] = driver_threats
    
    # --- By grupo aggregation ---
    # Ensure priority_df has grupo attached and MDV column
    if not priority_df.empty and mdv_id_col and GRUPO_COL in priority_df.columns:
        # Get (grupo, mdv_id) pairs
        group_base = priority_df[[GRUPO_COL, mdv_id_col]].drop_duplicates()
        group_base = group_base.rename(columns={mdv_id_col: "mdv_id"})
        
        # Merge with overall base_df to ensure consistent landscape-wide scale
        # but scoped to the MdVs present in each grupo
        grupo_agg = group_base.merge(base_df, on="mdv_id", how="inner")
        result["IMPACT_POTENTIAL_BY_GRUPO_BY_MDV"] = grupo_agg
        logger.info(f"Computed IMPACT_POTENTIAL_BY_GRUPO for {len(grupo_agg)} pairs")
    else:
        result["IMPACT_POTENTIAL_BY_GRUPO_BY_MDV"] = pd.DataFrame()
    
    result["DRIVER_THREATS_BY_GRUPO"] = pd.DataFrame()  # Simplified
    
    logger.info(f"Computed IMPACT_POTENTIAL for {len(base_df)} MdV")
    return result


# =============================================================================
# SERVICE CRITICALITY INDEX (SCI) - from Storyline 2
# =============================================================================

def compute_SCI_service(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute Service Criticality Index (SCI).
    
    Components:
    - links_mdv: number of unique MdV linked to service
    - users: sum of nr_usuarios
    - seasonality: months_falta_count / 12
    - priority_weight: mean priority of linked MdV
    
    Args:
        tables: Dict of loaded tables
        dim_context_geo: Dimension table
        params: Pipeline parameters
        
    Returns:
        Dict with SCI_OVERALL and SCI_BY_GRUPO
    """
    result = {}
    local_weights = params.get("local_weights", {})
    
    se_mdv_df = tables.get("TIDY_3_5_SE_MDV", pd.DataFrame())
    
    if se_mdv_df.empty:
        logger.warning("TIDY_3_5_SE_MDV is empty, cannot compute SCI")
        result["SCI_OVERALL"] = pd.DataFrame()
        result["SCI_BY_GRUPO"] = pd.DataFrame()
        return result
    
    se_mdv_df = se_mdv_df.copy()
    se_mdv_df = attach_geo(se_mdv_df, dim_context_geo)
    
    # Identify columns
    se_col = pick_first_existing_col(se_mdv_df, SE_CODE_CANDIDATES)
    mdv_col = pick_first_existing_col(se_mdv_df, MDV_ID_CANDIDATES)
    
    if not se_col:
        logger.warning("No service column found in TIDY_3_5_SE_MDV")
        result["SCI_OVERALL"] = pd.DataFrame()
        result["SCI_BY_GRUPO"] = pd.DataFrame()
        return result
    
    # Aggregate by service
    agg_dict = {}
    if mdv_col:
        agg_dict["mdv_id"] = (mdv_col, "nunique")
    
    if "nr_usuarios" in se_mdv_df.columns:
        se_mdv_df = coerce_numeric(se_mdv_df, ["nr_usuarios"])
        agg_dict["users"] = ("nr_usuarios", "sum")
    
    # Check for months of shortage
    if "mes_falta" in se_mdv_df.columns:
        se_mdv_df["months_falta_count"] = se_mdv_df["mes_falta"].apply(
            lambda x: len(str(x).split(",")) if pd.notna(x) and str(x).strip() else 0
        )
        agg_dict["seasonality"] = ("months_falta_count", "mean")
    
    sci_overall = se_mdv_df.groupby(se_col, as_index=False).agg(**agg_dict)
    sci_overall = sci_overall.rename(columns={se_col: "se_code"})
    
    # Normalize components
    if "mdv_id" in sci_overall.columns:
        sci_overall["links_mdv_norm"] = minmax(sci_overall["mdv_id"])
    else:
        sci_overall["links_mdv_norm"] = 0.5
    
    if "users" in sci_overall.columns:
        sci_overall["users_norm"] = minmax(sci_overall["users"])
    else:
        sci_overall["users_norm"] = 0.5
    
    if "seasonality" in sci_overall.columns:
        sci_overall["seasonality_norm"] = minmax(sci_overall["seasonality"])
    else:
        sci_overall["seasonality_norm"] = 0.5
    
    # Compute SCI
    w_links = local_weights.get("w_links_mdv", 0.30)
    w_users = local_weights.get("w_users", 0.25)
    w_season = local_weights.get("w_seasonality", 0.25)
    w_priority = local_weights.get("w_priority_weight", 0.20)
    
    sci_overall["SCI"] = (
        w_links * sci_overall["links_mdv_norm"] +
        w_users * sci_overall["users_norm"] +
        w_season * sci_overall["seasonality_norm"] +
        w_priority * 0.5  # Default if priority not available
    )
    sci_overall["SCI_norm"] = minmax(sci_overall["SCI"])
    
    result["SCI_OVERALL"] = sci_overall
    
    # By grupo
    if GRUPO_COL in se_mdv_df.columns:
        sci_by_grupo = se_mdv_df.groupby([GRUPO_COL, se_col], as_index=False).agg(**agg_dict)
        sci_by_grupo = sci_by_grupo.rename(columns={se_col: "se_code"})
        result["SCI_BY_GRUPO"] = sci_by_grupo
    else:
        result["SCI_BY_GRUPO"] = pd.DataFrame()
    
    logger.info(f"Computed SCI for {len(sci_overall)} services")
    return result


# =============================================================================
# ECOSYSTEM LEVERAGE INDEX (ELI) - from Storyline 2
# =============================================================================

def compute_ELI_ecosystem(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
    sci_overall: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """
    Compute Ecosystem Leverage Index (ELI).
    
    Components:
    - connectivity: n_services + n_livelihoods
    - critical_services_share: mean SCI of linked services
    
    Args:
        tables: Dict of loaded tables
        dim_context_geo: Dimension table
        params: Pipeline parameters
        sci_overall: Pre-computed SCI table
        
    Returns:
        Dict with ELI_OVERALL and ELI_BY_GRUPO
    """
    result = {}
    local_weights = params.get("local_weights", {})
    
    eco_se_df = tables.get("TIDY_3_4_ECO_SE", pd.DataFrame())
    eco_mdv_df = tables.get("TIDY_3_4_ECO_MDV", pd.DataFrame())
    ecosistemas_df = tables.get("TIDY_3_4_ECOSISTEMAS", pd.DataFrame())
    
    if eco_se_df.empty and ecosistemas_df.empty:
        logger.warning("No ecosystem data available, cannot compute ELI")
        result["ELI_OVERALL"] = pd.DataFrame()
        result["ELI_BY_GRUPO"] = pd.DataFrame()
        return result
    
    # Build ecosystem stats
    eco_stats = []
    
    # Get ecosystems from either source
    if not ecosistemas_df.empty:
        eco_col = pick_first_existing_col(ecosistemas_df, ["ecosistema_id", "eco_id", "ecosistema"])
        if eco_col:
            eco_list = ecosistemas_df[eco_col].dropna().unique()
        else:
            eco_list = []
    else:
        eco_col = pick_first_existing_col(eco_se_df, ["ecosistema_id", "eco_id", "ecosistema"])
        if eco_col:
            eco_list = eco_se_df[eco_col].dropna().unique()
        else:
            eco_list = []
    
    # Count services per ecosystem
    se_col = pick_first_existing_col(eco_se_df, SE_CODE_CANDIDATES) if not eco_se_df.empty else None
    eco_col_se = pick_first_existing_col(eco_se_df, ["ecosistema_id", "eco_id", "ecosistema"]) if not eco_se_df.empty else None
    
    for eco in eco_list:
        stats = {"ecosystem": eco}
        
        # Count services
        if se_col and eco_col_se:
            mask = eco_se_df[eco_col_se] == eco
            n_services = eco_se_df.loc[mask, se_col].nunique()
            stats["n_services"] = n_services
            
            # Get mean SCI of linked services
            if not sci_overall.empty and "se_code" in sci_overall.columns:
                linked_services = eco_se_df.loc[mask, se_col].unique()
                linked_sci = sci_overall[sci_overall["se_code"].isin(linked_services)]["SCI_norm"]
                stats["mean_sci"] = linked_sci.mean() if len(linked_sci) > 0 else 0.5
            else:
                stats["mean_sci"] = 0.5
        else:
            stats["n_services"] = 0
            stats["mean_sci"] = 0.5
        
        # Count livelihoods
        mdv_col = pick_first_existing_col(eco_mdv_df, MDV_ID_CANDIDATES) if not eco_mdv_df.empty else None
        eco_col_mdv = pick_first_existing_col(eco_mdv_df, ["ecosistema_id", "eco_id", "ecosistema"]) if not eco_mdv_df.empty else None
        
        if mdv_col and eco_col_mdv:
            mask = eco_mdv_df[eco_col_mdv] == eco
            stats["n_livelihoods"] = eco_mdv_df.loc[mask, mdv_col].nunique()
        else:
            stats["n_livelihoods"] = 0
        
        eco_stats.append(stats)
    
    if not eco_stats:
        result["ELI_OVERALL"] = pd.DataFrame()
        result["ELI_BY_GRUPO"] = pd.DataFrame()
        return result
    
    eli_overall = pd.DataFrame(eco_stats)
    
    # Compute connectivity
    eli_overall["connectivity"] = eli_overall["n_services"] + eli_overall["n_livelihoods"]
    eli_overall["connectivity_norm"] = minmax(eli_overall["connectivity"])
    
    # Compute ELI
    w_conn = local_weights.get("w_connectivity", 0.50)
    w_sci = local_weights.get("w_critical_services_share", 0.50)
    
    eli_overall["ELI"] = (
        w_conn * eli_overall["connectivity_norm"] +
        w_sci * eli_overall["mean_sci"]
    )
    eli_overall["ELI_norm"] = minmax(eli_overall["ELI"])
    
    result["ELI_OVERALL"] = eli_overall
    result["ELI_BY_GRUPO"] = pd.DataFrame()  # Simplified for now
    
    logger.info(f"Computed ELI for {len(eli_overall)} ecosystems")
    return result


# =============================================================================
# EQUITY VULNERABILITY INDEX (EVI) - from Storyline 3
# =============================================================================

def compute_EVI(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute Equity Vulnerability Index (EVI).
    
    Components:
    - diff_intensity: counts of differentiated impacts by grupo
    - barriers_rate: share of records with non-empty barriers
    - capacity_gap: from survey responses
    
    Args:
        tables: Dict of loaded tables
        dim_context_geo: Dimension table
        params: Pipeline parameters
        
    Returns:
        Dict with EVI_OVERALL, EVI_BY_GRUPO, and EVI evidence
    """
    result = {}
    local_weights = params.get("local_weights", {})
    
    # --- Differentiated impacts ---
    dif_df = tables.get("TIDY_4_2_1_DIFERENCIADO", pd.DataFrame())
    if dif_df.empty:
        dif_df = tables.get("TIDY_4_2_2_DIFERENCIADO", pd.DataFrame())
    
    diff_stats = pd.DataFrame()
    if not dif_df.empty:
        dif_df = attach_geo(dif_df, dim_context_geo)
        dif_group_col = pick_first_existing_col(dif_df, DIF_GROUP_CANDIDATES)
        
        if GRUPO_COL in dif_df.columns:
            diff_stats = dif_df.groupby(GRUPO_COL, as_index=False).agg(
                diff_count=("context_id", "count") if "context_id" in dif_df.columns else (dif_df.columns[0], "count"),
                n_dif_groups=(dif_group_col, "nunique") if dif_group_col else (dif_df.columns[0], "nunique")
            )
            diff_stats["diff_intensity_norm"] = minmax(diff_stats["diff_count"])
        else:
            # Overall only
            diff_stats = pd.DataFrame([{
                "diff_count": len(dif_df),
                "n_dif_groups": dif_df[dif_group_col].nunique() if dif_group_col else 0,
                "diff_intensity_norm": 0.5
            }])
    
    # --- Barriers/inclusion from TIDY_3_5_SE_MDV ---
    se_mdv_df = tables.get("TIDY_3_5_SE_MDV", pd.DataFrame())
    barriers_stats = pd.DataFrame()
    
    if not se_mdv_df.empty:
        se_mdv_df = attach_geo(se_mdv_df, dim_context_geo)
        barriers_col = pick_first_existing_col(se_mdv_df, BARRIERS_CANDIDATES)
        inclusion_col = pick_first_existing_col(se_mdv_df, INCLUSION_CANDIDATES)
        
        if barriers_col or inclusion_col:
            se_mdv_df["has_barriers"] = se_mdv_df[barriers_col].notna() & (se_mdv_df[barriers_col].astype(str).str.strip() != "") if barriers_col else False
            se_mdv_df["has_inclusion"] = se_mdv_df[inclusion_col].notna() & (se_mdv_df[inclusion_col].astype(str).str.strip() != "") if inclusion_col else False
            
            if GRUPO_COL in se_mdv_df.columns:
                barriers_stats = se_mdv_df.groupby(GRUPO_COL, as_index=False).agg(
                    barriers_rate=("has_barriers", "mean"),
                    inclusion_rate=("has_inclusion", "mean"),
                    n_records=("has_barriers", "count")
                )
            else:
                barriers_stats = pd.DataFrame([{
                    "barriers_rate": se_mdv_df["has_barriers"].mean(),
                    "inclusion_rate": se_mdv_df["has_inclusion"].mean(),
                    "n_records": len(se_mdv_df)
                }])
    
    # --- Capacity gap from surveys ---
    responses_df = tables.get("TIDY_7_1_RESPONSES", pd.DataFrame())
    capacity_stats = pd.DataFrame()
    
    if not responses_df.empty and "response" in responses_df.columns:
        responses_df = attach_geo(responses_df, dim_context_geo)
        responses_df["response_numeric"] = pd.to_numeric(responses_df["response"], errors="coerce")
        responses_df["response_0_1"] = minmax(responses_df["response_numeric"])
        
        if GRUPO_COL in responses_df.columns:
            capacity_stats = responses_df.groupby(GRUPO_COL, as_index=False).agg(
                capacity_mean=("response_0_1", "mean")
            )
            capacity_stats["capacity_gap"] = 1 - capacity_stats["capacity_mean"].fillna(0.5)
        else:
            capacity_stats = pd.DataFrame([{
                "capacity_gap": 1 - responses_df["response_0_1"].mean() if not responses_df["response_0_1"].isna().all() else 0.5
            }])
    
    # --- Combine into EVI ---
    # Use diff_stats as base if available, otherwise barriers_stats
    if not diff_stats.empty and GRUPO_COL in diff_stats.columns:
        evi_df = diff_stats.copy()
    elif not barriers_stats.empty and GRUPO_COL in barriers_stats.columns:
        evi_df = barriers_stats.copy()
        evi_df["diff_intensity_norm"] = 0.5
    else:
        # Create single row for overall
        evi_df = pd.DataFrame([{"grupo": "ALL", "diff_intensity_norm": 0.5}])
    
    # Merge barriers if available
    if not barriers_stats.empty and "barriers_rate" in barriers_stats.columns:
        if GRUPO_COL in barriers_stats.columns and GRUPO_COL in evi_df.columns:
            evi_df = evi_df.merge(
                barriers_stats[[GRUPO_COL, "barriers_rate"]], 
                on=GRUPO_COL, 
                how="left"
            )
        else:
            evi_df["barriers_rate"] = barriers_stats["barriers_rate"].iloc[0] if len(barriers_stats) > 0 else 0.5
    else:
        evi_df["barriers_rate"] = 0.5
    
    # Ensure barriers_rate column exists after merge
    if "barriers_rate" not in evi_df.columns:
        evi_df["barriers_rate"] = 0.5
    
    # Merge capacity if available
    if not capacity_stats.empty and "capacity_gap" in capacity_stats.columns:
        if GRUPO_COL in capacity_stats.columns and GRUPO_COL in evi_df.columns:
            evi_df = evi_df.merge(
                capacity_stats[[GRUPO_COL, "capacity_gap"]], 
                on=GRUPO_COL, 
                how="left"
            )
        else:
            evi_df["capacity_gap"] = capacity_stats["capacity_gap"].iloc[0] if len(capacity_stats) > 0 else 0.5
    else:
        evi_df["capacity_gap"] = 0.5
    
    # Ensure capacity_gap column exists after merge
    if "capacity_gap" not in evi_df.columns:
        evi_df["capacity_gap"] = 0.5
    
    # Normalize - ensure columns exist
    evi_df["barriers_rate"] = evi_df.get("barriers_rate", pd.Series([0.5] * len(evi_df))).fillna(0.5)
    evi_df["capacity_gap"] = evi_df.get("capacity_gap", pd.Series([0.5] * len(evi_df))).fillna(0.5)
    
    # Compute EVI
    w_diff = local_weights.get("w_diff_intensity", 0.40)
    w_barriers = local_weights.get("w_barriers_rate", 0.30)
    w_cap = local_weights.get("w_capacity_gap_equity", 0.30)
    
    evi_df["EVI"] = (
        w_diff * evi_df["diff_intensity_norm"] +
        w_barriers * evi_df["barriers_rate"] +
        w_cap * evi_df["capacity_gap"]
    )
    evi_df["EVI_norm"] = minmax(evi_df["EVI"])
    
    if GRUPO_COL in evi_df.columns:
        result["EVI_BY_GRUPO"] = evi_df
        # Overall = mean across grupos
        result["EVI_OVERALL"] = pd.DataFrame([{
            "EVI": evi_df["EVI"].mean(),
            "EVI_norm": evi_df["EVI_norm"].mean()
        }])
    else:
        result["EVI_OVERALL"] = evi_df
        result["EVI_BY_GRUPO"] = pd.DataFrame()
    
    logger.info(f"Computed EVI for {len(evi_df)} groups")
    return result


# =============================================================================
# FEASIBILITY INDEX - from Storyline 4
# =============================================================================

def compute_FEASIBILITY(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute Feasibility Index.
    
    Components:
    - network_strength: collaboration rate from actor relations
    - dialogue_coverage: count/quality of dialogue spaces
    - conflict_risk: event count normalized
    
    Args:
        tables: Dict of loaded tables
        dim_context_geo: Dimension table
        params: Pipeline parameters
        
    Returns:
        Dict with FEASIBILITY_OVERALL, FEASIBILITY_BY_GRUPO, CONFLICT_RISK_BY_GRUPO,
        and governance evidence tables
    """
    result = {}
    local_weights = params.get("local_weights", {})
    
    # --- Network strength from TIDY_5_1_RELACIONES ---
    relations_df = tables.get("TIDY_5_1_RELACIONES", pd.DataFrame())
    network_stats = pd.DataFrame()
    
    if not relations_df.empty:
        relations_df = attach_geo(relations_df, dim_context_geo)
        rel_type_col = pick_first_existing_col(relations_df, REL_TYPE_CANDIDATES)
        
        if rel_type_col:
            relations_df["is_collab"] = relations_df[rel_type_col].apply(
                lambda x: 1 if canonical_text(x) in ["colabora", "colaboracion", "cooperation", "alianza"] else 0
            )
        else:
            relations_df["is_collab"] = 0.5
        
        if GRUPO_COL in relations_df.columns:
            network_stats = relations_df.groupby(GRUPO_COL, as_index=False).agg(
                collab_rate=("is_collab", "mean"),
                n_relations=("is_collab", "count")
            )
        else:
            network_stats = pd.DataFrame([{
                "collab_rate": relations_df["is_collab"].mean(),
                "n_relations": len(relations_df)
            }])
        
        network_stats["network_strength_norm"] = minmax(network_stats["collab_rate"])
    else:
        network_stats = pd.DataFrame([{"network_strength_norm": 0.5}])
    
    # --- Dialogue coverage from TIDY_5_2_DIALOGO_ACTOR ---
    dialogo_actor_df = tables.get("TIDY_5_2_DIALOGO_ACTOR", pd.DataFrame())
    dialogo_df = tables.get("TIDY_5_2_DIALOGO", pd.DataFrame())
    dialogue_stats = pd.DataFrame()
    
    if not dialogo_df.empty:
        dialogo_df = attach_geo(dialogo_df, dim_context_geo)
        space_col = pick_first_existing_col(dialogo_df, DIALOGO_NAME_CANDIDATES)
        
        if GRUPO_COL in dialogo_df.columns and space_col:
            dialogue_stats = dialogo_df.groupby(GRUPO_COL, as_index=False).agg(
                n_spaces=(space_col, "nunique")
            )
        else:
            dialogue_stats = pd.DataFrame([{
                "n_spaces": dialogo_df[space_col].nunique() if space_col else len(dialogo_df)
            }])
        
        dialogue_stats["dialogue_coverage_norm"] = minmax(dialogue_stats["n_spaces"])
    else:
        dialogue_stats = pd.DataFrame([{"dialogue_coverage_norm": 0.5}])
    
    # --- Conflict risk from TIDY_6_1_CONFLICT_EVENTS ---
    conflicts_df = tables.get("TIDY_6_1_CONFLICT_EVENTS", pd.DataFrame())
    conflict_stats = pd.DataFrame()
    
    if not conflicts_df.empty:
        conflicts_df = attach_geo(conflicts_df, dim_context_geo)
        
        if GRUPO_COL in conflicts_df.columns:
            conflict_stats = conflicts_df.groupby(GRUPO_COL, as_index=False).agg(
                n_conflicts=("context_id", "count") if "context_id" in conflicts_df.columns else (conflicts_df.columns[0], "count")
            )
        else:
            conflict_stats = pd.DataFrame([{
                "n_conflicts": len(conflicts_df)
            }])
        
        conflict_stats["conflict_risk"] = minmax(conflict_stats["n_conflicts"])
    else:
        conflict_stats = pd.DataFrame([{"conflict_risk": 0.5}])
    
    # --- Combine into Feasibility ---
    # Start with all available groups from dim_context_geo to avoid dropping groups with partial data
    if GRUPO_COL in dim_context_geo.columns:
        all_grupos = dim_context_geo[GRUPO_COL].dropna().unique()
        if len(all_grupos) > 0:
            feas_df = pd.DataFrame({GRUPO_COL: all_grupos})
        else:
            feas_df = pd.DataFrame([{GRUPO_COL: "Zona Única"}])
    else:
        feas_df = pd.DataFrame([{GRUPO_COL: "Zona Única"}])
    
    # Merge network stats
    if not network_stats.empty:
        if GRUPO_COL in network_stats.columns:
            feas_df = feas_df.merge(
                network_stats[[GRUPO_COL, "network_strength_norm"]], 
                on=GRUPO_COL, 
                how="left"
            )
        else:
            feas_df["network_strength_norm"] = network_stats["network_strength_norm"].iloc[0]
    else:
        feas_df["network_strength_norm"] = 0.5
    
    # Merge dialogue coverage
    if not dialogue_stats.empty:
        if GRUPO_COL in dialogue_stats.columns:
            feas_df = feas_df.merge(
                dialogue_stats[[GRUPO_COL, "dialogue_coverage_norm"]], 
                on=GRUPO_COL, 
                how="left"
            )
        else:
            if "dialogue_coverage_norm" not in feas_df.columns:
                feas_df["dialogue_coverage_norm"] = dialogue_stats["dialogue_coverage_norm"].iloc[0]
    else:
        if "dialogue_coverage_norm" not in feas_df.columns:
            feas_df["dialogue_coverage_norm"] = 0.5
    
    # Merge conflict risk
    if not conflict_stats.empty:
        if GRUPO_COL in conflict_stats.columns:
            feas_df = feas_df.merge(
                conflict_stats[[GRUPO_COL, "conflict_risk"]], 
                on=GRUPO_COL, 
                how="left"
            )
        else:
            if "conflict_risk" not in feas_df.columns:
                feas_df["conflict_risk"] = conflict_stats["conflict_risk"].iloc[0]
    else:
        if "conflict_risk" not in feas_df.columns:
            feas_df["conflict_risk"] = 0.5
    
    # Fill NaNs
    feas_df["network_strength_norm"] = feas_df.get("network_strength_norm", pd.Series([0.5])).fillna(0.5)
    feas_df["dialogue_coverage_norm"] = feas_df.get("dialogue_coverage_norm", pd.Series([0.5])).fillna(0.5)
    feas_df["conflict_risk"] = feas_df.get("conflict_risk", pd.Series([0.5])).fillna(0.5)
    
    # Compute Feasibility
    w_network = local_weights.get("w_network_strength", 0.35)
    w_dialogue = local_weights.get("w_dialogue_coverage", 0.25)
    w_conflict = local_weights.get("w_conflict_risk", 0.40)
    
    feas_df["feasibility"] = (
        w_network * feas_df["network_strength_norm"] +
        w_dialogue * feas_df["dialogue_coverage_norm"] +
        w_conflict * (1 - feas_df["conflict_risk"])
    )
    feas_df["feasibility_norm"] = minmax(feas_df["feasibility"])
    
    if GRUPO_COL in feas_df.columns:
        result["FEASIBILITY_BY_GRUPO"] = feas_df
        result["CONFLICT_RISK_BY_GRUPO"] = feas_df[[GRUPO_COL, "conflict_risk"]]
        # Overall = mean across grupos
        result["FEASIBILITY_OVERALL"] = pd.DataFrame([{
            "feasibility": feas_df["feasibility"].mean(),
            "feasibility_norm": feas_df["feasibility_norm"].mean()
        }])
    else:
        result["FEASIBILITY_OVERALL"] = feas_df
        result["FEASIBILITY_BY_GRUPO"] = pd.DataFrame()
        result["CONFLICT_RISK_BY_GRUPO"] = pd.DataFrame()
    
    # --- MdV-level variation (for Portfolio spreading) ---
    feasibility_mdv = pd.DataFrame()
    mapeo_df = tables.get("TIDY_4_2_1_MAPEO_CONFLICTO", pd.DataFrame())
    amenaza_mdv_df = tables.get("TIDY_4_2_1_AMENAZA_MDV", pd.DataFrame())
    priorizacion_df = tables.get("TIDY_3_2_PRIORIZACION", pd.DataFrame())
    
    mapeo_df = tables.get("TIDY_4_2_1_MAPEO_CONFLICTO", pd.DataFrame())
    amenaza_mdv_df = tables.get("TIDY_4_2_1_AMENAZA_MDV", pd.DataFrame())
    lookup_mdv = tables.get("LOOKUP_MDV", pd.DataFrame())
    
    if not (mapeo_df.empty or amenaza_mdv_df.empty or lookup_mdv.empty):
        try:
            m = mapeo_df.copy()
            a = amenaza_mdv_df.copy()
            l = lookup_mdv.copy()
            
            # Canonicalize join keys
            m["amenaza_mdv_id"] = m["amenaza_mdv_id"].apply(canonical_text)
            a["amenaza_mdv_id"] = a["amenaza_mdv_id"].apply(canonical_text)
            a["mdv_name_norm"] = a["mdv_name"].apply(canonical_text) if "mdv_name" in a.columns else ""
            l["mdv_name_norm"] = l["mdv_name"].apply(canonical_text)
            
            # 1. Link mapeo to mdv_name (via amenaza_mdv_id)
            mdv_conflicts = m.merge(
                a[["amenaza_mdv_id", "mdv_name_norm"]], 
                on="amenaza_mdv_id", 
                how="inner"
            )
            
            # 2. Link mdv_name to mdv_id
            mdv_conflicts = mdv_conflicts.merge(
                l[["mdv_id", "mdv_name_norm"]], 
                on="mdv_name_norm", 
                how="inner"
            )
            
            # 3. Aggregate conflicts per mdv_id
            if not mdv_conflicts.empty:
                mdv_risk = mdv_conflicts.groupby("mdv_id", as_index=False).size().rename(columns={"size": "mdv_conflict_count"})
            else:
                mdv_risk = pd.DataFrame(columns=["mdv_id", "mdv_conflict_count"])
            
            # 4. Start with ALL MdVs and left-join conflict counts
            all_mdv = l[["mdv_id", "mdv_name"]].drop_duplicates()
            feasibility_mdv = all_mdv.merge(mdv_risk, on="mdv_id", how="left")
            feasibility_mdv["mdv_conflict_count"] = feasibility_mdv["mdv_conflict_count"].fillna(0)
            feasibility_mdv["mdv_conflict_risk_norm"] = minmax(feasibility_mdv["mdv_conflict_count"])
            feasibility_mdv["mdv_name_norm"] = feasibility_mdv["mdv_name"].apply(canonical_text)
            logger.info(f"Computed MdV-level conflict risk for {len(feasibility_mdv)} MdVs (all MdVs included)")

        except Exception as e:
            logger.warning(f"Could not compute MdV-level conflict risk: {e}")


    result["FEASIBILITY_BY_MDV"] = feasibility_mdv

    # --- Governance evidence ---
    # Top actors
    actors_df = tables.get("TIDY_5_1_ACTORES", pd.DataFrame())
    if not actors_df.empty:
        actor_name_col = pick_first_existing_col(actors_df, ACTOR_NAME_CANDIDATES)
        if actor_name_col:
            result["GOVERNANCE_EVIDENCE_OVERALL"] = actors_df[[actor_name_col]].head(10).rename(
                columns={actor_name_col: "top_actors"}
            )
        else:
            result["GOVERNANCE_EVIDENCE_OVERALL"] = pd.DataFrame()
    else:
        result["GOVERNANCE_EVIDENCE_OVERALL"] = pd.DataFrame()
    
    result["GOVERNANCE_EVIDENCE_BY_GRUPO"] = pd.DataFrame()
    
    logger.info(f"Computed FEASIBILITY for {len(feas_df)} groups")
    return result


# =============================================================================
# MASTER FUNCTION
# =============================================================================

def compute_all_local_metrics(
    tables: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute all local metrics if storyline outputs are not provided.
    
    Args:
        tables: Dict of loaded tables
        params: Pipeline parameters
        
    Returns:
        Dict of all computed metric tables
    """
    all_metrics = {}
    
    # Build dimension table
    dim_context_geo = build_dim_context_geo(
        tables.get("LOOKUP_CONTEXT", pd.DataFrame()),
        tables.get("LOOKUP_GEO", pd.DataFrame())
    )
    all_metrics["DIM_CONTEXT_GEO"] = dim_context_geo
    
    # Impact Potential (API)
    api_results = compute_API_mdv(tables, dim_context_geo, params)
    all_metrics.update(api_results)
    
    # Service Criticality Index (SCI)
    sci_results = compute_SCI_service(tables, dim_context_geo, params)
    all_metrics.update(sci_results)
    
    # Ecosystem Leverage Index (ELI)
    eli_results = compute_ELI_ecosystem(
        tables, 
        dim_context_geo, 
        params,
        sci_results.get("SCI_OVERALL", pd.DataFrame())
    )
    all_metrics.update(eli_results)
    
    # Equity Vulnerability Index (EVI)
    evi_results = compute_EVI(tables, dim_context_geo, params)
    all_metrics.update(evi_results)
    
    # Feasibility
    feas_results = compute_FEASIBILITY(tables, dim_context_geo, params)
    all_metrics.update(feas_results)
    
    logger.info(f"Computed {len(all_metrics)} local metric tables")
    return all_metrics
