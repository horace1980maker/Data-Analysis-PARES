import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from .transforms import (
    canonical_text, minmax, attach_geo, pick_first_existing_col, 
    coerce_numeric, parse_range_to_midpoint, frequency_table
)
from .config import (
    DIF_GROUP_CANDIDATES, DIF_NOTES_CANDIDATES, SE_CODE_CANDIDATES,
    BARRIER_CANDIDATES, INCLUSION_CANDIDATES, ACCESS_CANDIDATES
)
import yaml
import os

logger = logging.getLogger(__name__)

def load_params(config_path: str = "config/params.yaml") -> Dict[str, Any]:
    """Load parameters from YAML file."""
    # Try local to the module or current working dir
    paths = [
        config_path,
        os.path.join(os.path.dirname(__file__), "..", config_path),
        os.path.join(os.getcwd(), "storyline3_pipeline", config_path)
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    return {}

def build_dim_context_geo(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build DIM_CONTEXT_GEO by joining LOOKUP_CONTEXT and LOOKUP_GEO."""
    ctx = tables.get("LOOKUP_CONTEXT", pd.DataFrame())
    geo = tables.get("LOOKUP_GEO", pd.DataFrame())
    
    if ctx.empty or geo.empty:
        return pd.DataFrame()
    
    return ctx.merge(geo, on='geo_id', how='left')

def process_metrics(tables: Dict[str, pd.DataFrame], params: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Main orchestration for metric computation."""
    outputs = {}
    dim_context_geo = build_dim_context_geo(tables)
    
    # 1. Differentiated Impacts (DIF)
    outputs.update(compute_dif_metrics(tables, dim_context_geo, params))
    
    # 2. Service Access & Barriers (SE)
    outputs.update(compute_se_metrics(tables, dim_context_geo, params))
    
    # 3. Capacity Gap
    outputs.update(compute_capacity_metrics(tables, params))
    
    # 4. EVI Calculation
    outputs.update(compute_evi(outputs, params))
    
    # 5. Hotspots
    outputs.update(compute_hotspots(outputs, params))
    
    return outputs

def compute_dif_metrics(tables, dim_context_geo, params) -> Dict[str, pd.DataFrame]:
    """Compute differentiated impact metrics from TIDY_4_2_1/2_DIFERENCIADO tables."""
    res = {}
    
    # Try both differenciado tables and combine
    dif1 = tables.get("TIDY_4_2_1_DIFERENCIADO", pd.DataFrame())
    dif2 = tables.get("TIDY_4_2_2_DIFERENCIADO", pd.DataFrame())
    
    # Combine both if available
    dfs_to_combine = []
    if not dif1.empty:
        dif1['source'] = 'mdv'
        dfs_to_combine.append(dif1)
    if not dif2.empty:
        dif2['source'] = 'se'
        dfs_to_combine.append(dif2)
    
    if not dfs_to_combine:
        logger.warning("No DIFERENCIADO tables found or they are empty.")
        return res
    
    df = pd.concat(dfs_to_combine, ignore_index=True)
    
    # Find the group column
    dif_col = pick_first_existing_col(df, DIF_GROUP_CANDIDATES)
    if not dif_col:
        logger.warning(f"No differentiated group column found. Columns: {list(df.columns)}")
        return res
    
    # Standardize group names
    df['dif_group_std'] = df[dif_col].apply(canonical_text)
    
    # Simple count-based aggregation (works with minimal columns)
    grouped = df.groupby('dif_group_std').agg(
        count_records=('dif_group_std', 'count')
    ).reset_index()
    
    # Add extra stats if possible
    if 'amenaza_mdv_id' in df.columns:
        grouped_mdv = df.groupby('dif_group_std')['amenaza_mdv_id'].nunique().reset_index()
        grouped_mdv.columns = ['dif_group_std', 'n_unique_threats']
        grouped = grouped.merge(grouped_mdv, on='dif_group_std', how='left')
    elif 'amenaza_se_id' in df.columns:
        grouped_se = df.groupby('dif_group_std')['amenaza_se_id'].nunique().reset_index()
        grouped_se.columns = ['dif_group_std', 'n_unique_threats']
        grouped = grouped.merge(grouped_se, on='dif_group_std', how='left')
    
    res['DIF_LIVELIHOOD_OVERALL'] = grouped.sort_values('count_records', ascending=False)
    
    # Intensity is just the count for now (simple proxy)
    res['DIF_INTENSITY_OVERALL'] = grouped[['dif_group_std', 'count_records']].copy()
    res['DIF_INTENSITY_OVERALL'].columns = ['dif_group_std', 'intensity']
    res['DIF_INTENSITY_OVERALL'] = res['DIF_INTENSITY_OVERALL'].sort_values('intensity', ascending=False)
    
    logger.info(f"Computed DIF metrics: {len(grouped)} groups found")
    return res

def compute_se_metrics(tables, dim_context_geo, params) -> Dict[str, pd.DataFrame]:
    res = {}
    df = tables.get("TIDY_3_5_SE_MDV", pd.DataFrame())
    if df.empty:
        return res
        
    df = attach_geo(df, dim_context_geo)
    
    # Resilient column picking
    bar_col = pick_first_existing_col(df, BARRIER_CANDIDATES)
    acc_col = pick_first_existing_col(df, ACCESS_CANDIDATES)
    inc_col = pick_first_existing_col(df, INCLUSION_CANDIDATES)
    
    # Frequency tables
    if bar_col: res['BARRIERS_FREQ_OVERALL'] = frequency_table(df, bar_col, [])
    if acc_col: res['ACCESS_FREQ_OVERALL'] = frequency_table(df, acc_col, [])
    if inc_col: res['INCLUSION_FREQ_OVERALL'] = frequency_table(df, inc_col, [])
    
    if 'grupo' in df.columns:
        if bar_col: res['BARRIERS_FREQ_BY_GRUPO'] = frequency_table(df, bar_col, ['grupo'])
        if acc_col: res['ACCESS_FREQ_BY_GRUPO'] = frequency_table(df, acc_col, ['grupo'])
        if inc_col: res['INCLUSION_FREQ_BY_GRUPO'] = frequency_table(df, inc_col, ['grupo'])

    # Barrier rates
    def calc_rates(sub_df):
        total = len(sub_df)
        if total == 0: return pd.Series({'barriers_rate': 0.0, 'inclusion_rate': 0.0})
        b_count = sub_df[bar_col].notna().sum() if bar_col else 0
        i_count = sub_df[inc_col].notna().sum() if inc_col else 0
        return pd.Series({'barriers_rate': b_count/total, 'inclusion_rate': i_count/total})

    res['BARRIER_RATES_OVERALL'] = pd.DataFrame([calc_rates(df)])
    if 'grupo' in df.columns:
        res['BARRIER_RATES_BY_GRUPO'] = df.groupby('grupo', group_keys=True).apply(calc_rates, include_groups=False).reset_index()
    if 'grupo' in df.columns and 'mdv_id' in df.columns:
        res['BARRIER_RATES_BY_MDV_BY_GRUPO'] = df.groupby(['grupo', 'mdv_id', 'mdv_name'], group_keys=True).apply(calc_rates, include_groups=False).reset_index()
        
    return res

def compute_capacity_metrics(tables, params) -> Dict[str, pd.DataFrame]:
    res = {}
    resp = tables.get("TIDY_7_1_RESPONDENTS", pd.DataFrame())
    ans = tables.get("TIDY_7_1_RESPONSES", pd.DataFrame())
    
    if resp.empty or ans.empty:
        return res
        
    # Merge responses with respondent metadata
    df = ans.merge(resp, on='respondent_id', how='left')
    
    # Join with LOOKUP_MDV if mdv_name is missing
    if 'mdv_name' not in df.columns and 'mdv_id' in df.columns:
        lookup_mdv = tables.get("LOOKUP_MDV", pd.DataFrame())
        if not lookup_mdv.empty and 'mdv_id' in lookup_mdv.columns:
            mdv_cols = ['mdv_id']
            if 'mdv_name' in lookup_mdv.columns:
                mdv_cols.append('mdv_name')
            df = df.merge(lookup_mdv[mdv_cols].drop_duplicates(), on='mdv_id', how='left')
    
    # Join with LOOKUP_CA_QUESTIONS for question_text
    if 'question_text' not in df.columns and 'question_id' in df.columns:
        lookup_q = tables.get("LOOKUP_CA_QUESTIONS", pd.DataFrame())
        if not lookup_q.empty and 'question_id' in lookup_q.columns:
            q_cols = ['question_id']
            if 'question_text' in lookup_q.columns:
                q_cols.append('question_text')
            df = df.merge(lookup_q[q_cols].drop_duplicates(), on='question_id', how='left')
    
    # Midpoint and normalization
    # Force recalculation if response_numeric is missing or all NaN/null
    if 'response_numeric' not in df.columns or df['response_numeric'].isna().all():
        if 'response_raw' in df.columns:
            df['response_numeric'] = df['response_raw'].apply(parse_range_to_midpoint)
        else:
            logger.warning("No response_raw column found to compute response_numeric")
    
    # Normalize 0-1 (assuming 0-100 scale for questions)
    if 'response_numeric' in df.columns:
        df['response_0_1'] = df['response_numeric'] / 100.0
    else:
        df['response_0_1'] = 0.5 # Fallback

    
    # Questions overall - include question_text if available
    q_group_cols = ['question_id']
    if 'question_text' in df.columns:
        q_group_cols.append('question_text')
    res['CAPACITY_QUESTIONS_OVERALL'] = df.groupby(q_group_cols)['response_0_1'].mean().reset_index()
    if 'grupo' in df.columns:
        res['CAPACITY_QUESTIONS_BY_GRUPO'] = df.groupby(['grupo'] + q_group_cols)['response_0_1'].mean().reset_index()
        
    # MdV overall
    dv_cols = ['mdv_id']
    if 'mdv_name' in df.columns:
        dv_cols.append('mdv_name')
    if 'mdv_id' in df.columns:
        res['CAPACITY_BY_MDV_OVERALL'] = df.groupby(dv_cols)['response_0_1'].mean().reset_index()
        if 'grupo' in df.columns:
            res['CAPACITY_BY_MDV_BY_GRUPO'] = df.groupby(['grupo'] + dv_cols)['response_0_1'].mean().reset_index()
            
    return res


def compute_evi(metrics: Dict[str, pd.DataFrame], params: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    res = {}
    w_dif = params.get('w_differentiated_impacts', 0.45)
    w_bar = params.get('w_access_barriers', 0.25)
    w_inc = params.get('w_inclusion_exclusion', 0.15)
    w_cap = params.get('w_capacity_gap', 0.15)
    
    # We build EVI_BY_GRUPO
    df_geo = metrics.get('BARRIER_RATES_BY_GRUPO', pd.DataFrame())
    if df_geo.empty:
        # Try building from other sources if available
        if 'DIF_INTENSITY_BY_GRUPO' in metrics:
            df_geo = metrics['DIF_INTENSITY_BY_GRUPO'][['grupo']].drop_duplicates()
        else:
            return res
            
    # Compile components
    evi_df = df_geo[['grupo']].copy()
    
    # 1. DIF Intensity
    dif = metrics.get('DIF_INTENSITY_BY_GRUPO', pd.DataFrame())
    if not dif.empty:
        dif_agg = dif.groupby('grupo')['intensity'].mean().reset_index()
        evi_df = evi_df.merge(dif_agg, on='grupo', how='left')
        evi_df['dif_norm'] = minmax(evi_df['intensity'].fillna(0))
    else:
        evi_df['dif_norm'] = 0.0
        
    # 2. Barriers & Inclusion
    bar = metrics.get('BARRIER_RATES_BY_GRUPO', pd.DataFrame())
    if not bar.empty:
        evi_df = evi_df.merge(bar, on='grupo', how='left')
        evi_df['bar_norm'] = minmax(evi_df['barriers_rate'].fillna(0))
        evi_df['inc_norm'] = minmax(evi_df['inclusion_rate'].fillna(0))
    else:
        evi_df['bar_norm'] = 0.0
        evi_df['inc_norm'] = 0.0
        
    # 3. Capacity Gap
    cap = metrics.get('CAPACITY_BY_MDV_BY_GRUPO', pd.DataFrame())
    if not cap.empty:
        cap_agg = cap.groupby('grupo')['response_0_1'].mean().reset_index()
        # gap = 1 - mean
        cap_agg['cap_gap'] = 1.0 - cap_agg['response_0_1']
        evi_df = evi_df.merge(cap_agg[['grupo', 'cap_gap']], on='grupo', how='left')
        evi_df['cap_norm'] = minmax(evi_df['cap_gap'].fillna(0))
    else:
        evi_df['cap_norm'] = 0.0
        
    # Compute EVI
    evi_df['EVI'] = (
        w_dif * evi_df['dif_norm'] +
        w_bar * evi_df['bar_norm'] +
        w_inc * evi_df['inc_norm'] +
        w_cap * evi_df['cap_norm']
    )
    
    res['EVI_BY_GRUPO'] = evi_df.sort_values('EVI', ascending=False)
    res['EVI_OVERALL'] = pd.DataFrame([{'EVI_mean': evi_df['EVI'].mean()}])
    
    return res

def compute_hotspots(metrics: Dict[str, pd.DataFrame], params: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    # Placeholder for more complex joining if needed
    # Usually handled in report.py by joining tables manually for the reader
    return {}
