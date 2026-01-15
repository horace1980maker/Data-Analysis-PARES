"""
Configuration and constants for Storyline 4.
Feasibility, Governance & Conflict Risk Analysis
"""

# =============================================================================
# SHEET DEFINITIONS
# =============================================================================

REQUIRED_SHEETS = [
    "LOOKUP_CONTEXT",
    "LOOKUP_GEO",
]

OPTIONAL_SHEETS = [
    # Dimension lookups
    "LOOKUP_ACTOR",
    "LOOKUP_CONFLICTO",
    # Actors and relations
    "TIDY_5_1_ACTORES",
    "TIDY_5_1_RELACIONES",
    # Dialogue spaces
    "TIDY_5_2_DIALOGO",
    "TIDY_5_2_DIALOGO_ACTOR",
    # Conflicts
    "TIDY_6_1_CONFLICT_EVENTS",
    "TIDY_6_2_CONFLICTO_ACTOR",
    # Conflict linkages (optional)
    "TIDY_4_2_1_MAPEO_CONFLICTO",
    "TIDY_4_2_2_MAPEO_CONFLICTO",
    # QA sheets
    "QA_INPUT_SCHEMA",
    "QA_PK_DUPLICATES",
    "QA_MISSING_IDS",
    "QA_FOREIGN_KEYS",
]

# =============================================================================
# COLUMN CANDIDATES (for flexible mapping)
# =============================================================================

# Actor identification
ACTOR_ID_CANDIDATES = ["actor_id", "id_actor", "cod_actor", "actor"]
ACTOR_NAME_CANDIDATES = ["nombre_actor", "actor", "name", "actor_name", "nombre"]
ACTOR_TYPE_CANDIDATES = ["tipo_actor", "type", "actor_type", "tipo"]

# Power and interest (for power-interest matrix)
POWER_CANDIDATES = ["poder", "power", "influencia", "influence"]
INTEREST_CANDIDATES = ["interes", "interest", "interés"]

# Relations
OTHER_ACTOR_CANDIDATES = ["other_actor_id", "actor_b_id", "target_actor_id", "otro_actor_id"]
OTHER_ACTOR_NAME_CANDIDATES = ["other_actor_name", "actor_b", "target_actor", "otro_actor", "nombre_otro_actor"]
REL_TYPE_CANDIDATES = ["rel_type", "tipo_relacion", "relationship_type", "tipo_rel", "tipo"]

# Conflict identification
CONFLICT_CODE_CANDIDATES = ["cod_conflict", "conflicto_id", "conflict_id", "codigo_conflicto", "cod_conflicto"]
CONFLICT_DESC_CANDIDATES = ["descripcion", "description", "desc", "detalle"]
CONFLICT_TYPE_CANDIDATES = ["tipo_conflicto", "conflict_type", "tipo"]
CONFLICT_LEVEL_CANDIDATES = ["nivel_conflicto", "conflict_level", "nivel", "level"]

# Year for conflict timeline
YEAR_CANDIDATES = ["ano_evento", "anio", "year", "ano", "año", "fecha"]

# Incidence and intensity
INCIDENCE_CANDIDATES = ["incidencia", "incidence", "frecuencia", "frequency"]
SUMA_CANDIDATES = ["suma", "sum", "total", "severity"]

# Conflict actor involvement
ACTOR_IMPACT_ON_CONFLICT_CANDIDATES = ["i_en_conflicto", "impact_on_conflict", "impacto_conflicto"]
CONFLICT_IMPACT_ON_ACTOR_CANDIDATES = ["i_en_actor", "impact_on_actor", "impacto_actor"]

# Dialogue spaces
DIALOGO_NAME_CANDIDATES = ["nombre_espacio", "espacio", "space_name", "nombre", "name"]
DIALOGO_TYPE_CANDIDATES = ["tipo", "type", "tipo_espacio"]
DIALOGO_SCOPE_CANDIDATES = ["alcance", "scope", "nivel", "level"]
STRENGTHS_CANDIDATES = ["fortalezas", "strengths", "fortaleza"]
WEAKNESSES_CANDIDATES = ["debilidades", "weaknesses", "debilidad"]

# Threat-conflict linkages
# TIDY_4_2_1_MAPEO_CONFLICTO has: map_id, amenaza_mdv_id, cod_conflict, conflicto_id
# TIDY_4_2_2_MAPEO_CONFLICTO has: map_id, amenaza_se_id, cod_conflict, conflicto_id
THREAT_ID_CANDIDATES = ["amenaza_mdv_id", "amenaza_se_id", "amenaza_id", "threat_id", "cod_amenaza"]
MDV_ID_CANDIDATES = ["amenaza_mdv_id", "mdv_id", "livelihood_id", "medio_vida_id"]
SE_ID_CANDIDATES = ["amenaza_se_id", "se_id", "cod_se", "service_id", "se_code"]

# =============================================================================
# OUTPUT TABLE NAMES
# =============================================================================

OUTPUT_TABLES = {
    # Actors
    "ACTORS_OVERALL": "actors_overall",
    "ACTORS_BY_GRUPO": "actors_by_grupo",
    "ACTOR_CENTRALITY_OVERALL": "actor_centrality_overall",
    "ACTOR_CENTRALITY_BY_GRUPO": "actor_centrality_by_grupo",
    "DYADS_OVERALL": "dyads_overall",
    "DYADS_BY_GRUPO": "dyads_by_grupo",
    # Dialogue
    "DIALOGUE_SPACES_OVERALL": "dialogue_spaces_overall",
    "DIALOGUE_SPACES_BY_GRUPO": "dialogue_spaces_by_grupo",
    "DIALOGUE_PARTICIPATION_OVERALL": "dialogue_participation_overall",
    "DIALOGUE_PARTICIPATION_BY_GRUPO": "dialogue_participation_by_grupo",
    "ACTOR_IN_SPACES_OVERALL": "actor_in_spaces_overall",
    "ACTOR_IN_SPACES_BY_GRUPO": "actor_in_spaces_by_grupo",
    "DIALOGUE_STRENGTHS_FREQ_OVERALL": "dialogue_strengths_freq_overall",
    "DIALOGUE_WEAKNESSES_FREQ_OVERALL": "dialogue_weaknesses_freq_overall",
    # Conflicts
    "CONFLICTS_OVERALL": "conflicts_overall",
    "CONFLICTS_BY_GRUPO": "conflicts_by_grupo",
    "CONFLICT_TIMELINE_OVERALL": "conflict_timeline_overall",
    "CONFLICT_TIMELINE_BY_GRUPO": "conflict_timeline_by_grupo",
    "CONFLICT_ACTORS_OVERALL": "conflict_actors_overall",
    # Linkages
    "LINK_MDV_THREAT_CONFLICT_OVERALL": "link_mdv_threat_conflict_overall",
    "LINK_SE_THREAT_CONFLICT_OVERALL": "link_se_threat_conflict_overall",
    "TOP_CONFLICT_LINKED_THREATS": "top_conflict_linked_threats",
    # Feasibility
    "FEASIBILITY_OVERALL": "feasibility_overall",
    "FEASIBILITY_BY_GRUPO": "feasibility_by_grupo",
}

# =============================================================================
# CONTEXT COLUMN
# =============================================================================

CONTEXT_ID_COL = "context_id"
GEO_ID_COL = "geo_id"
GRUPO_COL = "grupo"
PAISAJE_COL = "paisaje"
ADMIN0_COL = "admin0"
FECHA_COL = "fecha_iso"
