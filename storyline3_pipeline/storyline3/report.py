#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 3 Report Module
Generates HTML report with embedded tables and images.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# HTML TEMPLATES
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 3: Equidad y Vulnerabilidad Diferenciada - Informe Diagnóstico</title>
    <style>
        :root {{
            --primary-color: #5e35b1;
            --secondary-color: #7e57c2;
            --accent-color: #b39ddb;
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
            background-color: #ede7f6;
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
        <h1>📊 Historia 3: Equidad y Vulnerabilidad Diferenciada</h1>
        <p><strong>Informe Diagnóstico - ¿Quiénes son los más afectados?</strong></p>
        
        <div class="metadata">
            <strong>Organización:</strong> {org_name}<br>
            <strong>Generado:</strong> {timestamp}<br>
            <strong>Archivo de entrada:</strong> {input_file}<br>
            <strong>Alcance del Análisis:</strong> Impactos Diferenciados, Barreras de Acceso a Servicios, Brechas de Capacidad
        </div>
        
        <div class="toc">
            <h3>📋 Tabla de Contenidos</h3>
            <ul>
                <li><a href="#executive-summary">1. Resumen Ejecutivo</a></li>
                <li><a href="#differentiated-impacts">2. Impactos Diferenciados</a></li>
                <li><a href="#service-access">3. Acceso a Servicios y Barreras</a></li>
                <li><a href="#capacity-gaps">4. Brechas de Capacidad</a></li>
                <li><a href="#data-quality">5. Resumen de Calidad de Datos</a></li>
            </ul>
        </div>
        
        {content}
        
        <hr>
        <p style="text-align: center; color: #666; font-size: 0.85em;">
            Generado por Storyline 3 Pipeline v1.0.0 | Metodología PARES<br>
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
    
    # Count groups
    dif_overall = metrics_tables.get("DIF_LIVELIHOOD_OVERALL", pd.DataFrame())
    n_groups = len(dif_overall)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_groups}</div>
        <div class="stat-label">Grupos Vulnerables Identificados</div>
    </div>
    '''
    
    # EVI scores
    evi_by_grupo = metrics_tables.get("EVI_BY_GRUPO", pd.DataFrame())
    n_grupos = len(evi_by_grupo)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_grupos}</div>
        <div class="stat-label">Áreas Geográficas (Grupos)</div>
    </div>
    '''
    
    # Barriers
    barriers = metrics_tables.get("BARRIERS_FREQ_OVERALL", pd.DataFrame())
    n_barriers = len(barriers)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_barriers}</div>
        <div class="stat-label">Barreras de Acceso Distintas</div>
    </div>
    '''
    
    # Capacity questions
    cap_q = metrics_tables.get("CAPACITY_QUESTIONS_OVERALL", pd.DataFrame())
    n_cap = len(cap_q)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_cap}</div>
        <div class="stat-label">Preguntas de Capacidad Analizadas</div>
    </div>
    '''
    
    content += '</div>'  # stats-grid
    
    # EVI table
    if not evi_by_grupo.empty:
        content += '<h3>🎯 Índice de Vulnerabilidad de Equidad (EVI) por Grupo</h3>'
        cols = ["grupo", "EVI", "dif_norm", "bar_norm", "inc_norm", "cap_norm"]
        cols = [c for c in cols if c in evi_by_grupo.columns]
        display = evi_by_grupo[cols].sort_values("EVI", ascending=False).copy()
        display.columns = ["Grupo", "Indice EVI", "Diferenciado (Norm)", "Barreras (Norm)", "Inclusión (Norm)", "Capacidad (Norm)"][:len(cols)]
        content += df_to_html(display, max_rows=10)
    
    # EVI figure
    if "bar_evi_by_grupo" in figures:
        content += embed_image(figures["bar_evi_by_grupo"], "Índice de Vulnerabilidad de Equidad por Área Geográfica")
    
    content += '</section>'
    return content


