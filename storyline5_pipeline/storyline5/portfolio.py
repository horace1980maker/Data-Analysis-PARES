"""
Portfolio construction module for Storyline 5.
Builds candidate SbN/adaptation bundles and ranks them.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import (
    GRUPO_COL,
    MDV_ID_CANDIDATES,
    MDV_NAME_CANDIDATES,
    SE_CODE_CANDIDATES,
    THREAT_ID_CANDIDATES,
    THREAT_NAME_CANDIDATES,
    TIER_DO_NOW,
    TIER_DO_NEXT,
    TIER_DO_LATER,
    STORYLINE_COMPONENTS,
)
from .transforms import (
    canonical_text,
    minmax,
    pick_first_existing_col,
    stable_hash_id,
    quantile_tier,
    join_as_text,
)

logger = logging.getLogger(__name__)


# =============================================================================
# BUNDLE CONSTRUCTION
# =============================================================================

def select_candidate_mdv(
    impact_potential_df: pd.DataFrame,
    params: Dict[str, Any],
    scope: str = "overall",
    grupo: Optional[str] = None,
) -> pd.DataFrame:
    """
    Select candidate MdV for bundle construction.
    
    Args:
        impact_potential_df: Impact potential table with mdv_id and impact_potential_norm
        params: Pipeline parameters
        scope: "overall" or "by_grupo"
        grupo: Group name if scope is "by_grupo"
        
    Returns:
        DataFrame of selected candidate MdV
    """
    if impact_potential_df.empty:
        return pd.DataFrame()
    
    df = impact_potential_df.copy()
    
    # Apply grupo filter if needed
    if scope == "by_grupo" and grupo:
        if GRUPO_COL in df.columns:
            df = df[df[GRUPO_COL] == grupo]
    
    # Sort by impact potential
    if "impact_potential_norm" in df.columns:
        df = df.sort_values("impact_potential_norm", ascending=False)
    elif "impact_potential" in df.columns:
        df = df.sort_values("impact_potential", ascending=False)
    
    # Select top N
    if scope == "overall":
        n = params.get("top_n", 10)
    else:
        n = params.get("bundles_per_grupo", 5)
    
    return df.head(n)


def enrich_bundle_services(
    mdv_id: Any,
    se_mdv_df: pd.DataFrame,
    sci_df: pd.DataFrame,
    params: Dict[str, Any],
) -> Tuple[List[str], float]:
    """
    Get top services linked to an MdV.
    
    Args:
        mdv_id: MdV identifier
        se_mdv_df: Service-MdV linkage table
        sci_df: Service Criticality Index table
        params: Pipeline parameters
        
    Returns:
        Tuple of (list of service codes, mean SCI)
    """
    if se_mdv_df.empty:
        return [], 0.5
    
    mdv_col = pick_first_existing_col(se_mdv_df, MDV_ID_CANDIDATES)
    se_col = pick_first_existing_col(se_mdv_df, SE_CODE_CANDIDATES)
    
    if not mdv_col or not se_col:
        return [], 0.5
    
    # Filter to this MdV
    mask = se_mdv_df[mdv_col].astype(str) == str(mdv_id)
    linked_services = se_mdv_df.loc[mask, se_col].unique().tolist()
    
    if not linked_services:
        return [], 0.5
    
    # Get SCI for linked services and rank
    if not sci_df.empty and "se_code" in sci_df.columns and "SCI_norm" in sci_df.columns:
        service_sci = sci_df[sci_df["se_code"].isin(linked_services)][["se_code", "SCI_norm"]]
        service_sci = service_sci.sort_values("SCI_norm", ascending=False)
        
        max_services = params.get("max_services_per_bundle", 3)
        top_services = service_sci.head(max_services)["se_code"].tolist()
        mean_sci = service_sci["SCI_norm"].mean()
        
        return top_services, mean_sci
    
    # Return limited services with default SCI
    max_services = params.get("max_services_per_bundle", 3)
    return linked_services[:max_services], 0.5


def enrich_bundle_ecosystems(
    service_codes: List[str],
    eco_se_df: pd.DataFrame,
    eli_df: pd.DataFrame,
    params: Dict[str, Any],
) -> Tuple[List[str], float]:
    """
    Get ecosystems supporting the bundle's services.
    
    Args:
        service_codes: List of service codes in bundle
        eco_se_df: Ecosystem-Service linkage table
        eli_df: Ecosystem Leverage Index table
        params: Pipeline parameters
        
    Returns:
        Tuple of (list of ecosystem names, mean ELI)
    """
    if eco_se_df.empty or not service_codes:
        return [], 0.5
    
    se_col = pick_first_existing_col(eco_se_df, SE_CODE_CANDIDATES)
    eco_col = pick_first_existing_col(eco_se_df, ["ecosistema_id", "eco_id", "ecosistema"])
    
    if not se_col or not eco_col:
        return [], 0.5
    
    # Find ecosystems linked to these services
    mask = eco_se_df[se_col].isin(service_codes)
    linked_ecosystems = eco_se_df.loc[mask, eco_col].unique().tolist()
    
    if not linked_ecosystems:
        return [], 0.5
    
    # Get ELI for linked ecosystems
    if not eli_df.empty and "ecosystem" in eli_df.columns and "ELI_norm" in eli_df.columns:
        eco_eli = eli_df[eli_df["ecosystem"].isin(linked_ecosystems)][["ecosystem", "ELI_norm"]]
        eco_eli = eco_eli.sort_values("ELI_norm", ascending=False)
        
        max_ecosystems = params.get("max_ecosystems_per_bundle", 2)
        top_ecosystems = eco_eli.head(max_ecosystems)["ecosystem"].tolist()
        mean_eli = eco_eli["ELI_norm"].mean()
        
        return top_ecosystems, mean_eli
    
    max_ecosystems = params.get("max_ecosystems_per_bundle", 2)
    return linked_ecosystems[:max_ecosystems], 0.5


def enrich_bundle_threats(
    mdv_id: Any,
    driver_threats_df: pd.DataFrame,
    params: Dict[str, Any],
) -> List[str]:
    """
    Get top threats driving risk for an MdV.
    
    Args:
        mdv_id: MdV identifier
        driver_threats_df: Driver threats table
        params: Pipeline parameters
        
    Returns:
        List of threat names/IDs
    """
    if driver_threats_df.empty:
        return []
    
    # Filter to this MdV
    if "mdv_id" in driver_threats_df.columns:
        mask = driver_threats_df["mdv_id"].astype(str) == str(mdv_id)
        mdv_threats = driver_threats_df[mask]
    else:
        mdv_threats = driver_threats_df
    
    # Get threat identifier
    threat_col = pick_first_existing_col(mdv_threats, THREAT_NAME_CANDIDATES)
    if not threat_col:
        threat_col = pick_first_existing_col(mdv_threats, THREAT_ID_CANDIDATES)
    
    if not threat_col:
        return []
    
    max_threats = params.get("max_threats_per_bundle", 3)
    return mdv_threats[threat_col].head(max_threats).tolist()


def enrich_bundle_equity(
    grupo: Optional[str],
    evi_by_grupo: pd.DataFrame,
    se_mdv_df: pd.DataFrame,
    mdv_id: Any,
) -> Dict[str, Any]:
    """
    Get equity signals for a bundle.
    
    Args:
        grupo: Group name (or None for overall)
        evi_by_grupo: EVI by grupo table
        se_mdv_df: Service-MdV table with barriers/inclusion
        mdv_id: MdV identifier
        
    Returns:
        Dict with equity signals
    """
    equity = {
        "evi_score": 0.5,
        "top_barriers": [],
        "top_inclusion": [],
    }
    
    # Get EVI score for grupo
    if not evi_by_grupo.empty and grupo and GRUPO_COL in evi_by_grupo.columns:
        mask = evi_by_grupo[GRUPO_COL] == grupo
        if mask.any() and "EVI_norm" in evi_by_grupo.columns:
            equity["evi_score"] = evi_by_grupo.loc[mask, "EVI_norm"].iloc[0]
    
    # Get barriers/inclusion tokens for this MdV
    if not se_mdv_df.empty:
        mdv_col = pick_first_existing_col(se_mdv_df, MDV_ID_CANDIDATES)
        barriers_col = pick_first_existing_col(se_mdv_df, ["barreras", "barriers"])
        inclusion_col = pick_first_existing_col(se_mdv_df, ["inclusion", "acceso"])
        
        if mdv_col:
            mask = se_mdv_df[mdv_col].astype(str) == str(mdv_id)
            
            if barriers_col:
                barrier_texts = se_mdv_df.loc[mask, barriers_col].dropna().astype(str).tolist()
                equity["top_barriers"] = barrier_texts[:3]
            
            if inclusion_col:
                inclusion_texts = se_mdv_df.loc[mask, inclusion_col].dropna().astype(str).tolist()
                equity["top_inclusion"] = inclusion_texts[:3]
    
    return equity


def enrich_bundle_feasibility(
    grupo: Optional[str],
    feasibility_by_grupo: pd.DataFrame,
    conflict_risk_by_grupo: pd.DataFrame,
    governance_evidence: pd.DataFrame,
    feasibility_overall: Optional[pd.DataFrame] = None,
    feasibility_by_mdv: Optional[pd.DataFrame] = None,
    mdv_id: Any = None,
    mdv_name: Optional[str] = None,
    params: Dict[str, Any] = {},
) -> Dict[str, Any]:
    """
    Get feasibility signals for a bundle.
    
    Args:
        grupo: Group name (or None for overall)
        feasibility_by_grupo: Feasibility by grupo table
        conflict_risk_by_grupo: Conflict risk by grupo table
        governance_evidence: Governance evidence table
        feasibility_overall: Overall feasibility table
        feasibility_by_mdv: MdV-specific feasibility table
        mdv_id: Identifier of the MdV for this bundle
        params: Pipeline parameters for weights
        
    Returns:
        Dict with feasibility signals
    """
    local_weights = params.get("local_weights", {})
    w_network = local_weights.get("w_network_strength", 0.35)
    w_dialogue = local_weights.get("w_dialogue_coverage", 0.25)
    w_conflict = local_weights.get("w_conflict_risk", 0.40)

    feasibility = {
        "feasibility_score": 0.5,
        "conflict_risk": 0.5,
        "top_actors": [],
        "top_spaces": [],
        "network_strength_norm": 0.5,
        "dialogue_coverage_norm": 0.5,
    }
    
    # 1. Get territorial components (Network and Dialogue)
    if grupo and not feasibility_by_grupo.empty and GRUPO_COL in feasibility_by_grupo.columns:
        mask = feasibility_by_grupo[GRUPO_COL] == grupo
        if mask.any():
            feasibility["network_strength_norm"] = feasibility_by_grupo.loc[mask, "network_strength_norm"].iloc[0] if "network_strength_norm" in feasibility_by_grupo.columns else 0.5
            feasibility["dialogue_coverage_norm"] = feasibility_by_grupo.loc[mask, "dialogue_coverage_norm"].iloc[0] if "dialogue_coverage_norm" in feasibility_by_grupo.columns else 0.5
    elif feasibility_overall is not None and not feasibility_overall.empty:
        feasibility["network_strength_norm"] = feasibility_overall["network_strength_norm"].iloc[0] if "network_strength_norm" in feasibility_overall.columns else 0.5
        feasibility["dialogue_coverage_norm"] = feasibility_overall["dialogue_coverage_norm"].iloc[0] if "dialogue_coverage_norm" in feasibility_overall.columns else 0.5

    # 2. Get Conflict Risk (MdV-specific if possible, else territorial)
    found_mdv_risk = False
    if mdv_id and feasibility_by_mdv is not None and not feasibility_by_mdv.empty:
        # Try mdv_id match first
        mask = feasibility_by_mdv["mdv_id"].astype(str) == str(mdv_id)
        if mask.any() and "mdv_conflict_risk_norm" in feasibility_by_mdv.columns:
            feasibility["conflict_risk"] = feasibility_by_mdv.loc[mask, "mdv_conflict_risk_norm"].iloc[0]
            found_mdv_risk = True
        
        # Fallback to mdv_name match if mdv_id didn't work
        if not found_mdv_risk and mdv_name and "mdv_name_norm" in feasibility_by_mdv.columns:
            from .transforms import canonical_text
            mdv_name_norm = canonical_text(mdv_name)
            mask = feasibility_by_mdv["mdv_name_norm"] == mdv_name_norm
            if mask.any():
                feasibility["conflict_risk"] = feasibility_by_mdv.loc[mask, "mdv_conflict_risk_norm"].iloc[0]
                found_mdv_risk = True

    if not found_mdv_risk:
        if grupo and not conflict_risk_by_grupo.empty and GRUPO_COL in conflict_risk_by_grupo.columns:
            mask = conflict_risk_by_grupo[GRUPO_COL] == grupo
            if mask.any() and "conflict_risk" in conflict_risk_by_grupo.columns:
                feasibility["conflict_risk"] = conflict_risk_by_grupo.loc[mask, "conflict_risk"].iloc[0]
        elif not conflict_risk_by_grupo.empty and "conflict_risk" in conflict_risk_by_grupo.columns:
            feasibility["conflict_risk"] = conflict_risk_by_grupo["conflict_risk"].iloc[0]

    # 3. Recompute composite Feasibility score to allow variation
    feasibility["feasibility_score"] = (
        w_network * feasibility["network_strength_norm"] +
        w_dialogue * feasibility["dialogue_coverage_norm"] +
        w_conflict * (1 - feasibility["conflict_risk"])
    )
    
    # Get governance highlights
    if not governance_evidence.empty and "top_actors" in governance_evidence.columns:
        feasibility["top_actors"] = governance_evidence["top_actors"].head(3).tolist()
    
    return feasibility


def build_bundle(
    mdv_row: pd.Series,
    tables: Dict[str, pd.DataFrame],
    metrics: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
    scope: str,
    grupo: Optional[str],
    paisaje: str = "Unknown",
) -> Dict[str, Any]:
    """
    Build a complete bundle for an MdV.
    
    Args:
        mdv_row: Row from candidate MdV table
        tables: Raw data tables
        metrics: Computed metrics tables
        params: Pipeline parameters
        scope: "overall" or "by_grupo"
        grupo: Group name if by_grupo
        paisaje: Landscape name
        
    Returns:
        Bundle dictionary
    """
    mdv_id = mdv_row.get("mdv_id", mdv_row.get("mdv_name", "unknown"))
    mdv_name = mdv_row.get("mdv_name", str(mdv_id))
    
    # Get services
    services, mean_sci = enrich_bundle_services(
        mdv_id,
        tables.get("TIDY_3_5_SE_MDV", pd.DataFrame()),
        metrics.get("SCI_OVERALL", pd.DataFrame()),
        params
    )
    
    # Get ecosystems
    ecosystems, mean_eli = enrich_bundle_ecosystems(
        services,
        tables.get("TIDY_3_4_ECO_SE", pd.DataFrame()),
        metrics.get("ELI_OVERALL", pd.DataFrame()),
        params
    )
    
    # Get threats
    threats = enrich_bundle_threats(
        mdv_id,
        metrics.get("DRIVER_THREATS_OVERALL", pd.DataFrame()),
        params
    )
    
    # Get equity signals
    equity = enrich_bundle_equity(
        grupo,
        metrics.get("EVI_BY_GRUPO", pd.DataFrame()),
        tables.get("TIDY_3_5_SE_MDV", pd.DataFrame()),
        mdv_id
    )
    
    # Get feasibility signals
    feasibility = enrich_bundle_feasibility(
        grupo,
        metrics.get("FEASIBILITY_BY_GRUPO", pd.DataFrame()),
        metrics.get("CONFLICT_RISK_BY_GRUPO", pd.DataFrame()),
        metrics.get("GOVERNANCE_EVIDENCE_OVERALL", pd.DataFrame()),
        metrics.get("FEASIBILITY_OVERALL", pd.DataFrame()),
        metrics.get("FEASIBILITY_BY_MDV", pd.DataFrame()),
        mdv_id,
        mdv_name,
        params
    )
    
    # Generate deterministic bundle_id
    bundle_id = stable_hash_id(
        paisaje,
        grupo or "ALL",
        mdv_id,
        ",".join(sorted([str(s) for s in services])),
        ",".join(sorted([str(t) for t in threats]))
    )
    
    # Build bundle dict
    bundle = {
        "bundle_id": bundle_id,
        "scope": scope,
        "grupo": grupo or "ALL",
        "paisaje": paisaje,
        "mdv_id": str(mdv_id),
        "mdv_name": mdv_name,
        "services": services,
        "services_text": join_as_text(services, ", ", 5),
        "ecosystems": ecosystems,
        "ecosystems_text": join_as_text(ecosystems, ", ", 3),
        "threats": threats,
        "threats_text": join_as_text(threats, ", ", 5),
        "n_services": len(services),
        "n_ecosystems": len(ecosystems),
        "n_threats": len(threats),
        # Component scores
        "impact_potential_norm": float(mdv_row.get("impact_potential_norm", 0.5)),
        "mean_sci": mean_sci,
        "mean_eli": mean_eli,
        "leverage": 0.7 * mean_sci + 0.3 * mean_eli,  # Combined leverage
        "evi_score": float(equity.get("evi_score", 0.5)),
        "feasibility_score": float(feasibility.get("feasibility_score", 0.5)),
        "conflict_risk": float(feasibility.get("conflict_risk", 0.5)),
        # Evidence snippets
        "top_barriers": equity.get("top_barriers", []),
        "top_inclusion": equity.get("top_inclusion", []),
        "top_actors": feasibility.get("top_actors", []),
    }
    
    return bundle


def build_bundles_for_scope(
    tables: Dict[str, pd.DataFrame],
    metrics: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
    scope: str,
    grupo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Build all bundles for a scope (overall or specific grupo).
    
    Args:
        tables: Raw data tables
        metrics: Computed metrics tables
        params: Pipeline parameters
        scope: "overall" or "by_grupo"
        grupo: Group name if by_grupo
        
    Returns:
        List of bundle dictionaries
    """
    # Get impact potential table
    if scope == "by_grupo" and grupo:
        ip_df = metrics.get("IMPACT_POTENTIAL_BY_GRUPO_BY_MDV", pd.DataFrame())
        if ip_df.empty:
            ip_df = metrics.get("IMPACT_POTENTIAL_BY_MDV", pd.DataFrame())
    else:
        ip_df = metrics.get("IMPACT_POTENTIAL_BY_MDV", pd.DataFrame())
    
    # Select candidates
    candidates = select_candidate_mdv(ip_df, params, scope, grupo)
    
    if candidates.empty:
        logger.warning(f"No candidate MdV for scope={scope}, grupo={grupo}")
        return []
    
    # Get paisaje from context
    dim_geo = metrics.get("DIM_CONTEXT_GEO", pd.DataFrame())
    paisaje = "Unknown"
    if not dim_geo.empty and "paisaje" in dim_geo.columns:
        paisaje = dim_geo["paisaje"].dropna().iloc[0] if not dim_geo["paisaje"].dropna().empty else "Unknown"
    
    # Build bundles
    bundles = []
    for _, row in candidates.iterrows():
        bundle = build_bundle(row, tables, metrics, params, scope, grupo, paisaje)
        bundles.append(bundle)
    
    logger.info(f"Built {len(bundles)} bundles for scope={scope}, grupo={grupo}")
    return bundles


