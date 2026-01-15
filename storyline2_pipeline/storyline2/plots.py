#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 Plots Module
Generates visualizations using matplotlib.
"""

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import GRUPO_COL, SE_CODE_NAMES

logger = logging.getLogger(__name__)

# Color palette
COLORS = {
    "primary": "#009EE2",
    "secondary": "#001F89",
    "accent": "#00C49A",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "neutral": "#94A3B8",
}

# Gradient colors for bars
BAR_COLORS = [
    "#009EE2", "#00B4D8", "#00C49A", "#48CAE4", "#90E0EF",
    "#ADE8F4", "#CAF0F8", "#E0F7FA", "#F0F9FF", "#F8FAFC",
]


def setup_style():
    """Configure matplotlib style."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#E2E8F0",
        "axes.labelcolor": "#334155",
        "text.color": "#334155",
        "xtick.color": "#64748B",
        "ytick.color": "#64748B",
        "grid.color": "#E2E8F0",
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
    })


def get_color_gradient(n: int) -> List[str]:
    """Get n colors from the gradient palette."""
    if n <= len(BAR_COLORS):
        return BAR_COLORS[:n]
    # Repeat colors if needed
    return (BAR_COLORS * ((n // len(BAR_COLORS)) + 1))[:n]


def save_figure(fig: plt.Figure, path: str, dpi: int = 150) -> str:
    """Save figure to file and return path."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    logger.debug(f"Saved figure: {path}")
    return path


def fig_to_base64(fig: plt.Figure, dpi: int = 150) -> str:
    """Convert figure to base64 string for HTML embedding."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return f"data:image/png;base64,{b64}"


# =============================================================================
# BAR CHARTS
# =============================================================================

def plot_top_services_sci(
    df: pd.DataFrame,
    scenario: str,
    outdir: str,
    top_n: int = 10,
    grupo: Optional[str] = None,
) -> Optional[str]:
    """
    Create horizontal bar chart of top services by SCI.
    
    Args:
        df: DataFrame with se_key and sci columns
        scenario: Scenario name for title
        outdir: Output directory
        top_n: Number of top services to show
        grupo: Optional grupo name for by-group charts
        
    Returns:
        Path to saved figure, or None if no data
    """
    setup_style()
    
    if df.empty or "sci" not in df.columns:
        return None
    
    # Filter to grupo if specified
    data = df.copy()
    if grupo and GRUPO_COL in data.columns:
        data = data[data[GRUPO_COL] == grupo]
    
    # Sort and take top N
    data = data.nlargest(top_n, "sci")
    
    if data.empty:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))
    
    y_pos = range(len(data))
    colors = get_color_gradient(len(data))
    
    bars = ax.barh(y_pos, data["sci"], color=colors, edgecolor="white", linewidth=0.5)
    
    # Labels
    ax.set_yticks(y_pos)
    labels = data["se_key"].astype(str).tolist()
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    
    ax.set_xlabel("Service Criticality Index (SCI)")
    
    title = f"Top {len(data)} Critical Services - {scenario.replace('_', ' ').title()}"
    if grupo:
        title += f" ({grupo})"
    ax.set_title(title, fontweight="bold", pad=10)
    
    # Add labels inside bars (User Request: Black font, combined Name+Value)
    for i, (bar, key, val) in enumerate(zip(bars, data["se_key"], data["sci"])):
        # Name + Value inside bar (left-aligned)
        name = SE_CODE_NAMES.get(str(key).strip(), str(key))
        label = f"{name} ({val:.2f})"
        
        # Always use black text (visible on light bars and on white background if it overflows)
        # Position at start of bar
        ax.text(0.02, bar.get_y() + bar.get_height()/2,
                label, va="center", ha="left", fontsize=9, color="black", fontweight="bold")
    
    ax.set_xlim(0, max(data["sci"]) * 1.15)
    
    # Save
    suffix = f"_{grupo}" if grupo else ""
    filename = f"bar_top_services_SCI_{scenario}{suffix}.png"
    path = str(Path(outdir) / "figures" / filename)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    return save_figure(fig, path)


def plot_top_ecosystems_eli(
    df: pd.DataFrame,
    outdir: str,
    top_n: int = 10,
    grupo: Optional[str] = None,
) -> Optional[str]:
    """
    Create horizontal bar chart of top ecosystems by ELI.
    """
    setup_style()
    
    if df.empty:
        return None
    
    # Find ELI column
    eli_col = "eli" if "eli" in df.columns else "eli_norm"
    if eli_col not in df.columns:
        return None
    
    # Find ecosystem label column
    eco_col = None
    for col in ["ecosistema", "ecosistema_label", "ecosistema_id"]:
        if col in df.columns:
            eco_col = col
            break
    if not eco_col:
        return None
    
    # Filter to grupo if specified
    data = df.copy()
    if grupo and GRUPO_COL in data.columns:
        data = data[data[GRUPO_COL] == grupo]
    
    # Sort and take top N
    data = data.nlargest(top_n, eli_col)
    
    if data.empty:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))
    
    y_pos = range(len(data))
    colors = get_color_gradient(len(data))
    
    bars = ax.barh(y_pos, data[eli_col], color=colors, edgecolor="white", linewidth=0.5)
    
    # Labels
    ax.set_yticks(y_pos)
    labels = data[eco_col].astype(str).tolist()
    # Truncate long labels
    labels = [l[:40] + "..." if len(l) > 40 else l for l in labels]
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    
    ax.set_xlabel("Ecosystem Leverage Index (ELI)")
    
    title = f"Top {len(data)} Ecosystems by Leverage"
    if grupo:
        title += f" ({grupo})"
    ax.set_title(title, fontweight="bold", pad=10)
    
    # Add value labels
    for bar, val in zip(bars, data[eli_col]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f"{val:.2f}", va="center", fontsize=9, color="#64748B")
    
    ax.set_xlim(0, max(data[eli_col]) * 1.15)
    
    # Save
    suffix = f"_{grupo}" if grupo else "_overall"
    filename = f"bar_top_ecosystems_ELI{suffix}.png"
    path = str(Path(outdir) / "figures" / filename)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    return save_figure(fig, path)


