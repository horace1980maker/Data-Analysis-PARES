"""
Plotting module for Storyline 5.
Generates visualization figures using matplotlib.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pandas as pd

# Use non-interactive backend
matplotlib.use("Agg")

logger = logging.getLogger(__name__)

# Color schemes matching storyline1/4 reports
COLORS = {
    "primary": "#00695c",      # Teal
    "secondary": "#26a69a",    # Light teal
    "accent": "#ffb300",       # Amber
    "do_now": "#2e7d32",       # Green
    "do_next": "#ff9800",      # Orange
    "do_later": "#c62828",     # Red
    "impact": "#1565c0",       # Blue
    "leverage": "#7cb342",     # Light green
    "equity": "#8e24aa",       # Purple
    "feasibility": "#00838f",  # Cyan
}

TIER_COLORS = {
    "Do now": COLORS["do_now"],
    "Do next": COLORS["do_next"],
    "Do later": COLORS["do_later"],
}


def setup_plot_style():
    """Set up consistent plot styling."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 14,
        "figure.dpi": 100,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def portfolio_matrix(
    bundles_df: pd.DataFrame,
    scenario: str,
    outdir: str,
    scope: str = "overall",
    grupo: Optional[str] = None,
) -> Optional[str]:
    """
    Create portfolio matrix: x=feasibility, y=impact, size=equity.
    
    Args:
        bundles_df: Ranked bundles DataFrame
        scenario: Scenario name
        outdir: Output directory
        scope: "overall" or "by_grupo"
        grupo: Group name if by_grupo
        
    Returns:
        Path to saved figure
    """
    if bundles_df.empty:
        return None
    
    df = bundles_df.copy()
    
    # Filter to grupo if specified
    if grupo and "grupo" in df.columns:
        df = df[df["grupo"] == grupo]
    
    if df.empty:
        return None
    
    # Limit to top 15 for readability
    df = df.head(15)
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Get values
    x = df["feasibility_score"].fillna(0.5)
    y = df["impact_potential_norm"].fillna(0.5)
    sizes = df["evi_score"].fillna(0.5) * 500 + 100  # Scale for visibility
    
    # Color by tier
    colors = df["tier"].map(TIER_COLORS).fillna(COLORS["secondary"])
    
    # Scatter plot
    scatter = ax.scatter(x, y, s=sizes, c=colors, alpha=0.7, edgecolors="white", linewidth=2)
    
    # Annotate top bundles
    for idx, row in df.head(10).iterrows():
        label = str(row.get("mdv_name", row.get("mdv_id", "")))[:20]
        ax.annotate(
            label,
            (row["feasibility_score"], row["impact_potential_norm"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            alpha=0.8
        )
    
    # Labels and title
    ax.set_xlabel("Feasibility Score", fontweight="bold")
    ax.set_ylabel("Impact Potential", fontweight="bold")
    
    title_scope = f" - {grupo}" if grupo else " (Overall)"
    ax.set_title(f"Portfolio Matrix: {scenario.title()}{title_scope}", fontsize=14, fontweight="bold")
    
    # Add quadrant lines
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.axvline(x=0.5, color="gray", linestyle="--", alpha=0.5)
    
    # Quadrant labels
    ax.text(0.75, 0.95, "High Impact\nHigh Feasibility", transform=ax.transAxes, 
            fontsize=9, alpha=0.5, ha="center")
    ax.text(0.25, 0.95, "High Impact\nLow Feasibility", transform=ax.transAxes,
            fontsize=9, alpha=0.5, ha="center")
    
    # Legend for tiers
    legend_elements = [
        plt.scatter([], [], c=TIER_COLORS["Do now"], s=100, label="Do now"),
        plt.scatter([], [], c=TIER_COLORS["Do next"], s=100, label="Do next"),
        plt.scatter([], [], c=TIER_COLORS["Do later"], s=100, label="Do later"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", framealpha=0.9)
    
    # Add note about bubble size
    ax.text(0.02, 0.02, "Bubble size = Equity urgency", transform=ax.transAxes,
            fontsize=8, alpha=0.6)
    
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    
    # Save
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    if grupo:
        filename = f"portfolio_matrix_{grupo.lower().replace(' ', '_')}_{scenario}.png"
    else:
        filename = f"portfolio_matrix_overall_{scenario}.png"
    
    filepath = figures_dir / filename
    fig.savefig(filepath)
    plt.close(fig)
    
    logger.debug(f"Saved portfolio matrix: {filepath}")
    return str(filepath)


def stacked_components_chart(
    bundles_df: pd.DataFrame,
    scenario: str,
    outdir: str,
) -> Optional[str]:
    """
    Create stacked bar chart showing component contributions for top bundles.
    
    Args:
        bundles_df: Ranked bundles DataFrame
        scenario: Scenario name
        outdir: Output directory
        
    Returns:
        Path to saved figure
    """
    if bundles_df.empty:
        return None
    
    df = bundles_df.head(10).copy()
    
    if df.empty:
        return None
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Get component values
    components = {
        "Impact Potential": df["impact_potential_norm"].fillna(0),
        "Leverage (SCI×ELI)": df["leverage"].fillna(0),
        "Equity Urgency": df["evi_score"].fillna(0),
        "Feasibility": df["feasibility_score"].fillna(0),
    }
    
    component_colors = [COLORS["impact"], COLORS["leverage"], COLORS["equity"], COLORS["feasibility"]]
    
    # Create labels
    labels = [str(row.get("mdv_name", row.get("mdv_id", "")))[:20] for _, row in df.iterrows()]
    x = np.arange(len(labels))
    width = 0.6
    
    # Stacked bars
    bottom = np.zeros(len(df))
    for (name, values), color in zip(components.items(), component_colors):
        ax.bar(x, values, width, label=name, bottom=bottom, color=color, alpha=0.85)
        bottom += values.values
    
    ax.set_xlabel("Bundle (MdV)", fontweight="bold")
    ax.set_ylabel("Cumulative Score", fontweight="bold")
    ax.set_title(f"Component Contributions - Top 10 Bundles ({scenario.title()})", 
                 fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend(loc="upper right", framealpha=0.9)
    
    plt.tight_layout()
    
    # Save
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    filepath = figures_dir / f"stacked_components_top_bundles_overall_{scenario}.png"
    fig.savefig(filepath)
    plt.close(fig)
    
    logger.debug(f"Saved stacked components chart: {filepath}")
    return str(filepath)


def bundle_scores_by_grupo(
    bundles_df: pd.DataFrame,
    scenario: str,
    outdir: str,
) -> Optional[str]:
    """
    Create bar chart of mean portfolio scores by grupo.
    
    Args:
        bundles_df: Ranked bundles with grupo column
        scenario: Scenario name
        outdir: Output directory
        
    Returns:
        Path to saved figure
    """
    if bundles_df.empty or "grupo" not in bundles_df.columns:
        return None
    
    df = bundles_df.copy()
    
    # Aggregate by grupo
    grupo_stats = df.groupby("grupo").agg({
        "portfolio_score": "mean",
        "tier": lambda x: x.value_counts().to_dict()
    }).reset_index()
    
    if grupo_stats.empty:
        return None
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(grupo_stats))
    width = 0.5
    
    # Main bars
    bars = ax.bar(x, grupo_stats["portfolio_score"], width, color=COLORS["primary"], alpha=0.85)
    
    ax.set_xlabel("Grupo", fontweight="bold")
    ax.set_ylabel("Mean Portfolio Score", fontweight="bold")
    ax.set_title(f"Bundle Scores by Grupo ({scenario.title()})", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(grupo_stats["grupo"], rotation=0)
    
    # Add tier counts as annotations
    for i, (idx, row) in enumerate(grupo_stats.iterrows()):
        tier_counts = row["tier"] if isinstance(row["tier"], dict) else {}
        tier_text = ", ".join([f"{k[:2]}:{v}" for k, v in tier_counts.items()])
        if tier_text:
            ax.annotate(tier_text, (i, row["portfolio_score"] + 0.02),
                       ha="center", fontsize=8, alpha=0.7)
    
    ax.set_ylim(0, min(1.0, grupo_stats["portfolio_score"].max() * 1.2))
    
    plt.tight_layout()
    
    # Save
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    filepath = figures_dir / f"bar_bundle_scores_by_grupo_{scenario}.png"
    fig.savefig(filepath)
    plt.close(fig)
    
    logger.debug(f"Saved bundle scores by grupo: {filepath}")
    return str(filepath)


def top_services_in_bundles(
    bundles_df: pd.DataFrame,
    outdir: str,
) -> Optional[str]:
    """
    Create bar chart of most frequent services in top bundles.
    
    Args:
        bundles_df: Bundles DataFrame with services column
        outdir: Output directory
        
    Returns:
        Path to saved figure
    """
    if bundles_df.empty or "services" not in bundles_df.columns:
        return None
    
    # Flatten services
    all_services = []
    for services in bundles_df["services"].dropna():
        if isinstance(services, list):
            all_services.extend(services)
        elif isinstance(services, str):
            all_services.extend([s.strip() for s in services.split(",")])
    
    if not all_services:
        return None
    
    # Count frequencies
    service_counts = pd.Series(all_services).value_counts().head(10)
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(service_counts))
    bars = ax.barh(x, service_counts.values, color=COLORS["secondary"], alpha=0.85)
    
    ax.set_xlabel("Frequency in Bundles", fontweight="bold")
    ax.set_ylabel("Service", fontweight="bold")
    ax.set_title("Top Services Appearing in Bundles", fontsize=14, fontweight="bold")
    ax.set_yticks(x)
    ax.set_yticklabels([str(s)[:30] for s in service_counts.index])
    
    # Add count labels
    for i, v in enumerate(service_counts.values):
        ax.text(v + 0.1, i, str(v), va="center", fontsize=9)
    
    ax.invert_yaxis()
    plt.tight_layout()
    
    # Save
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    filepath = figures_dir / "bar_top_services_in_bundles_overall.png"
    fig.savefig(filepath)
    plt.close(fig)
    
    logger.debug(f"Saved top services chart: {filepath}")
    return str(filepath)


def top_threats_in_bundles(
    bundles_df: pd.DataFrame,
    outdir: str,
) -> Optional[str]:
    """
    Create bar chart of most frequent threats in top bundles.
    
    Args:
        bundles_df: Bundles DataFrame with threats column
        outdir: Output directory
        
    Returns:
        Path to saved figure
    """
    if bundles_df.empty or "threats" not in bundles_df.columns:
        return None
    
    # Flatten threats
    all_threats = []
    for threats in bundles_df["threats"].dropna():
        if isinstance(threats, list):
            all_threats.extend(threats)
        elif isinstance(threats, str):
            all_threats.extend([t.strip() for t in threats.split(",")])
    
    if not all_threats:
        return None
    
    # Count frequencies
    threat_counts = pd.Series(all_threats).value_counts().head(10)
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(threat_counts))
    bars = ax.barh(x, threat_counts.values, color=COLORS["accent"], alpha=0.85)
    
    ax.set_xlabel("Frequency in Bundles", fontweight="bold")
    ax.set_ylabel("Threat", fontweight="bold")
    ax.set_title("Top Threats Driving Bundle Risk", fontsize=14, fontweight="bold")
    ax.set_yticks(x)
    ax.set_yticklabels([str(t)[:30] for t in threat_counts.index])
    
    # Add count labels
    for i, v in enumerate(threat_counts.values):
        ax.text(v + 0.1, i, str(v), va="center", fontsize=9)
    
    ax.invert_yaxis()
    plt.tight_layout()
    
    # Save
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    filepath = figures_dir / "bar_top_threats_in_bundles_overall.png"
    fig.savefig(filepath)
    plt.close(fig)
    
    logger.debug(f"Saved top threats chart: {filepath}")
    return str(filepath)


def tier_distribution_chart(
    bundles_df: pd.DataFrame,
    scenario: str,
    outdir: str,
) -> Optional[str]:
    """
    Create pie chart of tier distribution.
    
    Args:
        bundles_df: Bundles with tier column
        scenario: Scenario name
        outdir: Output directory
        
    Returns:
        Path to saved figure
    """
    if bundles_df.empty or "tier" not in bundles_df.columns:
        return None
    
    tier_counts = bundles_df["tier"].value_counts()
    
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(8, 8))
    
    colors = [TIER_COLORS.get(t, COLORS["secondary"]) for t in tier_counts.index]
    
    wedges, texts, autotexts = ax.pie(
        tier_counts.values,
        labels=tier_counts.index,
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        explode=[0.02] * len(tier_counts),
    )
    
    ax.set_title(f"Bundle Tier Distribution ({scenario.title()})", fontsize=14, fontweight="bold")
    
    # Save
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    filepath = figures_dir / f"pie_tier_distribution_{scenario}.png"
    fig.savefig(filepath)
    plt.close(fig)
    
    logger.debug(f"Saved tier distribution chart: {filepath}")
    return str(filepath)


# =============================================================================
# MASTER FUNCTION
# =============================================================================

def generate_plots(
    portfolio_tables: Dict[str, pd.DataFrame],
    outdir: str,
    params: Dict[str, Any],
) -> Dict[str, str]:
    """
    Generate all plots for the portfolio.
    
    Args:
        portfolio_tables: Portfolio output tables
        outdir: Output directory
        params: Pipeline parameters
        
    Returns:
        Dict of plot_name -> filepath
    """
    figures = {}
    
    # Process each scenario
    scenarios = ["balanced", "equity_first", "feasibility_first"]
    
    for scenario in scenarios:
        # Overall portfolio matrix
        key_overall = f"BUNDLE_RANKING_OVERALL_{scenario.upper()}"
        if key_overall in portfolio_tables:
            path = portfolio_matrix(portfolio_tables[key_overall], scenario, outdir, "overall")
            if path:
                figures[f"portfolio_matrix_overall_{scenario}"] = path
            
            # Stacked components
            path = stacked_components_chart(portfolio_tables[key_overall], scenario, outdir)
            if path:
                figures[f"stacked_components_{scenario}"] = path
            
            # Tier distribution
            path = tier_distribution_chart(portfolio_tables[key_overall], scenario, outdir)
            if path:
                figures[f"tier_distribution_{scenario}"] = path
        
        # By grupo rankings
        key_grupo = f"BUNDLE_RANKING_BY_GRUPO_{scenario.upper()}"
        if key_grupo in portfolio_tables:
            df = portfolio_tables[key_grupo]
            
            # Bundle scores by grupo
            path = bundle_scores_by_grupo(df, scenario, outdir)
            if path:
                figures[f"bundle_scores_by_grupo_{scenario}"] = path
            
            # Portfolio matrices per grupo
            if "grupo" in df.columns:
                for grupo in df["grupo"].unique():
                    path = portfolio_matrix(df, scenario, outdir, "by_grupo", grupo)
                    if path:
                        grupo_safe = str(grupo).lower().replace(" ", "_")
                        figures[f"portfolio_matrix_{grupo_safe}_{scenario}"] = path
    
    # Service and threat frequency (use overall balanced bundles)
    if "BUNDLES_OVERALL" in portfolio_tables:
        path = top_services_in_bundles(portfolio_tables["BUNDLES_OVERALL"], outdir)
        if path:
            figures["top_services_in_bundles"] = path
        
        path = top_threats_in_bundles(portfolio_tables["BUNDLES_OVERALL"], outdir)
        if path:
            figures["top_threats_in_bundles"] = path
    
    logger.info(f"Generated {len(figures)} figures")
    return figures