def generate_differentiated_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate differentiated impacts section."""
    content = '<section id="differentiated-impacts" class="section"><h2>2. Impactos Diferenciados</h2>'
    content += '<p>Esta sección identifica qué subgrupos son los más afectados por las amenazas y su intensidad de exposición.</p>'
    
    has_data = False
    
    # Overall groups
    dif_overall = metrics_tables.get("DIF_LIVELIHOOD_OVERALL", pd.DataFrame())
    if not dif_overall.empty:
        has_data = True
        content += '<h3>👥 Subgrupos Afectados (General)</h3>'
        display = dif_overall.copy()
        if "dif_group" in display.columns:
            display.rename(columns={"dif_group": "Subgrupo"}, inplace=True)
        if "intensity" in display.columns:
            display.rename(columns={"intensity": "Intensidad"}, inplace=True)
        content += df_to_html(display, max_rows=15)
    
    # DIF figure
    if "bar_dif_groups_overall" in figures:
        has_data = True
        content += embed_image(figures["bar_dif_groups_overall"], "Principales Subgrupos Afectados por Intensidad")
    
    # Intensity
    intensity = metrics_tables.get("DIF_INTENSITY_OVERALL", pd.DataFrame())
    if not intensity.empty:
        has_data = True
        content += '<h3>📊 Intensidad por Subgrupo</h3>'
        display = intensity.sort_values("intensity", ascending=False).copy()
        if "dif_group" in display.columns:
            display.rename(columns={"dif_group": "Subgrupo"}, inplace=True)
        if "intensity" in display.columns:
            display.rename(columns={"intensity": "Intensidad"}, inplace=True)
        content += df_to_html(display, max_rows=10)
    
    if not has_data:
        content += '''
        <div class="warning">
            <strong>No hay datos de impacto diferenciado disponibles.</strong><br>
            Esta sección requiere las hojas: <code>TIDY_4_2_1_DIFERENCIADO</code> o <code>TIDY_4_2_2_DIFERENCIADO</code><br>
            Por favor, asegúrese de que su libro de entrada contenga estas tablas con columnas como: <code>dif_group</code>, <code>diferenciado</code>, <code>grupo_afectado</code>
        </div>
        '''
    
    content += '</section>'
    return content


def generate_access_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate service access and barriers section."""
    content = '<section id="service-access" class="section"><h2>3. Acceso a Servicios y Barreras</h2>'
    content += '<p>Análisis de barreras comunes y patrones de inclusión reportados por los Medios de Vida.</p>'
    
    has_data = False
    
    # Barriers
    barriers = metrics_tables.get("BARRIERS_FREQ_OVERALL", pd.DataFrame())
    if not barriers.empty:
        has_data = True
        content += '<h3>🚧 Barreras de Acceso más Comunes</h3>'
        display = barriers.copy()
        if "barrier" in display.columns:
            display.rename(columns={"barrier": "Barrera"}, inplace=True)
        if "count" in display.columns:
            display.rename(columns={"count": "Frecuencia"}, inplace=True)
        content += df_to_html(display, max_rows=15)
    
    # Barriers figure
    if "bar_top_barriers_overall" in figures:
        has_data = True
        content += embed_image(figures["bar_top_barriers_overall"], "Principales Barreras de Acceso a Servicios")
    
    # Barrier rates
    rates = metrics_tables.get("BARRIER_RATES_BY_GRUPO", pd.DataFrame())
    if not rates.empty:
        has_data = True
        content += '<h3>📈 Tasas de Barreras e Inclusión por Grupo</h3>'
        cols = [c for c in ["grupo", "barriers_rate", "inclusion_rate"] if c in rates.columns]
        display = rates[cols].copy()
        display.columns = ["Grupo", "Tasa de Barreras", "Tasa de Inclusión"][:len(cols)]
        content += df_to_html(display, max_rows=10)
    
    if not has_data:
        content += '''
        <div class="warning">
            <strong>No hay datos de acceso a servicios disponibles.</strong><br>
            Esta sección requiere la hoja: <code>TIDY_3_5_SE_MDV</code><br>
            Por favor, asegúrese de que su libro de entrada contenga columnas de barreras/acceso como: <code>barreras</code>, <code>acceso</code>, <code>inclusion</code>
        </div>
        '''
    
    content += '</section>'
    return content


