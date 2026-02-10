"""
Report module for Storyline 5.
Generates HTML diagnostic report with embedded tables and images.
Spanish/English bilingual with Teal/Amber theme matching storyline1/4.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

TIER_NAMES = {
    "Do now": "Acción inmediata",
    "Do next": "Acción siguiente",
    "Do later": "Acción posterior",
}

INDICATOR_TYPE_NAMES = {
    "OUTPUT": "PRODUCTO",
    "OUTCOME": "RESULTADO",
    "GOVERNANCE": "GOBERNANZA",
    "EQUITY": "EQUIDAD",
    "CAPACITY": "CAPACIDAD",
    "RISK": "RIESGO",
}

# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 5: Diseño de Portafolio SbN + Plan de Monitoreo</title>
    <style>
        :root {{
            --primary-color: #00695c;
            --secondary-color: #26a69a;
            --accent-color: #ffb300;
            --warning-color: #ff9800;
            --danger-color: #e53935;
            --success-color: #2e7d32;
            --light-bg: #f5f5f5;
            --border-color: #e0e0e0;
            --text-color: #333;
            --text-muted: #666;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background: linear-gradient(135deg, #e0f2f1 0%, #fff8e1 100%);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        h1 {{
            color: var(--primary-color);
            text-align: center;
            border-bottom: 3px solid var(--accent-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        h2 {{
            color: var(--secondary-color);
            border-left: 4px solid var(--accent-color);
            padding-left: 15px;
            margin-top: 40px;
        }}
        
        h3 {{
            color: var(--secondary-color);
            margin-top: 25px;
        }}
        
        .metadata {{
            background: var(--light-bg);
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        
        .toc {{
            background: #e0f2f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .toc h3 {{
            margin-top: 0;
            color: var(--primary-color);
        }}
        
        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .toc li {{
            padding: 5px 0;
        }}
        
        .toc a {{
            color: var(--primary-color);
            text-decoration: none;
        }}
        
        .toc a:hover {{
            text-decoration: underline;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            opacity: 0.9;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.9em;
        }}
        
        table th {{
            background: var(--secondary-color);
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
        }}
        
        table td {{
            padding: 10px 8px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        table tr:nth-child(even) {{
            background-color: var(--light-bg);
        }}
        
        table tr:hover {{
            background-color: #e8f5e9;
        }}
        
        .figure-container {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .figure-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .figure-caption {{
            font-style: italic;
            color: var(--text-muted);
            margin-top: 10px;
        }}
        
        .info {{
            background: #e3f2fd;
            border-left: 4px solid #1976d2;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .warning {{
            background: #fff3e0;
            border-left: 4px solid var(--warning-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .success {{
            background: #e8f5e9;
            border-left: 4px solid var(--success-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .bundle-card {{
            background: white;
            border: 2px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}
        
        .bundle-card.do-now {{
            border-left: 5px solid var(--success-color);
        }}
        
        .bundle-card.do-next {{
            border-left: 5px solid var(--warning-color);
        }}
        
        .bundle-card.do-later {{
            border-left: 5px solid var(--danger-color);
        }}
        
        .bundle-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .bundle-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary-color);
        }}
        
        .tier-badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .tier-do-now {{
            background: var(--success-color);
            color: white;
        }}
        
        .tier-do-next {{
            background: var(--warning-color);
            color: white;
        }}
        
        .tier-do-later {{
            background: var(--danger-color);
            color: white;
        }}
        
        .bundle-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        
        .detail-item {{
            padding: 8px;
            background: var(--light-bg);
            border-radius: 5px;
        }}
        
        .detail-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 3px;
        }}
        
        .score-bar {{
            background: #e0e0e0;
            height: 8px;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }}
        
        .score-fill {{
            height: 100%;
            border-radius: 4px;
        }}
        
        .score-impact {{
            background: #1565c0;
        }}
        
        .score-leverage {{
            background: #7cb342;
        }}
        
        .score-equity {{
            background: #8e24aa;
        }}
        
        .score-feasibility {{
            background: #00838f;
        }}
        
        .indicator-card {{
            background: #fafafa;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }}
        
        .indicator-type {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 10px;
        }}
        
        .type-output {{ background: #e3f2fd; color: #1565c0; }}
        .type-outcome {{ background: #e8f5e9; color: #2e7d32; }}
        .type-governance {{ background: #fce4ec; color: #c2185b; }}
        .type-equity {{ background: #f3e5f5; color: #7b1fa2; }}
        .type-capacity {{ background: #fff3e0; color: #ef6c00; }}
        .type-risk {{ background: #ffebee; color: #c62828; }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
            .toc {{
                page-break-after: always;
            }}
            h2 {{
                page-break-before: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Historia 5: Diseño de Portafolio SbN + Plan de Monitoreo</h1>
        <p><strong>Portafolio de Acciones SbN + Plan de Monitoreo</strong></p>
        
        <div class="metadata">
            <strong>Organización:</strong> {org_name}<br>
            <strong>Generado:</strong> {timestamp}<br>
            <strong>Archivo de entrada:</strong> {input_path}<br>
            <strong>Alcance del Análisis:</strong> Portafolio SbN, Priorización (Do Now/Next/Later), Plan de Monitoreo, Cobertura de Datos
        </div>
        
        <div class="toc">
            <h3>📋 Tabla de Contenidos</h3>
            <ul>
                <li><a href="#executive-summary">1. Resumen Ejecutivo</a></li>
                <li><a href="#portfolio-evidence">2. Evidencia del Portafolio</a></li>
                <li><a href="#bundle-details">3. Detalles de los Paquetes</a></li>
                <li><a href="#monitoring-plan">4. Plan de Monitoreo</a></li>
                <li><a href="#visualizations">5. Visualizaciones</a></li>
                <li><a href="#data-coverage">6. Cobertura y Calidad</a></li>
            </ul>
        </div>
        
        {content}
        
        <hr>
        <p style="text-align: center; color: #666; font-size: 0.85em;">
            Generado por Storyline 5 Pipeline v1.0.0 | Metodología PARES<br>
            © 2026 - Para uso analítico interno
        </p>
    </div>
</body>
</html>
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def encode_image_base64(image_path: str) -> str:
    """Encode an image file to base64 string."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    except Exception as e:
        logger.warning(f"Could not encode image {image_path}: {e}")
        return ""


