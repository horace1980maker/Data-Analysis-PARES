#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 Configuration
Defines sheet names, column definitions, and lookup dictionaries for code expansion.
"""

from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# REQUIRED SHEETS (fail gracefully if missing)
# ---------------------------------------------------------------------------

REQUIRED_SHEETS = [
    "LOOKUP_GEO",
    "LOOKUP_CONTEXT",
    "LOOKUP_MDV",
    "TIDY_3_2_PRIORIZACION",
    "TIDY_4_1_AMENAZAS",
    "TIDY_4_2_1_AMENAZA_MDV",
    "TIDY_7_1_RESPONDENTS",
    "TIDY_7_1_RESPONSES",
    "LOOKUP_CA_QUESTIONS",
]

OPTIONAL_SHEETS = [
    "QA_INPUT_SCHEMA",
    "QA_PK_DUPLICATES",
    "QA_MISSING_IDS",
    "QA_FOREIGN_KEYS",
]

# ---------------------------------------------------------------------------
# COLUMN DEFINITIONS
# ---------------------------------------------------------------------------

# Impact columns for TIDY_4_2_1_AMENAZA_MDV
IMPACT_COLS = [
    "i_economia",
    "i_alimentaria",
    "i_sanitaria",
    "i_ambiental",
    "i_personal",
    "i_comunitaria",
    "i_politica",
]

# Priority component columns for TIDY_3_2_PRIORIZACION
PRIORITY_COMPONENT_COLS = [
    "i_seg_alim",
    "i_area",
    "i_des_loc",
    "i_ambiente",
    "i_inclusion",
]

PRIORITY_TOTAL_COL = "i_total"

# Threat severity columns
THREAT_SEVERITY_COLS = ["magnitud", "frequencia", "tendencia", "suma"]

# ---------------------------------------------------------------------------
# OUTPUT TABLE NAMES
# ---------------------------------------------------------------------------

OUTPUT_TABLES = {
    # Priority metrics
    "priority_by_mdv_overall": "priority_by_mdv_overall",
    "priority_by_mdv_group": "priority_by_mdv_group",
    # Threat metrics
    "threats_overall": "threats_overall",
    "threats_by_group": "threats_by_group",
    # Impact/Risk metrics
    "risk_by_mdv_overall": "risk_by_mdv_overall",
    "risk_by_mdv_group": "risk_by_mdv_group",
    "top_threat_drivers_overall": "top_threat_drivers_overall",
    "top_threat_drivers_by_group": "top_threat_drivers_by_group",
    # Capacity metrics
    "capacity_overall_by_mdv": "capacity_overall_by_mdv",
    "capacity_by_group_by_mdv": "capacity_by_group_by_mdv",
    "capacity_overall_questions": "capacity_overall_questions",
    "capacity_by_group_questions": "capacity_by_group_questions",
    # API rankings (one per scenario)
    "rankings_overall": "rankings_overall_{scenario}",
    "rankings_by_group": "rankings_by_group_{scenario}",
}

# ---------------------------------------------------------------------------
# CODE EXPANSION LOOKUPS
# For translating codes/abbreviations to full names in reports
# ---------------------------------------------------------------------------

# Ecosystem Services (Servicios Ecosistémicos) - SE codes
SE_CODE_NAMES: Dict[str, str] = {
    "P1": "Alimentos",
    "P2": "Materias primas",
    "P3": "Agua dulce",
    "P4": "Recursos medicinales",
    "R1": "Regulación de la calidad del aire y el clima locales",
    "R2": "Secuestro y almacenamiento de carbono",
    "R3": "Moderación de los desastres naturales",
    "R4": "Tratamiento de las aguas residuales",
    "R5": "Prevención de la erosión y mantenimiento de la fertilidad del suelo",
    "R6": "Polinización",
    "R7": "Control biológico",
    "A1": "Hábitats para las especies",
    "A2": "Mantenimiento de la diversidad genética",
    "C1": "Actividades recreativas y salud mental y física",
    "C2": "Turismo",
    "C3": "Apreciación estética e inspiración para la cultura, el arte y el diseño",
    "C4": "Experiencia espiritual y sentido de pertenencia",
}

SE_SERVICE_TYPES: Dict[str, str] = {
    "P1": "Provisión", "P2": "Provisión", "P3": "Provisión", "P4": "Provisión",
    "R1": "Regulación", "R2": "Regulación", "R3": "Regulación", "R4": "Regulación",
    "R5": "Regulación", "R6": "Regulación", "R7": "Regulación",
    "A1": "Apoyo", "A2": "Apoyo",
    "C1": "Cultural", "C2": "Cultural", "C3": "Cultural", "C4": "Cultural",
}

# Threat evaluation (Calificación de Amenazas)
MAGNITUD_NAMES: Dict[int, str] = {
    1: 'Muy bajo, "Casi no nos afecta"',
    2: 'Bajo, "Nos afecta un poco, pero lo podemos manejar"',
    3: 'Moderado, "Nos complica bastante"',
    4: 'Alto "Nos golpea duro"',
    5: 'Muy alto "Nos deja sin nada"',
}

FRECUENCIA_NAMES: Dict[int, str] = {
    1: "Ocasional",
    2: "Recurrente",
    3: "Constante",
}

TENDENCIA_NAMES: Dict[int, str] = {
    3: "Nueva",
    2: "Aumenta",
    1: "Ligeramente aumenta",
    0: "Estable",
    -1: "Ligeramente disminuye",
    -2: "Disminuye",
}

# Conflict types (Tipo de Conflicto)
CONFLICT_TYPE_CODES: Dict[str, str] = {
    "C1": "Competencia por recursos naturales",
    "C2": "Desigualdad intergeneracional o de género",
    "C3": "Marginalización, tensión comunitaria o disturbios sociales",
    "C4": "Falta de comunicación y colaboración entre actores",
    "C5": "Instituciones frágiles o ineficientes",
    "C6": "Violencia, asesinatos o presencia de grupos armados",
    "C7": "Migración y desplazamientos forzados",
}

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS FOR CODE EXPANSION
# ---------------------------------------------------------------------------

def expand_se_code(code: str) -> str:
    """Expand ecosystem service code to full name."""
    if not code:
        return ""
    code_upper = str(code).strip().upper()
    return SE_CODE_NAMES.get(code_upper, code)


def expand_magnitud(value: int) -> str:
    """Expand magnitude value to descriptive name."""
    try:
        val = int(value)
        return MAGNITUD_NAMES.get(val, str(value))
    except (ValueError, TypeError):
        return str(value) if value else ""


def expand_frecuencia(value: int) -> str:
    """Expand frequency value to descriptive name."""
    try:
        val = int(value)
        return FRECUENCIA_NAMES.get(val, str(value))
    except (ValueError, TypeError):
        return str(value) if value else ""


def expand_tendencia(value: int) -> str:
    """Expand trend value to descriptive name."""
    try:
        val = int(value)
        return TENDENCIA_NAMES.get(val, str(value))
    except (ValueError, TypeError):
        return str(value) if value else ""


def expand_conflict_type(code: str) -> str:
    """Expand conflict type code to full name."""
    if not code:
        return ""
    code_upper = str(code).strip().upper()
    return CONFLICT_TYPE_CODES.get(code_upper, code)


# Common abbreviations used in the domain
ABBREVIATIONS: Dict[str, str] = {
    "MdV": "Medios de Vida (Livelihoods)",
    "SE": "Servicios Ecosistémicos (Ecosystem Services)",
    "SES": "Sistema Socio-Ecológico (Socio-Ecological System)",
    "CA": "Capacidad Adaptativa (Adaptive Capacity)",
    "API": "Índice de Prioridad de Acción (Action Priority Index)",
    "SbN": "Soluciones basadas en la Naturaleza (Nature-based Solutions)",
    "NbS": "Nature-based Solutions",
}


def get_config_path() -> Path:
    """Return path to config directory."""
    return Path(__file__).parent.parent / "config"


def get_weights_yaml_path() -> Path:
    """Return path to weights.yaml config file."""
    return get_config_path() / "weights.yaml"
