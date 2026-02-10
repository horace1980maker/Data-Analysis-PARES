#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 Report Module
Generates HTML report with embedded tables and images.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import GRUPO_COL, SE_CODE_NAMES

# SE_CODE_NAMES moved to config.py
def expand_se(code):
    """Format as 'Code - Name'."""
    c = str(code).strip()
    name = SE_CODE_NAMES.get(c, c)
    if name != c:
        return f"{c} - {name}"
    return c

logger = logging.getLogger(__name__)


# =============================================================================
# HTML TEMPLATES
# =============================================================================

# HTML template with embedded CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 2: Líneas de Vida de Servicios Ecosistémicos - Informe Diagnóstico</title>
    <style>
        :root {{
            --primary-color: #2c5530;
            --secondary-color: #4a7c59;
            --accent-color: #7cb342;
            --warning-color: #ff9800;
            --danger-color: #e53935;
            --light-bg: #f5f5f5;
            --card-bg: #ffffff;
            --text-color: #333333;
            --border-color: #e0e0e0;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--light-bg);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: var(--primary-color);
            border-bottom: 3px solid var(--accent-color);
            padding-bottom: 15px;
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
            font-size: 0.9em;
        }}
        
        .metadata strong {{
            color: var(--primary-color);
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .subsection {{
            margin-left: 20px;
            padding: 15px;
            background: var(--light-bg);
            border-radius: 5px;
            margin-top: 15px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1.25rem;
            border-radius: 12px;
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
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .figure-caption {{
            font-style: italic;
            color: #666;
            margin-top: 10px;
        }}
        
        .warning {{
            background: #fff3e0;
            border-left: 4px solid var(--warning-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .error {{
            background: #ffebee;
            border-left: 4px solid var(--danger-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .toc {{
            background: var(--light-bg);
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        
        .toc h3 {{
            margin-top: 0;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .toc li {{
            padding: 5px 0;
        }}
        
        .toc a {{
            color: var(--secondary-color);
            text-decoration: none;
        }}
        
        .toc a:hover {{
            color: var(--primary-color);
            text-decoration: underline;
        }}

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
        <h1>📊 Historia 2: Líneas de Vida de Servicios Ecosistémicos</h1>
        <p><strong>Informe Diagnóstico - Análisis de Seguridad Basada en la Naturaleza</strong></p>
        
        <div class="metadata">
            <strong>Organización:</strong> {org_name}<br>
            <strong>Generado:</strong> {timestamp}<br>
            <strong>Archivo de Entrada:</strong> {input_file}<br>
            <strong>Alcance del Análisis:</strong> Conectividad de Ecosistemas y Criticidad de Servicios
        </div>
        
        <div class="toc">
            <h3>📋 Tabla de Contenidos</h3>
            <ul>
                <li><a href="#executive-summary">1. Resumen Ejecutivo</a></li>
                <li><a href="#ecosystem-analysis">2. Análisis de Ecosistemas</a></li>
                <li><a href="#service-criticality">3. Análisis de Criticidad de Servicios</a></li>
                <li><a href="#threats-vulnerability">4. Amenazas y Vulnerabilidad</a></li>
                <li><a href="#data-quality">5. Resumen de Calidad de Datos</a></li>
            </ul>
        </div>
        
        {content}
        
        <hr>
        <p style="text-align: center; color: #666; font-size: 0.85em;">
            Generado por Storyline 2 Pipeline v1.0.0 | Metodología PARES<br>
            © 2026 - Para uso analítico interno
        </p>
    </div>
</body>
</html>
"""


# =============================================================================
# TABLE RENDERING
# =============================================================================

def df_to_html(
    df: pd.DataFrame,
    max_rows: int = 20,
    float_format: str = ":.2f",
) -> str:
    """Convert DataFrame to styled HTML table."""
    if df.empty:
        return "<p><em>No hay datos disponibles</em></p>"
    
    # Limit rows
    display_df = df.head(max_rows).copy()
    
    # Format floats
    for col in display_df.select_dtypes(include=["float64", "float32"]).columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    
    html = display_df.to_html(index=False, classes="data-table", escape=False)
    
    if len(df) > max_rows:
        html += f"<p><em>Mostrando las primeras {max_rows} de {len(df)} filas</em></p>"
    
    return html


def embed_image(path: str, caption: str = "") -> str:
    """Embed an image as base64 in HTML."""
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        html = f'<div class="figure-container"><img src="data:image/png;base64,{b64}" alt="Figure">'
        if caption:
            html += f'<p class="figure-caption">{caption}</p>'
        html += '</div>'
        return html
    except Exception as e:
        logger.warning(f"Failed to embed image {path}: {e}")
        return f'<div class="warning">Imagen no disponible: {Path(path).name}</div>'


# =============================================================================
# SECTION GENERATORS
# =============================================================================

def generate_executive_summary(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate executive summary section."""
    content = '<section id="executive-summary" class="section"><h2>1. Resumen Ejecutivo</h2>'
    
    # Stats cards
    content += '<div class="stats-grid">'
    
    # Count services
    sci_overall = metrics_tables.get("service_sci_components_overall", pd.DataFrame())
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{len(sci_overall)}</div>
        <div class="stat-label">Servicios Ecosistémicos Analizados</div>
    </div>
    '''
    
    # Count ecosystems
    eco_overall = metrics_tables.get("ecosystem_summary_overall", pd.DataFrame())
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{len(eco_overall)}</div>
        <div class="stat-label">Ecosistemas Mapeados</div>
    </div>
    '''
    
    # Count threats
    tps_overall = metrics_tables.get("tps_overall", pd.DataFrame())
    n_threats = tps_overall["amenaza_id"].nunique() if tps_overall is not None and "amenaza_id" in tps_overall.columns else 0
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_threats}</div>
        <div class="stat-label">Amenazas Identificadas</div>
    </div>
    '''
    
    # Count livelihoods affected
    ivl_overall = metrics_tables.get("ivl_overall", pd.DataFrame())
    n_mdv = ivl_overall["mdv_id"].nunique() if ivl_overall is not None and "mdv_id" in ivl_overall.columns else 0
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_mdv}</div>
        <div class="stat-label">Medios de Vida Expuestos</div>
    </div>
    '''
    
    content += '</div>'  # stats-grid
    
    # Top services (balanced scenario)
    content += '<h3>🎯 Principales Servicios Críticos (SCI - Equilibrado)</h3>'
    balanced_ranking = metrics_tables.get("service_ranking_overall_balanced", pd.DataFrame())
    if not balanced_ranking.empty:
        cols = ["rank", "se_key", "sci"]
        cols = [c for c in cols if c in balanced_ranking.columns]
        display = balanced_ranking[cols].copy()
        # Expand SE codes to full names
        if "se_key" in display.columns:
            display["se_key"] = display["se_key"].apply(expand_se)
        display.columns = ["Rango", "Servicio Ecosistémico", "Puntaje SCI"][:len(cols)]
        content += df_to_html(display, max_rows=10)
    else:
        content += "<p><em>No hay ranking de servicios disponible</em></p>"

    
    # SCI figure
    if "sci_overall_balanced" in figures:
        content += embed_image(figures["sci_overall_balanced"], "Principales Servicios por Índice de Criticidad")
    
    content += '</section>'
    return content


def generate_ecosystem_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate ecosystem connectivity and ELI section."""
    content = '<section id="ecosystem-analysis" class="section"><h2>2. Análisis de Ecosistemas</h2>'
    
    # Ecosystem summary
    content += '<h3>🌳 Resumen de Conectividad de Ecosistemas</h3>'
    eco_overall = metrics_tables.get("ecosystem_summary_overall", pd.DataFrame())
    if not eco_overall.empty:
        cols = ["ecosistema", "n_obs", "n_services", "n_livelihoods", "connectivity_norm"]
        cols = [c for c in cols if c in eco_overall.columns]
        display = eco_overall[cols].copy()
        display.columns = ["Ecosistema", "Observaciones", "Servicios", "Medios de Vida", "Conectividad Norm."][:len(cols)]
        sorted_eco = display.sort_values("Conectividad Norm.", ascending=False) if "Conectividad Norm." in display.columns else display
        content += df_to_html(sorted_eco, max_rows=15)
    
    # ELI rankings
    content += '<h3>📈 Índice de Apalancamiento del Ecosistema (ELI)</h3>'
    eli_overall = metrics_tables.get("ecosystem_eli_overall", pd.DataFrame())
    if not eli_overall.empty:
        cols = ["ecosistema", "connectivity_norm", "mean_sci_norm", "eli"]
        cols = [c for c in cols if c in eli_overall.columns]
        display = eli_overall[cols].copy()
        display.columns = ["Ecosistema", "Conectividad", "Criticidad Prom.", "ELI"][:len(cols)]
        sorted_eli = display.sort_values("ELI", ascending=False) if "ELI" in display.columns else display
        content += df_to_html(sorted_eli, max_rows=10)
    
    # ELI figure
    if "eli_overall" in figures:
        content += embed_image(figures["eli_overall"], "Principales Ecosistemas por Índice de Apalancamiento")
    
    # Heatmap
    if "heatmap_eco_service" in figures:
        content += embed_image(figures["heatmap_eco_service"], "Matriz de Conectividad Ecosistema-Servicio")
    
    content += '</section>'
    return content


def generate_service_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate service criticality section."""
    content = '<section id="service-criticality" class="section"><h2>3. Análisis de Criticidad de Servicios</h2>'
    
    # SCI components
    content += '<h3>📊 Componentes de Criticidad del Servicio</h3>'
    sci_overall = metrics_tables.get("service_sci_components_overall", pd.DataFrame())
    if not sci_overall.empty:
        cols = ["se_key", "links_mdv", "users", "seasonality_fragility", "priority_weight"]
        cols = [c for c in cols if c in sci_overall.columns]
        display = sci_overall[cols].copy()
        if "se_key" in display.columns:
            display["se_key"] = display["se_key"].apply(expand_se)
        display.columns = ["Servicio Ecosistémico", "Vínculos MdV", "Usuarios", "Fragilidad Estacional", "Peso de Prioridad"][:len(cols)]
        content += df_to_html(display, max_rows=15)
    
    # Service-Livelihood heatmap
    if "heatmap_service_mdv" in figures:
        content += embed_image(figures["heatmap_service_mdv"], "Matriz de Dependencia Servicio-Medio de Vida")
    
    content += '</section>'
    return content


def generate_threat_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate threat pressure and vulnerability section."""
    content = '<section id="threats-vulnerability" class="section"><h2>4. Amenazas y Vulnerabilidad</h2>'
    
    # TPS summary
    content += '<h3>⚠️ Presión de Amenazas sobre los Servicios (TPS)</h3>'
    tps_overall = metrics_tables.get("tps_overall", pd.DataFrame())
    if not tps_overall.empty:
        # Aggregate by threat
        cols = ["amenaza", "se_key", "sum_pressure", "mean_pressure", "n_rows"]
        cols = [c for c in cols if c in tps_overall.columns]
        display = tps_overall[cols].copy()
        if "se_key" in display.columns:
            display["se_key"] = display["se_key"].apply(expand_se)
        display.columns = ["Amenaza", "Servicio Ecosistémico", "Presión Total", "Presión Promedio", "Filas"][:len(cols)]
        sorted_tps = display.sort_values("Presión Total", ascending=False) if "Presión Total" in display.columns else display
        content += df_to_html(sorted_tps, max_rows=15)
    
    # Threat pressure figure
    if "threat_pressure" in figures:
        content += embed_image(figures["threat_pressure"], "Principales Amenazas que Presionan los Servicios")
    
    # IVL summary
    content += '<h3>🔗 Vulnerabilidad Indirecta de los Medios de Vida (IVL)</h3>'
    ivl_overall = metrics_tables.get("ivl_overall", pd.DataFrame())
    if not ivl_overall.empty:
        cols = ["mdv_name", "amenaza", "sum_pressure_via_services"]
        cols = [c for c in cols if c in ivl_overall.columns]
        display = ivl_overall[cols].copy()
        display.columns = ["Medio de Vida", "Amenaza", "Presión Total vía Servicios"][:len(cols)]
        sorted_ivl = display.sort_values("Presión Total vía Servicios", ascending=False) if "Presión Total vía Servicios" in display.columns else display
        content += df_to_html(sorted_ivl, max_rows=15)
    
    # Livelihood exposure figure
    if "livelihood_exposure" in figures:
        content += embed_image(figures["livelihood_exposure"], "Principales Medios de Vida Expuestos (vía Servicios)")
    
    content += '</section>'
    return content


def generate_qa_section(
    tables: Dict[str, pd.DataFrame],
    warnings: List[str],
) -> str:
    """Generate QA summary section."""
    content = '<section id="data-quality" class="section"><h2>5. Resumen de Calidad de Datos</h2>'
    
    # Warnings
    if warnings:
        content += '<h3>⚠️ Advertencias</h3>'
        for w in warnings:
            content += f'<div class="warning">{w}</div>'
    
    # QA sheets
    qa_sheets = ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]
    has_qa = False
    
    for sheet in qa_sheets:
        qa_df = tables.get(sheet, pd.DataFrame())
        if not qa_df.empty:
            has_qa = True
            content += f'<h3>{sheet}</h3>'
            content += df_to_html(qa_df, max_rows=10)
    
    if not has_qa and not warnings:
        content += '<p>✅ No se detectaron problemas de calidad.</p>'
    
    content += '</section>'
    return content


# =============================================================================
# MAIN REPORT GENERATOR
# =============================================================================

def generate_report(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str],
    tables: Optional[Dict[str, pd.DataFrame]] = None,
    org_name: str = "Organización",
) -> str:
    """
    Generate complete HTML report.
    
    Args:
        metrics_tables: Dict of computed metrics tables
        figures: Dict of figure name -> file path
        input_path: Path to input file (for display)
        warnings: List of warning messages
        tables: Optional dict of input tables for QA section
        
    Returns:
        Complete HTML report string
    """
    content = ""
    
    # Executive summary
    content += generate_executive_summary(metrics_tables, figures)
    
    # Ecosystem analysis
    content += generate_ecosystem_section(metrics_tables, figures)
    
    # Service criticality
    content += generate_service_section(metrics_tables, figures)
    
    # Threats & vulnerability
    content += generate_threat_section(metrics_tables, figures)
    
    # QA section
    content += generate_qa_section(tables or {}, warnings)
    
    # Build final HTML
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_file = Path(input_path).name
    
    html = HTML_TEMPLATE.format(
        org_name=org_name,
        timestamp=timestamp,
        input_file=input_file,
        content=content,
    )
    
    logger.info("Generated HTML report")
    return html
