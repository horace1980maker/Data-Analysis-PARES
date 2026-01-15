"""
Report module for Storyline 4.
Generates HTML diagnostic report with embedded tables and images.
Spanish language support included.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import GRUPO_COL

logger = logging.getLogger(__name__)


# =============================================================================
# HTML TEMPLATE - Spanish/English bilingual with Teal/Amber theme
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Storyline 4: Viabilidad, Gobernanza y Riesgo de Conflicto</title>
    <style>
        :root {{
            --primary-color: #00695c;
            --secondary-color: #26a69a;
            --accent-color: #ffb300;
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
            background-color: #e0f2f1;
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
        
        .success {{
            background: #e0f2f1;
            border-left: 4px solid var(--primary-color);
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
        
        .feasibility-high {{
            color: #2e7d32;
            font-weight: bold;
        }}
        
        .feasibility-medium {{
            color: #ff9800;
            font-weight: bold;
        }}
        
        .feasibility-low {{
            color: #c62828;
            font-weight: bold;
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
        <h1>📊 Historia 4: Viabilidad, Gobernanza y Riesgo de Conflicto</h1>
        <p><strong>Informe Diagnóstico - Viabilidad, Gobernanza y Riesgo de Conflicto</strong></p>
        
        <div class="metadata">
            <strong>Generado:</strong> {timestamp}<br>
            <strong>Archivo de entrada:</strong> {input_file}<br>
            <strong>Alcance del análisis:</strong> Actores, Espacios de Diálogo, Conflictos, Viabilidad
        </div>
        
        <div class="toc">
            <h3>📋 Tabla de Contenidos</h3>
            <ul>
                <li><a href="#executive-summary">1. Resumen Ejecutivo</a></li>
                <li><a href="#actors-networks">2. Actores y Redes</a></li>
                <li><a href="#dialogue-spaces">3. Espacios de Diálogo</a></li>
                <li><a href="#conflicts">4. Análisis de Conflictos</a></li>
                <li><a href="#linkages">5. Vínculos con Amenazas</a></li>
                <li><a href="#data-quality">6. Calidad de Datos</a></li>
            </ul>
        </div>
        
        {content}
        
        <hr>
        <p style="text-align: center; color: #666; font-size: 0.85em;">
            Generado por Storyline 4 Pipeline v1.0.0 | Metodología PARES<br>
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
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate executive summary section."""
    content = '<section id="executive-summary" class="section"><h2>1. Resumen Ejecutivo</h2>'
    
    # Stats cards
    content += '<div class="stats-grid">'
    
    # Count actors
    actors_overall = metrics.get("ACTORS_OVERALL", pd.DataFrame())
    n_actors = len(actors_overall)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_actors}</div>
        <div class="stat-label">Actores Identificados</div>
    </div>
    '''
    
    # Count dialogue spaces
    spaces_overall = metrics.get("DIALOGUE_SPACES_OVERALL", pd.DataFrame())
    n_spaces = len(spaces_overall)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_spaces}</div>
        <div class="stat-label">Espacios de Diálogo</div>
    </div>
    '''
    
    # Count conflicts
    conflicts_overall = metrics.get("CONFLICTS_OVERALL", pd.DataFrame())
    n_conflicts = len(conflicts_overall)
    content += f'''
    <div class="stat-card">
        <div class="stat-value">{n_conflicts}</div>
        <div class="stat-label">Conflictos Registrados</div>
    </div>
    '''
    
    # Feasibility score
    feasibility = metrics.get("FEASIBILITY_OVERALL", pd.DataFrame())
    if not feasibility.empty and "feasibility_score" in feasibility.columns:
        feas_score = feasibility["feasibility_score"].iloc[0]
        feas_class = "feasibility-high" if feas_score >= 0.6 else "feasibility-medium" if feas_score >= 0.4 else "feasibility-low"
        content += f'''
        <div class="stat-card">
            <div class="stat-value {feas_class}">{feas_score:.2f}</div>
            <div class="stat-label">Índice de Viabilidad</div>
        </div>
        '''
    
    content += '</div>'  # stats-grid
    
    # Feasibility by grupo
    feas_grupo = metrics.get("FEASIBILITY_BY_GRUPO", pd.DataFrame())
    if not feas_grupo.empty:
        content += '<h3>🎯 Viabilidad por Zona</h3>'
        cols = [c for c in ["grupo", "feasibility_score", "actor_strength_norm", "dialogue_norm", "conflict_risk_norm"] if c in feas_grupo.columns]
        if cols:
            display = feas_grupo[cols].sort_values("feasibility_score", ascending=False).copy()
            display.columns = ["Zona (Grupo)", "Indice Viabilidad", "Fortaleza Actores", "Diálogo", "Riesgo Conflicto"][:len(cols)]
            content += df_to_html(display)
    
    # Feasibility figure
    if "bar_feasibility_by_grupo" in figures:
        content += embed_image(figures["bar_feasibility_by_grupo"], "Índice de Viabilidad por Zona")
    
    content += '</section>'
    return content


