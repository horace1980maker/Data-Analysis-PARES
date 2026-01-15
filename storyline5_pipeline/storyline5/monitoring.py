"""
Monitoring plan module for Storyline 5.
Generates MEAL-ready indicator library and bundle-to-indicator mappings.
"""

import logging
from typing import Any, Dict, List

import pandas as pd

from .transforms import stable_hash_id, join_as_text

logger = logging.getLogger(__name__)


# =============================================================================
# INDICATOR LIBRARY
# =============================================================================

# Predefined indicator templates
INDICATOR_TEMPLATES = [
    {
        "indicator_name": "Participants engaged in bundle actions",
        "indicator_type": "OUTPUT",
        "definition": "Number of participants (individuals or households) actively engaged in the bundle's SbN/adaptation actions",
        "unit_of_measure": "# participants",
        "disaggregation_suggestions": "grupo, mdv, gender, age group",
        "frequency": "Quarterly",
        "data_source_suggestions": "Participation registers, attendance records",
        "linked_storyline_component": "impact_potential",
    },
    {
        "indicator_name": "Area/units under SbN practice",
        "indicator_type": "OUTPUT",
        "definition": "Area (hectares) or number of units where SbN practices from the bundle are being implemented (to be validated)",
        "unit_of_measure": "hectares or # units",
        "disaggregation_suggestions": "grupo, ecosystem type",
        "frequency": "Biannual",
        "data_source_suggestions": "Field monitoring, GIS mapping, administrative records",
        "linked_storyline_component": "leverage",
    },
    {
        "indicator_name": "Perceived availability of critical service",
        "indicator_type": "OUTCOME",
        "definition": "Participant-reported availability of the bundle's critical ecosystem services during shortage periods (0-100 scale)",
        "unit_of_measure": "% availability score",
        "disaggregation_suggestions": "grupo, service type, mdv",
        "frequency": "Biannual",
        "data_source_suggestions": "Follow-up household surveys, participatory assessments",
        "linked_storyline_component": "leverage",
    },
    {
        "indicator_name": "Months of shortage for critical service",
        "indicator_type": "OUTCOME",
        "definition": "Number of months per year where critical services are reported as unavailable or insufficient (tracking change over time)",
        "unit_of_measure": "# months",
        "disaggregation_suggestions": "grupo, service type",
        "frequency": "Annual",
        "data_source_suggestions": "Follow-up surveys using same format as baseline (mes_falta)",
        "linked_storyline_component": "leverage",
    },
    {
        "indicator_name": "Active dialogue spaces with key actors",
        "indicator_type": "GOVERNANCE",
        "definition": "Number of dialogue spaces that remain active and include participation from the bundle's key governance actors",
        "unit_of_measure": "# active spaces",
        "disaggregation_suggestions": "grupo, space type, actor type",
        "frequency": "Quarterly",
        "data_source_suggestions": "Meeting records, dialogue space registers",
        "linked_storyline_component": "feasibility",
    },
    {
        "indicator_name": "Agreements/actions from dialogue spaces",
        "indicator_type": "GOVERNANCE",
        "definition": "Number of documented agreements or follow-up actions emerged from dialogue spaces related to the bundle topic",
        "unit_of_measure": "# agreements/actions",
        "disaggregation_suggestions": "grupo, space type, action status",
        "frequency": "Quarterly",
        "data_source_suggestions": "Meeting minutes, follow-up tracking",
        "linked_storyline_component": "feasibility",
    },
    {
        "indicator_name": "Participation from prioritized groups",
        "indicator_type": "EQUITY",
        "definition": "Share of participants from groups identified as having differentiated vulnerability or barriers (as per baseline)",
        "unit_of_measure": "% of participants",
        "disaggregation_suggestions": "grupo, mdv, priority group type",
        "frequency": "Quarterly",
        "data_source_suggestions": "Participation registers with demographic data",
        "linked_storyline_component": "equity_urgency",
    },
    {
        "indicator_name": "Reduction in access barriers mentions",
        "indicator_type": "EQUITY",
        "definition": "Change in frequency of barrier mentions for the bundle's critical services compared to baseline",
        "unit_of_measure": "% change in mentions",
        "disaggregation_suggestions": "grupo, service type, barrier type",
        "frequency": "Annual",
        "data_source_suggestions": "Follow-up surveys using same format as baseline (barreras)",
        "linked_storyline_component": "equity_urgency",
    },
    {
        "indicator_name": "Capacity survey score change",
        "indicator_type": "CAPACITY",
        "definition": "Mean score change in selected capacity assessment survey questions relevant to the bundle's constraints",
        "unit_of_measure": "Score change (scale points)",
        "disaggregation_suggestions": "grupo, mdv, question category",
        "frequency": "Annual",
        "data_source_suggestions": "Follow-up CA survey using same instrument as baseline",
        "linked_storyline_component": "impact_potential",
    },
    {
        "indicator_name": "Threat impact narrative changes",
        "indicator_type": "RISK",
        "definition": "Qualitative changes in community-reported threat impacts affecting the bundle's target livelihoods (to track, not claim reduction)",
        "unit_of_measure": "Narrative summary",
        "disaggregation_suggestions": "grupo, threat type, mdv",
        "frequency": "Annual",
        "data_source_suggestions": "Follow-up threat mapping using same format as baseline",
        "linked_storyline_component": "impact_potential",
    },
    {
        "indicator_name": "Conflict dynamics evolution",
        "indicator_type": "RISK",
        "definition": "Documented changes in conflict events or actor relations in the bundle's implementation area (tracking, not claiming causation)",
        "unit_of_measure": "Event count / relation quality",
        "disaggregation_suggestions": "grupo, conflict type",
        "frequency": "Biannual",
        "data_source_suggestions": "Follow-up conflict mapping, actor relation surveys",
        "linked_storyline_component": "feasibility",
    },
    {
        "indicator_name": "Service-livelihood linkage stability",
        "indicator_type": "OUTCOME",
        "definition": "Proportion of baseline service-livelihood linkages that remain active or have strengthened",
        "unit_of_measure": "% stable/improved linkages",
        "disaggregation_suggestions": "grupo, service type, mdv",
        "frequency": "Annual",
        "data_source_suggestions": "Follow-up SE-MDV mapping",
        "linked_storyline_component": "leverage",
    },
]


