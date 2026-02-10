#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 Report Module
Generates an HTML diagnostic report with embedded tables and images.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import (
    ABBREVIATIONS,
    CONFLICT_TYPE_CODES,
    FRECUENCIA_NAMES,
    MAGNITUD_NAMES,
    SE_CODE_NAMES,
    TENDENCIA_NAMES,
    expand_conflict_type,
    expand_frecuencia,
    expand_magnitud,
    expand_se_code,
    expand_tendencia,
)

logger = logging.getLogger(__name__)

# HTML template with embedded CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historia 1: ¿Dónde actuar primero? - Informe Diagnóstico</title>
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
        
        .success {{
            background: #e8f5e9;
            border-left: 4px solid var(--accent-color);
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .abbreviations {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        
        .abbreviations h3 {{
            margin-top: 0;
            color: #1565c0;
        }}
        
        .abbr-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
        }}
        
        .abbr-item {{
            padding: 5px 10px;
            background: white;
            border-radius: 3px;
        }}
        
        .abbr-code {{
            font-weight: bold;
            color: var(--primary-color);
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
        
        .qa-summary {{
            margin-top: 20px;
        }}
        
        .qa-item {{
            margin-bottom: 15px;
        }}
        
        .qa-status {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        
        .qa-ok {{
            background: #c8e6c9;
            color: #2e7d32;
        }}
        
        .qa-warning {{
            background: #ffecb3;
            color: #f57c00;
        }}
        
        .qa-error {{
            background: #ffcdd2;
            color: #c62828;
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
        <h1>📊 Historia 1: ¿Dónde actuar primero?</h1>
        <p><strong>Informe Diagnóstico - Análisis de Prioridad Basado en Evidencia</strong></p>
        
        <div class="metadata">
            <strong>Organización:</strong> {org_name}<br>
            <strong>Generado:</strong> {generation_time}<br>
            <strong>Archivo de Entrada:</strong> {input_file}<br>
            <strong>Alcance del Análisis:</strong> General + Por Grupo
        </div>
        
        {abbreviations_section}
        
        <div class="toc">
            <h3>📋 Tabla de Contenidos</h3>
            <ul>
                <li><a href="#executive-summary">1. Resumen Ejecutivo</a></li>
                <li><a href="#priority-analysis">2. Análisis de Prioridad</a></li>
                <li><a href="#threat-analysis">3. Análisis de Amenazas</a></li>
                <li><a href="#capacity-analysis">4. Análisis de Capacidad</a></li>
                <li><a href="#api-rankings">5. Rankings del Índice de Prioridad de Acción (IPA)</a></li>
                <li><a href="#drivers">6. Motores de Amenaza</a></li>
                <li><a href="#visualizations">7. Visualizaciones</a></li>
                <li><a href="#qa-summary">8. Resumen de Calidad (QA)</a></li>
            </ul>
        </div>
        
        {content}
        
        <hr>
        <p style="text-align: center; color: #666; font-size: 0.85em;">
            Generado por Storyline 1 Pipeline v1.0.0 | Metodología PARES<br>
            © 2026 - Para uso analítico interno
        </p>
    </div>
</body>
</html>
"""


def encode_image_base64(image_path: str) -> str:
    """Encode an image file to base64 string."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    except Exception as e:
        logger.warning(f"Failed to encode image {image_path}: {e}")
        return ""


def df_to_html(df: pd.DataFrame, max_rows: int = 20, float_format: str = ":.2f") -> str:
    """Convert DataFrame to HTML table with formatting."""
    if df.empty:
        return "<p><em>No hay datos disponibles</em></p>"
    
    # Truncate if too many rows
    if len(df) > max_rows:
        display_df = df.head(max_rows).copy()
        truncation_note = f"<p><em>Mostrando {max_rows} de {len(df)} filas</em></p>"
    else:
        display_df = df.copy()
        truncation_note = ""
    
    # Format float columns
    for col in display_df.select_dtypes(include=["float64", "float32"]).columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    
    html = display_df.to_html(index=False, classes="", escape=False, na_rep="")
    return html + truncation_note


def generate_abbreviations_section() -> str:
    """Generate HTML section explaining abbreviations and codes."""
    items = []
    
    # General abbreviations
    for abbr, meaning in ABBREVIATIONS.items():
        items.append(f'<div class="abbr-item"><span class="abbr-code">{abbr}</span>: {meaning}</div>')
    
    # SE codes (first few)
    items.append('<div class="abbr-item"><strong>--- Códigos de Servicios Ecosistémicos ---</strong></div>')
    for code, name in list(SE_CODE_NAMES.items())[:8]:
        items.append(f'<div class="abbr-item"><span class="abbr-code">{code}</span>: {name}</div>')
    items.append('<div class="abbr-item"><em>... y más códigos P/R/A/C</em></div>')
    
    # Conflict codes (first few)
    items.append('<div class="abbr-item"><strong>--- Códigos de Tipo de Conflicto ---</strong></div>')
    for code, name in list(CONFLICT_TYPE_CODES.items())[:4]:
        items.append(f'<div class="abbr-item"><span class="abbr-code">{code}</span>: {name}</div>')
    items.append('<div class="abbr-item"><em>... C5-C7</em></div>')
    
    return f"""
    <div class="abbreviations">
        <h3>📖 Referencia de Abreviaturas y Códigos</h3>
        <div class="abbr-list">
            {''.join(items)}
        </div>
    </div>
    """


def generate_executive_summary(
    tables: Dict[str, pd.DataFrame],
    top_n: int = 5,
) -> str:
    """Generate executive summary section."""
    sections = []
    
    sections.append('<section id="executive-summary" class="section">')
    sections.append('<h2>1. Resumen Ejecutivo</h2>')
    
    # Top livelihoods overall (balanced scenario)
    rankings_balanced = tables.get("rankings_overall_balanced", pd.DataFrame())
    if not rankings_balanced.empty:
        sections.append('<h3>🌱 Medios de Vida de Máxima Prioridad (General - Escenario Equilibrado)</h3>')
        top = rankings_balanced.head(top_n)[["rank", "mdv_name", "api_score", "priority_norm", "risk_norm", "cap_gap_norm"]]
        top.columns = ["Rango", "Medio de Vida (MdV)", "Puntaje IPA", "Prioridad", "Riesgo", "Brecha de Capacidad"]
        sections.append(df_to_html(top, max_rows=top_n))
    
    # Top livelihoods by grupo
    rankings_group = tables.get("rankings_by_group_balanced", pd.DataFrame())
    if not rankings_group.empty and "grupo" in rankings_group.columns:
        sections.append('<h3>🗺️ Medios de Vida de Máxima Prioridad por Grupo</h3>')
        for grupo in rankings_group["grupo"].dropna().unique():
            grupo_data = rankings_group[rankings_group["grupo"] == grupo].head(3)
            if not grupo_data.empty:
                sections.append(f'<div class="subsection"><strong>{grupo}:</strong>')
                display = grupo_data[["rank", "mdv_name", "api_score"]]
                display.columns = ["Rango", "Medio de Vida", "Puntaje IPA"]
                sections.append(df_to_html(display, max_rows=5))
                sections.append('</div>')
    
    # Top threats overall
    threats = tables.get("threats_overall", pd.DataFrame())
    if not threats.empty:
        sections.append('<h3>⚠️ Principales Amenazas (General)</h3>')
        top_threats = threats.nlargest(top_n, "mean_suma")[["amenaza", "tipo_amenaza", "mean_suma", "mean_magnitud", "mean_frequencia"]]
        top_threats.columns = ["Amenaza", "Tipo", "Severidad (Suma)", "Magnitud", "Frecuencia"]
        
        # Expand magnitude and frequency values
        if "Magnitude" in top_threats.columns:
            top_threats["Magnitude"] = top_threats["Magnitude"].apply(
                lambda x: expand_magnitud(int(round(x))) if pd.notna(x) else ""
            )
        if "Frequency" in top_threats.columns:
            top_threats["Frequency"] = top_threats["Frequency"].apply(
                lambda x: expand_frecuencia(int(round(x))) if pd.notna(x) else ""
            )
        
        sections.append(df_to_html(top_threats, max_rows=top_n))
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_priority_section(tables: Dict[str, pd.DataFrame]) -> str:
    """Generate priority analysis section with dual views: field ranking and analytical mean."""
    sections = []
    
    sections.append('<section id="priority-analysis" class="section">')
    sections.append('<h2>2. Análisis de Prioridad</h2>')
    sections.append('<p>Los puntajes de prioridad se derivan de TIDY_3_2_PRIORIZACION, midiendo la importancia del medio de vida a través de múltiples dimensiones.</p>')
    
    sections.append('''
    <div class="info-box" style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #1976d2;">
        <h4 style="margin-top: 0; color: #1565c0;">&#128202; Dos Vistas para Comparación</h4>
        <ul style="margin-bottom: 0;">
            <li><strong>Ranking de Campo</strong>: Utiliza los puntajes brutos de <code>i_total</code> calculados durante el taller, clasificados dentro de cada grupo. Esto respeta la metodología participativa.</li>
            <li><strong>Promedio Analítico</strong>: Agrega los puntajes a través de contextos utilizando la media, permitiendo comparaciones en todo el paisaje.</li>
        </ul>
    </div>
    ''')
    
    # -------------------------------------------------------------------------
    # FIELD-STYLE RANKING: How each zone ranked their livelihoods
    # -------------------------------------------------------------------------
    field_ranking = tables.get("priority_field_ranking", pd.DataFrame())
    sections.append('<h3>🌍 Ranking de Campo por Grupo</h3>')
    sections.append('<p><em>Muestra cómo cada grupo clasificó sus medios de vida basándose en los puntajes i_total durante el taller.</em></p>')
    
    # Create side-by-side tables for each grupo
    if not field_ranking.empty and "grupo" in field_ranking.columns:
        sections.append('<div class="comparison-grid" style="display: flex; flex-wrap: wrap; gap: 20px;">')
        
        for grupo in sorted(field_ranking["grupo"].dropna().unique()):
            grupo_data = field_ranking[field_ranking["grupo"] == grupo].copy()
            grupo_data = grupo_data.sort_values("rank_in_zona").head(10)
            
            if not grupo_data.empty:
                sections.append(f'<div class="zone-card" style="flex: 1; min-width: 280px; background: #fafafa; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">')
                sections.append(f'<h4 style="color: var(--primary-color); margin-top: 0;">{grupo}</h4>')
                
                cols = ["rank_in_zona", "mdv_name", "i_total"]
                cols = [c for c in cols if c in grupo_data.columns]
                display = grupo_data[cols].copy()
                display.columns = ["Rango", "Medio de Vida (MdV)", "i_total"][:len(cols)]
                display["Rango"] = display["Rango"].astype(int)
                sections.append(df_to_html(display))
                sections.append('</div>')
        
        sections.append('</div>')  # End comparison-grid
    
    # -------------------------------------------------------------------------
    # ANALYTICAL MEAN VIEW: Cross-landscape comparison
    # -------------------------------------------------------------------------
    priority_overall = tables.get("priority_by_mdv_overall", pd.DataFrame())
    if not priority_overall.empty:
        sections.append('<h3>📈 Vista de Promedio Analítico</h3>')
        sections.append('<p><em>Puntajes promedio agregados en todos los contextos, normalizados para la comparación entre medios de vida.</em></p>')
        
        display = priority_overall.nlargest(10, "mean_i_total").copy()
        cols = ["mdv_name", "mean_i_total", "priority_norm", "n_records"]
        cols = [c for c in cols if c in display.columns]
        display = display[cols]
        display.columns = ["Medio de Vida (MdV)", "Puntaje Total Promedio", "Normalizado [0-1]", "Contextos"][:len(cols)]
        sections.append(df_to_html(display))
    
    # By grupo (mean view)
    priority_group = tables.get("priority_by_mdv_group", pd.DataFrame())
    if not priority_group.empty and "grupo" in priority_group.columns:
        sections.append('<h3>Promedio por Grupo (para cálculo del IPA)</h3>')
        sections.append('<p><em>Estos valores promedio se utilizan en el cálculo del Índice de Prioridad de Acción (IPA).</em></p>')
        
        sections.append('<div style="display: flex; flex-wrap: wrap; gap: 15px;">')
        for grupo in sorted(priority_group["grupo"].dropna().unique()):
            grupo_data = priority_group[priority_group["grupo"] == grupo].nlargest(5, "mean_i_total")
            if not grupo_data.empty:
                sections.append(f'<div style="flex: 1; min-width: 250px;">')
                sections.append(f'<h4>{grupo}</h4>')
                cols = ["mdv_name", "mean_i_total", "priority_norm"]
                cols = [c for c in cols if c in grupo_data.columns]
                display = grupo_data[cols]
                display.columns = ["Medio de Vida", "Puntaje Promedio", "Normalizado"][:len(cols)]
                sections.append(df_to_html(display))
                sections.append('</div>')
        sections.append('</div>')
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_threat_section(tables: Dict[str, pd.DataFrame]) -> str:
    """Generate threat analysis section."""
    sections = []
    
    sections.append('<section id="threat-analysis" class="section">')
    sections.append('<h2>3. Análisis de Amenazas</h2>')
    sections.append('<p>La severidad de la amenaza se deriva de TIDY_4_1_AMENAZAS, midiendo magnitud, frecuencia y tendencia.</p>')
    
    # Magnitude scale explanation
    sections.append('<div class="subsection">')
    sections.append('<strong>Escala de Magnitud:</strong><br>')
    for val, name in MAGNITUD_NAMES.items():
        sections.append(f'{val} = {name}<br>')
    sections.append('</div>')
    
    # Overall threats
    threats = tables.get("threats_overall", pd.DataFrame())
    if not threats.empty:
        sections.append('<h3>Principales Amenazas Generales</h3>')
        display = threats.nlargest(10, "mean_suma").copy()
        cols = ["amenaza", "tipo_amenaza", "mean_suma", "mean_magnitud", "mean_frequencia", "mean_tendencia", "n"]
        cols = [c for c in cols if c in display.columns]
        display = display[cols]
        display.columns = ["Amenaza", "Tipo de Amenaza", "Suma Promedio", "Magnitud Promedio", "Frecuencia Promedio", "Tendencia Promedio", "Muestras"][:len(cols)]
        sections.append(df_to_html(display))
    
    # By grupo
    threats_group = tables.get("threats_by_group", pd.DataFrame())
    if not threats_group.empty and "grupo" in threats_group.columns:
        sections.append('<h3>Principales Amenazas por Grupo</h3>')
        for grupo in sorted(threats_group["grupo"].dropna().unique()):
            grupo_data = threats_group[threats_group["grupo"] == grupo].nlargest(5, "mean_suma")
            if not grupo_data.empty:
                sections.append(f'<div class="subsection"><strong>{grupo}</strong>')
                cols = ["amenaza", "mean_suma", "mean_magnitud"]
                cols = [c for c in cols if c in grupo_data.columns]
                display = grupo_data[cols]
                display.columns = ["Amenaza", "Suma Promedio", "Magnitud Promedio"][:len(cols)]
                sections.append(df_to_html(display))
                sections.append('</div>')
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_capacity_section(tables: Dict[str, pd.DataFrame]) -> str:
    """Generate capacity analysis section."""
    sections = []
    
    sections.append('<section id="capacity-analysis" class="section">')
    sections.append('<h2>4. Análisis de Capacidad (Capacidad Adaptativa)</h2>')
    sections.append('<p>Los puntajes de capacidad se derivan de las respuestas a las encuestas (TIDY_7_1_RESPONSES). Puntajes más altos = más capacidad; Brecha de Capacidad = 1 - Capacidad.</p>')
    
    # Overall by MDV
    capacity = tables.get("capacity_overall_by_mdv", pd.DataFrame())
    if not capacity.empty:
        sections.append('<h3>Capacidad por Medio de Vida (General)</h3>')
        display = capacity.nsmallest(10, "mean_response_0_1").copy()  # Lowest capacity = biggest gap
        cols = ["mdv_name", "mean_response_0_1", "capacity_gap", "cap_gap_norm", "n_responses"]
        cols = [c for c in cols if c in display.columns]
        display = display[cols]
        display.columns = ["Medio de Vida", "Capacidad (0-1)", "Brecha de Capacidad", "Brecha Normalizada", "Respuestas"][:len(cols)]
        sections.append('<p><em>Mostrando los medios de vida con menor capacidad (mayores brechas):</em></p>')
        sections.append(df_to_html(display))
    
    # Bottleneck questions
    questions = tables.get("capacity_overall_questions", pd.DataFrame())
    if not questions.empty:
        sections.append('<h3>Cuellos de Botella de Capacidad - Preguntas con Menor Puntaje</h3>')
        display = questions.head(10).copy()
        cols = ["question_text", "mean_response_0_1", "n_responses"]
        cols = [c for c in cols if c in display.columns]
        if cols:
            display = display[cols]
            display.columns = ["Pregunta", "Puntaje Promedio (0-1)", "Respuestas"][:len(cols)]
            sections.append(df_to_html(display))
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_api_section(tables: Dict[str, pd.DataFrame]) -> str:
    """Generate API rankings section."""
    sections = []
    
    sections.append('<section id="api-rankings" class="section">')
    sections.append('<h2>5. Rankings del Índice de Prioridad de Acción (IPA)</h2>')
    sections.append('''
    <p>El IPA combina Prioridad, Riesgo y Brecha de Capacidad con pesos configurables:</p>
    <ul>
        <li><strong>Equilibrado:</strong> 40% Prioridad + 40% Riesgo + 20% Brecha de Capacidad</li>
        <li><strong>Medio de Vida Primero:</strong> 50% Prioridad + 30% Riesgo + 20% Brecha de Capacidad</li>
        <li><strong>Riesgo Primero:</strong> 30% Prioridad + 50% Riesgo + 20% Brecha de Capacidad</li>
    </ul>
    ''')
    
    # Overall rankings for each scenario
    for scenario in ["balanced", "livelihood_first", "risk_first"]:
        key = f"rankings_overall_{scenario}"
        if key in tables and not tables[key].empty:
            label = {
                "balanced": "Escenario: Equilibrado",
                "livelihood_first": "Escenario: Medio de Vida Primero",
                "risk_first": "Escenario: Riesgo Primero"
            }.get(scenario, scenario)
            sections.append(f'<h3>{label}</h3>')
            display = tables[key].head(10).copy()
            cols = ["rank", "mdv_name", "api_score", "priority_norm", "risk_norm", "cap_gap_norm"]
            cols = [c for c in cols if c in display.columns]
            display = display[cols]
            display.columns = ["Rango", "Medio de Vida", "IPA", "Prioridad", "Riesgo", "Brecha Cap."][:len(cols)]
            sections.append(df_to_html(display))
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_drivers_section(tables: Dict[str, pd.DataFrame]) -> str:
    """Generate threat drivers section."""
    sections = []
    
    sections.append('<section id="drivers" class="section">')
    sections.append('<h2>6. Motores de Amenaza por Medio de Vida</h2>')
    sections.append('<p>Para cada medio de vida prioritario, estas son las amenazas que más contribuyen a su exposición al riesgo.</p>')
    
    # Get top livelihoods
    rankings = tables.get("rankings_overall_balanced", pd.DataFrame())
    drivers = tables.get("top_threat_drivers_overall", pd.DataFrame())
    
    if not rankings.empty and not drivers.empty:
        top_mdv_ids = rankings.head(5)["mdv_id"].tolist()
        
        for mdv_id in top_mdv_ids:
            mdv_drivers = drivers[drivers["mdv_id"] == mdv_id].head(5)
            if not mdv_drivers.empty:
                mdv_name = mdv_drivers["mdv_name"].iloc[0] if "mdv_name" in mdv_drivers.columns else mdv_id
                sections.append(f'<div class="subsection"><h4>🌾 {mdv_name}</h4>')
                cols = ["driver_rank", "amenaza", "sum_weighted_impact"]
                cols = [c for c in cols if c in mdv_drivers.columns]
                display = mdv_drivers[cols]
                display.columns = ["Rango", "Amenaza", "Impacto Ponderado"][:len(cols)]
                sections.append(df_to_html(display))
                sections.append('</div>')
    else:
        sections.append('<p><em>No hay datos de motores disponibles</em></p>')
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_visualizations_section(figures: Dict[str, str]) -> str:
    """Generate visualizations section with embedded images."""
    sections = []
    
    sections.append('<section id="visualizations" class="section">')
    sections.append('<h2>7. Visualizaciones</h2>')
    
    if not figures:
        sections.append('<p><em>No se generaron figuras</em></p>')
        sections.append('</section>')
        return '\n'.join(sections)
    
    # Embed each figure
    figure_titles = {
        "quadrant_priority_risk": "Análisis de Cuadrante: Prioridad vs Riesgo",
        "bar_threats_overall": "Principales Amenazas por Severidad (General)",
        "bar_threats_by_group": "Principales Amenazas por Grupo",
    }
    
    for fig_name, fig_path in figures.items():
        if not Path(fig_path).exists():
            continue
        
        # Determine title
        if fig_name.startswith("bar_api_overall_"):
            scenario = fig_name.replace("bar_api_overall_", "")
            scenario_map = {
                "balanced": "Escenario Equilibrado",
                "livelihood_first": "Escenario Medio de Vida Primero",
                "risk_first": "Escenario Riesgo Primero"
            }
            title = f"Principales Medios de Vida por IPA ({scenario_map.get(scenario, scenario)})"
        elif fig_name.startswith("bar_api_by_group_"):
            scenario = fig_name.replace("bar_api_by_group_", "")
            scenario_map = {
                "balanced": "Escenario Equilibrado",
                "livelihood_first": "Escenario Medio de Vida Primero",
                "risk_first": "Escenario Riesgo Primero"
            }
            title = f"Principales Medios de Vida por IPA por Grupo ({scenario_map.get(scenario, scenario)})"
        else:
            title = figure_titles.get(fig_name, fig_name.replace("_", " ").title())
        
        # Encode image
        img_data = encode_image_base64(fig_path)
        if img_data:
            sections.append(f'''
            <div class="figure-container">
                <h4>{title}</h4>
                <img src="data:image/png;base64,{img_data}" alt="{title}">
                <p class="figure-caption">{title}</p>
            </div>
            ''')
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_qa_section(tables: Dict[str, pd.DataFrame]) -> str:
    """Generate QA summary section."""
    sections = []
    
    sections.append('<section id="qa-summary" class="section">')
    sections.append('<h2>8. Resumen de Aseguramiento de Calidad (QA)</h2>')
    sections.append('<p>Resumen de las verificaciones de calidad de datos de las hojas QA_*.</p>')
    
    qa_sheets = ["QA_INPUT_SCHEMA", "QA_PK_DUPLICATES", "QA_MISSING_IDS", "QA_FOREIGN_KEYS"]
    
    for qa_name in qa_sheets:
        qa_df = tables.get(qa_name, pd.DataFrame())
        sections.append(f'<div class="qa-item">')
        sections.append(f'<h4>{qa_name}</h4>')
        
        if qa_df.empty:
            sections.append('<span class="qa-status qa-ok">✓ No se encontraron problemas o no está disponible</span>')
        else:
            # Check for issues
            n_issues = len(qa_df)
            if n_issues > 0:
                sections.append(f'<span class="qa-status qa-warning">⚠ {n_issues} elementos por revisar</span>')
                sections.append(df_to_html(qa_df.head(10)))
            else:
                sections.append('<span class="qa-status qa-ok">✓ Sin problemas</span>')
        
        sections.append('</div>')
    
    sections.append('</section>')
    return '\n'.join(sections)


def generate_report(
    tables: Dict[str, pd.DataFrame],
    figures: Dict[str, str],
    input_path: str,
    warnings: List[str],
    org_name: str = "Organización",
) -> str:
    """
    Generate the complete HTML diagnostic report.
    
    Args:
        tables: Dict of all computed tables
        figures: Dict of figure name -> file path
        input_path: Path to input workbook
        warnings: List of warning messages
        org_name: Name of the organization for metadata
        
    Returns:
        HTML string
    """
    # Generate content sections
    content_parts = [
        generate_executive_summary(tables),
        generate_priority_section(tables),
        generate_threat_section(tables),
        generate_capacity_section(tables),
        generate_api_section(tables),
        generate_drivers_section(tables),
        generate_visualizations_section(figures),
        generate_qa_section(tables),
    ]
    
    # Add warnings if any
    if warnings:
        warning_section = '<section class="section"><h2>⚠️ Advertencias</h2>'
        for w in warnings:
            warning_section += f'<div class="warning">{w}</div>'
        warning_section += '</section>'
        content_parts.insert(0, warning_section)
    
    content = '\n'.join(content_parts)
    
    # Fill template
    html = HTML_TEMPLATE.format(
        org_name=org_name,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        input_file=Path(input_path).name,
        abbreviations_section=generate_abbreviations_section(),
        content=content,
    )
    
    logger.info("Generated HTML report")
    return html
