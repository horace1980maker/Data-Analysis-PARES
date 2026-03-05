#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 4 — Interpreted Report
Generates an HTML report with rich, data-driven narrative explanations
for Feasibility, Governance & Conflict Risk analysis.

Follows the same pattern as storyline1/interpreted_report.py and
storyline5/interpreted_report.py.
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
    <title>Historia 4 — Informe Interpretado: Viabilidad, Gobernanza y Conflicto</title>
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
            background: linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%);
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
        .toc ol {{ padding-left: 20px; }}
        .toc li {{ margin-bottom: 6px; }}
        .toc a {{ color: var(--info); text-decoration: none; }}
        .toc a:hover {{ text-decoration: underline; }}

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

        .interp {{
            background: #e0f2f1;
            border-left: 4px solid var(--primary-light);
            border-radius: 0 8px 8px 0;
            padding: 16px 20px;
            margin: 16px 0;
            font-size: 0.95rem;
            color: #004d40;
        }}
        .interp strong {{ color: var(--primary); }}
        .interp.what {{
            background: var(--info-bg);
            border-left-color: var(--info);
            color: #0d47a1;
        }}
        .interp.what strong {{ color: var(--info); }}
        .interp.insight {{
            background: #fff3e0;
            border-left-color: var(--warning);
            color: #e65100;
        }}
        .interp.insight strong {{ color: var(--warning); }}
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

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #4a148c, #7b1fa2);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{ font-size: 2rem; font-weight: 700; }}
        .stat-label {{ font-size: 0.85rem; opacity: 0.9; }}

        .feasibility-high {{ color: #2e7d32; font-weight: bold; }}
        .feasibility-medium {{ color: #ff9800; font-weight: bold; }}
        .feasibility-low {{ color: #c62828; font-weight: bold; }}

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
        tr:nth-child(even) {{ background: #f5f5f5; }}
        tr:hover {{ background: #e8f5e9; }}

        .figure-box {{
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
            text-align: center;
            background: var(--surface);
        }}
        .figure-box img {{ max-width: 100%; height: auto; border-radius: 8px; }}
        .figure-box .fig-title {{
            font-weight: 600; color: var(--primary);
            margin-bottom: 12px; font-size: 1.05rem;
        }}
        .figure-box .fig-caption {{
            font-size: 0.85rem; color: var(--text-secondary);
            margin-top: 10px; font-style: italic;
        }}

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
        <h1>🏛️ Historia 4: Viabilidad, Gobernanza y Riesgo de Conflicto</h1>
        <div class="subtitle">Informe Interpretado — Análisis de Condiciones Habilitantes</div>
        <div class="meta">Organización: {org_name} | Generado: {timestamp}</div>
    </div>

    <div class="toc">
        <h2>📋 Contenido</h2>
        <ol>
            <li><a href="#sec1">Resumen</a></li>
            <li><a href="#sec2">Actores y Redes</a></li>
            <li><a href="#sec3">Espacios de Diálogo</a></li>
            <li><a href="#sec4">Análisis de Conflictos</a></li>
            <li><a href="#sec5">Vínculos con Amenazas</a></li>
            <li><a href="#sec6">Calidad de Datos</a></li>
        </ol>
    </div>

    {content}

    <div class="footer">
        Informe Interpretado generado por Storyline 4 Pipeline — Metodología PARES<br>
        © 2026 — Para uso analítico interno
    </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _fmt(val, decimals=2):
    if pd.isna(val):
        return "—"
    if isinstance(val, (int, np.integer)):
        return str(val)
    return f"{val:.{decimals}f}"


def _encode_image(path: str) -> Optional[str]:
    p = Path(path)
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def _df_to_html(df: pd.DataFrame, max_rows: int = 20) -> str:
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


# ---------------------------------------------------------------------------
# SECTION 1 — EXECUTIVE SUMMARY
# ---------------------------------------------------------------------------

def section_executive_summary(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec1">')
    parts.append('<h2>1. Resumen</h2>')

    parts.append(_interp(
        "Historia 4 analiza las <strong>condiciones habilitantes</strong> para la implementación "
        "de Soluciones basadas en la Naturaleza (SbN). Se centra en tres pilares: "
        "<strong>Actores y redes</strong> (¿quiénes pueden facilitar u obstaculizar?), "
        "<strong>Espacios de diálogo</strong> (¿existen mecanismos de coordinación?) y "
        "<strong>Conflictos</strong> (¿qué dinámicas de conflicto podrían afectar la implementación?). "
        "El <strong>Índice de Viabilidad</strong> sintetiza estas tres dimensiones en un único puntaje "
        "(0-1) que indica cuán factible es implementar intervenciones SbN en el territorio.",
        "what"
    ))

    # Stats
    actors_overall = metrics.get("ACTORS_OVERALL", pd.DataFrame())
    spaces_overall = metrics.get("DIALOGUE_SPACES_OVERALL", pd.DataFrame())
    conflicts_overall = metrics.get("CONFLICTS_OVERALL", pd.DataFrame())
    feasibility = metrics.get("FEASIBILITY_OVERALL", pd.DataFrame())

    n_actors = len(actors_overall)
    n_spaces = len(spaces_overall)
    n_conflicts = len(conflicts_overall)
    feas_score = None
    if not feasibility.empty and "feasibility_score" in feasibility.columns:
        feas_score = feasibility["feasibility_score"].iloc[0]

    parts.append('<div class="stats-grid">')
    parts.append(f'<div class="stat-card"><div class="stat-value">{n_actors}</div><div class="stat-label">Actores Identificados</div></div>')
    parts.append(f'<div class="stat-card"><div class="stat-value">{n_spaces}</div><div class="stat-label">Espacios de Diálogo</div></div>')
    parts.append(f'<div class="stat-card"><div class="stat-value">{n_conflicts}</div><div class="stat-label">Conflictos Registrados</div></div>')
    if feas_score is not None:
        feas_class = "feasibility-high" if feas_score >= 0.6 else "feasibility-medium" if feas_score >= 0.4 else "feasibility-low"
        parts.append(f'<div class="stat-card"><div class="stat-value {feas_class}">{feas_score:.2f}</div><div class="stat-label">Índice de Viabilidad</div></div>')
    parts.append('</div>')

    # Narrative interpretation of the feasibility score
    if feas_score is not None:
        if feas_score >= 0.6:
            feas_narrative = (
                f"El Índice de Viabilidad global es <strong>{feas_score:.2f}</strong>, lo que indica "
                f"<strong>condiciones favorables</strong> para la implementación de intervenciones SbN. "
                f"La presencia de {n_actors} actores identificados y {n_spaces} espacios de diálogo activos "
                f"sugiere una base institucional sólida. "
            )
        elif feas_score >= 0.4:
            feas_narrative = (
                f"El Índice de Viabilidad global es <strong>{feas_score:.2f}</strong>, lo que indica "
                f"<strong>condiciones moderadas</strong> para la implementación. Se recomienda fortalecer "
                f"las capacidades de los actores existentes y ampliar los espacios de diálogo antes de "
                f"escalar las intervenciones. "
            )
        else:
            feas_narrative = (
                f"El Índice de Viabilidad global es <strong>{feas_score:.2f}</strong>, lo que indica "
                f"<strong>condiciones desafiantes</strong> para la implementación. Se requiere un trabajo "
                f"previo significativo en fortalecimiento de actores, creación de espacios de diálogo y "
                f"gestión de conflictos antes de implementar intervenciones SbN a escala. "
            )

        if n_conflicts > 0:
            feas_narrative += (
                f"Los <strong>{n_conflicts} conflictos</strong> identificados son un factor de riesgo "
                f"que debe considerarse en la planificación."
            )
        else:
            feas_narrative += "No se registraron conflictos, lo cual es un indicador positivo para la viabilidad."

        parts.append(_interp(feas_narrative, "insight"))

    # Feasibility by group
    feas_grupo = metrics.get("FEASIBILITY_BY_GRUPO", pd.DataFrame())
    if not feas_grupo.empty:
        parts.append('<h3>🎯 Viabilidad por Grupo</h3>')
        parts.append(_interp(
            "La tabla siguiente muestra el <strong>Índice de Viabilidad</strong> desglosado por grupo territorial. "
            "El índice se compone de tres sub-dimensiones: "
            "<strong>Fortaleza de actores</strong> (¿tienen los actores capacidad y presencia?), "
            "<strong>Diálogo</strong> (¿existen y funcionan los espacios de coordinación?), y "
            "<strong>Riesgo de Conflicto</strong> (valores bajos = menor riesgo = mayor viabilidad). "
            "Grupos con puntaje <span class='feasibility-high'>≥ 0.6</span> tienen condiciones favorables; "
            "<span class='feasibility-medium'>0.4-0.6</span> moderadas; "
            "<span class='feasibility-low'>< 0.4</span> desafiantes.",
            "read"
        ))
        cols = [c for c in ["grupo", "feasibility_score", "actor_strength_norm", "dialogue_norm", "conflict_risk_norm"] if c in feas_grupo.columns]
        if cols:
            display = feas_grupo[cols].sort_values("feasibility_score", ascending=False).copy()
            col_names = {"grupo": "Grupo", "feasibility_score": "Viabilidad",
                         "actor_strength_norm": "Fortaleza Actores", "dialogue_norm": "Diálogo",
                         "conflict_risk_norm": "Riesgo Conflicto"}
            display.columns = [col_names.get(c, c) for c in cols]
            parts.append(_df_to_html(display))

        # Data-driven: identify strongest and weakest group
        if "feasibility_score" in feas_grupo.columns and len(feas_grupo) > 1:
            best = feas_grupo.loc[feas_grupo["feasibility_score"].idxmax()]
            worst = feas_grupo.loc[feas_grupo["feasibility_score"].idxmin()]
            gap = best["feasibility_score"] - worst["feasibility_score"]
            parts.append(_interp(
                f"El grupo <strong>{best.get('grupo', '—')}</strong> presenta la mayor viabilidad "
                f"({best['feasibility_score']:.2f}), mientras que <strong>{worst.get('grupo', '—')}</strong> "
                f"tiene la menor ({worst['feasibility_score']:.2f}). "
                f"La brecha entre ambos es de <strong>{gap:.2f}</strong>. "
                + ("Esta diferencia significativa sugiere que las estrategias deben adaptarse por zona." if gap > 0.15
                   else "Esta diferencia modesta sugiere condiciones relativamente homogéneas entre grupos."),
                "insight"
            ))

    if "bar_feasibility_by_grupo" in figures:
        parts.append(_embed_figure(
            figures["bar_feasibility_by_grupo"],
            "Índice de Viabilidad por Grupo",
            "Barras más altas = mayor viabilidad para la implementación de SbN."
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 2 — ACTORS & NETWORKS
# ---------------------------------------------------------------------------

def section_actors(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec2">')
    parts.append('<h2>2. Actores y Redes</h2>')

    parts.append(_interp(
        "Esta sección analiza los <strong>actores clave</strong> del territorio y sus redes de "
        "<strong>colaboración</strong> y <strong>conflicto</strong>. Los actores se evalúan por su "
        "<strong>centralidad</strong> (cuántas conexiones tienen): un actor con alta centralidad de "
        "colaboración es un <strong>articulador potencial</strong>; un actor con alta centralidad de "
        "conflicto es un <strong>nodo de tensión</strong>. Las matrices de relaciones muestran el "
        "tejido institucional del territorio.",
        "what"
    ))

    # Actor centrality
    centrality = metrics.get("ACTOR_CENTRALITY_OVERALL", pd.DataFrame())
    if not centrality.empty:
        parts.append('<h3>🔗 Centralidad de Actores</h3>')
        parts.append(_interp(
            "La <strong>centralidad</strong> mide cuántas relaciones (de colaboración o conflicto) "
            "tiene cada actor. Valores altos de <strong>Grado Colaboración</strong> indican actores bien "
            "conectados que pueden facilitar la coordinación. Valores altos de <strong>Grado Conflicto</strong> "
            "señalan actores frecuentemente involucrados en dinámicas de tensión — no necesariamente negativos, "
            "pero que requieren atención especial en la gestión de procesos.",
            "read"
        ))

        name_col = "actor_name" if "actor_name" in centrality.columns else "actor_id"
        cols = [c for c in [name_col, "out_degree_colabora", "out_degree_conflicto", "out_degree_total"] if c in centrality.columns]
        if cols:
            display = centrality.nlargest(10, "out_degree_total") if "out_degree_total" in centrality.columns else centrality.head(10)
            display = display[cols].copy()
            col_names = {name_col: "Actor", "out_degree_colabora": "Grado Colaboración",
                         "out_degree_conflicto": "Grado Conflicto", "out_degree_total": "Grado Total"}
            display.columns = [col_names.get(c, c) for c in cols]
            parts.append(_df_to_html(display))

        # Data-driven: top collaborator vs top conflict actor
        if "out_degree_colabora" in centrality.columns and "out_degree_conflicto" in centrality.columns:
            top_collab = centrality.loc[centrality["out_degree_colabora"].idxmax()]
            top_conflict = centrality.loc[centrality["out_degree_conflicto"].idxmax()]
            collab_name = top_collab.get("actor_name", top_collab.get("actor_id", "—"))
            conflict_name = top_conflict.get("actor_name", top_conflict.get("actor_id", "—"))

            narrative = (
                f"El actor más articulador es <strong>{collab_name}</strong> "
                f"con {int(top_collab['out_degree_colabora'])} relaciones de colaboración. "
            )
            if top_conflict["out_degree_conflicto"] > 0:
                narrative += (
                    f"El actor más involucrado en conflictos es <strong>{conflict_name}</strong> "
                    f"con {int(top_conflict['out_degree_conflicto'])} relaciones de conflicto. "
                )
            else:
                narrative += "No se identificaron actores en relaciones de conflicto significativas. "

            parts.append(_interp(narrative, "insight"))

    # Collaboration figure
    if "bar_top_actors_collab_overall" in figures:
        parts.append(_embed_figure(
            figures["bar_top_actors_collab_overall"],
            "Actores con Mayor Colaboración",
            "Estos actores son aliados potenciales para articular intervenciones SbN."
        ))

    # Conflict figure
    if "bar_top_actors_conflict_overall" in figures:
        parts.append(_embed_figure(
            figures["bar_top_actors_conflict_overall"],
            "Actores con Mayor Conflicto",
            "Estos actores requieren estrategias de gestión de relaciones."
        ))

    # Collaboration heatmap
    if "heatmap_dyads_collab_overall" in figures:
        parts.append('<h3>📊 Matriz de Colaboración</h3>')
        parts.append(_interp(
            "La <strong>matriz de colaboración</strong> muestra las relaciones de cooperación entre actores. "
            "Colores más intensos indican vínculos más frecuentes o fuertes. "
            "Las concentraciones de color revelan <strong>clústeres de colaboración</strong> — grupos de actores "
            "que trabajan juntos y que pueden servir como plataformas para escalar acciones.",
            "read"
        ))
        parts.append(_embed_figure(
            figures["heatmap_dyads_collab_overall"],
            "Red de Colaboración entre Actores"
        ))

    # Conflict heatmap
    if "heatmap_dyads_conflict_overall" in figures:
        parts.append('<h3>📊 Matriz de Conflicto</h3>')
        parts.append(_interp(
            "La <strong>matriz de conflicto</strong> muestra las relaciones de tensión entre actores. "
            "Identificar los pares con mayor conflicto es clave para diseñar "
            "<strong>estrategias de mediación</strong> antes de implementar proyectos SbN.",
            "read"
        ))
        parts.append(_embed_figure(
            figures["heatmap_dyads_conflict_overall"],
            "Red de Conflicto entre Actores"
        ))

    if centrality.empty:
        parts.append(_interp(
            "<strong>No hay datos de actores disponibles.</strong> "
            "Esta sección requiere las hojas <code>TIDY_5_1_ACTORES</code> y <code>TIDY_5_1_RELACIONES</code> "
            "en el archivo de entrada.",
            "warning"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 3 — DIALOGUE SPACES
# ---------------------------------------------------------------------------

def section_dialogue(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec3">')
    parts.append('<h2>3. Espacios de Diálogo</h2>')

    parts.append(_interp(
        "Los <strong>espacios de diálogo</strong> son mecanismos de coordinación donde los actores "
        "discuten y toman decisiones sobre el uso de recursos naturales. Su presencia y funcionamiento "
        "son indicadores críticos de <strong>gobernanza participativa</strong> e influyen directamente en "
        "la viabilidad de las intervenciones SbN. Se analizan: espacios existentes, participación de actores, "
        "y fortalezas/debilidades identificadas.",
        "what"
    ))

    has_data = False

    # Dialogue spaces
    spaces = metrics.get("DIALOGUE_SPACES_OVERALL", pd.DataFrame())
    if not spaces.empty:
        has_data = True
        parts.append('<h3>🏛️ Espacios Identificados</h3>')
        parts.append(_interp(
            f"Se identificaron <strong>{len(spaces)} espacios de diálogo</strong>. "
            "La tabla muestra sus características principales. "
            "Un territorio con múltiples espacios activos tiene mayor capacidad de gobernanza.",
            "read"
        ))
        display = spaces.copy()
        rename_map = {"id_espacio": "ID", "nombre_espacio": "Nombre", "tipo": "Tipo", "alcance": "Alcance"}
        display.rename(columns={k: v for k, v in rename_map.items() if k in display.columns}, inplace=True)
        parts.append(_df_to_html(display))

    # Participation
    if "bar_dialogue_participation" in figures:
        has_data = True
        parts.append(_embed_figure(
            figures["bar_dialogue_participation"],
            "Participación en Espacios de Diálogo",
            "Barras más altas indican espacios con mayor presencia de actores."
        ))

    # Actor presence in spaces
    actor_spaces = metrics.get("ACTOR_IN_SPACES_OVERALL", pd.DataFrame())
    if not actor_spaces.empty:
        has_data = True
        parts.append('<h3>👥 Actores con Mayor Presencia</h3>')
        parts.append(_interp(
            "Actores que participan en <strong>múltiples espacios de diálogo</strong> son "
            "<strong>articuladores institucionales</strong> — tienen visión transversal y pueden conectar "
            "agendas entre diferentes plataformas. Son aliados estratégicos para socializar propuestas SbN.",
            "read"
        ))
        display = actor_spaces.head(10).copy()
        name_col = "actor_name" if "actor_name" in display.columns else "nombre_actor" if "nombre_actor" in display.columns else None
        id_col = next((c for c in ["actor_id", "id_actor"] if c in display.columns), None)
        if name_col and id_col:
            display.drop(columns=[id_col], inplace=True)
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif name_col:
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif id_col:
            display.rename(columns={id_col: "Actor (ID)"}, inplace=True)
        if "n_spaces" in display.columns:
            display.rename(columns={"n_spaces": "N° Espacios"}, inplace=True)
        parts.append(_df_to_html(display))

    if "bar_actor_in_spaces" in figures:
        has_data = True
        parts.append(_embed_figure(
            figures["bar_actor_in_spaces"],
            "Actores en Múltiples Espacios",
            "Actores con presencia en más espacios son articuladores clave."
        ))

    # Strengths
    strengths = metrics.get("DIALOGUE_STRENGTHS_FREQ_OVERALL", pd.DataFrame())
    if not strengths.empty:
        has_data = True
        parts.append('<h3>✅ Fortalezas del Sistema de Diálogo</h3>')
        parts.append(_interp(
            "Las <strong>fortalezas</strong> son aspectos positivos del sistema de diálogo identificados "
            "por los participantes. Su frecuencia indica cuán ampliamente son reconocidas. "
            "Estas fortalezas son la <strong>base sobre la cual construir</strong> las intervenciones SbN.",
            "read"
        ))
        display = strengths.head(10).copy()
        display.rename(columns={"strength": "Fortaleza", "count": "Frecuencia"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

    # Weaknesses
    weaknesses = metrics.get("DIALOGUE_WEAKNESSES_FREQ_OVERALL", pd.DataFrame())
    if not weaknesses.empty:
        has_data = True
        parts.append('<h3>⚠️ Debilidades del Sistema de Diálogo</h3>')
        parts.append(_interp(
            "Las <strong>debilidades</strong> son brechas o limitaciones del sistema de diálogo. "
            "Su frecuencia indica prioridad de atención. Abordar estas debilidades es esencial "
            "para crear las <strong>condiciones habilitantes</strong> necesarias para la implementación exitosa de SbN.",
            "read"
        ))
        display = weaknesses.head(10).copy()
        display.rename(columns={"weakness": "Debilidad", "count": "Frecuencia"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

        # Data-driven: top weakness
        top_weakness = weaknesses.iloc[0]
        w_name = top_weakness.get("weakness", top_weakness.get("Debilidad", ""))
        if w_name:
            parts.append(_interp(
                f"La debilidad más frecuente es <strong>«{w_name}»</strong>. "
                "Se recomienda diseñar acciones específicas para abordar este hallazgo antes de "
                "escalar intervenciones SbN.",
                "insight"
            ))

    if not has_data:
        parts.append(_interp(
            "<strong>No hay datos de espacios de diálogo disponibles.</strong> "
            "Esta sección requiere las hojas <code>TIDY_5_2_DIALOGO</code> y "
            "<code>TIDY_5_2_DIALOGO_ACTOR</code>.",
            "warning"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 4 — CONFLICTS
# ---------------------------------------------------------------------------

def section_conflicts(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec4">')
    parts.append('<h2>4. Análisis de Conflictos</h2>')

    parts.append(_interp(
        "Esta sección analiza las <strong>dinámicas de conflicto</strong> del territorio: tipos de conflicto, "
        "su evolución en el tiempo y los actores involucrados. Los conflictos no son inherentemente negativos — "
        "pueden revelar <strong>tensiones estructurales</strong> sobre el acceso a recursos que cualquier "
        "intervención SbN debe considerar. Ignorar los conflictos puede llevar al fracaso de proyectos; "
        "comprenderlos permite diseñar estrategias de implementación más robustas.",
        "what"
    ))

    has_data = False

    # Conflict timeline
    timeline = metrics.get("CONFLICT_TIMELINE_OVERALL", pd.DataFrame())
    if not timeline.empty:
        has_data = True
        parts.append('<h3>📈 Línea de Tiempo de Conflictos</h3>')
        parts.append(_interp(
            "La línea de tiempo muestra <strong>cómo ha evolucionado</strong> la frecuencia de eventos de conflicto. "
            "Tendencias crecientes pueden indicar escalamiento; periodos de calma pueden reflejar "
            "intervenciones exitosas o cambios estacionales. Los picos suelen coincidir con "
            "decisiones sobre uso de recursos (cosechas, permisos, etc.).",
            "read"
        ))
        display = timeline.copy()
        display.rename(columns={"anio": "Año", "year": "Año", "n_events": "N° Eventos"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

    if "line_conflict_timeline_overall" in figures:
        has_data = True
        parts.append(_embed_figure(
            figures["line_conflict_timeline_overall"],
            "Eventos de Conflicto en el Tiempo",
            "Observe las tendencias: ¿están aumentando, disminuyendo o se mantienen estables?"
        ))

    # Top conflicts
    conflicts = metrics.get("CONFLICTS_OVERALL", pd.DataFrame())
    if not conflicts.empty:
        has_data = True
        parts.append('<h3>🔥 Principales Conflictos</h3>')
        parts.append(_interp(
            "Los conflictos se clasifican por <strong>número de eventos</strong> registrados. "
            "Los conflictos más frecuentes representan <strong>fricciones estructurales</strong> "
            "que probablemente afectarán la implementación de intervenciones SbN. "
            "Cada uno debe considerarse en el diseño de estrategias de mitigación.",
            "read"
        ))

        display = conflicts.head(10).copy()
        desc_col = "conflict_description" if "conflict_description" in display.columns else "descripcion" if "descripcion" in display.columns else None
        id_col = next((c for c in ["conflicto_id", "conflict_id", "cod_conflict", "codigo_conflicto"] if c in display.columns), None)

        if desc_col and id_col:
            display["Conflicto"] = display.apply(
                lambda row: f"{row[id_col]} - {row[desc_col]}" if pd.notna(row[desc_col]) else str(row[id_col]), axis=1
            )
            display.drop(columns=[id_col, desc_col], inplace=True)
        elif desc_col:
            display.rename(columns={desc_col: "Conflicto"}, inplace=True)
        elif id_col:
            display.rename(columns={id_col: "Conflicto"}, inplace=True)
        if "n_events" in display.columns:
            display.rename(columns={"n_events": "Eventos"}, inplace=True)
        if "Conflicto" in display.columns:
            cols = ["Conflicto"] + [c for c in display.columns if c != "Conflicto"]
            display = display[cols]
        parts.append(_df_to_html(display))

        # Data-driven narrative
        top_conflict = conflicts.iloc[0]
        c_desc = top_conflict.get("conflict_description", top_conflict.get("descripcion", top_conflict.get("conflicto_id", "—")))
        c_events = top_conflict.get("n_events", 0)
        if c_desc and not pd.isna(c_desc):
            parts.append(_interp(
                f"El conflicto más frecuente es <strong>«{c_desc}»</strong> "
                f"con <strong>{int(c_events)} eventos</strong> registrados. "
                "Se recomienda mapear los actores involucrados en este conflicto específico "
                "y diseñar mecanismos de diálogo focalizados.",
                "insight"
            ))

    if "bar_top_conflicts" in figures:
        has_data = True
        parts.append(_embed_figure(
            figures["bar_top_conflicts"],
            "Conflictos por Número de Eventos",
            "Los conflictos con más eventos requieren mayor atención en la planificación."
        ))

    # Conflict actors
    conflict_actors = metrics.get("CONFLICT_ACTORS_OVERALL", pd.DataFrame())
    if not conflict_actors.empty:
        has_data = True
        parts.append('<h3>👤 Actores en Conflictos</h3>')
        parts.append(_interp(
            "Los actores más involucrados en conflictos son <strong>puntos de intervención prioritaria</strong>. "
            "No necesariamente son «causantes» — pueden ser actores que median entre partes o que están "
            "posicionados en nodos de tensión estructural. Incluirlos en procesos de diálogo es crítico.",
            "read"
        ))

        display = conflict_actors.head(15).copy()
        name_col = "actor_name" if "actor_name" in display.columns else "nombre_actor" if "nombre_actor" in display.columns else None
        id_col = next((c for c in ["actor_id", "id_actor"] if c in display.columns), None)
        if name_col and id_col:
            display.drop(columns=[id_col], inplace=True)
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif name_col:
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif id_col:
            display.rename(columns={id_col: "Actor (ID)"}, inplace=True)
        display.rename(columns={"n_conflicts": "N° Conflictos", "n_records": "N° Conflictos"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

    if not has_data:
        parts.append(_interp(
            "<strong>No hay datos de conflictos disponibles.</strong> "
            "Esta sección requiere las hojas <code>TIDY_6_1_CONFLICT_EVENTS</code> y "
            "<code>TIDY_6_2_CONFLICTO_ACTOR</code>.",
            "warning"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 5 — THREAT-CONFLICT LINKAGES
# ---------------------------------------------------------------------------

def section_linkages(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    parts = []
    parts.append('<section id="sec5">')
    parts.append('<h2>5. Vínculos con Amenazas</h2>')

    parts.append(_interp(
        "Esta sección explora las <strong>conexiones entre conflictos, amenazas y medios de vida</strong>. "
        "Estas conexiones revelan cómo las dinámicas de conflicto están vinculadas a presiones sobre "
        "recursos naturales específicos. Cuando un conflicto está vinculado a una amenaza que afecta "
        "un medio de vida prioritario, se convierte en un <strong>factor de riesgo directo</strong> "
        "para las intervenciones SbN planificadas.",
        "what"
    ))

    has_data = False

    # Threats linked to conflicts
    threats_linked = metrics.get("TOP_CONFLICT_LINKED_THREATS", pd.DataFrame())
    if not threats_linked.empty:
        has_data = True
        parts.append('<h3>🔗 Amenazas Vinculadas a Conflictos</h3>')
        parts.append(_interp(
            "Las amenazas con más conflictos asociados representan <strong>puntos calientes de tensión</strong>. "
            "Si una amenaza tiene múltiples conflictos, las intervenciones en esa área enfrentarán mayor resistencia "
            "o complejidad social.",
            "read"
        ))
        display = threats_linked.copy()
        display.rename(columns={"amenaza": "Amenaza", "n_conflicts": "N° Conflictos"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

    if "bar_threats_linked_conflicts" in figures:
        has_data = True
        parts.append(_embed_figure(
            figures["bar_threats_linked_conflicts"],
            "Amenazas más Vinculadas a Conflictos",
            "Amenazas con más conflictos asociados requieren estrategias de gestión social."
        ))

    # MDV linkages
    link_mdv = metrics.get("LINK_MDV_THREAT_CONFLICT_OVERALL", pd.DataFrame())
    if not link_mdv.empty:
        has_data = True
        parts.append('<h3>🌾 Vínculos Medios de Vida - Amenazas - Conflictos</h3>')
        parts.append(_interp(
            "Esta tabla muestra las <strong>cadenas causales completas</strong>: un medio de vida está amenazado "
            "por un factor específico, y ese factor está asociado a un conflicto social. "
            "Las intervenciones SbN más efectivas abordan <strong>simultáneamente</strong> la amenaza ecológica "
            "y la tensión social asociada.",
            "read"
        ))
        display = link_mdv.head(15).copy()
        display.rename(columns={"mdv_name": "Medio de Vida", "amenaza": "Amenaza", "conflicto_id": "Conflicto"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

    # SE linkages
    link_se = metrics.get("LINK_SE_THREAT_CONFLICT_OVERALL", pd.DataFrame())
    if not link_se.empty:
        has_data = True
        parts.append('<h3>🌿 Vínculos Servicios Ecosistémicos - Amenazas - Conflictos</h3>')
        parts.append(_interp(
            "Cuando un <strong>servicio ecosistémico</strong> está amenazado y además vinculado a un conflicto, "
            "se necesita una <strong>estrategia integrada</strong> que combine restauración ecológica "
            "con gestión social del conflicto.",
            "read"
        ))
        display = link_se.head(15).copy()
        display.rename(columns={"se_code": "Servicio", "amenaza": "Amenaza", "conflicto_id": "Conflicto"}, inplace=True, errors="ignore")
        parts.append(_df_to_html(display))

    if not has_data:
        parts.append(_interp(
            "No se encontraron tablas de mapeo de conflictos con amenazas. "
            "Esto no es necesariamente negativo — las hojas <code>TIDY_4_2_1_MAPEO_CONFLICTO</code> "
            "y <code>TIDY_4_2_2_MAPEO_CONFLICTO</code> son opcionales.",
            "insight"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SECTION 6 — DATA QUALITY
# ---------------------------------------------------------------------------

def section_data_quality(
    tables: Dict[str, pd.DataFrame],
    warnings: List[str],
) -> str:
    parts = []
    parts.append('<section id="sec6">')
    parts.append('<h2>6. Calidad de Datos</h2>')

    parts.append(_interp(
        "Esta sección documenta la <strong>cobertura y calidad</strong> de los datos utilizados. "
        "Las advertencias señalan posibles limitaciones en la interpretación de los resultados. "
        "Una alta calidad de datos fortalece la confianza en las conclusiones del análisis.",
        "what"
    ))

    if warnings:
        parts.append('<h3>⚠️ Advertencias</h3>')
        parts.append(_interp(
            f"Se detectaron <strong>{len(warnings)} advertencias</strong> durante el procesamiento. "
            "Cada advertencia puede indicar datos faltantes, hojas incompletas o inconsistencias "
            "que limitan el alcance de alguna sección del análisis.",
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
                    "Los controles automáticos verifican la integridad de los datos de entrada. "
                    "Duplicados, IDs faltantes o inconsistencias pueden afectar la precisión de los cálculos.",
                    "read"
                ))
                has_qa = True
            parts.append(f'<h4>{qa_sheet}</h4>')
            parts.append(_df_to_html(qa_df, max_rows=10))

    if not has_qa and not warnings:
        parts.append(_interp(
            "<strong>✓ No se detectaron problemas de calidad.</strong> "
            "Los datos de entrada pasaron todos los controles automáticos.",
            "insight"
        ))

    parts.append('</section>')
    return "\n".join(parts)


# ==========================================================================
# MASTER FUNCTION
# ==========================================================================

def generate_interpreted_report(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str],
    tables: Optional[Dict[str, pd.DataFrame]] = None,
    org_name: str = "Organización",
) -> str:
    """
    Generate the complete interpreted HTML report for Storyline 4.

    Same signature as storyline4.report.generate_report for drop-in usage.

    Args:
        metrics: Dict of computed metrics tables
        figures: Dict of figure name -> file path
        input_path: Path to input file
        warnings: List of warning messages
        tables: Optional dict of input tables for QA section
        org_name: Name of the organization

    Returns:
        Complete interpreted HTML report string
    """
    content = ""
    content += section_executive_summary(metrics, figures)
    content += section_actors(metrics, figures)
    content += section_dialogue(metrics, figures)
    content += section_conflicts(metrics, figures)
    content += section_linkages(metrics, figures)
    content += section_data_quality(tables or {}, warnings)

    html = HTML_TEMPLATE.format(
        org_name=org_name,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        content=content,
    )

    logger.info("Generated interpreted HTML report for Storyline 4")
    return html