# =============================================================================
# PORTFOLIO SCORING
# =============================================================================

def score_bundles(
    bundles_df: pd.DataFrame,
    weights: Dict[str, float],
    scenario_name: str,
) -> pd.DataFrame:
    """
    Score bundles using a specific weight scenario.
    
    Args:
        bundles_df: DataFrame of bundles
        weights: Dict with w_impact_potential, w_leverage, w_equity_urgency, w_feasibility
        scenario_name: Name of the scenario
        
    Returns:
        DataFrame with portfolio_score and ranking added
    """
    if bundles_df.empty:
        return bundles_df
    
    df = bundles_df.copy()
    
    # Get weights
    w_ip = weights.get("w_impact_potential", 0.35)
    w_lev = weights.get("w_leverage", 0.25)
    w_eq = weights.get("w_equity_urgency", 0.20)
    w_feas = weights.get("w_feasibility", 0.20)
    
    # Ensure columns exist
    df["impact_potential_norm"] = df.get("impact_potential_norm", pd.Series([0.5]*len(df))).fillna(0.5)
    df["leverage"] = df.get("leverage", pd.Series([0.5]*len(df))).fillna(0.5)
    df["evi_score"] = df.get("evi_score", pd.Series([0.5]*len(df))).fillna(0.5)
    df["feasibility_score"] = df.get("feasibility_score", pd.Series([0.5]*len(df))).fillna(0.5)
    
    # Normalize within this DataFrame
    df["impact_norm"] = minmax(df["impact_potential_norm"])
    df["leverage_norm"] = minmax(df["leverage"])
    df["equity_norm"] = minmax(df["evi_score"])
    df["feasibility_norm"] = minmax(df["feasibility_score"])
    
    # Compute portfolio score
    df["portfolio_score"] = (
        w_ip * df["impact_norm"] +
        w_lev * df["leverage_norm"] +
        w_eq * df["equity_norm"] +
        w_feas * df["feasibility_norm"]
    )
    
    # Add scenario name
    df["scenario"] = scenario_name
    
    # Sort and rank
    df = df.sort_values("portfolio_score", ascending=False)
    df["rank"] = range(1, len(df) + 1)
    
    return df


