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
from . import narrative

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

# HTML Template aligned with Storyline 1 (Interpreted Report)
# HTML Template aligned with Storyline 1 (Interpreted Report)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 2: Servicios Ecosistémicos — Informe Interpretado</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2e7d32;   /* Green 800 */
            --primary-light: #43a047; /* Green 600 */
            --accent: #66bb6a;    /* Green 400 */
            --accent-light: #a5d6a7;
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
            background: #f1f8e9;
            border-left: 4px solid var(--accent);
            border-radius: 0 8px 8px 0;
            padding: 16px 20px;
            margin: 16px 0;
            font-size: 0.95rem;
            color: #33691e;
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
            background: #e8f5e9;
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
            max-width: 85%;
            height: auto;
            border-radius: 8px;
            margin: 0 auto;
            display: block;
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
        <h1>📊 Historia 2: Servicios Ecosistémicos</h1>
        <div class="subtitle">Informe Diagnóstico — Conectividad, Criticidad y Apalancamiento</div>
        <div class="meta">Generado: {timestamp} | Organización: {org_name}</div>
    </div>

    <div class="toc">
        <h2>📋 Contenido</h2>
        <ol>
            <li><a href="#executive-summary">Resumen Ejecutivo</a></li>
            <li><a href="#ecosystem-analysis">Análisis de Ecosistemas</a></li>
            <li><a href="#service-criticality">Análisis de Criticidad de Servicios</a></li>
            <li><a href="#threats-vulnerability">Amenazas y Vulnerabilidad</a></li>
            <li><a href="#data-quality">Resumen de Calidad de Datos</a></li>
        </ol>
    </div>

    {content}

    <div class="footer">
        Generado por Storyline 2 Pipeline — Metodología PARES<br>
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
    
    content += _interp(
        "Este análisis evalúa la estructura de la red ecológica. "
        "<strong>Conectividad:</strong> Mide qué tan central es un ecosistema para el flujo de servicios. "
        "<strong>Apalancamiento (ELI):</strong> Identifica ecosistemas estratégicos que, con poca intervención, "
        "generan beneficios para muchos servicios críticos.",
        "what"
    )

    # Narrative
    eco_overall = metrics_tables.get("ecosystem_summary_overall", pd.DataFrame())
    eli_overall = metrics_tables.get("ecosystem_eli_overall", pd.DataFrame())
    narrative_text = narrative.generate_ecosystem_narrative(eco_overall, eli_overall)
    if narrative_text:
        content += _interp(narrative_text, "insight")
    
    # Ecosystem summary
    content += '<h3>🌳 Resumen de Conectividad de Ecosistemas</h3>'
    content += _interp(
        "La tabla muestra los ecosistemas ordenados por su conectividad normalizada. "
        "Un valor alto indica que el ecosistema soporta una gran variedad de servicios y medios de vida.",
        "read"
    )

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
    content += _interp(
        "El ELI combina la conectividad del ecosistema con la criticidad de los servicios que provee. "
        "Un ELI alto señala un ecosistema 'Piedra Angular': protegerlo asegura servicios vitales para la comunidad.",
        "read"
    )

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
    
    content += _interp(
        "El <strong>Índice de Criticidad del Servicio (SCI)</strong> mide qué tan esencial es un servicio ecosistémico "
        "para la comunidad. Considera cuántos medios de vida dependen de él (Grado), cuántos usuarios lo reportan (Prevalencia), "
        "la prioridad que le asignan (Importancia) y si su disponibilidad es estacional (Fragilidad).",
        "what"
    )

    # Narrative
    sci_ranking = metrics_tables.get("service_ranking_overall_balanced", pd.DataFrame())
    narrative_text = narrative.generate_service_narrative(sci_ranking)
    if narrative_text:
        content += _interp(narrative_text, "insight")
    
    # SCI components
    content += '<h3>📊 Componentes de Criticidad del Servicio</h3>'
    content += _interp(
        "Desglose de los factores que impulsan la criticidad. "
        "Identifique si un servicio es crítico por ser muy usado (Usuarios) o por ser vital para una actividad económica clave (Vínculos MdV).",
        "read"
    )

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
    
    content += _interp(
        "Este análisis conecta las amenazas reportadas con los servicios y medios de vida. "
        "<strong>TPS (Threat Pressure on Services):</strong> Cuánto está siendo afectado un servicio por el conjunto de amenazas. "
        "<strong>IVL (Indirect Vulnerability of Livelihoods):</strong> Cuánto riesgo corre un medio de vida debido al deterioro de los servicios de los que depende.",
        "what"
    )

    # TPS Narrative
    tps_overall = metrics_tables.get("tps_overall", pd.DataFrame())
    tps_narrative = narrative.generate_threat_narrative(tps_overall)
    
    # IVL Narrative
    ivl_overall = metrics_tables.get("ivl_overall", pd.DataFrame())
    ivl_narrative = narrative.generate_vulnerability_narrative(ivl_overall)

    if tps_narrative or ivl_narrative:
        combined_narrative = (tps_narrative + "\n" + ivl_narrative) if (tps_narrative and ivl_narrative) else (tps_narrative or ivl_narrative)
        content += _interp(combined_narrative, "insight")
    
    # TPS summary
    content += '<h3>⚠️ Presión de Amenazas sobre los Servicios (TPS)</h3>'
    tps_overall = metrics_tables.get("tps_overall", pd.DataFrame())
    if not tps_overall.empty:
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
