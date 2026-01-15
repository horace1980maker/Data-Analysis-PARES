import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import logging
from typing import Dict, List
import pandas as pd

logger = logging.getLogger(__name__)

def generate_plots(metrics: Dict[str, pd.DataFrame], outdir: str, params: Dict) -> Dict[str, str]:
    """Generate all Matplotlib plots for Storyline 3."""
    fig_dir = os.path.join(outdir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    plot_map = {}
    top_n = params.get('top_n', 10)
    
    # 1. DIF Groups Overall
    if 'DIF_INTENSITY_OVERALL' in metrics:
        df = metrics['DIF_INTENSITY_OVERALL'].sort_values('intensity', ascending=False).head(top_n)
        if not df.empty:
            plt.figure(figsize=(10, 6))
            plt.barh(df['dif_group_std'], df['intensity'], color='skyblue')
            plt.title('Top Impacted Subgroups (Differentiated Intensity)')
            plt.xlabel('Intensity Proxy')
            plt.tight_layout()
            path = os.path.join(fig_dir, "bar_dif_groups_overall.png")
            plt.savefig(path)
            plt.close()
            plot_map['bar_dif_groups_overall'] = path

    # 2. Barriers Overall
    if 'BARRIERS_FREQ_OVERALL' in metrics:
        df = metrics['BARRIERS_FREQ_OVERALL'].head(top_n)
        if not df.empty:
            plt.figure(figsize=(10, 6))
            plt.barh(df['item'], df['count'], color='salmon')
            plt.title('Top Service Access Barriers (Overall)')
            plt.xlabel('Frequency')
            plt.tight_layout()
            path = os.path.join(fig_dir, "bar_top_barriers_overall.png")
            plt.savefig(path)
            plt.close()
            plot_map['bar_top_barriers_overall'] = path

    # 3. Capacity Bottom Questions
    if 'CAPACITY_QUESTIONS_OVERALL' in metrics:
        df = metrics['CAPACITY_QUESTIONS_OVERALL'].sort_values('response_0_1', ascending=True).head(top_n)
        if not df.empty:
            plt.figure(figsize=(10, 6))
            # Prefer question_text over question_id for labels
            label_col = 'question_text' if 'question_text' in df.columns else 'question_id'
            labels = df[label_col].astype(str).tolist()
            # Truncate long labels
            labels = [l[:50] + '...' if len(l) > 50 else l for l in labels]
            plt.barh(range(len(df)), df['response_0_1'], color='lightgreen')
            plt.yticks(range(len(df)), labels)
            plt.title('Lowest Capacity Scores by Question')
            plt.xlabel('Mean Score (0-1)')
            plt.xlim(0, 1)
            plt.tight_layout()
            path = os.path.join(fig_dir, "bar_capacity_bottom_questions_overall.png")
            plt.savefig(path)
            plt.close()
            plot_map['bar_capacity_bottom_questions_overall'] = path


    # 4. EVI by Grupo
    if 'EVI_BY_GRUPO' in metrics:
        df = metrics['EVI_BY_GRUPO'].sort_values('EVI', ascending=True)
        if not df.empty:
            plt.figure(figsize=(10, 6))
            plt.barh(df['grupo'], df['EVI'], color='gold')
            plt.title('Equity Vulnerability Index (EVI) by Grupo')
            plt.xlabel('EVI Score (0-1)')
            plt.xlim(0, 1)
            plt.tight_layout()
            path = os.path.join(fig_dir, "bar_evi_by_grupo.png")
            plt.savefig(path)
            plt.close()
            plot_map['bar_evi_by_grupo'] = path

    # By Grupo Specific Plots
    grupos = []
    if 'DIF_INTENSITY_BY_GRUPO' in metrics:
        grupos = metrics['DIF_INTENSITY_BY_GRUPO']['grupo'].unique()
        
    for g in grupos:
        g_safe = "".join([c if c.isalnum() else "_" for c in str(g)])
        
        # DIF by Grupo
        df_g = metrics['DIF_INTENSITY_BY_GRUPO'][metrics['DIF_INTENSITY_BY_GRUPO']['grupo'] == g].sort_values('intensity', ascending=False).head(top_n)
        if not df_g.empty:
            plt.figure(figsize=(10, 6))
            plt.barh(df_g['dif_group_std'], df_g['intensity'], color='skyblue')
            plt.title(f'Impacted Subgroups in {g}')
            plt.xlabel('Intensity Proxy')
            plt.tight_layout()
            path = os.path.join(fig_dir, f"bar_dif_groups_by_grupo_{g_safe}.png")
            plt.savefig(path)
            plt.close()
            plot_map[f'bar_dif_groups_{g_safe}'] = path
            
        # Barriers by Grupo
        if 'BARRIERS_FREQ_BY_GRUPO' in metrics:
            df_b = metrics['BARRIERS_FREQ_BY_GRUPO'][metrics['BARRIERS_FREQ_BY_GRUPO']['grupo'] == g].head(top_n)
            if not df_b.empty:
                plt.figure(figsize=(10, 6))
                plt.barh(df_b['item'], df_b['count'], color='salmon')
                plt.title(f'Top Barriers in {g}')
                plt.xlabel('Frequency')
                plt.tight_layout()
                path = os.path.join(fig_dir, f"bar_top_barriers_by_grupo_{g_safe}.png")
                plt.savefig(path)
                plt.close()
                plot_map[f'bar_top_barriers_{g_safe}'] = path

    return plot_map