def assign_tiers(
    bundles_df: pd.DataFrame,
    params: Dict[str, Any],
) -> pd.DataFrame:
    """
    Assign tiers (Do now, Do next, Do later) to bundles.
    
    Args:
        bundles_df: DataFrame with portfolio_score
        params: Pipeline parameters with tiers and conflict_gate config
        
    Returns:
        DataFrame with tier column added
    """
    if bundles_df.empty:
        return bundles_df
    
    df = bundles_df.copy()
    tiers_config = params.get("tiers", {})
    
    # Assign initial tiers by quantile
    if "portfolio_score" in df.columns:
        df["tier"] = quantile_tier(df["portfolio_score"], tiers_config)
    else:
        df["tier"] = TIER_DO_LATER
    
    # Apply conflict gate
    conflict_gate = params.get("conflict_gate", {})
    if conflict_gate.get("enabled", False) and "conflict_risk" in df.columns:
        max_risk = conflict_gate.get("max_conflict_risk_for_do_now", 0.70)
        downgrade_steps = conflict_gate.get("downgrade_steps", 1)
        
        tier_order = [TIER_DO_NOW, TIER_DO_NEXT, TIER_DO_LATER]
        
        for idx, row in df.iterrows():
            if row["conflict_risk"] > max_risk and row["tier"] == TIER_DO_NOW:
                # Downgrade
                current_idx = tier_order.index(row["tier"])
                new_idx = min(current_idx + downgrade_steps, len(tier_order) - 1)
                df.at[idx, "tier"] = tier_order[new_idx]
                df.at[idx, "tier_downgraded"] = True
            else:
                df.at[idx, "tier_downgraded"] = False
    else:
        df["tier_downgraded"] = False
    
    return df


