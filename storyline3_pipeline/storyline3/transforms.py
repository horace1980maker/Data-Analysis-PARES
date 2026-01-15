import pandas as pd
import numpy as np
import re
import unicodedata
from typing import List, Optional
from .config import SURVEY_RANGE_MAP

def canonical_text(text: any) -> str:
    """Normalize text: lower, strip accents, collapse spaces."""
    if pd.isna(text):
        return ""
    s = str(text).lower().strip()
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\s+', ' ', s)
    return s

def minmax(series: pd.Series) -> pd.Series:
    """Safe 0-1 scaling."""
    if series.empty:
        return series
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(0.5, index=series.index)
    return (series - s_min) / (s_max - s_min)

def attach_geo(df: pd.DataFrame, dim_context_geo: pd.DataFrame) -> pd.DataFrame:
    """Join LOOKUP_CONTEXT -> LOOKUP_GEO to retrieve {admin0, paisaje, grupo, fecha_iso} if context_id exists."""
    if df.empty or 'context_id' not in df.columns:
        return df
    return df.merge(dim_context_geo, on='context_id', how='left')

def pick_first_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return the first candidate column name that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return None

def coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Ensure columns are numeric, filling NaNs with 0."""
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def parse_range_to_midpoint(val: any) -> float:
    """Parse range tags like '40-60' to 50 via config map or regex."""
    s = str(val).strip()
    if s in SURVEY_RANGE_MAP:
        return float(SURVEY_RANGE_MAP[s])
    # Try regex if not in map
    match = re.search(r'(\d+)\s*-\s*(\d+)', s)
    if match:
        return (float(match.group(1)) + float(match.group(2))) / 2.0
    try:
        return float(s)
    except:
        return np.nan

def explode_text_to_items(value: any) -> List[str]:
    """Split text by common delimiters and return cleaned list."""
    if pd.isna(value) or value == "":
        return []
    s = str(value)
    # Split by common separators: , ; | / \n and " y " (cautiously)
    delims = r'[,;|/\n\r]+'
    items = re.split(delims, s)
    
    final_items = []
    for item in items:
        # Split by " y " or " " if it's strictly Spanish "and"
        sub_items = re.split(r'\s+y\s+', item, flags=re.IGNORECASE)
        for si in sub_items:
            clean = si.strip().lower()
            if clean:
                final_items.append(clean)
    return list(set(final_items))

def frequency_table(df: pd.DataFrame, text_col: str, group_cols: List[str], min_text_len: int = 2) -> pd.DataFrame:
    """Exlodes a text column and returns counts/proportions."""
    if df.empty or text_col not in df.columns:
        return pd.DataFrame()
    
    # Explode
    rows = []
    for _, row in df.iterrows():
        items = explode_text_to_items(row[text_col])
        for it in items:
            if len(it) >= min_text_len:
                d = {gc: row[gc] for gc in group_cols if gc in df.columns}
                d['item'] = it
                rows.append(d)
    
    if not rows:
        return pd.DataFrame()
    
    exploded = pd.DataFrame(rows)
    # Check if group_cols are actually in exploded
    actual_groups = [c for c in group_cols if c in exploded.columns]
    
    counts = exploded.groupby(actual_groups + ['item']).size().reset_index(name='count')
    
    if actual_groups:
        totals = counts.groupby(actual_groups)['count'].transform('sum')
    else:
        totals = counts['count'].sum()
        
    counts['rate'] = counts['count'] / totals
    return counts.sort_values(actual_groups + ['count'], ascending=False)
