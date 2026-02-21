
import pandas as pd
from typing import List

def generate_demographics_narrative(demographics_df: pd.DataFrame) -> str:
    """Generate narrative for demographics section."""
    if demographics_df.empty:
        return ""
        
    try:
        total = demographics_df['count'].sum()
        groups = demographics_df['grupo'].nunique()
        
        text = f"El análisis incluye a **{total} participantes** de **{groups} grupos** distintos. "
        
        # Highlight largest group
        largest = demographics_df.loc[demographics_df['count'].idxmax()]
        text += f"El grupo mayoritario es **{largest['grupo']}** con el {largest['percentage']:.1f}% del total. "
        
        return text
    except Exception:
        return ""

def generate_access_narrative(barriers_df: pd.DataFrame) -> str:
    """Generate narrative for access barriers."""
    if barriers_df.empty:
        return ""
        
    try:
        # Sort by barrier rate
        sorted_df = barriers_df.sort_values("barriers_rate", ascending=False)
        top_group = sorted_df.iloc[0]
        
        text = f"El grupo **{top_group['grupo']}** reporta la mayor tasa de barreras de acceso ({top_group['barriers_rate']:.1%}). "
        
        if len(sorted_df) > 1:
            bottom_group = sorted_df.iloc[-1]
            diff = top_group['barriers_rate'] - bottom_group['barriers_rate']
            text += f"Existe una brecha de **{diff:.1%}** comparado con el grupo con menos barreras ({bottom_group['grupo']})."
            
        return text
    except Exception:
        return ""

def generate_impact_narrative(dif_df: pd.DataFrame) -> str:
    """Generate narrative for differentiated impacts."""
    if dif_df.empty:
        return ""
        
    try:
        top_impact = dif_df.iloc[0]
        text = f"El grupo **{top_impact['dif_group_std']}** muestra la mayor intensidad de impactos diferenciados "
        text += f"(Score: {top_impact['intensity']}). "
        
        return text
    except Exception:
        return ""

def generate_evi_narrative(evi_df: pd.DataFrame) -> str:
    """Generate narrative for Equity Vulnerability Index."""
    if evi_df.empty:
        return ""
        
    try:
        sorted_df = evi_df.sort_values("EVI", ascending=False)
        most_vulnerable = sorted_df.iloc[0]
        
        text = f"Según el Índice de Vulnerabilidad de Equidad (EVI), el grupo **{most_vulnerable['grupo']}** "
        text += f"es el más vulnerable con un puntaje de **{most_vulnerable['EVI']:.2f}**. "
        
        # Analyze components if available
        components = []
        if most_vulnerable.get('dif_norm', 0) > 0.7: components.append("impactos diferenciados altos")
        if most_vulnerable.get('bar_norm', 0) > 0.7: components.append("barreras de acceso severas")
        if most_vulnerable.get('cap_norm', 0) > 0.7: components.append("baja capacidad adaptativa")
        
        if components:
            text += f"Esto se debe principalmente a: {', '.join(components)}."
            
        return text
    except Exception:
        return ""