def build_indicator_library(params: Dict[str, Any]) -> pd.DataFrame:
    """
    Build the indicator library from templates.
    
    Args:
        params: Pipeline parameters with monitoring configuration
        
    Returns:
        DataFrame of indicators
    """
    monitoring_config = params.get("monitoring", {})
    max_indicators = monitoring_config.get("max_indicators_total", 12)
    include_governance = monitoring_config.get("include_governance", True)
    include_equity = monitoring_config.get("include_equity", True)
    
    # Filter templates based on config
    indicators = []
    for template in INDICATOR_TEMPLATES:
        # Skip governance indicators if not included
        if not include_governance and template["indicator_type"] == "GOVERNANCE":
            continue
        # Skip equity indicators if not included
        if not include_equity and template["indicator_type"] == "EQUITY":
            continue
        
        indicators.append(template)
        
        if len(indicators) >= max_indicators:
            break
    
    # Add indicator IDs
    for indicator in indicators:
        indicator["indicator_id"] = stable_hash_id(
            indicator["indicator_name"],
            indicator["indicator_type"]
        )
    
    df = pd.DataFrame(indicators)
    
    # Reorder columns
    col_order = [
        "indicator_id", "indicator_name", "indicator_type", "definition",
        "unit_of_measure", "disaggregation_suggestions", "frequency",
        "data_source_suggestions", "linked_storyline_component"
    ]
    df = df[[c for c in col_order if c in df.columns]]
    
    logger.info(f"Built indicator library with {len(df)} indicators")
    return df


# =============================================================================
# BUNDLE-TO-INDICATOR MAPPING
# =============================================================================