def plot_threat_pressure(
    df: pd.DataFrame,
    outdir: str,
    top_n: int = 10,
) -> Optional[str]:
    """
    Create horizontal bar chart of top threats by pressure.
    """
    setup_style()
    
    if df.empty or "sum_pressure" not in df.columns:
        return None
    
    # Find threat label column
    threat_col = "amenaza" if "amenaza" in df.columns else "amenaza_id"
    if threat_col not in df.columns:
        return None
    
    # Aggregate by threat (sum across services)
    agg_cols = [threat_col]
    if "tipo_amenaza" in df.columns:
        agg_cols.append("tipo_amenaza")
    
    aggregated = df.groupby(agg_cols, dropna=False)["sum_pressure"].sum().reset_index()
    data = aggregated.nlargest(top_n, "sum_pressure")
    
    if data.empty:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))
    
    y_pos = range(len(data))
    colors = [COLORS["danger"] if i < 3 else COLORS["warning"] if i < 6 else COLORS["neutral"] 
              for i in range(len(data))]
    
    bars = ax.barh(y_pos, data["sum_pressure"], color=colors, edgecolor="white", linewidth=0.5)
    
    # Labels
    ax.set_yticks(y_pos)
    labels = data[threat_col].astype(str).tolist()
    labels = [l[:45] + "..." if len(l) > 45 else l for l in labels]
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    
    ax.set_xlabel("Total Pressure on Services")
    ax.set_title(f"Top {len(data)} Threats Pressuring Services", fontweight="bold", pad=10)
    
    # Add value labels
    for bar, val in zip(bars, data["sum_pressure"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}", va="center", fontsize=9, color="#64748B")
    
    ax.set_xlim(0, max(data["sum_pressure"]) * 1.15)
    
    # Save
    filename = "bar_top_threat_pressure_overall.png"
    path = str(Path(outdir) / "figures" / filename)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    return save_figure(fig, path)


def plot_livelihood_exposure(
    df: pd.DataFrame,
    outdir: str,
    top_n: int = 10,
) -> Optional[str]:
    """
    Create horizontal bar chart of top livelihoods by exposure (IVL).
    """
    setup_style()
    
    if df.empty or "sum_pressure_via_services" not in df.columns:
        return None
    
    # Find MDV label column
    mdv_col = "mdv_name" if "mdv_name" in df.columns else "mdv_id"
    if mdv_col not in df.columns:
        return None
    
    # Aggregate by MDV
    aggregated = df.groupby(mdv_col, dropna=False)["sum_pressure_via_services"].sum().reset_index()
    data = aggregated.nlargest(top_n, "sum_pressure_via_services")
    
    if data.empty:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, max(4, len(data) * 0.4)))
    
    y_pos = range(len(data))
    colors = get_color_gradient(len(data))
    
    bars = ax.barh(y_pos, data["sum_pressure_via_services"], color=colors, edgecolor="white", linewidth=0.5)
    
    # Labels
    ax.set_yticks(y_pos)
    labels = data[mdv_col].astype(str).tolist()
    labels = [l[:40] + "..." if len(l) > 40 else l for l in labels]
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    
    ax.set_xlabel("Indirect Vulnerability (via Services)")
    ax.set_title(f"Top {len(data)} Exposed Livelihoods", fontweight="bold", pad=10)
    
    # Add value labels
    for bar, val in zip(bars, data["sum_pressure_via_services"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}", va="center", fontsize=9, color="#64748B")
    
    ax.set_xlim(0, max(data["sum_pressure_via_services"]) * 1.15)
    
    # Save
    filename = "bar_top_livelihood_exposure_overall.png"
    path = str(Path(outdir) / "figures" / filename)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    return save_figure(fig, path)


# =============================================================================
# HEATMAPS
# =============================================================================

def plot_ecosystem_service_heatmap(
    eco_se: pd.DataFrame,
    outdir: str,
    max_items: int = 15,
) -> Optional[str]:
    """
    Create heatmap of ecosystem vs service connections.
    """
    setup_style()
    
    if eco_se.empty:
        return None
    
    # Find key columns
    eco_col = None
    for col in ["ecosistema", "ecosistema_id"]:
        if col in eco_se.columns:
            eco_col = col
            break
    
    se_col = None
    for col in ["cod_se", "se_id", "se_key"]:
        if col in eco_se.columns:
            se_col = col
            break
    
    if not eco_col or not se_col:
        return None
    
    # Create cross-tabulation
    crosstab = pd.crosstab(eco_se[eco_col], eco_se[se_col])
    
    # Limit to top items
    if len(crosstab.index) > max_items:
        row_totals = crosstab.sum(axis=1).nlargest(max_items).index
        crosstab = crosstab.loc[row_totals]
    if len(crosstab.columns) > max_items:
        col_totals = crosstab.sum(axis=0).nlargest(max_items).index
        crosstab = crosstab[col_totals]
    
    if crosstab.empty:
        return None
    
    # Create figure
    fig_height = max(6, len(crosstab.index) * 0.5)
    fig_width = max(8, len(crosstab.columns) * 0.6)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Create heatmap
    im = ax.imshow(crosstab.values, cmap="Blues", aspect="auto")
    
    # Labels
    ax.set_xticks(range(len(crosstab.columns)))
    ax.set_yticks(range(len(crosstab.index)))
    
    xlabels = [str(l)[:15] for l in crosstab.columns]
    ylabels = [str(l)[:25] for l in crosstab.index]
    
    ax.set_xticklabels(xlabels, rotation=45, ha="right")
    ax.set_yticklabels(ylabels)
    
    ax.set_xlabel("Ecosystem Services")
    ax.set_ylabel("Ecosystems")
    ax.set_title("Ecosystem-Service Connectivity Matrix", fontweight="bold", pad=10)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Connection Count")
    
    # Add value annotations for non-zero cells
    for i in range(len(crosstab.index)):
        for j in range(len(crosstab.columns)):
            val = crosstab.values[i, j]
            if val > 0:
                color = "white" if val > crosstab.values.max() * 0.5 else "black"
                ax.text(j, i, str(int(val)), ha="center", va="center", 
                       fontsize=8, color=color)
    
    plt.tight_layout()
    
    # Save
    filename = "heatmap_ecosystem_vs_service_overall.png"
    path = str(Path(outdir) / "figures" / filename)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    return save_figure(fig, path)


def plot_service_livelihood_heatmap(
    se_mdv: pd.DataFrame,
    outdir: str,
    max_items: int = 15,
) -> Optional[str]:
    """
    Create heatmap of service vs livelihood connections.
    """
    setup_style()
    
    if se_mdv.empty:
        return None
    
    # Find key columns
    se_col = None
    for col in ["cod_se", "se_id", "se_key"]:
        if col in se_mdv.columns:
            se_col = col
            break
    
    mdv_col = "mdv_name" if "mdv_name" in se_mdv.columns else "mdv_id"
    
    if not se_col or mdv_col not in se_mdv.columns:
        return None
    
    # Create cross-tabulation
    crosstab = pd.crosstab(se_mdv[se_col], se_mdv[mdv_col])
    
    # Limit to top items
    if len(crosstab.index) > max_items:
        row_totals = crosstab.sum(axis=1).nlargest(max_items).index
        crosstab = crosstab.loc[row_totals]
    if len(crosstab.columns) > max_items:
        col_totals = crosstab.sum(axis=0).nlargest(max_items).index
        crosstab = crosstab[col_totals]
    
    if crosstab.empty:
        return None
    
    # Create figure
    fig_height = max(6, len(crosstab.index) * 0.5)
    fig_width = max(8, len(crosstab.columns) * 0.6)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Create heatmap
    im = ax.imshow(crosstab.values, cmap="Greens", aspect="auto")
    
    # Labels
    ax.set_xticks(range(len(crosstab.columns)))
    ax.set_yticks(range(len(crosstab.index)))
    
    xlabels = [str(l)[:20] for l in crosstab.columns]
    ylabels = [str(l)[:15] for l in crosstab.index]
    
    ax.set_xticklabels(xlabels, rotation=45, ha="right")
    ax.set_yticklabels(ylabels)
    
    ax.set_xlabel("Livelihoods (MdV)")
    ax.set_ylabel("Ecosystem Services")
    ax.set_title("Service-Livelihood Dependency Matrix", fontweight="bold", pad=10)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Connection Count")
    
    # Add value annotations for non-zero cells
    for i in range(len(crosstab.index)):
        for j in range(len(crosstab.columns)):
            val = crosstab.values[i, j]
            if val > 0:
                color = "white" if val > crosstab.values.max() * 0.5 else "black"
                ax.text(j, i, str(int(val)), ha="center", va="center", 
                       fontsize=8, color=color)
    
    plt.tight_layout()
    
    # Save
    filename = "heatmap_service_vs_livelihood_overall.png"
    path = str(Path(outdir) / "figures" / filename)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    return save_figure(fig, path)


# =============================================================================
# MAIN PLOTS GENERATOR
# =============================================================================

def generate_all_plots(
    metrics_tables: Dict[str, pd.DataFrame],
    outdir: str,
    tables: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict[str, str]:
    """
    Generate all Storyline 2 visualizations.
    
    Args:
        metrics_tables: Dict of computed metrics tables
        outdir: Output directory
        tables: Optional dict of input tables for heatmaps
        
    Returns:
        Dict mapping figure name to file path
    """
    figures: Dict[str, str] = {}
    
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # SCI bar charts
    for key, df in metrics_tables.items():
        if key.startswith("service_ranking_overall_"):
            scenario = key.replace("service_ranking_overall_", "")
            path = plot_top_services_sci(df, scenario, outdir)
            if path:
                figures[f"sci_overall_{scenario}"] = path
    
    # ELI bar charts
    eli_overall = metrics_tables.get("ecosystem_eli_overall", pd.DataFrame())
    if not eli_overall.empty:
        path = plot_top_ecosystems_eli(eli_overall, outdir)
        if path:
            figures["eli_overall"] = path
    
    eli_by_grupo = metrics_tables.get("ecosystem_eli_by_grupo", pd.DataFrame())
    if not eli_by_grupo.empty and GRUPO_COL in eli_by_grupo.columns:
        for grupo in eli_by_grupo[GRUPO_COL].dropna().unique():
            path = plot_top_ecosystems_eli(eli_by_grupo, outdir, grupo=grupo)
            if path:
                figures[f"eli_{grupo}"] = path
    
    # Threat pressure chart
    tps_overall = metrics_tables.get("tps_overall", pd.DataFrame())
    if not tps_overall.empty:
        path = plot_threat_pressure(tps_overall, outdir)
        if path:
            figures["threat_pressure"] = path
    
    # Livelihood exposure chart
    ivl_overall = metrics_tables.get("ivl_overall", pd.DataFrame())
    if not ivl_overall.empty:
        path = plot_livelihood_exposure(ivl_overall, outdir)
        if path:
            figures["livelihood_exposure"] = path
    
    # Heatmaps (need original tables)
    if tables:
        eco_se = tables.get("TIDY_3_4_ECO_SE", pd.DataFrame())
        if not eco_se.empty:
            path = plot_ecosystem_service_heatmap(eco_se, outdir)
            if path:
                figures["heatmap_eco_service"] = path
        
        se_mdv = tables.get("TIDY_3_5_SE_MDV", pd.DataFrame())
        if not se_mdv.empty:
            path = plot_service_livelihood_heatmap(se_mdv, outdir)
            if path:
                figures["heatmap_service_mdv"] = path
    
    logger.info(f"Generated {len(figures)} figures")
    return figures