def generate_capacity_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate capacity gaps section."""
    content = '<section id="capacity-gaps" class="section"><h2>4. Brechas de Capacidad</h2>'
    content += '<p>Los puntajes reflejan la capacidad individual y colectiva para adaptarse a las amenazas (0 = Baja Capacidad, 1 = Alta Capacidad).</p>'
    
    has_data = False
    
    # Questions
    questions = metrics_tables.get("CAPACITY_QUESTIONS_OVERALL", pd.DataFrame())
    if not questions.empty:
        has_data = True
        content += '<h3>❓ Preguntas con Menor Capacidad</h3>'
        sorted_q = questions.sort_values("response_0_1", ascending=True).copy() if "response_0_1" in questions.columns else questions.copy()
        # Prefer question_text, drop question_id if both exist
        if "question_text" in sorted_q.columns:
            if "question_id" in sorted_q.columns:
                sorted_q.drop(columns=["question_id"], inplace=True)
            sorted_q.rename(columns={"question_text": "Pregunta"}, inplace=True)
        elif "question_id" in sorted_q.columns:
            sorted_q.rename(columns={"question_id": "Pregunta"}, inplace=True)
        if "response_0_1" in sorted_q.columns:
            sorted_q.rename(columns={"response_0_1": "Puntaje (0-1)"}, inplace=True)
        content += df_to_html(sorted_q, max_rows=10)

    
    # Capacity figure
    if "bar_capacity_bottom_questions_overall" in figures:
        has_data = True
        content += embed_image(figures["bar_capacity_bottom_questions_overall"], "Cuellos de Botella de Capacidad")
    
    # By MDV
    cap_mdv = metrics_tables.get("CAPACITY_BY_MDV_OVERALL", pd.DataFrame())
    if not cap_mdv.empty:
        has_data = True
        content += '<h3>🌾 Capacidad por Medio de Vida</h3>'
        sorted_mdv = cap_mdv.sort_values("response_0_1", ascending=True).copy() if "response_0_1" in cap_mdv.columns else cap_mdv.copy()
        # Prefer mdv_name, drop mdv_id if both exist
        if "mdv_name" in sorted_mdv.columns:
            if "mdv_id" in sorted_mdv.columns:
                sorted_mdv.drop(columns=["mdv_id"], inplace=True)
            sorted_mdv.rename(columns={"mdv_name": "Medio de Vida"}, inplace=True)
        elif "mdv_id" in sorted_mdv.columns:
            sorted_mdv.rename(columns={"mdv_id": "Medio de Vida"}, inplace=True)
        if "response_0_1" in sorted_mdv.columns:
            sorted_mdv.rename(columns={"response_0_1": "Capacidad (0-1)"}, inplace=True)
        content += df_to_html(sorted_mdv, max_rows=10)

    
    if not has_data:
        content += '''
        <div class="warning">
            <strong>No hay datos de encuesta de capacidad disponibles.</strong><br>
            Esta sección requiere las hojas: <code>TIDY_7_1_RESPONDENTS</code> y <code>TIDY_7_1_RESPONSES</code><br>
            Por favor, asegúrese de que su libro de entrada contenga datos de respuestas a la encuesta.
        </div>
        '''
    
    content += '</section>'
    return content


def generate_qa_section(
    tables: Dict[str, pd.DataFrame],
) -> str:
    """Generate QA summary section."""
    content = '<section id="data-quality" class="section"><h2>5. Resumen de Calidad de Datos</h2>'
    
    qa_sheets = ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]
    has_qa = False
    
    for sheet in qa_sheets:
        qa_df = tables.get(sheet, pd.DataFrame())
        if not qa_df.empty:
            has_qa = True
            content += f'<h3>{sheet}</h3>'
            content += df_to_html(qa_df, max_rows=10)
    
    if not has_qa:
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
    tables: Optional[Dict[str, pd.DataFrame]] = None,
    org_name: str = "Organización",
) -> str:
    """
    Generate complete HTML report.
    
    Args:
        metrics_tables: Dict of computed metrics tables
        figures: Dict of figure name -> file path
        input_path: Path to input XLSX
        tables: Optional dict of input tables for QA section
        
    Returns:
        Complete HTML report string
    """
    content = ""
    
    # Executive summary
    content += generate_executive_summary(metrics_tables, figures)
    
    # Differentiated impacts
    content += generate_differentiated_section(metrics_tables, figures)
    
    # Service access
    content += generate_access_section(metrics_tables, figures)
    
    # Capacity gaps
    content += generate_capacity_section(metrics_tables, figures)
    
    # QA section
    content += generate_qa_section(tables or {})
    
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