def get_priority_indicators_for_bundle(
    bundle: Dict[str, Any],
    indicator_library: pd.DataFrame,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Determine which indicators should be assigned to a bundle.
    
    Args:
        bundle: Bundle dictionary
        indicator_library: Full indicator library
        params: Pipeline parameters
        
    Returns:
        List of assigned indicator mappings
    """
    monitoring_config = params.get("monitoring", {})
    max_per_bundle = monitoring_config.get("indicators_per_bundle", 6)
    
    assignments = []
    
    # Always include OUTPUT indicator (participants)
    output_indicators = indicator_library[indicator_library["indicator_type"] == "OUTPUT"]
    if not output_indicators.empty:
        assignments.append({
            "indicator_id": output_indicators.iloc[0]["indicator_id"],
            "rationale": "Track participation in bundle actions"
        })
    
    # Include OUTCOME indicator if bundle has services
    if bundle.get("n_services", 0) > 0:
        outcome_indicators = indicator_library[
            (indicator_library["indicator_type"] == "OUTCOME") &
            (indicator_library["linked_storyline_component"] == "leverage")
        ]
        if not outcome_indicators.empty:
            assignments.append({
                "indicator_id": outcome_indicators.iloc[0]["indicator_id"],
                "rationale": f"Track service availability for: {bundle.get('services_text', 'linked services')}"
            })
    
    # Include GOVERNANCE indicator if feasibility_score exists
    governance_indicators = indicator_library[indicator_library["indicator_type"] == "GOVERNANCE"]
    if not governance_indicators.empty:
        assignments.append({
            "indicator_id": governance_indicators.iloc[0]["indicator_id"],
            "rationale": "Track dialogue space engagement for implementation support"
        })
    
    # Include EQUITY indicator if evi_score is high
    evi_score = bundle.get("evi_score", 0.5)
    if evi_score > 0.4:
        equity_indicators = indicator_library[indicator_library["indicator_type"] == "EQUITY"]
        if not equity_indicators.empty:
            assignments.append({
                "indicator_id": equity_indicators.iloc[0]["indicator_id"],
                "rationale": f"Equity priority (EVI={evi_score:.2f})"
            })
    
    # Include RISK indicator if conflict_risk is high
    conflict_risk = bundle.get("conflict_risk", 0.5)
    if conflict_risk > 0.5:
        risk_indicators = indicator_library[indicator_library["indicator_type"] == "RISK"]
        if not risk_indicators.empty:
            assignments.append({
                "indicator_id": risk_indicators.iloc[0]["indicator_id"],
                "rationale": f"Conflict monitoring priority (risk={conflict_risk:.2f})"
            })
    
    # Include CAPACITY indicator
    capacity_indicators = indicator_library[indicator_library["indicator_type"] == "CAPACITY"]
    if not capacity_indicators.empty and len(assignments) < max_per_bundle:
        assignments.append({
            "indicator_id": capacity_indicators.iloc[0]["indicator_id"],
            "rationale": "Track capacity development progress"
        })
    
    return assignments[:max_per_bundle]


def map_bundles_to_indicators(
    bundles_df: pd.DataFrame,
    indicator_library: pd.DataFrame,
    params: Dict[str, Any],
) -> pd.DataFrame:
    """
    Create mapping of bundles to indicators.
    
    Args:
        bundles_df: DataFrame of bundles (typically top-ranked)
        indicator_library: Indicator library
        params: Pipeline parameters
        
    Returns:
        DataFrame with bundle_id, indicator_id, rationale_link_to_evidence
    """
    if bundles_df.empty or indicator_library.empty:
        return pd.DataFrame(columns=["bundle_id", "indicator_id", "rationale_link_to_evidence"])
    
    mappings = []
    
    for _, bundle_row in bundles_df.iterrows():
        bundle = bundle_row.to_dict()
        bundle_id = bundle.get("bundle_id", "")
        
        assignments = get_priority_indicators_for_bundle(bundle, indicator_library, params)
        
        for assignment in assignments:
            # Lookup indicator_name from library
            ind_id = assignment["indicator_id"]
            ind_row = indicator_library[indicator_library["indicator_id"] == ind_id]
            ind_name = ind_row["indicator_name"].iloc[0] if not ind_row.empty else ind_id
            
            mappings.append({
                "bundle_id": bundle_id,
                "mdv_name": bundle.get("mdv_name", ""),
                "grupo": bundle.get("grupo", "ALL"),
                "indicator_id": ind_id,
                "indicator_name": ind_name,
                "rationale_link_to_evidence": assignment["rationale"],
            })
    
    logger.info(f"Created {len(mappings)} bundle-to-indicator mappings")
    return pd.DataFrame(mappings)


# =============================================================================
# MONITORING PLAN TABLE
# =============================================================================

def build_monitoring_plan(
    bundles_to_indicators: pd.DataFrame,
    indicator_library: pd.DataFrame,
    bundles_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the complete monitoring plan table.
    
    Args:
        bundles_to_indicators: Mapping table
        indicator_library: Indicator library
        bundles_df: Bundles with tier information
        
    Returns:
        Merged monitoring plan table
    """
    if bundles_to_indicators.empty:
        return pd.DataFrame()
    
    # Merge with indicator details
    plan = bundles_to_indicators.merge(
        indicator_library,
        on="indicator_id",
        how="left"
    )
    
    # Merge with bundle tier if available
    if not bundles_df.empty and "bundle_id" in bundles_df.columns and "tier" in bundles_df.columns:
        tier_info = bundles_df[["bundle_id", "tier", "rank"]].drop_duplicates(subset=["bundle_id"])
        plan = plan.merge(tier_info, on="bundle_id", how="left")
    
    # Order columns
    col_order = [
        "bundle_id", "mdv_name", "grupo", "tier", "rank",
        "indicator_id", "indicator_name", "indicator_type",
        "definition", "unit_of_measure", "frequency",
        "rationale_link_to_evidence", "data_source_suggestions"
    ]
    plan = plan[[c for c in col_order if c in plan.columns]]
    
    # Sort by tier priority, then rank
    tier_order = {"Do now": 0, "Do next": 1, "Do later": 2}
    if "tier" in plan.columns:
        plan["tier_sort"] = plan["tier"].map(tier_order).fillna(3)
        plan = plan.sort_values(["tier_sort", "rank", "indicator_type"])
        plan = plan.drop(columns=["tier_sort"])
    
    logger.info(f"Built monitoring plan with {len(plan)} entries")
    return plan


# =============================================================================
# MASTER FUNCTION
# =============================================================================

def build_monitoring_tables(
    portfolio_tables: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Build all monitoring plan tables.
    
    Args:
        portfolio_tables: Portfolio output tables (including ranked bundles)
        params: Pipeline parameters
        
    Returns:
        Dict with INDICATORS, BUNDLES_TO_INDICATORS, MONITORING_PLAN
    """
    result = {}
    
    # Build indicator library
    indicator_library = build_indicator_library(params)
    result["INDICATORS"] = indicator_library
    
    # Get top ranked bundles for mapping (prefer balanced scenario)
    top_bundles = pd.DataFrame()
    for key in ["BUNDLE_RANKING_OVERALL_BALANCED", "BUNDLE_RANKING_BY_GRUPO_BALANCED"]:
        if key in portfolio_tables and not portfolio_tables[key].empty:
            ranked = portfolio_tables[key]
            # Take top N by tier priority
            if "tier" in ranked.columns:
                do_now = ranked[ranked["tier"] == "Do now"]
                do_next = ranked[ranked["tier"] == "Do next"]
                top_bundles = pd.concat([top_bundles, do_now.head(5), do_next.head(5)])
            else:
                top_bundles = pd.concat([top_bundles, ranked.head(10)])
    
    top_bundles = top_bundles.drop_duplicates(subset=["bundle_id"])
    
    # Map bundles to indicators
    bundles_to_indicators = map_bundles_to_indicators(
        top_bundles,
        indicator_library,
        params
    )
    result["BUNDLES_TO_INDICATORS"] = bundles_to_indicators
    
    # Build full monitoring plan
    monitoring_plan = build_monitoring_plan(
        bundles_to_indicators,
        indicator_library,
        top_bundles
    )
    result["MONITORING_PLAN"] = monitoring_plan
    
    logger.info(f"Built monitoring tables: {list(result.keys())}")
    return result
