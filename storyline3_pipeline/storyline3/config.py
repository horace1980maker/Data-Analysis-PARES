"""
Configuration and constants for Storyline 3.
"""

# Sheet names
REQUIRED_SHEETS = [
    "LOOKUP_CONTEXT",
    "LOOKUP_GEO"
]

OPTIONAL_SHEETS = [
    "LOOKUP_MDV",
    "LOOKUP_SE",
    "LOOKUP_CA_QUESTIONS",
    "TIDY_4_1_AMENAZAS",
    "TIDY_4_2_1_DIFERENCIADO",
    "TIDY_4_2_2_DIFERENCIADO",
    "TIDY_3_5_SE_MDV",
    "TIDY_7_1_RESPONDENTS",
    "TIDY_7_1_RESPONSES",
    "QA_INPUT_SCHEMA",
    "QA_PK_DUPLICATES",
    "QA_MISSING_IDS",
    "QA_FOREIGN_KEYS"
]

# Column candidates for flexible mapping
DIF_GROUP_CANDIDATES = ["group_label", "dif_group", "diferenciado", "grupo_afectado", "grupo", "subgrupo", "poblacion"]
DIF_NOTES_CANDIDATES = ["dif_notes", "descripcion", "explicacion", "comentario", "detalle"]
SE_CODE_CANDIDATES = ["cod_se", "se_code", "se", "codigo_se"]

# Text fields to tokenize / frequency count
BARRIER_CANDIDATES = ["barreras", "barrera", "obstaculo", "limitacion", "barriers"]
INCLUSION_CANDIDATES = ["inclusion", "exclusion", "participacion", "groups_included"]
ACCESS_CANDIDATES = ["acceso", "accesso", "acceder", "access"]

# Survey midpoint mapping (same as Storyline 1)
SURVEY_RANGE_MAP = {
    "0-20": 10,
    "20-40": 30,
    "40-60": 50,
    "60-80": 70,
    "80-100": 90,
    "0": 0,
    "100": 100
}