def df_to_html(
    df: pd.DataFrame,
    max_rows: int = 20,
    float_format: str = ":.2f",
) -> str:
    """Convert DataFrame to styled HTML table."""
    if df.empty:
        return "<p><em>No data available / Sin datos disponibles</em></p>"
    
    df_display = df.head(max_rows).copy()
    
    # Format numeric columns
    for col in df_display.select_dtypes(include=["float64", "float32"]).columns:
        df_display[col] = df_display[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    
    html = df_display.to_html(index=False, classes="", na_rep="—")
    
    if len(df) > max_rows:
        html += f"<p><em>Mostrando {max_rows} de {len(df)} filas</em></p>"
    
    return html


def embed_image(path: str, caption: str = "") -> str:
    """Embed an image as base64 in HTML."""
    if not path or not Path(path).exists():
        return ""
    
    b64 = encode_image_base64(path)
    if not b64:
        return ""
    
    html = f'<div class="figure-container">'
    html += f'<img src="data:image/png;base64,{b64}" alt="{caption}">'
    if caption:
        html += f'<p class="figure-caption">{caption}</p>'
    html += '</div>'
    return html


def get_tier_class(tier: str) -> str:
    """Get CSS class for tier."""
    tier_lower = str(tier).lower().replace(" ", "-")
    return tier_lower


def get_tier_badge_class(tier: str) -> str:
    """Get CSS class for tier badge."""
    if "now" in str(tier).lower():
        return "tier-do-now"
    elif "next" in str(tier).lower():
        return "tier-do-next"
    else:
        return "tier-do-later"


# =============================================================================
# SECTION GENERATORS
# =============================================================================

def generate_executive_summary(
    portfolio_tables: Dict[str, pd.DataFrame],
    monitoring_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate executive summary section."""
    html = '<section id="executive-summary">'
    html += '<h2>1. Resumen Ejecutivo</h2>'
    
    # Count bundles
    bundles_overall = portfolio_tables.get("BUNDLES_OVERALL", pd.DataFrame())
    bundles_by_grupo = portfolio_tables.get("BUNDLES_BY_GRUPO", pd.DataFrame())
    
    overall_count = len(bundles_overall)
    by_grupo_count = len(bundles_by_grupo)
    
    # Tier counts from balanced scenario
    tier_counts = {"Do now": 0, "Do next": 0, "Do later": 0}
    balanced_overall = portfolio_tables.get("BUNDLE_RANKING_OVERALL_BALANCED", pd.DataFrame())
    if not balanced_overall.empty and "tier" in balanced_overall.columns:
        tier_counts = balanced_overall["tier"].value_counts().to_dict()
    
    indicators = monitoring_tables.get("INDICATORS", pd.DataFrame())
    indicator_count = len(indicators)
    
    # Stats cards
    html += '<div class="stats-grid">'
    html += f'<div class="stat-card"><div class="stat-value">{overall_count}</div><div class="stat-label">Paquetes Totales</div></div>'
    html += f'<div class="stat-card"><div class="stat-value">{by_grupo_count}</div><div class="stat-label">Paquetes por Grupo</div></div>'
    html += f'<div class="stat-card"><div class="stat-value">{tier_counts.get("Do now", 0)}</div><div class="stat-label">Prioridad Inmediata</div></div>'
    html += f'<div class="stat-card"><div class="stat-value">{indicator_count}</div><div class="stat-label">Indicadores de Monitoreo</div></div>'
    html += '</div>'
    
    # Key findings
    html += '<div class="info">'
    html += '<strong>Hallazgos Clave:</strong>'
    html += '<ul>'
    html += f'<li>El portafolio incluye <strong>{overall_count} paquetes candidatos</strong> a nivel de paisaje general</li>'
    html += f'<li><strong>{tier_counts.get("Do now", 0)} paquetes</strong> recomendados para acción inmediata ("Acción inmediata") basados en un puntaje equilibrado</li>'
    html += f'<li>El plan de monitoreo incluye <strong>{indicator_count} indicadores</strong> de tipo PRODUCTO, RESULTADO, GOBERNANZA y EQUIDAD</li>'
    html += '</ul>'
    html += '</div>'
    
    # Top bundles table (balanced scenario)
    html += '<h3>Top 5 Paquetes (Escenario Equilibrado)</h3>'
    if not balanced_overall.empty:
        top5 = balanced_overall.head(5)[["rank", "mdv_name", "grupo", "portfolio_score", "tier"]].copy()
        top5["tier"] = top5["tier"].map(TIER_NAMES).fillna(top5["tier"])
        top5.columns = ["Rango", "MdV", "Grupo", "Puntaje", "Prioridad"]
        html += df_to_html(top5, max_rows=5)
    else:
        html += '<p><em>No hay datos de clasificación disponibles</em></p>'
    
    # Tier distribution chart
    for scenario in ["balanced"]:
        key = f"tier_distribution_{scenario}"
        if key in figures:
            html += embed_image(figures[key], f"Distribución de Prioridad (Escenario Equilibrado)")
    
    html += '</section>'
    return html


def generate_portfolio_evidence(
    portfolio_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate portfolio evidence section."""
    html = '<section id="portfolio-evidence">'
    html += '<h2>2. Evidencia del Portafolio</h2>'
    
    html += '<div class="info">'
    html += '<strong>Enfoque Basado en Evidencia:</strong> '
    html += 'Todos los paquetes están etiquetados como "candidatos a ser medidos/validados". No declaramos efectos ecológicos, solo adjuntamos evidencia de los datos de línea base.'
    html += '</div>'
    
    # Portfolio matrix (balanced)
    if "portfolio_matrix_overall_balanced" in figures:
        html += '<h3>Matriz de Portafolio</h3>'
        html += embed_image(
            figures["portfolio_matrix_overall_balanced"],
            "Matriz de Portafolio: X=Viabilidad, Y=Potencial de Impacto, Tamaño=Urgencia de Equidad"
        )
    
    # Stacked components
    if "stacked_components_balanced" in figures:
        html += '<h3>Contribución de Componentes</h3>'
        html += embed_image(
            figures["stacked_components_balanced"],
            "Componentes apilados para los 10 principales paquetes mostrando el peso relativo de cada factor"
        )
    
    # Evidence table
    evidence_overall = portfolio_tables.get("BUNDLE_EVIDENCE_OVERALL", pd.DataFrame())
    if not evidence_overall.empty:
        html += '<h3>Resumen de Evidencia</h3>'
        html += df_to_html(evidence_overall, max_rows=30)
    
    html += '</section>'
    return html


def generate_bundle_details(
    portfolio_tables: Dict[str, pd.DataFrame],
) -> str:
    """Generate bundle details section with cards."""
    html = '<section id="bundle-details">'
    html += '<h2>3. Detalles de los Paquetes</h2>'
    
    balanced_overall = portfolio_tables.get("BUNDLE_RANKING_OVERALL_BALANCED", pd.DataFrame())
    
    if balanced_overall.empty:
        html += '<p><em>No hay datos de paquetes disponibles</em></p>'
        html += '</section>'
        return html
    
    # Show top 10 bundles as cards
    for _, row in balanced_overall.head(10).iterrows():
        tier = row.get("tier", "Do later")
        tier_display = TIER_NAMES.get(tier, tier)
        tier_class = get_tier_class(tier)
        badge_class = get_tier_badge_class(tier)
        
        html += f'<div class="bundle-card {tier_class}">'
        html += '<div class="bundle-header">'
        html += f'<span class="bundle-title">#{int(row.get("rank", 0))}: {row.get("mdv_name", "Desconocido")}</span>'
        html += f'<span class="tier-badge {badge_class}">{tier_display}</span>'
        html += '</div>'
        
        html += '<div class="bundle-details">'
        
        # Services
        html += '<div class="detail-item">'
        html += '<div class="detail-label">Servicios Críticos</div>'
        html += f'<div>{row.get("services_text", "—")}</div>'
        html += '</div>'
        
        # Ecosystems
        html += '<div class="detail-item">'
        html += '<div class="detail-label">Ecosistemas de Soporte</div>'
        html += f'<div>{row.get("ecosystems_text", "—")}</div>'
        html += '</div>'
        
        # Threats
        html += '<div class="detail-item">'
        html += '<div class="detail-label">Amenazas Clave</div>'
        html += f'<div>{row.get("threats_text", "—")}</div>'
        html += '</div>'
        
        # Grupo
        html += '<div class="detail-item">'
        html += '<div class="detail-label">Grupo</div>'
        html += f'<div>{row.get("grupo", "TODOS")}</div>'
        html += '</div>'
        
        html += '</div>'  # bundle-details
        
        # Score bars
        html += '<div style="margin-top: 15px;">'
        
        scores = [
            ("Potencial de Impacto", row.get("impact_potential_norm", 0.5), "score-impact"),
            ("Apalancamiento", row.get("leverage", 0.5), "score-leverage"),
            ("Urgencia de Equidad", row.get("evi_score", 0.5), "score-equity"),
            ("Viabilidad", row.get("feasibility_score", 0.5), "score-feasibility"),
        ]
        
        for label, value, css_class in scores:
            pct = min(100, max(0, float(value) * 100))
            html += f'<div style="margin: 5px 0;">'
            html += f'<small>{label}: {value:.2f}</small>'
            html += f'<div class="score-bar"><div class="score-fill {css_class}" style="width: {pct}%"></div></div>'
            html += '</div>'
        
        html += '</div>'
        html += '</div>'  # bundle-card
    
    html += '</section>'
    return html


def generate_monitoring_plan_section(
    monitoring_tables: Dict[str, pd.DataFrame],
) -> str:
    """Generate monitoring plan section."""
    html = '<section id="monitoring-plan">'
    html += '<h2>4. Plan de Monitoreo</h2>'
    
    html += '<div class="info">'
    html += '<strong>Indicadores Listos para MEAL:</strong> '
    html += 'Estos indicadores están diseñados para seguimiento/medición y no declaran causalidad o impacto.'
    html += '</div>'
    
    # Indicator library
    indicators = monitoring_tables.get("INDICATORS", pd.DataFrame())
    html += '<h3>Biblioteca de Indicadores</h3>'
    
    if not indicators.empty:
        for _, row in indicators.iterrows():
            ind_type = row.get("indicator_type", "OUTPUT")
            if pd.isna(ind_type):
                ind_type = "OUTPUT"
            type_display = INDICATOR_TYPE_NAMES.get(ind_type, ind_type)
            type_class = f"type-{str(ind_type).lower()}"
            
            html += '<div class="indicator-card">'
            html += f'<span class="indicator-type {type_class}">{type_display}</span>'
            html += f'<strong>{row.get("indicator_name", "")}</strong>'
            html += f'<p style="margin: 10px 0 5px 0; color: #666;">{row.get("definition", "")}</p>'
            html += f'<small><strong>Unidad:</strong> {row.get("unit_of_measure", "")} | '
            html += f'<strong>Frecuencia:</strong> {row.get("frequency", "")} | '
            html += f'<strong>Desagregación:</strong> {row.get("disaggregation_suggestions", "")}</small>'
            html += '</div>'
    else:
        html += '<p><em>No hay indicadores definidos</em></p>'
    
    # Bundle-to-indicator mapping
    mapping = monitoring_tables.get("BUNDLES_TO_INDICATORS", pd.DataFrame())
    html += '<h3>Mapeo Paquete-Indicador</h3>'
    
    if not mapping.empty:
        # Simplified table view - use indicator_name instead of indicator_id
        display_cols = ["mdv_name", "grupo", "indicator_name", "rationale_link_to_evidence"]
        avail_cols = [c for c in display_cols if c in mapping.columns]
        display = mapping[avail_cols].copy()
        display.columns = ["Nombre MdV", "Grupo", "Indicador", "Razón/Vínculo"][:len(avail_cols)]
        html += df_to_html(display, max_rows=25)
    else:
        html += '<p><em>No hay mapeos disponibles</em></p>'
    
    html += '</section>'
    return html


def generate_visualizations_section(figures: Dict[str, str]) -> str:
    """Generate visualizations section."""
    html = '<section id="visualizations">'
    html += '<h2>5. Visualizaciones</h2>'
    
    # Group figures by type
    figure_groups = {
        "Matrices de Portafolio": [k for k in figures if "portfolio_matrix" in k],
        "Análisis de Componentes": [k for k in figures if "component" in k or "stacked" in k],
        "Comparaciones por Grupo": [k for k in figures if "by_grupo" in k],
        "Análisis de Frecuencia": [k for k in figures if "top_services" in k or "top_threats" in k],
    }
    
    for group_name, fig_keys in figure_groups.items():
        if fig_keys:
            html += f'<h3>{group_name}</h3>'
            for key in fig_keys:
                if key in figures:
                    caption = key.replace("_", " ").title()
                    html += embed_image(figures[key], caption)
    
    html += '</section>'
    return html


def generate_data_coverage_section(
    portfolio_tables: Dict[str, pd.DataFrame],
    warnings: List[str],
    tables: Dict[str, pd.DataFrame],
) -> str:
    """Generate data coverage and QA section."""
    html = '<section id="data-coverage">'
    html += '<h2>6. Cobertura de Datos y Calidad</h2>'
    
    # Coverage summary
    coverage = portfolio_tables.get("COVERAGE_SUMMARY", pd.DataFrame())
    if not coverage.empty:
        html += '<h3>Disponibilidad de Datos</h3>'
        html += df_to_html(coverage, max_rows=30)
    
    # Warnings
    if warnings:
        html += '<h3>Advertencias</h3>'
        html += '<div class="warning">'
        html += '<ul>'
        for w in warnings:
            html += f'<li>{w}</li>'
        html += '</ul>'
        html += '</div>'
    
    # QA sheets if present
    qa_sheets = ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]
    has_qa = False
    for qa_sheet in qa_sheets:
        qa_df = tables.get(qa_sheet, pd.DataFrame())
        if not qa_df.empty:
            if not has_qa:
                html += '<h3>Hallazgos de Calidad</h3>'
                has_qa = True
            html += f'<h4>{qa_sheet}</h4>'
            html += df_to_html(qa_df, max_rows=10)
    
    if not has_qa and not warnings:
        html += '<div class="success">'
        html += '<strong>✓ No se detectaron problemas de calidad</strong>'
        html += '</div>'
    
    html += '</section>'
    return html


# =============================================================================
# MASTER FUNCTION
# =============================================================================

def generate_report(
    portfolio_tables: Dict[str, pd.DataFrame],
    monitoring_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str],
    tables: Dict[str, pd.DataFrame],
    org_name: str = "Organización",
) -> str:
    """
    Generate the complete HTML report.
    
    Args:
        portfolio_tables: Portfolio output tables
        monitoring_tables: Monitoring plan tables
        figures: Dict of figure name -> path
        input_path: Path to input file
        warnings: List of warning messages
        tables: Raw input tables (for QA)
        org_name: Name of the organization for metadata
        
    Returns:
        Complete HTML report string
    """
    # Generate all sections
    content = ""
    content += generate_executive_summary(portfolio_tables, monitoring_tables, figures)
    content += generate_portfolio_evidence(portfolio_tables, figures)
    content += generate_bundle_details(portfolio_tables)
    content += generate_monitoring_plan_section(monitoring_tables)
    content += generate_visualizations_section(figures)
    content += generate_data_coverage_section(portfolio_tables, warnings, tables)
    
    # Fill template
    html = HTML_TEMPLATE.format(
        org_name=org_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        input_path=input_path,
        content=content,
    )
    
    logger.info("Generated HTML report")
    return html
