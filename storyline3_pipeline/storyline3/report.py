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
from . import narrative

logger = logging.getLogger(__name__)


# =============================================================================
# HTML TEMPLATES
# =============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 3: Equidad y Vulnerabilidad Diferenciada — Informe Interpretado</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #5e35b1;   /* Deep Purple 600 */
            --primary-light: #7e57c2; /* Deep Purple 400 */
            --accent: #b39ddb;    /* Deep Purple 200 */
            --accent-light: #d1c4e9;
            --warning: #ef6c00;
            --danger: #c62828;
            --info: #1565c0;
            --info-bg: #e3f2fd;
            --bg: #fafafa;
            --surface: #ffffff;
            --border: #e0e0e0;
            --text: #212121;
            --text-secondary: #616161;
            --text-light: #9e9e9e;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            font-size: 15px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            padding: 40px 32px;
        }}
        .report-header {{
            text-align: center;
            padding: 48px 24px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            border-radius: 16px;
            margin-bottom: 40px;
        }}
        .report-header h1 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .report-header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        .report-header .meta {{
            margin-top: 16px;
            font-size: 0.85rem;
            opacity: 0.7;
        }}

        /* Table of contents */
        .toc {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px 32px;
            margin-bottom: 40px;
        }}
        .toc h2 {{
            font-size: 1.1rem;
            color: var(--primary);
            margin-bottom: 12px;
        }}
        .toc ol {{
            padding-left: 20px;
        }}
        .toc li {{
            margin-bottom: 6px;
        }}
        .toc a {{
            color: var(--info);
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}

        /* Sections */
        section {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 32px;
        }}
        section h2 {{
            font-size: 1.4rem;
            color: var(--primary);
            border-bottom: 3px solid var(--accent);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        section h3 {{
            font-size: 1.15rem;
            color: var(--primary-light);
            margin: 28px 0 12px 0;
        }}
        section h4 {{
            font-size: 1rem;
            color: var(--text);
            margin: 20px 0 8px 0;
        }}

        /* Interpretation boxes */
        .interp {{
            background: #f3e5f5; /* Purple 50 */
            border-left: 4px solid var(--accent);
            border-radius: 0 8px 8px 0;
            padding: 16px 20px;
            margin: 16px 0;
            font-size: 0.95rem;
            color: #4a148c; /* Purple 900 */
        }}
        .interp strong {{
            color: var(--primary);
        }}
        .interp.what {{
            background: var(--info-bg);
            border-left-color: var(--info);
            color: #0d47a1;
        }}
        .interp.what strong {{
            color: var(--info);
        }}
        .interp.insight {{
            background: #fff3e0;
            border-left-color: var(--warning);
            color: #e65100;
        }}
        .interp.insight strong {{
            color: var(--warning);
        }}
        .interp.warning {{
            background: #fce4ec;
            border-left-color: var(--danger);
            color: var(--danger);
        }}
        .interp-label {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0 20px 0;
            font-size: 0.9rem;
        }}
        th {{
            background: var(--primary);
            color: white;
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        td {{
            padding: 8px 14px;
            border-bottom: 1px solid var(--border);
        }}
        tr:nth-child(even) {{
            background: #f5f5f5;
        }}
        tr:hover {{
            background: #ede7f6; /* Purple 50 hover */
        }}

        /* Figures */
        .figure-box {{
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
            text-align: center;
            background: var(--surface);
        }}
        .figure-box img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        .figure-box .fig-title {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 12px;
            font-size: 1.05rem;
        }}
        .figure-box .fig-caption {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 10px;
            font-style: italic;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 24px 0;
            font-size: 0.8rem;
            color: var(--text-light);
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
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

        @media print {{
            body {{ font-size: 12px; }}
            .container {{ max-width: 100%; padding: 0; }}
            section {{ box-shadow: none; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="report-header">
        <h1>📊 Historia 3: Equidad y Vulnerabilidad Diferenciada</h1>
        <div class="subtitle">Informe Diagnóstico — ¿Quiénes son los más afectados?</div>
        <div class="meta">Generado: {timestamp} | Organización: {org_name}</div>
    </div>

    <div class="toc">
        <h2>📋 Contenido</h2>
        <ol>
            <li><a href="#executive-summary">Resumen Ejecutivo</a></li>
            <li><a href="#differentiated-impacts">Impactos Diferenciados</a></li>
            <li><a href="#service-access">Acceso a Servicios y Barreras</a></li>
            <li><a href="#capacity-gaps">Brechas de Capacidad</a></li>
            <li><a href="#data-quality">Resumen de Calidad de Datos</a></li>
        </ol>
    </div>

    {content}

    <div class="footer">
        Generado por Storyline 3 Pipeline — Metodología PARES<br>
        © 2026 — Para uso analítico interno
    </div>
</div>
</body>
</html>
"""


def _interp(text: str, kind: str = "read") -> str:
    """Create an interpretation box.  kind: what | read | insight | warning"""
    labels = {
        "what": "📘 ¿Qué es esto?",
        "read": "📖 Cómo leer esta información",
        "insight": "💡 Hallazgos Clave",
        "warning": "⚠️ Atención",
    }
    css_class = kind if kind in ("what", "insight", "warning") else ""
    return f"""<div class="interp {css_class}">
    <div class="interp-label">{labels.get(kind, "📖 Interpretación")}</div>
    {text}
</div>"""


def embed_image(path: str, title: str) -> str:
    """Embed local image file as base64 into HTML."""
    if not path:
        return ""
    
    try:
        # If already base64
        if path.startswith("data:image"):
            src = path
        else:
            p = Path(path)
            if not p.exists():
                logger.warning(f"Image not found: {path}")
                return ""
                
            with open(p, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            
            mime_type = "image/png"
            if p.suffix.lower() in [".jpg", ".jpeg"]:
                mime_type = "image/jpeg"
            elif p.suffix.lower() == ".svg":
                mime_type = "image/svg+xml"
                
            src = f"data:{mime_type};base64,{b64_data}"
            
        return f"""
        <div class="figure-box">
            <img src="{src}" alt="{title}">
            <div class="fig-title">{title}</div>
        </div>
        """
    except Exception as e:
        logger.error(f"Error embedding image {path}: {e}")
        return ""


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
        <div class="stat-label">Grupos Vulnerables</div>
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
        <div class="stat-label">Barreras Distintas</div>
    </div>
    '''
    
    # Capacity questions
    cap_q = metrics_tables.get("CAPACITY_QUESTIONS_OVERALL", pd.DataFrame())
    n_cap = len(cap_q)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_cap}</div>
        <div class="stat-label">Preguntas de Capacidad</div>
    </div>
    '''
    
    content += '</div>'  # stats-grid

    # Narrative overview
    evi_narrative = narrative.generate_evi_narrative(evi_by_grupo)
    if evi_narrative:
        content += _interp(evi_narrative, "insight")
    
    # EVI table
    content += '<h3>🎯 Índice de Vulnerabilidad de Equidad (EVI) por Grupo</h3>'
    if not evi_by_grupo.empty:
        cols = ["grupo", "EVI", "dif_norm", "bar_norm", "inc_norm", "cap_norm"]
        cols = [c for c in cols if c in evi_by_grupo.columns]
        display = evi_by_grupo[cols].sort_values("EVI", ascending=False).copy()
        display.columns = ["Grupo", "Indice EVI", "Diferenciado", "Barreras", "Inclusión", "Capacidad"][:len(cols)]
        content += df_to_html(display, max_rows=10)
    else:
        content += "<p><em>No hay datos del índice EVI disponibles.</em></p>"
    
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
    
    content += _interp(
        "Esta sección identifica qué subgrupos son los más afectados por las amenazas y la intensidad de su exposición. "
        "Permite priorizar acciones para grupos específicos (ej. mujeres, jóvenes, grupos indígenas).",
        "what"
    )
    
    has_data = False
    
    # Narrative
    dif_overall = metrics_tables.get("DIF_LIVELIHOOD_OVERALL", pd.DataFrame())
    dif_narrative = narrative.generate_impact_narrative(metrics_tables.get("DIF_INTENSITY_OVERALL", pd.DataFrame()))
    
    if dif_narrative:
        content += _interp(dif_narrative, "insight")

    # Overall groups
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
        content += _interp(
            "No hay datos de impacto diferenciado disponibles. "
            "Esta sección requiere las hojas <code>TIDY_4_2_1_DIFERENCIADO</code> o <code>TIDY_4_2_2_DIFERENCIADO</code>.",
            "warning"
        )
    
    content += '</section>'
    return content


def generate_access_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate service access and barriers section."""
    content = '<section id="service-access" class="section"><h2>3. Acceso a Servicios y Barreras</h2>'
    
    content += _interp(
        "Análisis de barreras comunes (físicas, económicas, sociales) y patrones de inclusión reportados por los Medios de Vida. "
        "Ayuda a diseñar intervenciones que mejoren el acceso equitativo.",
        "what"
    )
    
    has_data = False
    
    # Barriers
    barriers = metrics_tables.get("BARRIERS_FREQ_OVERALL", pd.DataFrame())
    
    # Accessibility narrative
    barrier_rates = metrics_tables.get("BARRIER_RATES_BY_GRUPO", pd.DataFrame())
    acc_narrative = narrative.generate_access_narrative(barrier_rates)
    if acc_narrative:
         content += _interp(acc_narrative, "insight")
    
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
    if not barrier_rates.empty:
        has_data = True
        content += '<h3>📈 Tasas de Barreras e Inclusión por Grupo</h3>'
        cols = [c for c in ["grupo", "barriers_rate", "inclusion_rate"] if c in barrier_rates.columns]
        display = barrier_rates[cols].copy()
        display.columns = ["Grupo", "Tasa de Barreras", "Tasa de Inclusión"][:len(cols)]
        content += df_to_html(display, max_rows=10)
    
    if not has_data:
        content += _interp(
            "No hay datos de acceso a servicios disponibles. "
            "Esta sección requiere la hoja <code>TIDY_3_5_SE_MDV</code> con columnas de barreras.",
            "warning"
        )
    
    content += '</section>'
    return content


def generate_capacity_section(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate capacity gaps section."""
    content = '<section id="capacity-gaps" class="section"><h2>4. Brechas de Capacidad</h2>'
    
    content += _interp(
        "Los puntajes reflejan la capacidad individual y colectiva para adaptarse a las amenazas (0 = Baja Capacidad, 1 = Alta Capacidad/Resiliencia). "
        "Identificar las preguntas con puntajes más bajos revela los 'puntos débiles' a fortalecer.",
        "what"
    )
    
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
        content += embed_image(figures["bar_capacity_bottom_questions_overall"], "Cuellos de Botella de Capacidad (Preguntas con Puntaje Más Bajo)")
    
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
        content += _interp(
            "No hay datos de encuesta de capacidad disponibles. "
            "Esta sección requiere las hojas <code>TIDY_7_1_RESPONDENTS</code> y <code>TIDY_7_1_RESPONSES</code> (o formato agregado).",
            "warning"
        )
    
    content += '</section>'
    return content


def generate_qa_section(
    tables: Dict[str, pd.DataFrame],
    warnings: List[str] = [],
) -> str:
    """Generate QA summary section."""
    content = '<section id="data-quality" class="section"><h2>5. Resumen de Calidad de Datos</h2>'
    
    if warnings:
        content += '<h3>⚠️ Advertencias</h3>'
        for w in warnings:
            content += f'<div class="warning">{w}</div>'
            
    qa_sheets = ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]
    has_qa = False
    
    for sheet in qa_sheets:
        qa_df = tables.get(sheet, pd.DataFrame())
        if not qa_df.empty:
            has_qa = True
            content += f'<h3>{sheet}</h3>'
            content += df_to_html(qa_df, max_rows=10)
    
    if not has_qa and not warnings:
        content += '<p>✅ No se detectaron problemas de calidad significativos.</p>'
    
    content += '</section>'
    return content


def generate_report(
    metrics_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str] = [],
    tables: Optional[Dict[str, pd.DataFrame]] = None,
    org_name: str = "Organización",
) -> str:
    """
    Generate complete HTML report.
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