# =============================================================================
# EVIDENCE TABLE
# =============================================================================

def build_evidence_table(bundles: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Build long-form evidence table for bundles.
    
    Args:
        bundles: List of bundle dictionaries
        
    Returns:
        DataFrame with bundle_id, evidence_type, evidence_value
    """
    evidence_rows = []
    
    for bundle in bundles:
        bundle_id = bundle.get("bundle_id", "")
        
        # Impact potential evidence
        evidence_rows.append({
            "bundle_id": bundle_id,
            "evidence_type": "impact_potential",
            "evidence_component": STORYLINE_COMPONENTS["impact_potential"],
            "evidence_value": f"{bundle.get('impact_potential_norm', 0.5):.2f}",
        })
        
        # Leverage evidence
        evidence_rows.append({
            "bundle_id": bundle_id,
            "evidence_type": "leverage",
            "evidence_component": STORYLINE_COMPONENTS["leverage"],
            "evidence_value": f"SCI={bundle.get('mean_sci', 0.5):.2f}, ELI={bundle.get('mean_eli', 0.5):.2f}",
        })
        
        # Services
        if bundle.get("services"):
            evidence_rows.append({
                "bundle_id": bundle_id,
                "evidence_type": "services",
                "evidence_component": "Critical services linked",
                "evidence_value": bundle.get("services_text", ""),
            })
        
        # Ecosystems
        if bundle.get("ecosystems"):
            evidence_rows.append({
                "bundle_id": bundle_id,
                "evidence_type": "ecosystems",
                "evidence_component": "Supporting ecosystems",
                "evidence_value": bundle.get("ecosystems_text", ""),
            })
        
        # Threats
        if bundle.get("threats"):
            evidence_rows.append({
                "bundle_id": bundle_id,
                "evidence_type": "threats",
                "evidence_component": "Driver threats",
                "evidence_value": bundle.get("threats_text", ""),
            })
        
        # Equity evidence
        evidence_rows.append({
            "bundle_id": bundle_id,
            "evidence_type": "equity_urgency",
            "evidence_component": STORYLINE_COMPONENTS["equity_urgency"],
            "evidence_value": f"EVI={bundle.get('evi_score', 0.5):.2f}",
        })
        
        # Barriers
        if bundle.get("top_barriers"):
            evidence_rows.append({
                "bundle_id": bundle_id,
                "evidence_type": "barriers",
                "evidence_component": "Access barriers mentioned",
                "evidence_value": join_as_text(bundle["top_barriers"], "; ", 3),
            })
        
        # Feasibility evidence
        evidence_rows.append({
            "bundle_id": bundle_id,
            "evidence_type": "feasibility",
            "evidence_component": STORYLINE_COMPONENTS["feasibility"],
            "evidence_value": f"Feasibility={bundle.get('feasibility_score', 0.5):.2f}, Conflict risk={bundle.get('conflict_risk', 0.5):.2f}",
        })
    
    return pd.DataFrame(evidence_rows)


# =============================================================================
# COVERAGE SUMMARY
# =============================================================================

def build_coverage_summary(
    tables: Dict[str, pd.DataFrame],
    metrics: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Build a coverage summary showing what data was available.
    
    Args:
        tables: Raw data tables
        metrics: Computed metrics tables
        
    Returns:
        DataFrame summarizing data coverage
    """
    rows = []
    
    # Check tables
    important_tables = [
        ("LOOKUP_CONTEXT", "required"),
        ("LOOKUP_GEO", "required"),
        ("LOOKUP_MDV", "required"),
        ("TIDY_3_2_PRIORIZACION", "storyline1"),
        ("TIDY_4_2_1_AMENAZA_MDV", "storyline1"),
        ("TIDY_3_5_SE_MDV", "storyline2"),
        ("TIDY_3_4_ECO_SE", "storyline2"),
        ("TIDY_4_2_1_DIFERENCIADO", "storyline3"),
        ("TIDY_5_1_RELACIONES", "storyline4"),
        ("TIDY_6_1_CONFLICT_EVENTS", "storyline4"),
    ]
    
    for table_name, category in important_tables:
        df = tables.get(table_name, pd.DataFrame())
        rows.append({
            "component": table_name,
            "category": category,
            "available": not df.empty,
            "row_count": len(df) if not df.empty else 0,
        })
    
    # Check computed metrics
    important_metrics = [
        ("IMPACT_POTENTIAL_BY_MDV", "impact_potential"),
        ("SCI_OVERALL", "leverage"),
        ("ELI_OVERALL", "leverage"),
        ("EVI_BY_GRUPO", "equity"),
        ("FEASIBILITY_BY_GRUPO", "feasibility"),
    ]
    
    for metric_name, category in important_metrics:
        df = metrics.get(metric_name, pd.DataFrame())
        rows.append({
            "component": f"COMPUTED:{metric_name}",
            "category": category,
            "available": not df.empty,
            "row_count": len(df) if not df.empty else 0,
        })
    
    return pd.DataFrame(rows)


# =============================================================================
# MASTER FUNCTION
# =============================================================================

def build_portfolio(
    tables: Dict[str, pd.DataFrame],
    metrics: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
    weight_scenarios: Dict[str, Dict[str, float]],
) -> Dict[str, pd.DataFrame]:
    """
    Build the complete SbN portfolio with bundles and rankings.
    
    Args:
        tables: Raw data tables
        metrics: Computed metrics tables
        params: Pipeline parameters
        weight_scenarios: Scoring scenarios from weights.yaml
        
    Returns:
        Dict of output tables
    """
    result = {}
    
    # Build bundles overall
    bundles_overall = build_bundles_for_scope(tables, metrics, params, "overall")
    bundles_overall_df = pd.DataFrame(bundles_overall) if bundles_overall else pd.DataFrame()
    result["BUNDLES_OVERALL"] = bundles_overall_df
    
    # Build bundles by grupo
    dim_geo = metrics.get("DIM_CONTEXT_GEO", pd.DataFrame())
    grupos = []
    if not dim_geo.empty and GRUPO_COL in dim_geo.columns:
        grupos = dim_geo[GRUPO_COL].dropna().unique().tolist()
    
    all_bundles_by_grupo = []
    for grupo in grupos:
        bundles_grupo = build_bundles_for_scope(tables, metrics, params, "by_grupo", grupo)
        all_bundles_by_grupo.extend(bundles_grupo)
    
    bundles_by_grupo_df = pd.DataFrame(all_bundles_by_grupo) if all_bundles_by_grupo else pd.DataFrame()
    result["BUNDLES_BY_GRUPO"] = bundles_by_grupo_df
    
    # Score and rank for each scenario
    bundle_counts = {"overall": len(bundles_overall), "by_grupo": len(all_bundles_by_grupo)}
    
    for scenario_name, weights in weight_scenarios.items():
        # Overall rankings
        if not bundles_overall_df.empty:
            ranked_overall = score_bundles(bundles_overall_df.copy(), weights, scenario_name)
            ranked_overall = assign_tiers(ranked_overall, params)
            result[f"BUNDLE_RANKING_OVERALL_{scenario_name.upper()}"] = ranked_overall
        
        # By grupo rankings
        if not bundles_by_grupo_df.empty:
            ranked_by_grupo = score_bundles(bundles_by_grupo_df.copy(), weights, scenario_name)
            ranked_by_grupo = assign_tiers(ranked_by_grupo, params)
            result[f"BUNDLE_RANKING_BY_GRUPO_{scenario_name.upper()}"] = ranked_by_grupo
    
    # Evidence tables
    result["BUNDLE_EVIDENCE_OVERALL"] = build_evidence_table(bundles_overall)
    result["BUNDLE_EVIDENCE_BY_GRUPO"] = build_evidence_table(all_bundles_by_grupo)
    
    # Coverage summary
    result["COVERAGE_SUMMARY"] = build_coverage_summary(tables, metrics)
    
    logger.info(f"Built portfolio: {bundle_counts}")
    return result, bundle_counts
