#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 — Interpreted Report Prototype
Generates an HTML report with rich descriptions for every table and chart.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSS + HTML TEMPLATE
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 1 — Informe Interpretado: ¿Dónde actuar primero?</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #1b5e20;
            --primary-light: #2e7d32;
            --accent: #66bb6a;
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

        /* Comparison grid */
        .grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 16px 0;
        }}
        .grid-card {{
            flex: 1;
            min-width: 280px;
            background: #fafafa;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
        }}
        .grid-card h4 {{
            margin-top: 0;
            color: var(--primary);
            font-size: 0.95rem;
        }}

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
        <h1>📊 Historia 1: ¿Dónde actuar primero?</h1>
        <div class="subtitle">Informe Diagnóstico Interpretado — Análisis de Prioridad Basado en Evidencia</div>
        <div class="meta">Generado: {generation_time} | Prototipo v0.1</div>
    </div>

    <div class="toc">
        <h2>📋 Contenido</h2>
        <ol>
            <li><a href="#sec1">Resumen</a></li>
            <li><a href="#sec2">Análisis de Prioridad</a></li>
            <li><a href="#sec3">Análisis de Amenazas</a></li>
            <li><a href="#sec4">Capacidad Adaptativa</a></li>
            <li><a href="#sec5">Índice de Prioridad de Acción (IPA)</a></li>
            <li><a href="#sec6">Motores de Amenaza por Medio de Vida</a></li>
            <li><a href="#sec7">Visualizaciones</a></li>
            <li><a href="#sec8">Resumen de Calidad (QA)</a></li>
        </ol>
    </div>

    {content}

    <div class="footer">
        Prototipo generado por Storyline 1 Pipeline — Metodología PARES<br>
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


# ---------------------------------------------------------------------------
# SECTION GENERATORS
# ---------------------------------------------------------------------------

