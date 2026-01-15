"""
Configuration and constants for Storyline 5.
SbN Portfolio Design + Monitoring Plan Pipeline
"""

# =============================================================================
# SHEET DEFINITIONS
# =============================================================================

REQUIRED_SHEETS = [
    "LOOKUP_CONTEXT",
    "LOOKUP_GEO",
    "LOOKUP_MDV",
    "TIDY_3_2_PRIORIZACION",
    "TIDY_4_2_1_AMENAZA_MDV",
    "TIDY_3_5_SE_MDV",
]

# Minimal data sheets needed for bundle construction
MINIMAL_DATA_SHEETS = [
    "TIDY_3_2_PRIORIZACION",      # Priority ranking
    "TIDY_4_2_1_AMENAZA_MDV",     # Threat-MDV linkages
    "TIDY_3_5_SE_MDV",            # Service-MDV linkages
]

# Optional dimension lookups
OPTIONAL_DIMENSION_SHEETS = [
    "LOOKUP_SE",                  # Services dimension
    "LOOKUP_ECOSISTEMA",          # Ecosystems dimension
    "LOOKUP_ACTOR",               # Actors dimension
    "LOOKUP_CONFLICTO",           # Conflicts dimension
    "LOOKUP_CA_QUESTIONS",        # Survey questions lookup
]

# Storyline 1 sources (priority/risk/capacity)
STORYLINE1_SHEETS = [
    "TIDY_3_2_PRIORIZACION",
    "TIDY_4_1_AMENAZAS",
    "TIDY_4_2_1_AMENAZA_MDV",
    "TIDY_7_1_RESPONDENTS",
    "TIDY_7_1_RESPONSES",
]

# Storyline 2 sources (lifelines)
STORYLINE2_SHEETS = [
    "TIDY_3_4_ECOSISTEMAS",
    "TIDY_3_4_ECO_SE",
    "TIDY_3_4_ECO_MDV",
    "TIDY_3_5_SE_MDV",
    "TIDY_3_5_SE_MONTHS",
    "TIDY_4_2_2_AMENAZA_SE",
]

# Storyline 3 sources (equity)
STORYLINE3_SHEETS = [
    "TIDY_4_2_1_DIFERENCIADO",
    "TIDY_4_2_2_DIFERENCIADO",
]

# Storyline 4 sources (feasibility/conflict)
STORYLINE4_SHEETS = [
    "TIDY_5_1_ACTORES",
    "TIDY_5_1_RELACIONES",
    "TIDY_5_2_DIALOGO",
    "TIDY_5_2_DIALOGO_ACTOR",
    "TIDY_6_1_CONFLICT_EVENTS",
    "TIDY_6_2_CONFLICTO_ACTOR",
    "TIDY_4_2_1_MAPEO_CONFLICTO",
    "TIDY_4_2_2_MAPEO_CONFLICTO",
]

# QA sheets (optional)
QA_SHEETS = [
    "QA_INPUT_SCHEMA",
    "QA_PK_DUPLICATES",
    "QA_MISSING_IDS",
    "QA_FOREIGN_KEYS",
]

# All optional sheets combined
OPTIONAL_SHEETS = (
    OPTIONAL_DIMENSION_SHEETS +
    STORYLINE1_SHEETS +
    STORYLINE2_SHEETS +
    STORYLINE3_SHEETS +
    STORYLINE4_SHEETS +
    QA_SHEETS
)

# =============================================================================
# COLUMN CANDIDATES (for flexible mapping)
# =============================================================================

# Service identification
SE_CODE_CANDIDATES = ["cod_se", "se_code", "se", "codigo_se", "se_id"]
SE_NAME_CANDIDATES = ["nombre_se", "se_name", "servicio", "service_name", "nombre"]

# Ecosystem identification
ECO_NAME_CANDIDATES = ["ecosistema", "eco", "ecosystem", "nombre_ecosistema"]
ECO_ID_CANDIDATES = ["ecosistema_id", "eco_id", "ecosystem_id"]

# Geographic/grouping
GRUPO_CANDIDATES = ["grupo", "zone", "zona", "group"]
PAISAJE_CANDIDATES = ["paisaje", "landscape", "paisaje_name"]

# MDV (Medio de Vida / Livelihood)
MDV_ID_CANDIDATES = ["mdv_id", "livelihood_id", "medio_vida_id"]
MDV_NAME_CANDIDATES = ["mdv_name", "medio_vida", "mdv", "nombre_mdv", "livelihood"]

# Impact columns (version 1)
IMPACT_COLS_V1 = [
    "i_economia", "i_sociedad", "i_salud", "i_educacion",
    "i_ambiental", "i_politico", "i_conflictos", "i_migracion"
]

# Impact columns (version 2)
IMPACT_COLS_V2 = [
    "i_economia", "i_alimentaria", "i_sanitaria", "i_ambiental",
    "i_personal", "i_comunitaria", "i_politica"
]

# Priority scoring
PRIORITY_CANDIDATES = ["i_total", "priority_score", "prioridad", "total_priority"]
RANKING_CANDIDATES = ["ranking", "rank", "orden", "posicion"]

# Threat identification
THREAT_ID_CANDIDATES = ["amenaza_id", "threat_id", "cod_amenaza"]
THREAT_NAME_CANDIDATES = ["amenaza", "threat", "nombre_amenaza", "threat_name"]
SUMA_CANDIDATES = ["suma", "suma_norm", "sum", "total", "severity"]

