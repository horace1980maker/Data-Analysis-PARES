#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 5 — Interpreted Report
Generates an HTML report with rich, data-driven narrative explanations
for the SbN Portfolio Design + Monitoring Plan.

Follows the same pattern as storyline1/interpreted_report.py.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# Tier display names
TIER_NAMES = {
    "Do now": "Acción inmediata",
    "Do next": "Próxima acción",
    "Do later": "Acción diferida",
}

INDICATOR_TYPE_NAMES = {
    "OUTPUT": "PRODUCTO",
    "OUTCOME": "RESULTADO",
    "GOVERNANCE": "GOBERNANZA",
    "EQUITY": "EQUIDAD",
    "CAPACITY": "CAPACIDAD",
    "RISK": "RIESGO",
}

# ---------------------------------------------------------------------------
# CSS + HTML TEMPLATE
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 5 — Informe Interpretado: Portafolio SbN + Monitoreo</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #00695c;
            --primary-light: #26a69a;
            --accent: #ffb300;
            --accent-light: #ffe082;
            --warning: #ef6c00;
            --danger: #c62828;
            --success: #2e7d32;
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
            background: #e0f2f1;
            border-left: 4px solid var(--primary-light);
            border-radius: 0 8px 8px 0;
            padding: 16px 20px;
            margin: 16px 0;
            font-size: 0.95rem;
            color: #004d40;
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

        /* Stats grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
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

        /* Bundle cards */
        .bundle-card {{
            background: white;
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}
        .bundle-card.do-now {{
            border-left: 5px solid var(--success);
        }}
        .bundle-card.do-next {{
            border-left: 5px solid var(--warning);
        }}
        .bundle-card.do-later {{
            border-left: 5px solid var(--danger);
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
            color: var(--primary);
        }}
        .tier-badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .tier-do-now {{
            background: var(--success);
            color: white;
        }}
        .tier-do-next {{
            background: var(--warning);
            color: white;
        }}
        .tier-do-later {{
            background: var(--danger);
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
            background: var(--bg);
            border-radius: 5px;
        }}
        .detail-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
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
        .score-impact {{ background: #1565c0; }}
        .score-leverage {{ background: #7cb342; }}
        .score-equity {{ background: #8e24aa; }}
        .score-feasibility {{ background: #00838f; }}

        /* Indicator cards */
        .indicator-card {{
            background: #fafafa;
            border: 1px solid var(--border);
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

        /* Footer */
        .footer {{
            text-align: center;
            padding: 24px 0;
            font-size: 0.8rem;
            color: var(--text-light);
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
        <h1>📊 Historia 5: Portafolio SbN + Plan de Monitoreo</h1>
        <div class="subtitle">Informe Interpretado — Diseño de Portafolio Basado en Evidencia</div>
        <div class="meta">Organización: {org_name} | Generado: {timestamp}</div>
    </div>

    <div class="toc">
        <h2>📋 Contenido</h2>
        <ol>
            <li><a href="#sec1">Resumen Ejecutivo</a></li>
            <li><a href="#sec2">Evidencia del Portafolio</a></li>
            <li><a href="#sec3">Detalles de los Paquetes</a></li>
            <li><a href="#sec4">Plan de Monitoreo</a></li>
            <li><a href="#sec5">Visualizaciones</a></li>
            <li><a href="#sec6">Cobertura y Calidad de Datos</a></li>
        </ol>
    </div>

    {content}

    <div class="footer">
        Informe Interpretado generado por Storyline 5 Pipeline — Metodología PARES<br>
        © 2026 — Para uso analítico interno
    </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HELPER UTILITIES
# ---------------------------------------------------------------------------

def _fmt(val, decimals=2):
    """Format a numeric value nicely."""
    if pd.isna(val):
        return "—"
    if isinstance(val, (int, np.integer)):
        return str(val)
    return f"{val:.{decimals}f}"


def _pct(val, decimals=0):
    """Format 0-1 value as percentage."""
    if pd.isna(val):
        return "—"
    return f"{val * 100:.{decimals}f}%"


def _encode_image(path: str) -> Optional[str]:
    """Encode image to base64."""
    p = Path(path)
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def _df_to_html(df: pd.DataFrame, max_rows: int = 20) -> str:
    """Convert DataFrame to styled HTML table."""
    if df.empty:
        return "<p><em>Sin datos disponibles</em></p>"
    display = df.head(max_rows).copy()
    html = "<table>\n<thead><tr>"
    for col in display.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead>\n<tbody>\n"
    for _, row in display.iterrows():
        html += "<tr>"
        for col in display.columns:
            val = row[col]
            if isinstance(val, float):
                html += f"<td>{val:.2f}</td>"
            elif pd.isna(val):
                html += "<td>—</td>"
            else:
                html += f"<td>{val}</td>"
        html += "</tr>\n"
    html += "</tbody></table>\n"
    if len(df) > max_rows:
        html += f"<p style='color: var(--text-light); font-size: 0.85rem;'><em>Mostrando {max_rows} de {len(df)} filas.</em></p>\n"
    return html


def _embed_figure(path: str, title: str = "", caption: str = "") -> str:
    """Embed a figure with optional interpretation text."""
    if not path or not Path(path).exists():
        return ""
    b64 = _encode_image(path)
    if not b64:
        return ""
    html = '<div class="figure-box">'
    if title:
        html += f'<div class="fig-title">{title}</div>'
    html += f'<img src="data:image/png;base64,{b64}" alt="{title}">'
    if caption:
        html += f'<div class="fig-caption">{caption}</div>'
    html += '</div>'
    return html


def _interp(text: str, kind: str = "read") -> str:
    """Create an interpretation box.  kind: what | read | insight | warning"""
    labels = {
        "what": "📘 ¿Qué es esto?",
        "read": "📖 Cómo leer esta información",
        "insight": "💡 Hallazgos clave",
        "warning": "⚠️ Atención",
    }
    css_class = kind if kind in ("what", "insight", "warning") else ""
    return f"""<div class="interp {css_class}">
    <div class="interp-label">{labels.get(kind, "📖 Interpretación")}</div>
    {text}
</div>"""


def _get_tier_class(tier: str) -> str:
    """Get CSS class for tier."""
    tier_lower = str(tier).lower().replace(" ", "-")
    return tier_lower


def _get_tier_badge_class(tier: str) -> str:
    """Get CSS class for tier badge."""
    if "now" in str(tier).lower():
        return "tier-do-now"
    elif "next" in str(tier).lower():
        return "tier-do-next"
    else:
        return "tier-do-later"


# ---------------------------------------------------------------------------
# SECTION 1 — EXECUTIVE SUMMARY
# ---------------------------------------------------------------------------

def section_executive_summary(
    portfolio_tables: Dict[str, pd.DataFrame],
    monitoring_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec1">')
    parts.append('<h2>1. Resumen Ejecutivo</h2>')

    parts.append(_interp(
        "Este resumen presenta los resultados clave del <strong>Diseño de Portafolio SbN</strong> "
        "(Soluciones basadas en la Naturaleza). El portafolio agrupa los medios de vida en "
        "<strong>paquetes de acción</strong>, cada uno asociado a ecosistemas, servicios ecosistémicos "
        "y amenazas específicas. Cada paquete se evalúa en cuatro dimensiones: "
        "<strong>Potencial de Impacto</strong> (¿cuánto puede mejorar?), "
        "<strong>Apalancamiento</strong> (¿cuánto valor estratégico tiene?), "
        "<strong>Urgencia de Equidad</strong> (¿afecta a grupos vulnerables?), y "
        "<strong>Viabilidad</strong> (¿es factible implementarlo?). "
        "Los paquetes se clasifican en tres niveles de prioridad: "
        "<strong>Acción inmediata</strong> (Do Now), <strong>Próxima acción</strong> (Do Next) "
        "y <strong>Acción diferida</strong> (Do Later).",
        "what"
    ))

    # Count bundles
    bundles_overall = portfolio_tables.get("BUNDLES_OVERALL", pd.DataFrame())
    balanced_overall = portfolio_tables.get("BUNDLE_RANKING_OVERALL_BALANCED", pd.DataFrame())

    overall_count = len(bundles_overall)

    # Tier counts
    tier_counts = {"Do now": 0, "Do next": 0, "Do later": 0}
    if not balanced_overall.empty and "tier" in balanced_overall.columns:
        tier_counts = balanced_overall["tier"].value_counts().to_dict()

    indicators = monitoring_tables.get("INDICATORS", pd.DataFrame())
    indicator_count = len(indicators)

    do_now = tier_counts.get("Do now", 0)
    do_next = tier_counts.get("Do next", 0)
    do_later = tier_counts.get("Do later", 0)

    # Stats grid
    parts.append('<div class="stats-grid">')
    parts.append(f'<div class="stat-card"><div class="stat-value">{overall_count}</div><div class="stat-label">Paquetes Totales</div></div>')
    parts.append(f'<div class="stat-card"><div class="stat-value">{do_now}</div><div class="stat-label">Acción Inmediata</div></div>')
    parts.append(f'<div class="stat-card"><div class="stat-value">{do_next}</div><div class="stat-label">Próxima Acción</div></div>')
    parts.append(f'<div class="stat-card"><div class="stat-value">{indicator_count}</div><div class="stat-label">Indicadores</div></div>')
    parts.append('</div>')

    # Data-driven insight
    if not balanced_overall.empty:
        parts.append(_interp(
            f"El portafolio identifica <strong>{overall_count} paquetes candidatos</strong> a nivel de paisaje. "
            f"De estos, <strong>{do_now} paquetes</strong> se clasifican como «Acción inmediata», lo que significa que "
            f"obtuvieron los puntajes más altos en la combinación de las cuatro dimensiones y representan las "
            f"intervenciones con mayor potencial de impacto y viabilidad. "
            f"Los <strong>{do_next} paquetes</strong> de «Próxima acción» también son importantes pero requieren "
            f"planificación adicional o fortalecimiento de condiciones habilitantes. "
            f"Los restantes <strong>{do_later} paquetes</strong> tienen menor urgencia relativa.",
            "insight"
        ))

    # Top bundles table
    parts.append('<h3>🏆 Top 5 Paquetes (Escenario Equilibrado)</h3>')

    parts.append(_interp(
        "La siguiente tabla muestra los 5 paquetes mejor clasificados bajo el <strong>escenario equilibrado</strong>, "
        "que asigna pesos semejantes a las cuatro dimensiones. "
        "El <strong>Puntaje</strong> de portafolio combina: 35% Potencial de Impacto + 25% Apalancamiento + "
        "20% Urgencia de Equidad + 20% Viabilidad. "
        "La columna <strong>Prioridad</strong> indica el nivel de urgencia de acción.",
        "read"
    ))

    if not balanced_overall.empty:
        top5_cols = ["rank", "mdv_name", "grupo", "portfolio_score", "tier"]
        avail = [c for c in top5_cols if c in balanced_overall.columns]
        top5 = balanced_overall.head(5)[avail].copy()
        if "tier" in top5.columns:
            top5["tier"] = top5["tier"].map(TIER_NAMES).fillna(top5["tier"])
        col_names = {"rank": "Rango", "mdv_name": "Medio de Vida", "grupo": "Grupo",
                     "portfolio_score": "Puntaje", "tier": "Prioridad"}
        top5.columns = [col_names.get(c, c) for c in avail]
        parts.append(_df_to_html(top5, max_rows=5))

        # Data-driven narrative for #1
        top1 = balanced_overall.iloc[0]
        name1 = top1.get("mdv_name", "—")
        score1 = _fmt(top1.get("portfolio_score", 0))
        services = top1.get("services_text", "—")
        ecosystems = top1.get("ecosystems_text", "—")

        narrative = (
            f"El paquete de mayor prioridad es <strong>{name1}</strong> "
            f"(puntaje = {score1}). "
        )

        # Identify the strongest dimension
        dims = {
            "Potencial de Impacto": top1.get("impact_potential_norm", 0),
            "Apalancamiento": top1.get("leverage", 0),
            "Urgencia de Equidad": top1.get("evi_score", 0),
            "Viabilidad": top1.get("feasibility_score", 0),
        }
        # Filter NaN
        dims = {k: v for k, v in dims.items() if pd.notna(v)}
        if dims:
            strongest = max(dims, key=dims.get)
            narrative += (
                f"Su dimensión más fuerte es <strong>{strongest}</strong> "
                f"({_fmt(dims[strongest])}). "
            )

        if services and services != "—":
            narrative += f"Los servicios ecosistémicos asociados incluyen: <em>{services}</em>. "
        if ecosystems and ecosystems != "—":
            narrative += f"Se apoya en los ecosistemas: <em>{ecosystems}</em>."

        parts.append(_interp(narrative, "insight"))

    # Tier distribution chart
    for scenario in ["balanced"]:
        key = f"tier_distribution_{scenario}"
        if key in figures:
            parts.append(_embed_figure(
                figures[key],
                "Distribución de Prioridad (Escenario Equilibrado)",
                "Los colores representan: Verde = Acción inmediata, Naranja = Próxima acción, Rojo = Acción diferida."
            ))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 2 — PORTFOLIO EVIDENCE
# ---------------------------------------------------------------------------

def section_portfolio_evidence(
    portfolio_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec2">')
    parts.append('<h2>2. Evidencia del Portafolio</h2>')

    parts.append(_interp(
        "Esta sección muestra la <strong>base de evidencia</strong> que respalda la clasificación de cada paquete. "
        "Es importante entender que el portafolio <strong>no declara efectos ecológicos</strong>; "
        "todos los paquetes están etiquetados como «candidatos a ser medidos/validados». "
        "La evidencia proviene de los datos de línea base de la metodología PARES: "
        "mapeo de servicios ecosistémicos, evaluación de amenazas, priorización participativa "
        "y análisis de equidad y capacidad adaptativa.",
        "what"
    ))

    # Portfolio matrix
    if "portfolio_matrix_overall_balanced" in figures:
        parts.append('<h3>📊 Matriz de Portafolio</h3>')
        parts.append(_interp(
            "La <strong>Matriz de Portafolio</strong> es una visualización bidimensional donde: "
            "<strong>Eje X</strong> = Viabilidad (mayor valor = más factible), "
            "<strong>Eje Y</strong> = Potencial de Impacto (mayor valor = mayor impacto potencial). "
            "El <strong>tamaño</strong> de cada punto representa la Urgencia de Equidad. "
            "Los paquetes ideales se ubican en la <strong>esquina superior derecha</strong> "
            "(alto impacto + alta viabilidad). Paquetes grandes en esa zona son las intervenciones "
            "de mayor prioridad porque combinan impacto, factibilidad y equidad.",
            "read"
        ))
        parts.append(_embed_figure(
            figures["portfolio_matrix_overall_balanced"],
            "Matriz de Portafolio (Escenario Equilibrado)",
            "X = Viabilidad, Y = Potencial de Impacto, Tamaño = Urgencia de Equidad"
        ))

    # Stacked components
    if "stacked_components_balanced" in figures:
        parts.append('<h3>🔧 Contribución de Componentes</h3>')
        parts.append(_interp(
            "Este gráfico muestra <strong>cómo se compone el puntaje</strong> de cada paquete. "
            "Cada barra está dividida en cuatro segmentos que representan las dimensiones del análisis. "
            "Esto permite identificar <strong>fortalezas y debilidades</strong> de cada paquete: "
            "un paquete con alto puntaje total pero muy dependiente de una sola dimensión puede ser "
            "más riesgoso que uno con puntaje equilibrado entre las cuatro dimensiones.",
            "read"
        ))
        parts.append(_embed_figure(
            figures["stacked_components_balanced"],
            "Componentes Apilados — Top 10 Paquetes",
            "Cada color representa una dimensión: Impacto, Apalancamiento, Equidad, Viabilidad"
        ))

    # Evidence table
    evidence_overall = portfolio_tables.get("BUNDLE_EVIDENCE_OVERALL", pd.DataFrame())
    if not evidence_overall.empty:
        parts.append('<h3>📋 Resumen de Evidencia</h3>')
        parts.append(_interp(
            "La tabla de evidencia muestra los datos específicos que respaldan la puntuación de cada paquete. "
            "Cada fila vincula un paquete con los servicios, ecosistemas y amenazas que lo definen, "
            "permitiendo <strong>rastrear las decisiones hasta los datos originales</strong>.",
            "read"
        ))
        parts.append(_df_to_html(evidence_overall, max_rows=30))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 3 — BUNDLE DETAILS
# ---------------------------------------------------------------------------

def section_bundle_details(
    portfolio_tables: Dict[str, pd.DataFrame],
) -> str:
    parts = []
    parts.append('<section id="sec3">')
    parts.append('<h2>3. Detalles de los Paquetes</h2>')

    parts.append(_interp(
        "Cada <strong>paquete de acción</strong> agrupa un medio de vida con los ecosistemas, servicios "
        "y amenazas que lo rodean. Las <strong>tarjetas</strong> a continuación muestran los 10 paquetes mejor "
        "clasificados con sus componentes detallados. Las barras de puntaje muestran el rendimiento en cada dimensión:<br><br>"
        "• <strong>Potencial de Impacto</strong>: basado en cuántos servicios y ecosistemas están vinculados.<br>"
        "• <strong>Apalancamiento</strong>: cuánto «efecto multiplicador» tiene la intervención.<br>"
        "• <strong>Urgencia de Equidad</strong>: si afecta grupos especialmente vulnerables o con barreras de acceso.<br>"
        "• <strong>Viabilidad</strong>: presencia de condiciones habilitantes (actores de gobernanza, espacios de diálogo, capacidad).",
        "what"
    ))

    balanced_overall = portfolio_tables.get("BUNDLE_RANKING_OVERALL_BALANCED", pd.DataFrame())

    if balanced_overall.empty:
        parts.append('<p><em>No hay datos de paquetes disponibles</em></p>')
        parts.append('</section>')
        return "\n".join(parts)

    # Show top 10 bundles as cards with interpretation
    for idx, (_, row) in enumerate(balanced_overall.head(10).iterrows()):
        tier = row.get("tier", "Do later")
        tier_display = TIER_NAMES.get(tier, tier)
        tier_class = _get_tier_class(tier)
        badge_class = _get_tier_badge_class(tier)
        rank = int(row.get("rank", idx + 1))
        mdv_name = row.get("mdv_name", "Desconocido")

        parts.append(f'<div class="bundle-card {tier_class}">')
        parts.append('<div class="bundle-header">')
        parts.append(f'<span class="bundle-title">#{rank}: {mdv_name}</span>')
        parts.append(f'<span class="tier-badge {badge_class}">{tier_display}</span>')
        parts.append('</div>')

        parts.append('<div class="bundle-details">')

        # Services
        services = row.get("services_text", "—")
        parts.append(f'<div class="detail-item"><div class="detail-label">Servicios Críticos</div><div>{services}</div></div>')

        # Ecosystems
        ecosystems = row.get("ecosystems_text", "—")
        parts.append(f'<div class="detail-item"><div class="detail-label">Ecosistemas de Soporte</div><div>{ecosystems}</div></div>')

        # Threats
        threats = row.get("threats_text", "—")
        parts.append(f'<div class="detail-item"><div class="detail-label">Amenazas Clave</div><div>{threats}</div></div>')

        # Grupo
        grupo = row.get("grupo", "TODOS")
        parts.append(f'<div class="detail-item"><div class="detail-label">Grupo/Zona</div><div>{grupo}</div></div>')

        parts.append('</div>')  # bundle-details

        # Score bars
        scores = [
            ("Potencial de Impacto", row.get("impact_potential_norm", 0.5), "score-impact"),
            ("Apalancamiento", row.get("leverage", 0.5), "score-leverage"),
            ("Urgencia de Equidad", row.get("evi_score", 0.5), "score-equity"),
            ("Viabilidad", row.get("feasibility_score", 0.5), "score-feasibility"),
        ]

        parts.append('<div style="margin-top: 15px;">')
        for label, value, css_class in scores:
            val = float(value) if pd.notna(value) else 0.5
            pct = min(100, max(0, val * 100))
            parts.append(f'<div style="margin: 5px 0;">')
            parts.append(f'<small>{label}: {val:.2f}</small>')
            parts.append(f'<div class="score-bar"><div class="score-fill {css_class}" style="width: {pct}%"></div></div>')
            parts.append('</div>')
        parts.append('</div>')

        # Per-bundle narrative interpretation
        impact = float(row.get("impact_potential_norm", 0)) if pd.notna(row.get("impact_potential_norm")) else 0
        leverage = float(row.get("leverage", 0)) if pd.notna(row.get("leverage")) else 0
        equity = float(row.get("evi_score", 0)) if pd.notna(row.get("evi_score")) else 0
        feasibility = float(row.get("feasibility_score", 0)) if pd.notna(row.get("feasibility_score")) else 0

        # Identify strengths and weaknesses
        dim_scores = {
            "Potencial de Impacto": impact,
            "Apalancamiento": leverage,
            "Urgencia de Equidad": equity,
            "Viabilidad": feasibility,
        }
        strengths = [k for k, v in dim_scores.items() if v >= 0.6]
        weaknesses = [k for k, v in dim_scores.items() if v < 0.4]

        narrative = f"<strong>{mdv_name}</strong>: "
        if strengths:
            narrative += f"Destaca por su {'alto ' if len(strengths) == 1 else 'alta '}{', '.join(strengths).lower()}. "
        if weaknesses:
            narrative += f"Se identifican oportunidades de mejora en {', '.join(weaknesses).lower()}. "

        if tier == "Do now":
            narrative += "Como paquete de «Acción inmediata», se recomienda <strong>iniciar la planificación e implementación</strong> a corto plazo."
        elif tier == "Do next":
            narrative += "Como paquete de «Próxima acción», se recomienda <strong>fortalecer las condiciones habilitantes</strong> antes de la implementación."
        else:
            narrative += "Este paquete puede abordarse en una <strong>fase posterior</strong> del programa."

        parts.append(_interp(narrative, "insight"))

        parts.append('</div>')  # bundle-card

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 4 — MONITORING PLAN
# ---------------------------------------------------------------------------

def section_monitoring_plan(
    monitoring_tables: Dict[str, pd.DataFrame],
) -> str:
    parts = []
    parts.append('<section id="sec4">')
    parts.append('<h2>4. Plan de Monitoreo</h2>')

    parts.append(_interp(
        "El <strong>Plan de Monitoreo</strong> proporciona indicadores <strong>listos para MEAL</strong> "
        "(Monitoreo, Evaluación, Aprendizaje y Rendición de cuentas). Estos indicadores están diseñados para "
        "<strong>dar seguimiento y medición</strong> — no para declarar causalidad o impacto. "
        "Se organizan en diferentes categorías que cubren desde los productos inmediatos de las acciones "
        "hasta los resultados a largo plazo y las condiciones de gobernanza y equidad.",
        "what"
    ))

    # Indicator types explanation
    parts.append(_interp(
        "Los indicadores se clasifican en las siguientes categorías:<br><br>"
        "• <strong>PRODUCTO</strong>: Miden acciones concretas realizadas (conteos, participantes, hectáreas).<br>"
        "• <strong>RESULTADO</strong>: Miden cambios percibidos o medidos (disponibilidad de servicios, tendencias de amenazas).<br>"
        "• <strong>GOBERNANZA</strong>: Miden la calidad de los procesos de toma de decisiones y diálogo.<br>"
        "• <strong>EQUIDAD</strong>: Miden la inclusión y participación de grupos vulnerables.<br>"
        "• <strong>CAPACIDAD</strong>: Miden fortalecimiento de habilidades y conocimientos.<br>"
        "• <strong>RIESGO</strong>: Monitorean dinámicas de conflicto y riesgos emergentes.",
        "read"
    ))

    # Indicator library
    indicators = monitoring_tables.get("INDICATORS", pd.DataFrame())
    parts.append('<h3>📚 Biblioteca de Indicadores</h3>')

    if not indicators.empty:
        # Count by type
        type_counts = {}
        if "indicator_type" in indicators.columns:
            type_counts = indicators["indicator_type"].value_counts().to_dict()

        if type_counts:
            type_summary_parts = []
            for t, count in type_counts.items():
                display_name = INDICATOR_TYPE_NAMES.get(t, t)
                type_summary_parts.append(f"<strong>{count}</strong> de {display_name}")
            parts.append(_interp(
                f"La biblioteca contiene <strong>{len(indicators)} indicadores</strong>: "
                + ", ".join(type_summary_parts) + ". "
                "Esta diversidad asegura un monitoreo integral que va más allá de simples conteos de actividades "
                "para incluir cambios en resultados, gobernanza y equidad.",
                "insight"
            ))

        for _, row in indicators.iterrows():
            ind_type = row.get("indicator_type", "OUTPUT")
            if pd.isna(ind_type):
                ind_type = "OUTPUT"
            type_display = INDICATOR_TYPE_NAMES.get(ind_type, ind_type)
            type_class = f"type-{str(ind_type).lower()}"

            parts.append('<div class="indicator-card">')
            parts.append(f'<span class="indicator-type {type_class}">{type_display}</span>')
            parts.append(f'<strong>{row.get("indicator_name", "")}</strong>')

            definition = row.get("definition", "")
            if definition and not pd.isna(definition):
                parts.append(f'<p style="margin: 10px 0 5px 0; color: #666;">{definition}</p>')

            unit = row.get("unit_of_measure", "")
            freq = row.get("frequency", "")
            disagg = row.get("disaggregation_suggestions", "")
            meta_parts = []
            if unit and not pd.isna(unit):
                meta_parts.append(f"<strong>Unidad:</strong> {unit}")
            if freq and not pd.isna(freq):
                meta_parts.append(f"<strong>Frecuencia:</strong> {freq}")
            if disagg and not pd.isna(disagg):
                meta_parts.append(f"<strong>Desagregación:</strong> {disagg}")
            if meta_parts:
                parts.append(f'<small>{" | ".join(meta_parts)}</small>')

            parts.append('</div>')
    else:
        parts.append('<p><em>No hay indicadores definidos</em></p>')

    # Bundle-to-indicator mapping
    mapping = monitoring_tables.get("BUNDLES_TO_INDICATORS", pd.DataFrame())
    parts.append('<h3>🔗 Mapeo Paquete-Indicador</h3>')

    parts.append(_interp(
        "Esta tabla muestra <strong>qué indicadores se asignan a cada paquete</strong> y la razón. "
        "La columna <strong>Razón/Vínculo</strong> explica por qué ese indicador es relevante para "
        "ese paquete específico, basándose en los datos de línea base. "
        "Esto permite un monitoreo <strong>focalizado y justificado por evidencia</strong>.",
        "read"
    ))

    if not mapping.empty:
        display_cols = ["mdv_name", "grupo", "indicator_name", "rationale_link_to_evidence"]
        avail_cols = [c for c in display_cols if c in mapping.columns]
        display = mapping[avail_cols].copy()
        col_names = {"mdv_name": "Medio de Vida", "grupo": "Grupo",
                     "indicator_name": "Indicador", "rationale_link_to_evidence": "Razón/Vínculo"}
        display.columns = [col_names.get(c, c) for c in avail_cols]
        parts.append(_df_to_html(display, max_rows=25))
    else:
        parts.append('<p><em>No hay mapeos disponibles</em></p>')

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 5 — VISUALIZATIONS
# ---------------------------------------------------------------------------

def section_visualizations(figures: Dict[str, str]) -> str:
    parts = []
    parts.append('<section id="sec5">')
    parts.append('<h2>5. Visualizaciones</h2>')

    parts.append(_interp(
        "Las visualizaciones a continuación complementan el análisis tabular. "
        "Cada gráfico ofrece una perspectiva diferente sobre el portafolio: "
        "la <strong>Matriz de Portafolio</strong> muestra posicionamiento estratégico, "
        "las <strong>barras apiladas</strong> revelan la composición de los puntajes, "
        "y los gráficos <strong>por grupo</strong> permiten comparar prioridades territoriales.",
        "what"
    ))

    # Group figures by type
    figure_groups = {
        "Matrices de Portafolio": {
            "keys": [k for k in figures if "portfolio_matrix" in k],
            "guide": "En estas matrices, busque paquetes en la esquina superior derecha (alta viabilidad + alto impacto). "
                     "Los puntos más grandes representan mayor urgencia de equidad.",
        },
        "Análisis de Componentes": {
            "keys": [k for k in figures if "component" in k or "stacked" in k],
            "guide": "Las barras apiladas muestran qué dimensión contribuye más al puntaje total de cada paquete.",
        },
        "Comparaciones por Grupo": {
            "keys": [k for k in figures if "by_grupo" in k],
            "guide": "Estas comparaciones revelan si las prioridades varían entre zonas/grupos territoriales.",
        },
        "Análisis de Frecuencia": {
            "keys": [k for k in figures if "top_services" in k or "top_threats" in k],
            "guide": "Los gráficos de frecuencia muestran cuáles servicios y amenazas aparecen más frecuentemente en el portafolio.",
        },
    }

    for group_name, group_info in figure_groups.items():
        fig_keys = group_info["keys"]
        if fig_keys:
            parts.append(f'<h3>{group_name}</h3>')
            parts.append(_interp(group_info["guide"], "read"))
            for key in fig_keys:
                if key in figures:
                    caption = key.replace("_", " ").title()
                    parts.append(_embed_figure(figures[key], caption))

    # Check if no figures at all
    all_keys = sum([g["keys"] for g in figure_groups.values()], [])
    if not all_keys:
        parts.append('<p><em>No se generaron visualizaciones para este análisis.</em></p>')

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 6 — DATA COVERAGE
# ---------------------------------------------------------------------------

def section_data_coverage(
    portfolio_tables: Dict[str, pd.DataFrame],
    warnings: List[str],
    tables: Dict[str, pd.DataFrame],
) -> str:
    parts = []
    parts.append('<section id="sec6">')
    parts.append('<h2>6. Cobertura y Calidad de Datos</h2>')

    parts.append(_interp(
        "Esta sección documenta la <strong>cobertura y calidad</strong> de los datos utilizados para construir el portafolio. "
        "Una alta cobertura de datos aumenta la confianza en las clasificaciones. "
        "Las advertencias indican posibles limitaciones que deben considerarse al interpretar los resultados. "
        "Los hallazgos de calidad (QA) señalan problemas técnicos en los datos de entrada que podrían "
        "afectar la precisión del análisis.",
        "what"
    ))

    # Coverage summary
    coverage = portfolio_tables.get("COVERAGE_SUMMARY", pd.DataFrame())
    if not coverage.empty:
        parts.append('<h3>📊 Disponibilidad de Datos</h3>')
        parts.append(_interp(
            "La tabla de cobertura muestra qué tablas de datos estuvieron disponibles para el análisis. "
            "Las tablas con <strong>más filas</strong> proporcionan mayor riqueza de información. "
            "Si alguna tabla crítica tiene 0 filas, los resultados del portafolio podrían no reflejar esa dimensión.",
            "read"
        ))
        parts.append(_df_to_html(coverage, max_rows=30))

    # Warnings
    if warnings:
        parts.append('<h3>⚠️ Advertencias</h3>')
        parts.append(_interp(
            f"Se detectaron <strong>{len(warnings)} advertencias</strong> durante el procesamiento. "
            "Las advertencias no impiden la generación del portafolio, pero pueden indicar "
            "datos faltantes o inconsistencias que limitan el alcance del análisis. "
            "Revise cada una para evaluar su impacto en la interpretación de los resultados.",
            "warning"
        ))
        html = '<ul>'
        for w in warnings:
            html += f'<li>{w}</li>'
        html += '</ul>'
        parts.append(html)

    # QA sheets
    qa_sheets = ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]
    has_qa = False
    for qa_sheet in qa_sheets:
        qa_df = tables.get(qa_sheet, pd.DataFrame())
        if not qa_df.empty:
            if not has_qa:
                parts.append('<h3>🔍 Hallazgos de Control de Calidad</h3>')
                parts.append(_interp(
                    "Los controles de calidad automáticos verifican la integridad de los datos de entrada. "
                    "Los problemas detectados pueden incluir duplicados, IDs faltantes o inconsistencias en el esquema. "
                    "Estos no invalidan necesariamente los resultados, pero deben revisarse para asegurar la precisión del análisis.",
                    "read"
                ))
                has_qa = True
            parts.append(f'<h4>{qa_sheet}</h4>')
            parts.append(_df_to_html(qa_df, max_rows=10))

    if not has_qa and not warnings:
        parts.append(_interp(
            "<strong>✓ No se detectaron problemas de calidad.</strong> "
            "Los datos de entrada pasaron todos los controles automáticos sin hallazgos.",
            "insight"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# MASTER FUNCTION
# ==========================================================================

def generate_interpreted_report(
    portfolio_tables: Dict[str, pd.DataFrame],
    monitoring_tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str],
    tables: Dict[str, pd.DataFrame],
    org_name: str = "Organización",
) -> str:
    """
    Generate the complete interpreted HTML report for Storyline 5.

    Same signature as storyline5.report.generate_report for drop-in usage.

    Args:
        portfolio_tables: Portfolio output tables
        monitoring_tables: Monitoring plan tables
        figures: Dict of figure name -> path
        input_path: Path to input file
        warnings: List of warning messages
        tables: Raw input tables (for QA)
        org_name: Name of the organization for metadata

    Returns:
        Complete interpreted HTML report string
    """
    # Generate all sections
    content = ""
    content += section_executive_summary(portfolio_tables, monitoring_tables, figures)
    content += section_portfolio_evidence(portfolio_tables, figures)
    content += section_bundle_details(portfolio_tables)
    content += section_monitoring_plan(monitoring_tables)
    content += section_visualizations(figures)
    content += section_data_coverage(portfolio_tables, warnings, tables)

    # Fill template
    html = HTML_TEMPLATE.format(
        org_name=org_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        content=content,
    )

    logger.info("Generated interpreted HTML report for Storyline 5")
    return html
