"""
Plotting module for Storyline 4.
Generates visualizations using matplotlib only.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (
    ACTOR_NAME_CANDIDATES,
    DIALOGO_NAME_CANDIDATES,
    GRUPO_COL,
)

logger = logging.getLogger(__name__)

# Configure matplotlib
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.autolayout": True,
})

# Color palette for Storyline 4 (teal/amber theme)
COLORS = {
    "primary": "#00695c",      # Teal 800
    "secondary": "#26a69a",    # Teal 400
    "accent": "#ffb300",       # Amber 600
    "warning": "#ff9800",      # Orange
    "danger": "#e53935",       # Red
    "colabora": "#4caf50",     # Green for collaboration
    "conflicto": "#f44336",    # Red for conflict
    "other": "#9e9e9e",        # Grey
    "neutral": "#607d8b",      # Blue Grey
}


def save_figure(fig: plt.Figure, outdir: str, name: str) -> str:
    """Save figure to output directory and return path."""
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    logger.debug(f"Saved figure: {path}")
    return str(path)


def bar_top_actors_by_degree(
    centrality: pd.DataFrame,
    degree_col: str,
    title: str,
    color: str,
    outdir: str,
    filename: str,
    top_n: int = 10,
) -> Optional[str]:
    """Create bar chart of top actors by degree."""
    if centrality.empty or degree_col not in centrality.columns:
        return None
    
    actor_col = None
    # Prefer name
    for candidate in ACTOR_NAME_CANDIDATES:
        if candidate in centrality.columns:
            actor_col = candidate
            break
            
    if not actor_col:
        if "actor_id" in centrality.columns:
            actor_col = "actor_id"
        else:
            # Try to find another identifier
            for col in centrality.columns:
                if "actor" in col.lower() and col != degree_col:
                    actor_col = col
                    break
    
    if actor_col not in centrality.columns:
        return None
    
    df = centrality.nlargest(top_n, degree_col)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(df))
    bars = ax.barh(y_pos, df[degree_col], color=color, edgecolor="white", linewidth=0.5)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df[actor_col].astype(str).str[:40])
    ax.set_xlabel("Degree (Number of Relations)")
    ax.set_title(title)
    ax.invert_yaxis()
    
    # Add value labels
    for bar, val in zip(bars, df[degree_col]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}", va="center", fontsize=8)
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    return save_figure(fig, outdir, filename)


def heatmap_dyads(
    dyads: pd.DataFrame,
    rel_type: str,
    title: str,
    outdir: str,
    filename: str,
    max_items: int = 20,
) -> Optional[str]:
    """Create heatmap of actor dyads (adjacency matrix approximation)."""
    if dyads.empty:
        return None
    
    # Filter by relation type
    rel_col = "rel_type_norm" if "rel_type_norm" in dyads.columns else None
    if rel_col:
        df = dyads[dyads[rel_col] == rel_type].copy()
    else:
        df = dyads.copy()
    
    if df.empty:
        return None
    
    # Find actor columns
    source_col = None
    target_col = None
    for col in df.columns:
        if "actor" in col.lower() and "other" not in col.lower() and source_col is None:
            source_col = col
        elif "other" in col.lower() or (source_col and "actor" in col.lower()):
            target_col = col
    
    if not source_col or not target_col:
        return None
    
    # Get top actors by frequency
    all_actors = pd.concat([df[source_col], df[target_col]]).value_counts()
    top_actors = all_actors.head(max_items).index.tolist()
    
    # Filter to top actors
    df = df[df[source_col].isin(top_actors) & df[target_col].isin(top_actors)]
    
    if df.empty:
        return None
    
    # Create matrix
    count_col = "count" if "count" in df.columns else df.columns[-1]
    matrix = df.pivot_table(
        index=source_col,
        columns=target_col,
        values=count_col,
        aggfunc="sum",
        fill_value=0
    )
    
    fig, ax = plt.subplots(figsize=(12, 10))
    cmap = "Greens" if rel_type == "colabora" else "Reds"
    
    im = ax.imshow(matrix.values, cmap=cmap, aspect="auto")
    
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_yticks(range(len(matrix.index)))
    ax.set_xticklabels(matrix.columns.astype(str).str[:15], rotation=45, ha="right")
    ax.set_yticklabels(matrix.index.astype(str).str[:15])
    
    ax.set_xlabel("Target Actor")
    ax.set_ylabel("Source Actor")
    ax.set_title(title)
    
    plt.colorbar(im, ax=ax, label="Relation Count")
    
    return save_figure(fig, outdir, filename)


def bar_dialogue_participation(
    participation: pd.DataFrame,
    outdir: str,
    filename: str,
    top_n: int = 10,
) -> Optional[str]:
    """Bar chart of top dialogue spaces by number of participants."""
    if participation.empty:
        return None
    
    # Find relevant columns
    # Find relevant columns
    space_col = None
    count_col = None
    
    # Try strict candidates for name
    for candidate in DIALOGO_NAME_CANDIDATES:
        if candidate in participation.columns:
            space_col = candidate
            break
            
    if not space_col:
        for col in participation.columns:
            if "dialog" in col.lower() or "espacio" in col.lower():
                space_col = col
                
    for col in participation.columns:
        if ("actor" in col.lower() or "n_" in col.lower()) and col != space_col:
            count_col = col
    
    if not space_col:
        space_col = participation.columns[0]
    if not count_col:
        count_col = participation.columns[-1]
    
    df = participation.nlargest(top_n, count_col)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(df))
    bars = ax.barh(y_pos, df[count_col], color=COLORS["primary"], edgecolor="white")
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df[space_col].astype(str).str[:50])
    ax.set_xlabel("Number of Participating Actors")
    ax.set_title("Top Dialogue Spaces by Participation / Espacios de Diálogo con Mayor Participación")
    ax.invert_yaxis()
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    return save_figure(fig, outdir, filename)


def bar_actor_in_spaces(
    actor_spaces: pd.DataFrame,
    outdir: str,
    filename: str,
    top_n: int = 10,
) -> Optional[str]:
    """Bar chart of actors present in most dialogue spaces."""
    if actor_spaces.empty:
        return None
    
    # Find columns
    # Find columns
    actor_col = None
    count_col = None
    
    # Prefer name
    for candidate in ACTOR_NAME_CANDIDATES:
        if candidate in actor_spaces.columns:
            actor_col = candidate
            break
            
    if not actor_col:
        for col in actor_spaces.columns:
            if "actor" in col.lower():
                actor_col = col
                break
                
    for col in actor_spaces.columns:
        if ("space" in col.lower() or "n_" in col.lower()) and col != actor_col:
            count_col = col
    
    if not actor_col:
        actor_col = actor_spaces.columns[0]
    if not count_col:
        count_col = actor_spaces.columns[-1]
    
    df = actor_spaces.nlargest(top_n, count_col)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(df))
    bars = ax.barh(y_pos, df[count_col], color=COLORS["secondary"], edgecolor="white")
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df[actor_col].astype(str).str[:40])
    ax.set_xlabel("Number of Dialogue Spaces")
    ax.set_title("Actors Present in Most Dialogue Spaces / Actores con Mayor Presencia en Espacios")
    ax.invert_yaxis()
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    return save_figure(fig, outdir, filename)


def line_conflict_timeline(
    timeline: pd.DataFrame,
    outdir: str,
    filename: str,
    grupo: Optional[str] = None,
) -> Optional[str]:
    """Line chart of conflict events over time."""
    if timeline.empty:
        return None
    
    year_col = "year"
    events_col = "n_events"
    
    if year_col not in timeline.columns or events_col not in timeline.columns:
        # Try to find similar columns
        for col in timeline.columns:
            if "year" in col.lower() or "ano" in col.lower() or "año" in col.lower():
                year_col = col
            elif "event" in col.lower() or "n_" in col.lower():
                events_col = col
    
    if year_col not in timeline.columns or events_col not in timeline.columns:
        return None
    
    df = timeline.sort_values(year_col)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df[year_col], df[events_col], marker="o", color=COLORS["danger"],
            linewidth=2, markersize=6)
    ax.fill_between(df[year_col], df[events_col], alpha=0.3, color=COLORS["danger"])
    
    ax.set_xlabel("Year / Año")
    ax.set_ylabel("Number of Conflict Events / Eventos de Conflicto")
    
    title = "Conflict Events Over Time / Eventos de Conflicto en el Tiempo"
    if grupo:
        title = f"{title} - {grupo}"
    ax.set_title(title)
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    
    return save_figure(fig, outdir, filename)


def bar_top_conflicts(
    conflicts: pd.DataFrame,
    outdir: str,
    filename: str,
    top_n: int = 10,
) -> Optional[str]:
    """Bar chart of top conflicts by number of events."""
    if conflicts.empty:
        return None
    
    # Find columns
    conflict_col = None
    events_col = None
    for col in conflicts.columns:
        if "conflict" in col.lower() or "cod_" in col.lower():
            conflict_col = col
        elif "event" in col.lower() or "n_" in col.lower():
            events_col = col
    
    if not conflict_col:
        conflict_col = conflicts.columns[0]
    if not events_col:
        events_col = "n_events" if "n_events" in conflicts.columns else conflicts.columns[-1]
    
    df = conflicts.nlargest(top_n, events_col)
    
    # Find description column
    desc_col = None
    for c in ["conflict_description", "descripcion", "description", "details"]:
        if c in df.columns:
            desc_col = c
            break
            
    if not desc_col:
        desc_col = conflict_col # Fallback to ID
        
    y_pos = range(len(df))
    bars = ax.barh(y_pos, df[events_col], color=COLORS["warning"], edgecolor="white")
    
    ax.set_yticks(y_pos)
    # Use description for y-ticks if available and not too long, else ID
    if desc_col != conflict_col:
        ax.set_yticklabels(df[desc_col].astype(str).str[:40])
    else:
        ax.set_yticklabels(df[conflict_col].astype(str).str[:40])
        
    ax.set_xlabel("Number of Events / Número de Eventos")
    ax.set_title("Top Conflicts by Events / Principales Conflictos por Eventos")
    ax.invert_yaxis()
    
    # Add labels inside bars (User Request: Black font, combined Name+Value)
    for bar, val, desc, code in zip(bars, df[events_col], df[desc_col], df[conflict_col]):
        if desc_col != conflict_col:
             # Use "Code - Desc" format if we have both
            label = f"{code} - {desc}" if len(str(desc)) < 30 else f"{desc}"
        else:
            label = str(code)
            
        label = f"{label} ({val:.0f})"
        
        ax.text(0.02, bar.get_y() + bar.get_height()/2,
                label, va="center", ha="left", color="black", fontsize=9, fontweight="bold")
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    return save_figure(fig, outdir, filename)


def bar_threats_linked_conflicts(
    threats: pd.DataFrame,
    outdir: str,
    filename: str,
    top_n: int = 10,
) -> Optional[str]:
    """Bar chart of top threats linked to conflicts."""
    if threats.empty:
        return None
    
    # Find columns
    threat_col = None
    count_col = None
    for col in threats.columns:
        if "amenaza" in col.lower() or "threat" in col.lower():
            threat_col = col
        elif "link" in col.lower() or "n_" in col.lower() or "count" in col.lower():
            count_col = col
    
    if not threat_col:
        threat_col = threats.columns[0]
    if not count_col:
        count_col = threats.columns[-1]
    
    df = threats.head(top_n)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(df))
    bars = ax.barh(y_pos, df[count_col], color=COLORS["accent"], edgecolor="white")
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df[threat_col].astype(str).str[:40])
    ax.set_xlabel("Number of Conflict Links / Vínculos con Conflictos")
    ax.set_title("Threats Most Linked to Conflicts / Amenazas más Vinculadas a Conflictos")
    ax.invert_yaxis()
    
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    return save_figure(fig, outdir, filename)


def bar_feasibility_by_grupo(
    feasibility: pd.DataFrame,
    outdir: str,
    filename: str,
) -> Optional[str]:
    """Bar chart of feasibility scores by grupo."""
    if feasibility.empty:
        return None
    
    grupo_col = GRUPO_COL if GRUPO_COL in feasibility.columns else "grupo"
    score_col = "feasibility_score"
    
    if grupo_col not in feasibility.columns or score_col not in feasibility.columns:
        return None
    
    df = feasibility.sort_values(score_col, ascending=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(df))
    
    # Color by score: higher = more green, lower = more red
    colors = [plt.cm.RdYlGn(val) for val in df[score_col]]
    
    bars = ax.barh(y_pos, df[score_col], color=colors, edgecolor="white")
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df[grupo_col].astype(str))
    ax.set_xlabel("Feasibility Score / Índice de Viabilidad")
    ax.set_title("Implementation Feasibility by Zone / Viabilidad de Implementación por Zona")
    
    # Add vertical line at 0.5
    ax.axvline(x=0.5, color=COLORS["neutral"], linestyle="--", alpha=0.5)
    
    ax.set_xlim(0, 1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    # Add value labels
    for bar, val in zip(bars, df[score_col]):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f"{val:.2f}", va="center", fontsize=9)
    
    return save_figure(fig, outdir, filename)


def generate_plots(
    metrics: Dict[str, pd.DataFrame],
    outdir: str,
    params: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate all plots for Storyline 4.
    
    Args:
        metrics: Dict of computed metrics tables
        outdir: Output directory
        params: Pipeline parameters
        
    Returns:
        Dict of plot name -> file path
    """
    plots = {}
    top_n = params.get("top_n", 10)
    max_heatmap = params.get("max_heatmap_items", 20)
    
    # Actor centrality - collaboration
    centrality_overall = metrics.get("ACTOR_CENTRALITY_OVERALL", pd.DataFrame())
    if not centrality_overall.empty and "out_degree_colabora" in centrality_overall.columns:
        path = bar_top_actors_by_degree(
            centrality_overall,
            "out_degree_colabora",
            "Top Actors by Collaboration Degree / Actores con Mayor Colaboración",
            COLORS["colabora"],
            outdir,
            "bar_top_actors_collab_overall",
            top_n=top_n,
        )
        if path:
            plots["bar_top_actors_collab_overall"] = path
    
    # Actor centrality - conflict
    if not centrality_overall.empty and "out_degree_conflicto" in centrality_overall.columns:
        path = bar_top_actors_by_degree(
            centrality_overall,
            "out_degree_conflicto",
            "Top Actors by Conflict Degree / Actores con Mayor Conflicto",
            COLORS["conflicto"],
            outdir,
            "bar_top_actors_conflict_overall",
            top_n=top_n,
        )
        if path:
            plots["bar_top_actors_conflict_overall"] = path
    
    # Dyads heatmaps
    dyads_overall = metrics.get("DYADS_OVERALL", pd.DataFrame())
    if not dyads_overall.empty:
        path = heatmap_dyads(
            dyads_overall,
            "colabora",
            "Collaboration Network / Red de Colaboración",
            outdir,
            "heatmap_dyads_collab_overall",
            max_items=max_heatmap,
        )
        if path:
            plots["heatmap_dyads_collab_overall"] = path
        
        path = heatmap_dyads(
            dyads_overall,
            "conflicto",
            "Conflict Network / Red de Conflicto",
            outdir,
            "heatmap_dyads_conflict_overall",
            max_items=max_heatmap,
        )
        if path:
            plots["heatmap_dyads_conflict_overall"] = path
    
    # Dialogue participation
    participation = metrics.get("DIALOGUE_PARTICIPATION_OVERALL", pd.DataFrame())
    if not participation.empty:
        path = bar_dialogue_participation(participation, outdir, "bar_dialogue_participation", top_n=top_n)
        if path:
            plots["bar_dialogue_participation"] = path
    
    # Actor in spaces
    actor_spaces = metrics.get("ACTOR_IN_SPACES_OVERALL", pd.DataFrame())
    if not actor_spaces.empty:
        path = bar_actor_in_spaces(actor_spaces, outdir, "bar_actor_in_spaces", top_n=top_n)
        if path:
            plots["bar_actor_in_spaces"] = path
    
    # Conflict timeline
    timeline_overall = metrics.get("CONFLICT_TIMELINE_OVERALL", pd.DataFrame())
    if not timeline_overall.empty:
        path = line_conflict_timeline(timeline_overall, outdir, "line_conflict_timeline_overall")
        if path:
            plots["line_conflict_timeline_overall"] = path
    
    # Conflict timeline by grupo
    timeline_grupo = metrics.get("CONFLICT_TIMELINE_BY_GRUPO", pd.DataFrame())
    if not timeline_grupo.empty and GRUPO_COL in timeline_grupo.columns:
        for grupo in timeline_grupo[GRUPO_COL].dropna().unique():
            grupo_data = timeline_grupo[timeline_grupo[GRUPO_COL] == grupo]
            safe_name = str(grupo).replace(" ", "_").replace("/", "_")[:20]
            path = line_conflict_timeline(
                grupo_data, outdir,
                f"line_conflict_timeline_{safe_name}",
                grupo=grupo,
            )
            if path:
                plots[f"line_conflict_timeline_{safe_name}"] = path
    
    # Top conflicts
    conflicts_overall = metrics.get("CONFLICTS_OVERALL", pd.DataFrame())
    if not conflicts_overall.empty:
        path = bar_top_conflicts(conflicts_overall, outdir, "bar_top_conflicts", top_n=top_n)
        if path:
            plots["bar_top_conflicts"] = path
    
    # Threats linked to conflicts
    threats_linked = metrics.get("TOP_CONFLICT_LINKED_THREATS", pd.DataFrame())
    if not threats_linked.empty:
        path = bar_threats_linked_conflicts(threats_linked, outdir, "bar_threats_linked_conflicts", top_n=top_n)
        if path:
            plots["bar_threats_linked_conflicts"] = path
    
    # Feasibility by grupo
    feasibility = metrics.get("FEASIBILITY_BY_GRUPO", pd.DataFrame())
    if not feasibility.empty:
        path = bar_feasibility_by_grupo(feasibility, outdir, "bar_feasibility_by_grupo")
        if path:
            plots["bar_feasibility_by_grupo"] = path
    
    logger.info(f"Generated {len(plots)} plots")
    return plots