# Actor identification
ACTOR_ID_CANDIDATES = ["actor_id", "id_actor", "cod_actor"]
ACTOR_NAME_CANDIDATES = ["nombre_actor", "actor", "name", "actor_name"]

# Dialogue identification
DIALOGO_ID_CANDIDATES = ["dialogo_id", "espacio_id", "space_id"]
DIALOGO_NAME_CANDIDATES = ["nombre_espacio", "espacio", "space_name", "nombre"]

# Conflict identification
CONFLICT_CODE_CANDIDATES = ["cod_conflict", "conflicto_id", "conflict_id", "codigo_conflicto"]
YEAR_CANDIDATES = ["ano_evento", "anio", "year", "ano", "año", "fecha"]

# Relation types
REL_TYPE_CANDIDATES = ["rel_type", "tipo_relacion", "relationship_type", "tipo_rel", "tipo"]

# Differentiated groups
DIF_GROUP_CANDIDATES = ["dif_group_std", "grupo_diferenciado", "dif_group", "vulnerable_group"]

# Barriers and inclusion
BARRIERS_CANDIDATES = ["barreras", "barriers", "obstaculos"]
INCLUSION_CANDIDATES = ["inclusion", "acceso", "access"]

# Survey responses
RESPONSE_CANDIDATES = ["response", "respuesta", "value", "valor"]
QUESTION_ID_CANDIDATES = ["question_id", "pregunta_id", "q_id"]

# =============================================================================
# OUTPUT TABLE NAMES
# =============================================================================

OUTPUT_TABLES = {
    # Bundles
    "BUNDLES_OVERALL": "bundles_overall",
    "BUNDLES_BY_GRUPO": "bundles_by_grupo",
    
    # Rankings per scenario
    "BUNDLE_RANKING_OVERALL_BALANCED": "bundle_ranking_overall_balanced",
    "BUNDLE_RANKING_OVERALL_EQUITY_FIRST": "bundle_ranking_overall_equity_first",
    "BUNDLE_RANKING_OVERALL_FEASIBILITY_FIRST": "bundle_ranking_overall_feasibility_first",
    "BUNDLE_RANKING_BY_GRUPO_BALANCED": "bundle_ranking_by_grupo_balanced",
    "BUNDLE_RANKING_BY_GRUPO_EQUITY_FIRST": "bundle_ranking_by_grupo_equity_first",
    "BUNDLE_RANKING_BY_GRUPO_FEASIBILITY_FIRST": "bundle_ranking_by_grupo_feasibility_first",
    
    # Evidence tables
    "BUNDLE_EVIDENCE_OVERALL": "bundle_evidence_overall",
    "BUNDLE_EVIDENCE_BY_GRUPO": "bundle_evidence_by_grupo",
    
    # Component indices
    "IMPACT_POTENTIAL_BY_MDV": "impact_potential_by_mdv",
    "IMPACT_POTENTIAL_BY_GRUPO_BY_MDV": "impact_potential_by_grupo_by_mdv",
    "SCI_OVERALL": "sci_overall",
    "SCI_BY_GRUPO": "sci_by_grupo",
    "ELI_OVERALL": "eli_overall",
    "ELI_BY_GRUPO": "eli_by_grupo",
    "EVI_OVERALL": "evi_overall",
    "EVI_BY_GRUPO": "evi_by_grupo",
    "FEASIBILITY_OVERALL": "feasibility_overall",
    "FEASIBILITY_BY_GRUPO": "feasibility_by_grupo",
    "CONFLICT_RISK_BY_GRUPO": "conflict_risk_by_grupo",
    
    # Driver evidence
    "DRIVER_THREATS_OVERALL": "driver_threats_overall",
    "DRIVER_THREATS_BY_GRUPO": "driver_threats_by_grupo",
    "GOVERNANCE_EVIDENCE_OVERALL": "governance_evidence_overall",
    "GOVERNANCE_EVIDENCE_BY_GRUPO": "governance_evidence_by_grupo",
    
    # Coverage
    "COVERAGE_SUMMARY": "coverage_summary",
    
    # Monitoring
    "INDICATORS": "indicators",
    "BUNDLES_TO_INDICATORS": "bundles_to_indicators",
    "MONITORING_PLAN": "monitoring_plan",
}

# =============================================================================
# CONTEXT COLUMNS
# =============================================================================

CONTEXT_ID_COL = "context_id"
GEO_ID_COL = "geo_id"
GRUPO_COL = "grupo"
PAISAJE_COL = "paisaje"
ADMIN0_COL = "admin0"
FECHA_COL = "fecha_iso"

# =============================================================================
# TIER LABELS
# =============================================================================

TIER_DO_NOW = "Do now"
TIER_DO_NEXT = "Do next"
TIER_DO_LATER = "Do later"

# =============================================================================
# INDICATOR TYPES
# =============================================================================

INDICATOR_TYPES = [
    "OUTPUT",
    "OUTCOME",
    "GOVERNANCE",
    "EQUITY",
    "CAPACITY",
    "RISK",
]

# =============================================================================
# STORYLINE COMPONENT MAPPING
# =============================================================================

STORYLINE_COMPONENTS = {
    "impact_potential": "Storyline 1 - Priority, Risk, Capacity Gap",
    "leverage": "Storyline 2 - Service/Ecosystem Criticality",
    "equity_urgency": "Storyline 3 - Equity Vulnerability",
    "feasibility": "Storyline 4 - Feasibility, Governance, Conflict Risk",
}
