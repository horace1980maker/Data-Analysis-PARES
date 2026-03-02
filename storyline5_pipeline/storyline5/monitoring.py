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

INDICATOR_TEMPLATES = [
    {
        "indicator_name": "Participantes involucrados en acciones del paquete",
        "indicator_type": "OUTPUT",
        "definition": "Número de participantes (individuos u hogares) activamente involucrados en acciones de adaptación/SbN del paquete",
        "unit_of_measure": "# participantes",
        "disaggregation_suggestions": "grupo, mdv, género, rango de edad",
        "frequency": "Trimestral",
        "data_source_suggestions": "Registros de participación, listas de asistencia",
        "linked_storyline_component": "impact_potential",
    },
    {
        "indicator_name": "Área/unidades bajo práctica SbN",
        "indicator_type": "OUTPUT",
        "definition": "Área (hectáreas) o número de unidades donde se están implementando prácticas SbN del paquete (por validar)",
        "unit_of_measure": "hectáreas o # unidades",
        "disaggregation_suggestions": "grupo, tipo de ecosistema",
        "frequency": "Semestral",
        "data_source_suggestions": "Monitoreo en campo, mapeo SIG, registros administrativos",
        "linked_storyline_component": "leverage",
    },
    {
        "indicator_name": "Disponibilidad percibida de servicio crítico",
        "indicator_type": "OUTCOME",
        "definition": "Disponibilidad de servicios ecosistémicos críticos del paquete reportada por participantes durante periodos de escasez (escala 0-100)",
        "unit_of_measure": "% puntaje de disponibilidad",
        "disaggregation_suggestions": "grupo, tipo de servicio, mdv",
        "frequency": "Semestral",
        "data_source_suggestions": "Encuestas a hogares de seguimiento, evaluaciones participativas",
        "linked_storyline_component": "leverage",
    },
    {
        "indicator_name": "Meses de escasez para servicio crítico",
        "indicator_type": "OUTCOME",
        "definition": "Número de meses por año en los que los servicios críticos son reportados como no disponibles o insuficientes (seguimiento del cambio en el tiempo)",
        "unit_of_measure": "# meses",
        "disaggregation_suggestions": "grupo, tipo de servicio",
        "frequency": "Anual",
        "data_source_suggestions": "Encuestas de seguimiento usando el mismo formato que la línea base (mes_falta)",
        "linked_storyline_component": "leverage",
    },
    {
        "indicator_name": "Espacios de diálogo activos con actores clave",
        "indicator_type": "GOVERNANCE",
        "definition": "Número de espacios de diálogo que se mantienen activos e incluyen la participación de los actores clave de gobernanza del paquete",
        "unit_of_measure": "# espacios activos",
        "disaggregation_suggestions": "grupo, tipo de espacio, tipo de actor",
        "frequency": "Trimestral",
        "data_source_suggestions": "Registros de reuniones, directorios de espacios de diálogo",
        "linked_storyline_component": "feasibility",
    },
    {
        "indicator_name": "Acuerdos/acciones de espacios de diálogo",
        "indicator_type": "GOVERNANCE",
        "definition": "Número de acuerdos documentados o acciones de seguimiento surgidos en espacios de diálogo relacionados con el tema del paquete",
        "unit_of_measure": "# acuerdos/acciones",
        "disaggregation_suggestions": "grupo, tipo de espacio, estado de acción",
        "frequency": "Trimestral",
        "data_source_suggestions": "Actas de reunión, seguimiento de acuerdos",
        "linked_storyline_component": "feasibility",
    },
    {
        "indicator_name": "Participación de grupos priorizados",
        "indicator_type": "EQUITY",
        "definition": "Proporción de participantes de grupos identificados con vulnerabilidad diferenciada o barreras (según línea base)",
        "unit_of_measure": "% de participantes",
        "disaggregation_suggestions": "grupo, mdv, tipo de grupo prioritario",
        "frequency": "Trimestral",
        "data_source_suggestions": "Registros de participación con datos demográficos",
        "linked_storyline_component": "equity_urgency",
    },
    {
        "indicator_name": "Reducción de menciones a barreras de acceso",
        "indicator_type": "EQUITY",
        "definition": "Cambio en la frecuencia de menciones a barreras para los servicios críticos del paquete comparado con línea base",
        "unit_of_measure": "% cambio en menciones",
        "disaggregation_suggestions": "grupo, tipo de servicio, tipo de barrera",
        "frequency": "Anual",
        "data_source_suggestions": "Encuestas de seguimiento usando el mismo formato que la línea base (barreras)",
        "linked_storyline_component": "equity_urgency",
    },
    {
        "indicator_name": "Cambio de puntaje en encuesta de capacidad",
        "indicator_type": "CAPACITY",
        "definition": "Cambio promedio del puntaje en encuestas seleccionadas de evaluación de capacidades relevantes a las restricciones del paquete",
        "unit_of_measure": "Cambio de puntaje (puntos de escala)",
        "disaggregation_suggestions": "grupo, mdv, categoría de pregunta",
        "frequency": "Anual",
        "data_source_suggestions": "Encuesta EC de seguimiento usando el mismo instrumento de línea base",
        "linked_storyline_component": "impact_potential",
    },
    {
        "indicator_name": "Cambios narrativos en impacto de la amenaza",
        "indicator_type": "RISK",
        "definition": "Cambios cualitativos en impactos de amenazas reportados por la comunidad afectando los mdv objetivo (para dar seguimiento, no reclamar reducción)",
        "unit_of_measure": "Resumen narrativo",
        "disaggregation_suggestions": "grupo, tipo de amenaza, mdv",
        "frequency": "Anual",
        "data_source_suggestions": "Mapeo de amenazas de seguimiento usando el mismo formato de línea base",
        "linked_storyline_component": "impact_potential",
    },
    {
        "indicator_name": "Evolución de dinámicas de conflicto",
        "indicator_type": "RISK",
        "definition": "Cambios documentados en eventos de conflicto o relaciones entre actores en el área de implementación (para monitorear, no asegurar causalidad)",
        "unit_of_measure": "Conteo de eventos / calidad de relaciones",
        "disaggregation_suggestions": "grupo, tipo de conflicto",
        "frequency": "Semestral",
        "data_source_suggestions": "Mapeo de conflictos de seguimiento, encuestas de relaciones entre actores",
        "linked_storyline_component": "feasibility",
    },
    {
        "indicator_name": "Estabilidad del enlace servicio-mdv",
        "indicator_type": "OUTCOME",
        "definition": "Proporción de vínculos servicio-mdv de línea base que se mantienen activos o se han fortalecido",
        "unit_of_measure": "% de vínculos estables/mejorados",
        "disaggregation_suggestions": "grupo, tipo de servicio, mdv",
        "frequency": "Anual",
        "data_source_suggestions": "Mapeo SE-MDV de seguimiento",
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
            "rationale": "Seguimiento a participación en acciones del paquete"
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
                "rationale": f"Seguimiento a disponibilidad de servicio para: {bundle.get('services_text', 'servicios vinculados')}"
            })
    
    # Include GOVERNANCE indicator if feasibility_score exists
    governance_indicators = indicator_library[indicator_library["indicator_type"] == "GOVERNANCE"]
    if not governance_indicators.empty:
        assignments.append({
            "indicator_id": governance_indicators.iloc[0]["indicator_id"],
            "rationale": "Seguimiento a involucramiento en espacios de diálogo para apoyo a implementación"
        })
    
    # Include EQUITY indicator if evi_score is high
    evi_score = bundle.get("evi_score", 0.5)
    if evi_score > 0.4:
        equity_indicators = indicator_library[indicator_library["indicator_type"] == "EQUITY"]
        if not equity_indicators.empty:
            assignments.append({
                "indicator_id": equity_indicators.iloc[0]["indicator_id"],
                "rationale": f"Prioridad de equidad (EVI={evi_score:.2f})"
            })
    
    # Include RISK indicator if conflict_risk is high
    conflict_risk = bundle.get("conflict_risk", 0.5)
    if conflict_risk > 0.5:
        risk_indicators = indicator_library[indicator_library["indicator_type"] == "RISK"]
        if not risk_indicators.empty:
            assignments.append({
                "indicator_id": risk_indicators.iloc[0]["indicator_id"],
                "rationale": f"Prioridad de monitoreo de conflicto (riesgo={conflict_risk:.2f})"
            })
    
    # Include CAPACITY indicator
    capacity_indicators = indicator_library[indicator_library["indicator_type"] == "CAPACITY"]
    if not capacity_indicators.empty and len(assignments) < max_per_bundle:
        assignments.append({
            "indicator_id": capacity_indicators.iloc[0]["indicator_id"],
            "rationale": "Seguimiento de mejora de capacidades"
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