def _load_tables(input_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load all CSV tables from the tables/ subdirectory."""
    tables = {}
    tables_dir = input_dir / "tables"
    if not tables_dir.exists():
        logger.warning("No tables directory found at %s", tables_dir)
        return tables
    for csv_file in sorted(tables_dir.glob("*.csv")):
        name = csv_file.stem
        try:
            tables[name] = pd.read_csv(csv_file)
        except Exception as e:
            logger.warning("Failed to load %s: %s", csv_file, e)
    logger.info("Loaded %d tables from %s", len(tables), tables_dir)
    return tables


def _load_figures(input_dir: Path) -> Dict[str, str]:
    """Load figure paths from figures/ subdirectory."""
    figures = {}
    fig_dir = input_dir / "figures"
    if not fig_dir.exists():
        return figures
    for png_file in sorted(fig_dir.glob("*.png")):
        figures[png_file.stem] = str(png_file)
    logger.info("Found %d figures in %s", len(figures), fig_dir)
    return figures


# ==========================================================================
# SECTION 1 — EXECUTIVE SUMMARY
# ==========================================================================

def section_executive_summary(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec1">')
    parts.append('<h2>1. Resumen</h2>')

    parts.append(_interp(
        "Este resumen presenta los resultados más importantes del análisis de prioridad. "
        "Los medios de vida (MdV) se clasifican según el <strong>Índice de Prioridad de Acción (IPA)</strong>, "
        "que combina tres dimensiones: la importancia del medio de vida para la comunidad (prioridad), "
        "el nivel de riesgo al que está expuesto (amenazas), y las brechas en la capacidad de las comunidades "
        "para adaptarse. El IPA se calcula en una escala de 0 a 1, donde valores más altos indican mayor urgencia de intervención.",
        "what"
    ))

    # Top MdV overall
    rankings = tables.get("rankings_overall_balanced", pd.DataFrame())
    if not rankings.empty:
        parts.append('<h3>🌱 Medios de Vida de Máxima Prioridad (Escenario Equilibrado)</h3>')

        parts.append(_interp(
            "La siguiente tabla muestra los medios de vida clasificados de mayor a menor urgencia. "
            "Las columnas <strong>Prioridad</strong>, <strong>Riesgo</strong> y <strong>Brecha de Capacidad</strong> "
            "están normalizadas entre 0 y 1. El <strong>Puntaje IPA</strong> es la combinación ponderada "
            "(40% prioridad + 40% riesgo + 20% brecha de capacidad).",
            "read"
        ))

        top = rankings.head(5).copy()
        display = top[["rank", "mdv_name", "api_score", "priority_norm", "risk_norm", "cap_gap_norm"]].copy()
        display.columns = ["Rango", "Medio de Vida", "Puntaje IPA", "Prioridad", "Riesgo", "Brecha Cap."]
        parts.append(_df_to_html(display, max_rows=10))

        # Data-driven narrative
        top1 = rankings.iloc[0]
        name1 = top1.get("mdv_name", "—")
        score1 = _fmt(top1.get("api_score", 0))
        n_total = len(rankings)

        narrative = (
            f"El medio de vida con mayor urgencia de intervención es <strong>{name1}</strong> "
            f"(IPA = {score1}), ocupando el primer lugar de {n_total} medios de vida evaluados. "
        )
        # Check what drives the top ranking
        p = top1.get("priority_norm", 0)
        r = top1.get("risk_norm", 0)
        c = top1.get("cap_gap_norm", 0)
        drivers = []
        if p >= 0.7:
            drivers.append("alta prioridad comunitaria")
        if r >= 0.7:
            drivers.append("alta exposición a amenazas")
        if c >= 0.7:
            drivers.append("brechas significativas de capacidad adaptativa")
        if drivers:
            narrative += "Esto se debe a: " + ", ".join(drivers) + ". "

        if len(rankings) >= 3:
            names_top3 = ", ".join(rankings.head(3)["mdv_name"].dropna().tolist())
            narrative += f"Los tres medios de vida más prioritarios son: <strong>{names_top3}</strong>."

        parts.append(_interp(narrative, "insight"))

    # Top threats overview
    threats = tables.get("threats_overall", pd.DataFrame())
    if not threats.empty:
        parts.append('<h3>⚠️ Principales Amenazas</h3>')
        top_threats = threats.nlargest(5, "mean_suma").copy()
        display = top_threats[["amenaza", "tipo_amenaza", "mean_suma"]].copy()
        display.columns = ["Amenaza", "Tipo", "Severidad"]
        parts.append(_df_to_html(display))

        t1 = top_threats.iloc[0]
        is_non_climate = top_threats["tipo_amenaza"].str.contains("no", case=False, na=False)
        climate_count = len(top_threats[~is_non_climate & top_threats["tipo_amenaza"].notna()])
        parts.append(_interp(
            f"La amenaza más severa es <strong>{t1.get('amenaza', '—')}</strong> "
            f"(severidad = {_fmt(t1.get('mean_suma', 0))}). "
            f"De las 5 amenazas principales, <strong>{climate_count}</strong> son de origen climático "
            f"y <strong>{5 - climate_count}</strong> son no climáticas.",
            "insight"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 2 — PRIORITY ANALYSIS
# ==========================================================================

def section_priority(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec2">')
    parts.append('<h2>2. Análisis de Prioridad</h2>')

    parts.append(_interp(
        "Los puntajes de prioridad provienen de la tabla <strong>TIDY_3_2_PRIORIZACION</strong> del proceso PARES. "
        "Durante los talleres participativos, cada grupo/zona clasificó sus medios de vida según múltiples dimensiones "
        "(económica, social, ambiental, etc.). El puntaje <code>i_total</code> es la suma de todas las dimensiones. "
        "Este análisis presenta <strong>dos vistas complementarias</strong>: "
        "el ranking de campo (tal como lo clasificaron los participantes en cada zona) "
        "y el promedio analítico (puntajes agregados para permitir la comparación entre zonas).",
        "what"
    ))

    # Field ranking by group
    field_ranking = tables.get("priority_field_ranking", pd.DataFrame())
    if not field_ranking.empty and "grupo" in field_ranking.columns:
        parts.append('<h3>🌍 Ranking de Campo por Zona</h3>')
        parts.append(_interp(
            "Cada tarjeta muestra cómo cada zona/grupo clasificó sus medios de vida durante el taller participativo. "
            "El <strong>Rango</strong> indica la posición dentro de esa zona específica, y el puntaje <strong>i_total</strong> "
            "refleja la suma acumulada de puntos asignados por los participantes. "
            "Un i_total más alto = más importante para esa zona.",
            "read"
        ))

        parts.append('<div class="grid">')
        for grupo in sorted(field_ranking["grupo"].dropna().unique()):
            gd = field_ranking[field_ranking["grupo"] == grupo].sort_values("rank_in_zona").head(8)
            if gd.empty:
                continue
            parts.append(f'<div class="grid-card"><h4>{grupo}</h4>')
            cols = [c for c in ["rank_in_zona", "mdv_name", "i_total"] if c in gd.columns]
            d = gd[cols].copy()
            d.columns = ["Rango", "Medio de Vida", "i_total"][:len(cols)]
            parts.append(_df_to_html(d))
            parts.append('</div>')
        parts.append('</div>')

        # Cross-zone comparison insight
        groups = sorted(field_ranking["grupo"].dropna().unique())
        if len(groups) >= 2:
            top_per_group = []
            for g in groups:
                gd = field_ranking[field_ranking["grupo"] == g].sort_values("rank_in_zona").head(1)
                if not gd.empty:
                    top_per_group.append(f"<strong>{g}</strong>: {gd.iloc[0].get('mdv_name', '—')}")
            narrative = "El medio de vida más prioritario en cada zona es: " + "; ".join(top_per_group) + ". "

            # Check for shared top MdVs
            all_top3 = []
            for g in groups:
                gd = field_ranking[field_ranking["grupo"] == g].sort_values("rank_in_zona").head(3)
                all_top3.extend(gd["mdv_name"].dropna().tolist())
            from collections import Counter
            shared = [name for name, count in Counter(all_top3).items() if count > 1]
            if shared:
                narrative += f"Los medios de vida que aparecen como prioritarios en <strong>múltiples zonas</strong> incluyen: {', '.join(shared)}."
            else:
                narrative += "Cada zona prioriza medios de vida diferentes, lo que sugiere <strong>necesidades diferenciadas por territorio</strong>."

            parts.append(_interp(narrative, "insight"))

    # Analytical mean view
    priority_overall = tables.get("priority_by_mdv_overall", pd.DataFrame())
    if not priority_overall.empty:
        parts.append('<h3>📈 Vista de Promedio Analítico (Paisaje Completo)</h3>')
        parts.append(_interp(
            "Esta tabla agrega los puntajes de prioridad a través de todos los contextos/talleres usando el promedio. "
            "La columna <strong>Normalizado [0-1]</strong> escala el puntaje para permitir la comparación con otros componentes del IPA. "
            "La columna <strong>Contextos</strong> indica en cuántos talleres se evaluó ese medio de vida "
            "(más contextos = evidencia más robusta).",
            "read"
        ))
        display = priority_overall.nlargest(10, "mean_i_total").copy()
        cols = [c for c in ["mdv_name", "mean_i_total", "priority_norm", "n_records"] if c in display.columns]
        display = display[cols]
        display.columns = ["Medio de Vida", "Puntaje Promedio", "Normalizado [0-1]", "Contextos"][:len(cols)]
        parts.append(_df_to_html(display))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 3 — THREAT ANALYSIS
# ==========================================================================

MAGNITUD_MAP = {1: "Leve", 2: "Menor", 3: "Moderada", 4: "Severa", 5: "Catastrófica"}
FRECUENCIA_MAP = {-1: "Decreciente", 0: "Estable", 1: "Creciente", 2: "Muy frecuente", 3: "Permanente"}
TENDENCIA_MAP = {-1: "Decreciente", 0: "Estable", 1: "Creciente", 2: "Acelerada"}


def section_threats(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec3">')
    parts.append('<h2>3. Análisis de Amenazas</h2>')

    parts.append(_interp(
        "Las amenazas provienen de la tabla <strong>TIDY_4_1_AMENAZAS</strong>. Cada amenaza se evaluó participativamente "
        "según tres criterios: <strong>Magnitud</strong> (1=leve a 5=catastrófica), <strong>Frecuencia</strong> "
        "(1=rara a 3=permanente), y <strong>Tendencia</strong> (-1=decreciente, 0=estable, 1=creciente, 2=acelerada). "
        "La <strong>Severidad</strong> (Suma) = Magnitud + Frecuencia + Tendencia. Un puntaje más alto indica mayor severidad global. "
        "Las amenazas se clasifican como <strong>climáticas</strong> (sequía, inundaciones, etc.) o <strong>no climáticas</strong> "
        "(contaminación, deforestación, etc.).",
        "what"
    ))

    # Overall threats
    threats = tables.get("threats_overall", pd.DataFrame())
    if not threats.empty:
        parts.append('<h3>Amenazas Principales (Paisaje Completo)</h3>')

        parts.append(_interp(
            "La siguiente tabla muestra las amenazas ordenadas por severidad. "
            "Compare <strong>Magnitud</strong> y <strong>Frecuencia</strong> para entender el perfil: "
            "una amenaza con alta magnitud pero baja frecuencia (ej. crecida) requiere preparación de emergencia, "
            "mientras que una amenaza con baja magnitud pero alta frecuencia (ej. erosión gradual) requiere adaptación estructural.",
            "read"
        ))

        display = threats.nlargest(10, "mean_suma").copy()
        cols = [c for c in ["amenaza", "tipo_amenaza", "mean_suma", "mean_magnitud", "mean_frequencia", "mean_tendencia", "n"]
                if c in display.columns]
        display = display[cols]
        display.columns = ["Amenaza", "Tipo", "Severidad", "Magnitud", "Frecuencia", "Tendencia", "Muestras"][:len(cols)]
        parts.append(_df_to_html(display))

        # Insight
        t1 = threats.nlargest(1, "mean_suma").iloc[0]
        is_non_climate_mask = threats["tipo_amenaza"].str.contains("no", case=False, na=False)
        climate = threats[~is_non_climate_mask & threats["tipo_amenaza"].notna()]
        non_climate = threats[is_non_climate_mask]
        avg_clim = climate["mean_suma"].mean() if not climate.empty else 0
        avg_non = non_climate["mean_suma"].mean() if not non_climate.empty else 0

        narrative = (
            f"La amenaza más severa es <strong>{t1.get('amenaza', '—')}</strong> "
            f"con una severidad promedio de <strong>{_fmt(t1.get('mean_suma', 0))}</strong>. "
        )
        if t1.get("mean_tendencia", 0) > 0:
            narrative += "Su tendencia es <strong>creciente</strong>, lo que indica que probablemente empeorará en el futuro. "
        elif t1.get("mean_tendencia", 0) < 0:
            narrative += "Su tendencia es <strong>decreciente</strong>, aunque su impacto actual sigue siendo significativo. "

        if avg_clim > avg_non:
            narrative += (
                f"En promedio, las amenazas climáticas (severidad={_fmt(avg_clim)}) "
                f"son <strong>más severas</strong> que las no climáticas (severidad={_fmt(avg_non)}), "
                "lo que refuerza la importancia de las estrategias de adaptación al cambio climático."
            )
        elif avg_non > avg_clim:
            narrative += (
                f"En promedio, las amenazas no climáticas (severidad={_fmt(avg_non)}) "
                f"superan a las climáticas (severidad={_fmt(avg_clim)}), "
                "sugiriendo que la gestión territorial y ambiental requiere atención prioritaria junto con la adaptación climática."
            )
        parts.append(_interp(narrative, "insight"))

    # By group
    threats_group = tables.get("threats_by_group", pd.DataFrame())
    if not threats_group.empty and "grupo" in threats_group.columns:
        parts.append('<h3>Amenazas por Zona/Grupo</h3>')
        parts.append(_interp(
            "Cada zona puede enfrentar un perfil de amenazas diferente. "
            "Compare las amenazas entre zonas para identificar riesgos <strong>compartidos</strong> "
            "(que requieren acciones coordinadas) vs. riesgos <strong>localizados</strong> "
            "(que necesitan intervenciones focalizadas).",
            "read"
        ))
        parts.append('<div class="grid">')
        for grupo in sorted(threats_group["grupo"].dropna().unique()):
            gd = threats_group[threats_group["grupo"] == grupo].nlargest(5, "mean_suma")
            if gd.empty:
                continue
            parts.append(f'<div class="grid-card"><h4>{grupo}</h4>')
            cols = [c for c in ["amenaza", "mean_suma", "mean_magnitud"] if c in gd.columns]
            d = gd[cols].copy()
            d.columns = ["Amenaza", "Severidad", "Magnitud"][:len(cols)]
            parts.append(_df_to_html(d))
            parts.append('</div>')
        parts.append('</div>')

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 4 — CAPACITY ANALYSIS
# ==========================================================================

def section_capacity(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec4">')
    parts.append('<h2>4. Análisis de Capacidad Adaptativa</h2>')

    parts.append(_interp(
        "Los puntajes de capacidad adaptativa se derivan de encuestas comunitarias (<strong>TIDY_7_1_RESPONSES</strong>). "
        "Los encuestados calificaron diversas dimensiones de capacidad (acceso a información, recursos financieros, "
        "organización comunitaria, etc.) en una escala Likert. Estos puntajes se normalizan a una escala de 0 a 1: "
        "<strong>Capacidad = puntaje promedio normalizado</strong>, y <strong>Brecha = 1 − Capacidad</strong>. "
        "Una brecha alta indica una área donde las comunidades tienen menos recursos o habilidades para adaptarse.",
        "what"
    ))

    # Capacity by MdV
    capacity = tables.get("capacity_overall_by_mdv", pd.DataFrame())
    if not capacity.empty:
        parts.append('<h3>Capacidad por Medio de Vida</h3>')
        parts.append(_interp(
            "Esta tabla muestra los medios de vida ordenados por <strong>menor capacidad</strong> (mayores brechas). "
            "Los que aparecen al inicio de la lista requieren mayor inversión en fortalecimiento de capacidades. "
            "La columna <strong>Respuestas</strong> indica la robustez estadística del dato.",
            "read"
        ))

        display = capacity.nsmallest(10, "mean_response_0_1").copy()
        cols = [c for c in ["mdv_name", "mean_response_0_1", "capacity_gap", "cap_gap_norm", "n_responses"]
                if c in display.columns]
        display = display[cols]
        display.columns = ["Medio de Vida", "Capacidad (0-1)", "Brecha", "Brecha Norm.", "Respuestas"][:len(cols)]
        parts.append(_df_to_html(display))

        # Insight
        lowest = capacity.nsmallest(1, "mean_response_0_1").iloc[0]
        highest = capacity.nlargest(1, "mean_response_0_1").iloc[0]
        gap_range = highest.get("mean_response_0_1", 1) - lowest.get("mean_response_0_1", 0)
        parts.append(_interp(
            f"El medio de vida con <strong>menor capacidad adaptativa</strong> es "
            f"<strong>{lowest.get('mdv_name', '—')}</strong> (capacidad = {_fmt(lowest.get('mean_response_0_1', 0))}), "
            f"mientras que <strong>{highest.get('mdv_name', '—')}</strong> tiene la mayor capacidad "
            f"(capacidad = {_fmt(highest.get('mean_response_0_1', 0))}). "
            f"La diferencia entre ambos es de <strong>{_fmt(gap_range)}</strong> puntos, "
            + ("lo que indica una <strong>distribución desigual</strong> de capacidades entre medios de vida." if gap_range > 0.3
               else "lo que sugiere una distribución relativamente <strong>homogénea</strong> de capacidades."),
            "insight"
        ))

    # Bottleneck questions
    questions = tables.get("capacity_overall_questions", pd.DataFrame())
    if not questions.empty:
        parts.append('<h3>🔍 Cuellos de Botella — Preguntas con Menor Puntaje</h3>')
        parts.append(_interp(
            "Estas son las preguntas de la encuesta donde las comunidades obtuvieron los puntajes más bajos. "
            "Cada pregunta representa una dimensión específica de capacidad adaptativa. "
            "Las preguntas con puntaje más bajo revelan los <strong>cuellos de botella</strong> "
            "que deben abordarse para fortalecer la resiliencia.",
            "read"
        ))
        display = questions.head(8).copy()
        cols = [c for c in ["question_text", "mean_response_0_1", "n_responses"] if c in display.columns]
        if cols:
            display = display[cols]
            display.columns = ["Pregunta", "Puntaje (0-1)", "Respuestas"][:len(cols)]
            parts.append(_df_to_html(display, max_rows=8))

            q1 = questions.iloc[0]
            parts.append(_interp(
                f"El cuello de botella más crítico es: \"<em>{q1.get('question_text', '—')}</em>\" "
                f"con un puntaje de <strong>{_fmt(q1.get('mean_response_0_1', 0))}</strong>. "
                "Este tema debería ser un foco prioritario en los programas de fortalecimiento de capacidades.",
                "insight"
            ))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 5 — ACTION PRIORITY INDEX
# ==========================================================================

def section_api(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec5">')
    parts.append('<h2>5. Índice de Prioridad de Acción (IPA)</h2>')

    parts.append(_interp(
        "El <strong>IPA</strong> es un índice compuesto basado en Análisis de Criterios Múltiples (MCDA). "
        "Combina tres componentes normalizados (0-1): "
        "<strong>Prioridad</strong> (importancia comunitaria), "
        "<strong>Riesgo</strong> (exposición a amenazas), y "
        "<strong>Brecha de Capacidad</strong> (debilidades adaptativas). "
        "Se calculan tres escenarios con diferentes pesos para evaluar la <strong>robustez</strong> de los resultados:<br><br>"
        "• <strong>Equilibrado</strong>: 40% Prioridad + 40% Riesgo + 20% Brecha<br>"
        "• <strong>Medio de Vida Primero</strong>: 50% Prioridad + 30% Riesgo + 20% Brecha<br>"
        "• <strong>Riesgo Primero</strong>: 30% Prioridad + 50% Riesgo + 20% Brecha<br><br>"
        "Si un medio de vida aparece entre los primeros en <strong>todos los escenarios</strong>, "
        "es una prioridad <strong>robusta</strong> que no depende de la elección de pesos.",
        "what"
    ))

    scenario_labels = {
        "balanced": "Escenario: Equilibrado",
        "livelihood_first": "Escenario: Medio de Vida Primero",
        "risk_first": "Escenario: Riesgo Primero",
    }

    # Collect top-5 for stability analysis
    top5_per_scenario = {}

    for scenario, label in scenario_labels.items():
        key = f"rankings_overall_{scenario}"
        df = tables.get(key, pd.DataFrame())
        if df.empty:
            continue

        parts.append(f'<h3>{label}</h3>')

        if scenario == "balanced":
            parts.append(_interp(
                "Este escenario da igual peso a la prioridad comunitaria y al riesgo. "
                "Es la referencia principal para la toma de decisiones cuando no hay razón para "
                "favorecer un criterio sobre otro.",
                "read"
            ))
        elif scenario == "livelihood_first":
            parts.append(_interp(
                "Este escenario enfatiza la importancia que las comunidades asignan al medio de vida. "
                "Útil cuando el objetivo es maximizar el impacto socioeconómico de las intervenciones.",
                "read"
            ))
        else:
            parts.append(_interp(
                "Este escenario enfatiza la exposición a amenazas. "
                "Útil cuando el objetivo principal es reducir la vulnerabilidad ante desastres o el cambio climático.",
                "read"
            ))

        display = df.head(10).copy()
        cols = [c for c in ["rank", "mdv_name", "api_score", "priority_norm", "risk_norm", "cap_gap_norm"]
                if c in display.columns]
        display = display[cols]
        display.columns = ["Rango", "Medio de Vida", "IPA", "Prioridad", "Riesgo", "Brecha Cap."][:len(cols)]
        parts.append(_df_to_html(display))

        top5_per_scenario[scenario] = set(df.head(5)["mdv_name"].dropna().tolist())

    # Stability analysis
    if len(top5_per_scenario) >= 2:
        all_sets = list(top5_per_scenario.values())
        stable = set.intersection(*all_sets) if all_sets else set()
        if stable:
            parts.append(_interp(
                f"<strong>Análisis de estabilidad:</strong> Los siguientes medios de vida aparecen en el Top 5 "
                f"de <strong>todos los escenarios</strong>, lo que indica prioridades robustas: "
                f"<strong>{', '.join(sorted(stable))}</strong>. "
                "Estos deberían ser el foco principal de las intervenciones SbN/adaptación.",
                "insight"
            ))
        else:
            # Check pairwise overlap
            parts.append(_interp(
                "No hay medios de vida que aparezcan en el Top 5 de todos los escenarios. "
                "Esto indica que la priorización es <strong>sensible a los pesos</strong>, "
                "lo cual requiere una discusión con los actores clave sobre qué criterio priorizar.",
                "warning"
            ))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 6 — THREAT DRIVERS
# ==========================================================================

def section_drivers(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec6">')
    parts.append('<h2>6. Motores de Amenaza por Medio de Vida</h2>')

    parts.append(_interp(
        "Para cada medio de vida prioritario, esta sección identifica las amenazas que más contribuyen "
        "a su exposición al riesgo. Los <strong>motores</strong> se calculan multiplicando el impacto de la amenaza "
        "sobre el medio de vida por la severidad de la amenaza. Esto permite diseñar <strong>intervenciones focalizadas</strong>: "
        "abordar los motores principales de los MdV más prioritarios tiene el mayor retorno de inversión.",
        "what"
    ))

    parts.append(_interp(
        "El <strong>Impacto Ponderado</strong> refleja cuánto contribuye cada amenaza al riesgo total de ese medio de vida. "
        "Un valor más alto indica una amenaza que tiene más influencia sobre ese medio de vida específico. "
        "Los motores están ordenados de mayor a menor impacto.",
        "read"
    ))

    rankings = tables.get("rankings_overall_balanced", pd.DataFrame())
    drivers = tables.get("top_threat_drivers_overall", pd.DataFrame())

    if not rankings.empty and not drivers.empty:
        top_mdv_ids = rankings.head(5)["mdv_id"].tolist()

        for mdv_id in top_mdv_ids:
            mdv_drivers = drivers[drivers["mdv_id"] == mdv_id].head(5)
            if mdv_drivers.empty:
                continue
            mdv_name = mdv_drivers["mdv_name"].iloc[0] if "mdv_name" in mdv_drivers.columns else mdv_id
            rank_row = rankings[rankings["mdv_id"] == mdv_id]
            rank_num = int(rank_row["rank"].iloc[0]) if not rank_row.empty else "?"

            parts.append(f'<h4>🌾 #{rank_num} — {mdv_name}</h4>')

            cols = [c for c in ["driver_rank", "amenaza", "sum_weighted_impact"] if c in mdv_drivers.columns]
            display = mdv_drivers[cols].copy()
            display.columns = ["Rango", "Amenaza", "Impacto Ponderado"][:len(cols)]
            parts.append(_df_to_html(display))

            # Per-MdV insight
            top_driver = mdv_drivers.iloc[0]
            parts.append(_interp(
                f"Para <strong>{mdv_name}</strong>, la amenaza más impactante es "
                f"<strong>{top_driver.get('amenaza', '—')}</strong>. "
                f"Las acciones de adaptación para este medio de vida deberían enfocarse primero en esta amenaza.",
                "insight"
            ))
    else:
        parts.append('<p><em>No hay datos de motores disponibles.</em></p>')

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 7 — VISUALIZATIONS
# ==========================================================================

FIGURE_DESCRIPTIONS = {
    "quadrant_priority_vs_risk_overall": {
        "title": "Análisis de Cuadrante: Prioridad vs Riesgo",
        "what": (
            "Este diagrama de dispersión posiciona cada medio de vida según dos ejes: "
            "<strong>Prioridad</strong> (eje horizontal, importancia comunitaria) y "
            "<strong>Riesgo</strong> (eje vertical, exposición a amenazas). "
            "El <strong>tamaño de la burbuja</strong> representa la brecha de capacidad adaptativa "
            "(burbuja más grande = menor capacidad)."
        ),
        "read": (
            "El gráfico se divide en cuatro cuadrantes:<br>"
            "• <strong>Superior derecho</strong> (Alta Prioridad + Alto Riesgo): Medios de vida que requieren <strong>acción inmediata</strong>.<br>"
            "• <strong>Superior izquierdo</strong> (Baja Prioridad + Alto Riesgo): Medios de vida en riesgo pero menos valorados; evaluar su protección indirecta.<br>"
            "• <strong>Inferior derecho</strong> (Alta Prioridad + Bajo Riesgo): Medios de vida importantes y relativamente seguros; <strong>mantener</strong>.<br>"
            "• <strong>Inferior izquierdo</strong> (Baja Prioridad + Bajo Riesgo): Menor urgencia de intervención."
        ),
    },
    "bar_top_threats_overall": {
        "title": "Principales Amenazas por Severidad (General)",
        "what": (
            "Este gráfico de barras muestra las amenazas ordenadas de mayor a menor severidad. "
            "La longitud de la barra corresponde al puntaje de severidad (Magnitud + Frecuencia + Tendencia)."
        ),
        "read": (
            "Las barras más largas representan las amenazas que requieren atención más urgente. "
            "Compare el color o las etiquetas para distinguir entre amenazas climáticas y no climáticas."
        ),
    },
    "bar_top_threats_by_group": {
        "title": "Principales Amenazas por Zona/Grupo",
        "what": (
            "Este gráfico muestra las amenazas más severas desglosadas por zona/grupo territorial. "
            "Cada zona tiene su propio conjunto de barras."
        ),
        "read": (
            "Compare las amenazas entre zonas. Si la misma amenaza es severa en múltiples zonas, "
            "requiere una estrategia coordinada. Si una amenaza solo afecta a una zona, la intervención puede focalizarse."
        ),
    },
}


def _get_bar_api_desc(scenario_key: str, overall: bool) -> dict:
    """Generate description for bar API charts."""
    scenario_map = {
        "balanced": "Equilibrado",
        "livelihood_first": "Medio de Vida Primero",
        "risk_first": "Riesgo Primero",
    }
    scenario = scenario_key.replace("bar_top_livelihoods_api_overall_", "").replace("bar_top_livelihoods_api_by_group_", "")
    label = scenario_map.get(scenario, scenario)
    scope = "paisaje completo" if overall else "cada zona/grupo"
    return {
        "title": f"Top Medios de Vida por IPA — {label} ({'General' if overall else 'Por Grupo'})",
        "what": (
            f"Este gráfico de barras muestra los medios de vida con mayor Índice de Prioridad de Acción (IPA) "
            f"bajo el escenario <strong>{label}</strong>, para el {scope}."
        ),
        "read": (
            f"Las barras más largas representan los medios de vida donde se necesita actuar con mayor urgencia. "
            f"El IPA combina prioridad, riesgo y brecha de capacidad con los pesos del escenario {label}."
        ),
    }


def section_visualizations(figures: Dict[str, str]) -> str:
    parts = []
    parts.append('<section id="sec7">')
    parts.append('<h2>7. Visualizaciones</h2>')

    parts.append(_interp(
        "Esta sección presenta todos los gráficos generados por el análisis. "
        "Cada gráfico incluye una explicación de qué muestra, cómo leer los ejes y colores, "
        "y qué patrones buscar.",
        "what"
    ))

    if not figures:
        parts.append('<p><em>No se generaron figuras.</em></p>')
        parts.append('</section>')
        return "\n".join(parts)

    for fig_name, fig_path in figures.items():
        img_data = _encode_image(fig_path)
        if not img_data:
            continue

        # Get description
        if fig_name in FIGURE_DESCRIPTIONS:
            desc = FIGURE_DESCRIPTIONS[fig_name]
        elif fig_name.startswith("bar_top_livelihoods_api_overall_"):
            desc = _get_bar_api_desc(fig_name, overall=True)
        elif fig_name.startswith("bar_top_livelihoods_api_by_group_"):
            desc = _get_bar_api_desc(fig_name, overall=False)
        else:
            desc = {
                "title": fig_name.replace("_", " ").title(),
                "what": "Gráfico del análisis de prioridad.",
                "read": "Consulte las etiquetas de los ejes para interpretar los valores.",
            }

        parts.append(f'<div class="figure-box">')
        parts.append(f'<div class="fig-title">{desc["title"]}</div>')
        parts.append(_interp(desc["what"], "what"))
        parts.append(_interp(desc["read"], "read"))
        parts.append(f'<img src="data:image/png;base64,{img_data}" alt="{desc["title"]}">')
        parts.append('</div>')

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# SECTION 8 — QA SUMMARY
# ==========================================================================

def section_qa(tables: Dict[str, pd.DataFrame]) -> str:
    parts = []
    parts.append('<section id="sec8">')
    parts.append('<h2>8. Resumen de Calidad de Datos (QA)</h2>')

    parts.append(_interp(
        "Este resumen indica la completitud y calidad de los datos utilizados en el análisis. "
        "La presencia de datos faltantes o tablas vacías puede afectar la confiabilidad de los resultados. "
        "Las tablas con pocas muestras (<strong>n</strong> bajo) deben interpretarse con precaución.",
        "what"
    ))

    # Build a simple summary of what tables were loaded
    parts.append('<h3>Inventario de Datos</h3>')
    parts.append(_interp(
        "La siguiente tabla muestra qué conjuntos de datos estaban disponibles y cuántos registros contienen. "
        "Tablas con 0 registros indican datos que no se recopilaron o que no pasaron la validación.",
        "read"
    ))

    rows = []
    for name, df in sorted(tables.items()):
        rows.append({"Tabla": name, "Registros": len(df), "Columnas": len(df.columns)})
    if rows:
        summary_df = pd.DataFrame(rows)
        parts.append(_df_to_html(summary_df, max_rows=30))

        empty_tables = [r["Tabla"] for r in rows if r["Registros"] == 0]
        if empty_tables:
            parts.append(_interp(
                f"Las siguientes tablas están vacías: <strong>{', '.join(empty_tables)}</strong>. "
                "Verifique si estos datos se recopilaron correctamente en los talleres.",
                "warning"
            ))
        else:
            parts.append(_interp(
                f"Todas las <strong>{len(rows)}</strong> tablas contienen datos. "
                "La cobertura de datos es completa para este análisis.",
                "insight"
            ))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# MAIN GENERATOR
# ==========================================================================

def generate_interpreted_report(
    tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str = "",
    warnings: list = None,
    org_name: str = "Organización",
) -> str:
    """
    Generate the interpreted HTML report from in-memory tables and figures.

    Args:
        tables: Dict of table_name -> DataFrame (from metrics pipeline)
        figures: Dict of figure_name -> file_path (from plots pipeline)
        input_path: Optional, path to original input file (for metadata)
        warnings: Optional, list of warnings from pipeline
        org_name: Organization name for display

    Returns:
        HTML string
    """
    content_parts = [
        section_executive_summary(tables),
        section_priority(tables),
        section_threats(tables),
        section_capacity(tables),
        section_api(tables),
        section_drivers(tables),
        section_visualizations(figures),
        section_qa(tables),
    ]

    content = "\n".join(content_parts)

    html = HTML_TEMPLATE.format(
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        content=content,
    )

    return html


def generate_interpreted_report_from_dir(input_dir: str) -> str:
    """
    Convenience wrapper: load tables/figures from disk, then generate report.
    Used by the CLI prototype runner.
    """
    input_path = Path(input_dir)
    tables = _load_tables(input_path)
    figures = _load_figures(input_path)
    return generate_interpreted_report(tables, figures, input_dir=input_dir)