def generate_actors_section(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate actors and networks section."""
    content = '<section id="actors-networks" class="section"><h2>2. Actores y Redes / Actors & Networks</h2>'
    content += '<p>Análisis de actores clave y sus redes de colaboración y conflicto. / Analysis of key actors and their collaboration and conflict networks.</p>'
    
    has_data = False
    
    # Actor centrality
    centrality = metrics.get("ACTOR_CENTRALITY_OVERALL", pd.DataFrame())
    if not centrality.empty:
        has_data = True
        content += '<h3>🔗 Centralidad de Actores</h3>'
        # Prefer actor_name over actor_id
        name_col = "actor_name" if "actor_name" in centrality.columns else "actor_id"
        cols = [c for c in [name_col, "out_degree_colabora", "out_degree_conflicto", "out_degree_total"] if c in centrality.columns]
        if cols:
            display = centrality.nlargest(10, "out_degree_total") if "out_degree_total" in centrality.columns else centrality.head(10)
            display = display[cols].copy()
            display.columns = ["Actor", "Grado Colaboración", "Grado Conflicto", "Grado Total"][:len(cols)]
            content += df_to_html(display)

    
    # Collaboration figure
    if "bar_top_actors_collab_overall" in figures:
        has_data = True
        content += embed_image(figures["bar_top_actors_collab_overall"], "Actores con Mayor Colaboración")
    
    # Conflict figure
    if "bar_top_actors_conflict_overall" in figures:
        has_data = True
        content += embed_image(figures["bar_top_actors_conflict_overall"], "Actores con Mayor Conflicto")
    
    # Dyads heatmaps
    if "heatmap_dyads_collab_overall" in figures:
        has_data = True
        content += '<h3>📊 Matriz de Colaboración</h3>'
        content += embed_image(figures["heatmap_dyads_collab_overall"], "Red de Colaboración entre Actores")
    
    if "heatmap_dyads_conflict_overall" in figures:
        has_data = True
        content += '<h3>📊 Matriz de Conflicto</h3>'
        content += embed_image(figures["heatmap_dyads_conflict_overall"], "Red de Conflicto entre Actores")
    
    if not has_data:
        content += '''
        <div class="warning">
            <strong>No hay datos de actores disponibles.</strong><br>
            Esta sección requiere la hoja: <code>TIDY_5_1_ACTORES</code> y <code>TIDY_5_1_RELACIONES</code>
        </div>
        '''
    
    content += '</section>'
    return content


def generate_dialogue_section(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate dialogue spaces section."""
    content = '<section id="dialogue-spaces" class="section"><h2>3. Espacios de Diálogo</h2>'
    content += '<p>Análisis de espacios de diálogo y participación de actores.</p>'
    
    has_data = False
    
    # Dialogue spaces
    spaces = metrics.get("DIALOGUE_SPACES_OVERALL", pd.DataFrame())
    if not spaces.empty:
        has_data = True
        content += '<h3>🏛️ Espacios de Diálogo Identificados</h3>'
        display = spaces.copy()
        if "id_espacio" in display.columns:
            display.rename(columns={"id_espacio": "ID Espacio"}, inplace=True)
        if "nombre_espacio" in display.columns:
            display.rename(columns={"nombre_espacio": "Nombre Espacio"}, inplace=True)
        if "tipo" in display.columns:
            display.rename(columns={"tipo": "Tipo"}, inplace=True)
        if "alcance" in display.columns:
            display.rename(columns={"alcance": "Alcance"}, inplace=True)
        content += df_to_html(display)
    
    # Participation figure
    if "bar_dialogue_participation" in figures:
        has_data = True
        content += embed_image(figures["bar_dialogue_participation"], "Participación en Espacios de Diálogo")
    
    # Actor in spaces
    actor_spaces = metrics.get("ACTOR_IN_SPACES_OVERALL", pd.DataFrame())
    if not actor_spaces.empty:
        has_data = True
        content += '<h3>👥 Actores con Mayor Presencia</h3>'
        display = actor_spaces.head(10).copy()
        
        # Handle Actor Name vs ID
        actor_col = "actor_id"
        if "actor_id" in display.columns: field_id = "actor_id"
        elif "id_actor" in display.columns: field_id = "id_actor"
        else: field_id = None

        name_col = None
        if "actor_name" in display.columns: name_col = "actor_name"
        elif "nombre_actor" in display.columns: name_col = "nombre_actor"
        
        if name_col and field_id:
            # Drop ID, keep Name
            display.drop(columns=[field_id], inplace=True)
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif name_col:
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif field_id:
            display.rename(columns={field_id: "Actor (ID)"}, inplace=True)

        if "n_spaces" in display.columns:
            display.rename(columns={"n_spaces": "N° Espacios"}, inplace=True)
        
        # Reorder to put Actor first
        if "Actor" in display.columns:
            cols = ["Actor"] + [c for c in display.columns if c != "Actor"]
            display = display[cols]
            
        content += df_to_html(display)
    
    if "bar_actor_in_spaces" in figures:
        has_data = True
        content += embed_image(figures["bar_actor_in_spaces"], "Actores en Múltiples Espacios")
    
    # Strengths/weaknesses
    strengths = metrics.get("DIALOGUE_STRENGTHS_FREQ_OVERALL", pd.DataFrame())
    if not strengths.empty:
        has_data = True
        content += '<h3>✅ Fortalezas Principales</h3>'
        display = strengths.head(10).copy()
        if "strength" in display.columns:
            display.rename(columns={"strength": "Fortaleza"}, inplace=True)
        if "count" in display.columns:
            display.rename(columns={"count": "Frecuencia"}, inplace=True)
        content += df_to_html(display)
    
    weaknesses = metrics.get("DIALOGUE_WEAKNESSES_FREQ_OVERALL", pd.DataFrame())
    if not weaknesses.empty:
        has_data = True
        content += '<h3>⚠️ Debilidades Principales</h3>'
        display = weaknesses.head(10).copy()
        if "weakness" in display.columns:
            display.rename(columns={"weakness": "Debilidad"}, inplace=True)
        if "count" in display.columns:
            display.rename(columns={"count": "Frecuencia"}, inplace=True)
        content += df_to_html(display)
    
    if not has_data:
        content += '''
        <div class="warning">
            <strong>No hay datos de diálogo disponibles.</strong><br>
            Esta sección requiere las hojas: <code>TIDY_5_2_DIALOGO</code> y <code>TIDY_5_2_DIALOGO_ACTOR</code>
        </div>
        '''
    
    content += '</section>'
    return content


def generate_conflicts_section(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate conflicts analysis section."""
    content = '<section id="conflicts" class="section"><h2>4. Análisis de Conflictos</h2>'
    content += '<p>Evolución temporal y caracterización de conflictos.</p>'
    
    has_data = False
    
    # Conflict timeline
    timeline = metrics.get("CONFLICT_TIMELINE_OVERALL", pd.DataFrame())
    if not timeline.empty:
        has_data = True
        content += '<h3>📈 Línea de Tiempo de Conflictos</h3>'
        display = timeline.copy()
        if "anio" in display.columns:
            display.rename(columns={"anio": "Año"}, inplace=True)
        elif "year" in display.columns:
            display.rename(columns={"year": "Año"}, inplace=True)
        if "n_events" in display.columns:
            display.rename(columns={"n_events": "N° Eventos"}, inplace=True)
        content += df_to_html(display)
    
    if "line_conflict_timeline_overall" in figures:
        has_data = True
        content += embed_image(figures["line_conflict_timeline_overall"], "Eventos de Conflicto en el Tiempo")
    
    # Top conflicts
    conflicts = metrics.get("CONFLICTS_OVERALL", pd.DataFrame())
    if not conflicts.empty:
        has_data = True
        content += '<h3>🔥 Principales Conflictos</h3>'
        display = conflicts.head(10).copy()
        
        # Identify descriptive and ID columns
        desc_col = None
        if "conflict_description" in display.columns: desc_col = "conflict_description"
        elif "descripcion" in display.columns: desc_col = "descripcion"
        
        id_col = None
        for c in ["conflicto_id", "conflict_id", "cod_conflict", "codigo_conflicto"]:
            if c in display.columns:
                id_col = c
                break
        
        # Combine if reasonably short, otherwise prefer description
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
        
        # Reorder
        if "Conflicto" in display.columns:
            cols = ["Conflicto"] + [c for c in display.columns if c != "Conflicto"]
            display = display[cols]
            
        content += df_to_html(display)

    
    if "bar_top_conflicts" in figures:
        has_data = True
        content += embed_image(figures["bar_top_conflicts"], "Conflictos por Número de Eventos")
    
    # Conflict actors
    conflict_actors = metrics.get("CONFLICT_ACTORS_OVERALL", pd.DataFrame())
    if not conflict_actors.empty:
        has_data = True
        content += '<h3>👤 Actores en Conflictos</h3>'
        display = conflict_actors.head(15).copy()
        
        # Handle Actor Name vs ID (Logic matching generate_dialogue_section)
        # We know we updated metrics.py to add actor_name
        name_col = None
        if "actor_name" in display.columns: name_col = "actor_name"
        elif "nombre_actor" in display.columns: name_col = "nombre_actor"
        
        id_col = None
        for c in ["actor_id", "id_actor", "ca_actor_col"]: # checking potential names
            if c in display.columns:
                id_col = c
                break
        
        if name_col and id_col:
            display.drop(columns=[id_col], inplace=True)
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif name_col:
            display.rename(columns={name_col: "Actor"}, inplace=True)
        elif id_col:
            display.rename(columns={id_col: "Actor (ID)"}, inplace=True)
            
        if "n_conflicts" in display.columns:
            display.rename(columns={"n_conflicts": "N° Conflictos"}, inplace=True)
        elif "n_records" in display.columns:
            display.rename(columns={"n_records": "N° Conflictos"}, inplace=True)
            
        content += df_to_html(display)
    
    if not has_data:
        content += '''
        <div class="warning">
            <strong>No hay datos de conflictos disponibles.</strong><br>
            Esta sección requiere las hojas: <code>TIDY_6_1_CONFLICT_EVENTS</code> y <code>TIDY_6_2_CONFLICTO_ACTOR</code>
        </div>
        '''
    
    content += '</section>'
    return content


def generate_linkages_section(
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
) -> str:
    """Generate threat-conflict linkages section."""
    content = '<section id="linkages" class="section"><h2>5. Vínculos con Amenazas</h2>'
    content += '<p>Relaciones entre conflictos, amenazas y medios de vida.</p>'
    
    # Debug logging
    linkage_keys = [k for k in metrics.keys() if 'LINK' in k or 'THREAT' in k]
    logger.info(f"Linkages section - available linkage keys in metrics: {linkage_keys}")
    logger.info(f"Linkages section - all metrics keys: {list(metrics.keys())}")
    
    has_data = False
    
    # Threats linked to conflicts
    threats_linked = metrics.get("TOP_CONFLICT_LINKED_THREATS", pd.DataFrame())
    if not threats_linked.empty:
        has_data = True
        content += '<h3>🔗 Amenazas Vinculadas a Conflictos</h3>'
        display = threats_linked.copy()
        if "amenaza" in display.columns:
            display.rename(columns={"amenaza": "Amenaza"}, inplace=True)
        if "n_conflicts" in display.columns:
            display.rename(columns={"n_conflicts": "N° Conflictos"}, inplace=True)
        content += df_to_html(display)
    
    if "bar_threats_linked_conflicts" in figures:
        has_data = True
        content += embed_image(figures["bar_threats_linked_conflicts"], "Amenazas más Vinculadas a Conflictos")
    
    # MDV linkages
    link_mdv = metrics.get("LINK_MDV_THREAT_CONFLICT_OVERALL", pd.DataFrame())
    if not link_mdv.empty:
        has_data = True
        content += '<h3>🌾 Vínculos Medios de Vida - Amenazas - Conflictos</h3>'
        display = link_mdv.head(15).copy()
        if "mdv_name" in display.columns:
            display.rename(columns={"mdv_name": "Medio de Vida"}, inplace=True)
        if "amenaza" in display.columns:
            display.rename(columns={"amenaza": "Amenaza"}, inplace=True)
        if "conflicto_id" in display.columns:
            display.rename(columns={"conflicto_id": "Conflicto"}, inplace=True)
        content += df_to_html(display)
    
    # SE linkages
    link_se = metrics.get("LINK_SE_THREAT_CONFLICT_OVERALL", pd.DataFrame())
    if not link_se.empty:
        has_data = True
        content += '<h3>🌿 Vínculos Servicios - Amenazas - Conflictos</h3>'
        display = link_se.head(15).copy()
        if "se_code" in display.columns:
            display.rename(columns={"se_code": "Servicio"}, inplace=True)
        if "amenaza" in display.columns:
            display.rename(columns={"amenaza": "Amenaza"}, inplace=True)
        if "conflicto_id" in display.columns:
            display.rename(columns={"conflicto_id": "Conflicto"}, inplace=True)
        content += df_to_html(display)
    
    if not has_data:
        content += '''
        <div class="success">
            <strong>No se encontraron tablas de mapeo de conflictos.</strong><br>
            Las hojas opcionales <code>TIDY_4_2_1_MAPEO_CONFLICTO</code> y <code>TIDY_4_2_2_MAPEO_CONFLICTO</code> no están presentes.
        </div>
        '''
    
    content += '</section>'
    return content


def generate_qa_section(
    tables: Dict[str, pd.DataFrame],
    warnings: List[str],
) -> str:
    """Generate QA summary section."""
    content = '<section id="data-quality" class="section"><h2>6. Calidad de Datos</h2>'
    
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
    metrics: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str],
    tables: Optional[Dict[str, pd.DataFrame]] = None,
) -> str:
    """
    Generate complete HTML report.
    
    Args:
        metrics: Dict of computed metrics tables
        figures: Dict of figure name -> file path
        input_path: Path to input file (for display)
        warnings: List of warning messages
        tables: Optional dict of input tables for QA section
        
    Returns:
        Complete HTML report string
    """
    content = ""
    
    # Executive summary
    content += generate_executive_summary(metrics, figures)
    
    # Actors & networks
    content += generate_actors_section(metrics, figures)
    
    # Dialogue spaces
    content += generate_dialogue_section(metrics, figures)
    
    # Conflicts
    content += generate_conflicts_section(metrics, figures)
    
    # Linkages
    content += generate_linkages_section(metrics, figures)
    
    # QA section
    content += generate_qa_section(tables or {}, warnings)
    
    # Build final HTML
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    input_file = Path(input_path).name
    
    html = HTML_TEMPLATE.format(
        timestamp=timestamp,
        input_file=input_file,
        content=content,
    )
    
    logger.info("Generated HTML report")
    return html
