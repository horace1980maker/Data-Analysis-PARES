# -*- coding: utf-8 -*-
"""
Storyline 2 Narrative Module
Generates descriptive text based on analysis metrics.
"""

import pandas as pd
from typing import Dict, List, Optional
from .config import GRUPO_COL

def generate_ecosystem_narrative(
    eco_overall: pd.DataFrame,
    eli_overall: pd.DataFrame,
    top_n: int = 3
) -> str:
    """
    Generate narrative for ecosystem analysis.
    Highlights:
    - Most connected ecosystem vs highest leverage (ELI).
    - Key stats for top ecosystems.
    """
    if eco_overall.empty:
        return "<p>No hay suficientes datos de ecosistemas para generar un análisis narrativo.</p>"
    
    narrative = []
    
    # 1. Connectivity Leader
    if "connectivity_norm" in eco_overall.columns:
        top_conn = eco_overall.sort_values("connectivity_norm", ascending=False).iloc[0]
        conn_name = top_conn.get("ecosistema", "Desconocido")
        n_serv = top_conn.get("n_services", 0)
        n_live = top_conn.get("n_livelihoods", 0)
        
        narrative.append(
            f"<p>El ecosistema con mayor conectividad es <strong>{conn_name}</strong>, "
            f"el cual provee {n_serv} servicios distintos y beneficia directamente a {n_live} medios de vida.</p>"
        )
    
    # 2. Leverage Leader (ELI)
    if not eli_overall.empty and "eli" in eli_overall.columns:
        top_eli = eli_overall.sort_values("eli", ascending=False).iloc[0]
        eli_name = top_eli.get("ecosistema", "Desconocido")
        eli_score = top_eli.get("eli", 0)
        
        if "connectivity_norm" in eco_overall.columns and eli_name != conn_name:
            narrative.append(
                f"<p>Sin embargo, en términos de valor estratégico (Apalancamiento), destaca <strong>{eli_name}</strong> "
                f"(ELI={eli_score:.2f}). Este ecosistema, aunque quizás no sea el más conectado en volumen, "
                f"sostiene servicios críticos para la comunidad, convirtiéndolo en una prioridad de conservación.</p>"
            )
        elif eli_name == conn_name:
            narrative.append(
                f"<p>Además, <strong>{eli_name}</strong> también lidera el Índice de Apalancamiento (ELI={eli_score:.2f}), "
                f"confirmando su rol central como pilar de la resiliencia local tanto por volumen de conexiones como por importancia estratégica.</p>"
            )
    
    return "\n".join(narrative)


def generate_service_narrative(
    sci_overall: pd.DataFrame,
    top_n: int = 3
) -> str:
    """
    Generate narrative for service criticality.
    Highlights:
    - Top critical service and its primary driver.
    """
    if sci_overall.empty:
        return "<p>No hay datos de servicios para analizar.</p>"
    
    # Needs columns: se_key, sci, links_mdv_norm, users_norm, priority_norm, seasonality_norm
    if "sci" not in sci_overall.columns:
        # Assuming sci_overall might be the raw component table without 'sci'. 
        # But report passes 'service_ranking_overall_balanced'.
        # Let's hope we get the ranking table.
        return ""

    top_services = sci_overall.sort_values("sci", ascending=False).head(top_n)
    
    if top_services.empty:
        return ""
        
    narrative = []
    
    # Top 1 Analysis
    top1 = top_services.iloc[0]
    s_name = top1.get("se_key", "Servicio")
    s_score = top1.get("sci", 0)
    
    # Determine main driver
    drivers = {
        "Vínculos con MdV": top1.get("links_mdv_norm", 0),
        "Número de Usuarios": top1.get("users_norm", 0),
        "Prioridad Local": top1.get("priority_norm", 0),
        "Estacionalidad": top1.get("seasonality_norm", 0)
    }
    main_driver = max(drivers, key=drivers.get)
    
    narrative.append(
        f"<p>El servicio más crítico identificado es <strong>{s_name}</strong> (SCI={s_score:.2f}). "
        f"Su alta importancia está impulsada principalmente por <strong>{main_driver}</strong>, "
        f"lo que indica que su pérdida tendría un impacto desproporcionado en la comunidad.</p>"
    )
    
    # List others
    if len(top_services) > 1:
        others = [f"<strong>{row.get('se_key', 'Unknown')}</strong>" for _, row in top_services.iloc[1:].iterrows()]
        narrative.append(
            f"<p>Le siguen en importancia {', '.join(others)}, formando el grupo de servicios esenciales que requieren monitoreo prioritario.</p>"
        )
        
    return "\n".join(narrative)


def generate_threat_narrative(
    tps_overall: pd.DataFrame,
    top_n: int = 3
) -> str:
    """
    Generate narrative for threats.
    Highlights:
    - Top pressure threat.
    - Breadth of impact (how many services affected).
    """
    if tps_overall.empty:
        return ""
    
    # Aggregate by threat to find the big one
    if "amenaza" in tps_overall.columns:
        threat_agg = tps_overall.groupby("amenaza").agg({
            "sum_pressure": "sum",
            "se_key": "nunique"
        }).reset_index().sort_values("sum_pressure", ascending=False)
        
        if threat_agg.empty:
            return ""
            
        top_threat = threat_agg.iloc[0]
        t_name = top_threat["amenaza"]
        t_services = top_threat["se_key"]
        
        narrative = f"<p>La amenaza predominante es <strong>{t_name}</strong>, la cual ejerce presión sobre " \
                    f"<strong>{t_services}</strong> servicios ecosistémicos distintos. " \
                    f"Esto sugiere una vulnerabilidad sistémica donde un solo evento de {t_name.lower()} podría " \
                    f"comprometer múltiples funciones ecológicas simultáneamente.</p>"
        
        return narrative
        
    return ""


def generate_vulnerability_narrative(
    ivl_overall: pd.DataFrame
) -> str:
    """
    Generate narrative for livelihood vulnerability.
    """
    if ivl_overall.empty:
        return ""
    
    # Identify most exposed livelihood
    if "sum_pressure_via_services" in ivl_overall.columns:
        # Aggregate by MDV (if not already unique by MDV)
        # ivl_overall is typically grouped by mdv + threat
        mdv_agg = ivl_overall.groupby("mdv_name")["sum_pressure_via_services"].sum().reset_index().sort_values("sum_pressure_via_services", ascending=False)
        
        if mdv_agg.empty:
            return ""
            
        top_mdv = mdv_agg.iloc[0]
        m_name = top_mdv["mdv_name"]
        
        narrative = f"<p>Los medios de vida más expuestos indirectamente (a través de la degradación de servicios) " \
                    f"están encabezados por <strong>{m_name}</strong>. Este medio de vida depende fuertemente de " \
                    f"servicios que están actualmente bajo alta presión de amenazas, lo que representa un riesgo oculto " \
                    f"no siempre visible en el análisis directo de impactos.</p>"
        
        return narrative

    return ""
