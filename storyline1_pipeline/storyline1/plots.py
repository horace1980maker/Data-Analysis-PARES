#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 Plots Module
Generates matplotlib visualizations for the analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Set matplotlib style
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 10


def bar_top_livelihoods_api_overall(
    rankings: pd.DataFrame,
    scenario: str,
    outdir: Path,
    top_n: int = 10,
) -> str:
    """
    Create bar chart of top livelihoods by API score (overall).
    
    Args:
        rankings: Rankings DataFrame with mdv_name and api_score columns
        scenario: Weight scenario name
        outdir: Output directory for figures
        top_n: Number of top items to show
        
    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if rankings.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title(f"Top Livelihoods by Action Priority Index ({scenario})")
    else:
        data = rankings.head(top_n).copy()
        
        # Create horizontal bar chart
        y_pos = np.arange(len(data))
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(data)))[::-1]
        
        bars = ax.barh(y_pos, data["api_score"], color=colors, edgecolor="black", linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(data["mdv_name"].tolist(), fontsize=9)
        ax.invert_yaxis()  # Highest at top
        
        ax.set_xlabel("Action Priority Index (API)")
        ax.set_title(f"Top {len(data)} Livelihoods by Action Priority Index\n(Scenario: {scenario.replace('_', ' ').title()})")
        
        # Add value labels
        for bar, val in zip(bars, data["api_score"]):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, 
                    f"{val:.2f}", va="center", fontsize=8)
    
    plt.tight_layout()
    
    fig_path = outdir / f"bar_top_livelihoods_api_overall_{scenario}.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    logger.info(f"Saved figure: {fig_path}")
    return str(fig_path)


def bar_top_livelihoods_api_by_group(
    rankings: pd.DataFrame,
    scenario: str,
    outdir: Path,
    top_n: int = 5,
) -> str:
    """
    Create bar chart of top livelihoods by API score for each grupo.
    
    Args:
        rankings: Rankings DataFrame with grupo, mdv_name, and api_score columns
        scenario: Weight scenario name
        outdir: Output directory for figures
        top_n: Number of top items per group
        
    Returns:
        Path to saved figure
    """
    if rankings.empty or "grupo" not in rankings.columns:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title(f"Top Livelihoods by API by Group ({scenario})")
        fig_path = outdir / f"bar_top_livelihoods_api_by_group_{scenario}.png"
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(fig_path)
    
    grupos = rankings["grupo"].dropna().unique()
    n_grupos = len(grupos)
    
    if n_grupos == 0:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No grupo data available", ha="center", va="center", fontsize=14)
        fig_path = outdir / f"bar_top_livelihoods_api_by_group_{scenario}.png"
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(fig_path)
    
    # Create subplots for each grupo
    fig, axes = plt.subplots(1, n_grupos, figsize=(5 * n_grupos, 6), squeeze=False)
    
    for idx, grupo in enumerate(sorted(grupos)):
        ax = axes[0, idx]
        group_data = rankings[rankings["grupo"] == grupo].head(top_n)
        
        if group_data.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_title(f"{grupo}")
            continue
        
        y_pos = np.arange(len(group_data))
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(group_data)))[::-1]
        
        bars = ax.barh(y_pos, group_data["api_score"], color=colors, edgecolor="black", linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(group_data["mdv_name"].tolist(), fontsize=8)
        ax.invert_yaxis()
        
        ax.set_xlabel("API Score")
        ax.set_title(f"{grupo}", fontsize=11, fontweight="bold")
        
        # Add value labels
        for bar, val in zip(bars, group_data["api_score"]):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2, 
                    f"{val:.2f}", va="center", fontsize=7)
    
    fig.suptitle(f"Top Livelihoods by Action Priority Index - By Group\n(Scenario: {scenario.replace('_', ' ').title()})", 
                 fontsize=12, fontweight="bold", y=1.02)
    
    plt.tight_layout()
    
    fig_path = outdir / f"bar_top_livelihoods_api_by_group_{scenario}.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    logger.info(f"Saved figure: {fig_path}")
    return str(fig_path)


def quadrant_priority_vs_risk(
    priority_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
    outdir: Path,
) -> str:
    """
    Create quadrant scatter plot: Priority vs Risk (bubble size = Capacity gap).
    
    Args:
        priority_df: Priority metrics with mdv_id, mdv_name, priority_norm
        risk_df: Risk metrics with mdv_id, risk_norm
        capacity_df: Capacity metrics with mdv_id, cap_gap_norm
        outdir: Output directory
        
    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    if priority_df.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title("Priority vs Risk Quadrant")
        fig_path = outdir / "quadrant_priority_vs_risk_overall.png"
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(fig_path)
    
    # Merge datasets
    data = priority_df[["mdv_id", "mdv_name", "priority_norm"]].copy()
    data["mdv_id"] = data["mdv_id"].astype(str)
    
    if not risk_df.empty:
        risk_subset = risk_df[["mdv_id", "risk_norm"]].copy()
        risk_subset["mdv_id"] = risk_subset["mdv_id"].astype(str)
        data = data.merge(risk_subset, on="mdv_id", how="left")
    else:
        data["risk_norm"] = 0.5
    
    if not capacity_df.empty:
        cap_subset = capacity_df[["mdv_id", "cap_gap_norm"]].copy()
        cap_subset["mdv_id"] = cap_subset["mdv_id"].astype(str)
        data = data.merge(cap_subset, on="mdv_id", how="left")
    else:
        data["cap_gap_norm"] = 0.5
    
    # Fill NaN
    data = data.fillna(0.5)
    
    # Compute bubble sizes (scaled for visibility)
    min_size = 100
    max_size = 1500
    sizes = min_size + (data["cap_gap_norm"] * (max_size - min_size))
    
    # Create scatter plot
    scatter = ax.scatter(
        data["priority_norm"],
        data["risk_norm"],
        s=sizes,
        c=data["cap_gap_norm"],
        cmap="RdYlGn_r",
        alpha=0.7,
        edgecolors="black",
        linewidth=0.5,
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Capacity Gap (1 - Adaptive Capacity)", fontsize=10)
    
    # Add quadrant lines
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.axvline(x=0.5, color="gray", linestyle="--", alpha=0.5)
    
    # Add quadrant labels
    ax.text(0.75, 0.95, "High Priority\nHigh Risk", ha="center", va="top", fontsize=9, 
            fontweight="bold", color="red", alpha=0.7, transform=ax.transAxes)
    ax.text(0.25, 0.95, "Low Priority\nHigh Risk", ha="center", va="top", fontsize=9, 
            fontweight="bold", color="orange", alpha=0.7, transform=ax.transAxes)
    ax.text(0.75, 0.05, "High Priority\nLow Risk", ha="center", va="bottom", fontsize=9, 
            fontweight="bold", color="green", alpha=0.7, transform=ax.transAxes)
    ax.text(0.25, 0.05, "Low Priority\nLow Risk", ha="center", va="bottom", fontsize=9, 
            fontweight="bold", color="gray", alpha=0.7, transform=ax.transAxes)
    
    # Label top livelihoods
    top_items = data.nlargest(10, "priority_norm")
    for _, row in top_items.iterrows():
        ax.annotate(
            str(row["mdv_name"])[:25] + ("..." if len(str(row["mdv_name"])) > 25 else ""),
            (row["priority_norm"], row["risk_norm"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
            alpha=0.8,
        )
    
    ax.set_xlabel("Priority Score (Normalized)", fontsize=11)
    ax.set_ylabel("Risk Score (Normalized)", fontsize=11)
    ax.set_title("Priority vs Risk Analysis\n(Bubble size = Capacity Gap)", fontsize=12, fontweight="bold")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    
    plt.tight_layout()
    
    fig_path = outdir / "quadrant_priority_vs_risk_overall.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    logger.info(f"Saved figure: {fig_path}")
    return str(fig_path)


def bar_top_threats_overall(
    threats_df: pd.DataFrame,
    outdir: Path,
    top_n: int = 10,
) -> str:
    """
    Create bar chart of top threats by severity (overall).
    
    Args:
        threats_df: Threats DataFrame with amenaza, mean_suma columns
        outdir: Output directory
        top_n: Number of top threats to show
        
    Returns:
        Path to saved figure
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if threats_df.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title("Top Threats by Severity")
    else:
        data = threats_df.nlargest(top_n, "mean_suma").copy()
        
        y_pos = np.arange(len(data))
        colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(data)))
        
        bars = ax.barh(y_pos, data["mean_suma"], color=colors, edgecolor="black", linewidth=0.5)
        
        # Create labels with threat type
        if "tipo_amenaza" in data.columns:
            labels = [f"{row['amenaza']} ({row['tipo_amenaza']})" if pd.notna(row['tipo_amenaza']) else row['amenaza']
                      for _, row in data.iterrows()]
        else:
            labels = data["amenaza"].tolist()
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        
        ax.set_xlabel("Severity Score (Mean Suma)")
        ax.set_title(f"Top {len(data)} Threats by Severity (Overall)", fontsize=12, fontweight="bold")
        
        # Add value labels
        for bar, val in zip(bars, data["mean_suma"]):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    f"{val:.1f}", va="center", fontsize=8)
    
    plt.tight_layout()
    
    fig_path = outdir / "bar_top_threats_overall.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    logger.info(f"Saved figure: {fig_path}")
    return str(fig_path)


def bar_top_threats_by_group(
    threats_df: pd.DataFrame,
    outdir: Path,
    top_n: int = 5,
) -> str:
    """
    Create bar chart of top threats by grupo.
    
    Args:
        threats_df: Threats DataFrame with grupo, amenaza, mean_suma columns
        outdir: Output directory
        top_n: Number of top threats per group
        
    Returns:
        Path to saved figure
    """
    if threats_df.empty or "grupo" not in threats_df.columns:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        ax.set_title("Top Threats by Severity by Group")
        fig_path = outdir / "bar_top_threats_by_group.png"
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(fig_path)
    
    grupos = threats_df["grupo"].dropna().unique()
    n_grupos = len(grupos)
    
    if n_grupos == 0:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No grupo data available", ha="center", va="center", fontsize=14)
        fig_path = outdir / "bar_top_threats_by_group.png"
        fig.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(fig_path)
    
    fig, axes = plt.subplots(1, n_grupos, figsize=(5 * n_grupos, 6), squeeze=False)
    
    for idx, grupo in enumerate(sorted(grupos)):
        ax = axes[0, idx]
        group_data = threats_df[threats_df["grupo"] == grupo].nlargest(top_n, "mean_suma")
        
        if group_data.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_title(f"{grupo}")
            continue
        
        y_pos = np.arange(len(group_data))
        colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(group_data)))
        
        bars = ax.barh(y_pos, group_data["mean_suma"], color=colors, edgecolor="black", linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(group_data["amenaza"].tolist(), fontsize=8)
        ax.invert_yaxis()
        
        ax.set_xlabel("Severity")
        ax.set_title(f"{grupo}", fontsize=11, fontweight="bold")
    
    fig.suptitle("Top Threats by Severity - By Group", fontsize=12, fontweight="bold", y=1.02)
    
    plt.tight_layout()
    
    fig_path = outdir / "bar_top_threats_by_group.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    logger.info(f"Saved figure: {fig_path}")
    return str(fig_path)


def generate_all_plots(
    tables: Dict[str, pd.DataFrame],
    outdir: str,
    scenarios: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Generate all plots for Storyline 1.
    
    Args:
        tables: Dict of computed metrics tables
        outdir: Output directory for figures
        scenarios: List of scenario names (default: all in rankings)
        
    Returns:
        Dict mapping figure name to file path
    """
    figures_dir = Path(outdir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    figures: Dict[str, str] = {}
    
    # Determine scenarios from available rankings
    if scenarios is None:
        scenarios = []
        for key in tables.keys():
            if key.startswith("rankings_overall_"):
                scenario = key.replace("rankings_overall_", "")
                scenarios.append(scenario)
        if not scenarios:
            scenarios = ["balanced"]
    
    # Generate API bar charts for each scenario
    for scenario in scenarios:
        # Overall rankings
        rankings_key = f"rankings_overall_{scenario}"
        if rankings_key in tables and not tables[rankings_key].empty:
            path = bar_top_livelihoods_api_overall(
                tables[rankings_key], scenario, figures_dir
            )
            figures[f"bar_api_overall_{scenario}"] = path
        
        # By-group rankings
        rankings_group_key = f"rankings_by_group_{scenario}"
        if rankings_group_key in tables and not tables[rankings_group_key].empty:
            path = bar_top_livelihoods_api_by_group(
                tables[rankings_group_key], scenario, figures_dir
            )
            figures[f"bar_api_by_group_{scenario}"] = path
    
    # Quadrant plot
    priority_df = tables.get("priority_by_mdv_overall", pd.DataFrame())
    risk_df = tables.get("risk_by_mdv_overall", pd.DataFrame())
    capacity_df = tables.get("capacity_overall_by_mdv", pd.DataFrame())
    
    path = quadrant_priority_vs_risk(priority_df, risk_df, capacity_df, figures_dir)
    figures["quadrant_priority_risk"] = path
    
    # Threat bar charts
    threats_overall = tables.get("threats_overall", pd.DataFrame())
    if not threats_overall.empty:
        path = bar_top_threats_overall(threats_overall, figures_dir)
        figures["bar_threats_overall"] = path
    
    threats_by_group = tables.get("threats_by_group", pd.DataFrame())
    if not threats_by_group.empty:
        path = bar_top_threats_by_group(threats_by_group, figures_dir)
        figures["bar_threats_by_group"] = path
    
    logger.info(f"Generated {len(figures)} figures")
    return figures
