"""
Transform utilities for Storyline 4.
Shared data manipulation functions.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def canonical_text(x: Any) -> str:
    """
    Normalize text: lowercase, strip, collapse whitespace, remove accents.
    
    Args:
        x: Input value (any type)
        
    Returns:
        Normalized string
    """
    if pd.isna(x):
        return ""
    s = str(x).strip().lower()
    # Normalize unicode
    s = unicodedata.normalize("NFKD", s)
    # Remove accents
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def minmax(series: pd.Series, fill_constant: float = 0.5) -> pd.Series:
    """
    Safe min-max scaling to [0, 1] range.
    
    Args:
        series: Numeric series to scale
        fill_constant: Value to use if series is constant (min == max)
        
    Returns:
        Scaled series
    """
    if series.empty:
        return series
    
    s = pd.to_numeric(series, errors="coerce")
    s_min = s.min()
    s_max = s.max()
    
    if pd.isna(s_min) or pd.isna(s_max) or s_min == s_max:
        return pd.Series([fill_constant] * len(s), index=s.index)
    
    return (s - s_min) / (s_max - s_min)


def attach_geo(
    df: pd.DataFrame,
    dim_context_geo: pd.DataFrame,
    context_col: str = "context_id",
) -> pd.DataFrame:
    """
    Join a DataFrame to DIM_CONTEXT_GEO to add geographic columns.
    
    Args:
        df: Source DataFrame
        dim_context_geo: Dimension table with context_id, grupo, paisaje, admin0, fecha_iso
        context_col: Name of context column in df
        
    Returns:
        DataFrame with geographic columns added
    """
    if df.empty or dim_context_geo.empty:
        return df
    
    if context_col not in df.columns:
        return df
    
    # Ensure context_id types match
    df = df.copy()
    df[context_col] = df[context_col].astype(str)
    
    dim = dim_context_geo.copy()
    if context_col in dim.columns:
        dim[context_col] = dim[context_col].astype(str)
    
    # Get geographic columns
    geo_cols = [c for c in ["grupo", "paisaje", "admin0", "fecha_iso"] if c in dim.columns]
    if not geo_cols:
        return df
    
    # Left join
    merge_cols = [context_col] + geo_cols
    dim_subset = dim[merge_cols].drop_duplicates(subset=[context_col])
    
    result = df.merge(dim_subset, on=context_col, how="left")
    return result


def pick_first_existing_col(
    df: pd.DataFrame,
    candidates: List[str],
) -> Optional[str]:
    """
    Find the first column from candidates that exists in the DataFrame.
    
    Args:
        df: DataFrame to search
        candidates: List of candidate column names
        
    Returns:
        First matching column name, or None if none found
    """
    if df.empty:
        return None
    
    # Normalize column names for comparison
    df_cols_lower = {c.lower(): c for c in df.columns}
    
    for candidate in candidates:
        candidate_lower = candidate.lower()
        if candidate_lower in df_cols_lower:
            return df_cols_lower[candidate_lower]
    
    return None


def coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Convert specified columns to numeric, coercing errors to NaN.
    
    Args:
        df: DataFrame to modify
        cols: Column names to convert
        
    Returns:
        DataFrame with converted columns
    """
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def normalize_rel_type(
    rel: Any,
    rel_type_map: Dict[str, List[str]],
) -> str:
    """
    Normalize a relation type string to canonical form.
    
    Args:
        rel: Raw relation type value
        rel_type_map: Mapping of canonical type -> list of variants
        
    Returns:
        Canonical relation type ('colabora', 'conflicto', or 'other')
    """
    rel_norm = canonical_text(rel)
    
    for canonical, variants in rel_type_map.items():
        for variant in variants:
            if variant.lower() in rel_norm or rel_norm in variant.lower():
                return canonical
    
    return "other"


def safe_group_agg(
    df: pd.DataFrame,
    group_cols: List[str],
    agg_spec: Dict[str, Any],
) -> pd.DataFrame:
    """
    Safely aggregate DataFrame by groups, handling missing columns.
    
    Args:
        df: DataFrame to aggregate
        group_cols: Columns to group by
        agg_spec: Aggregation specification (col -> agg_func or list of funcs)
        
    Returns:
        Aggregated DataFrame
    """
    if df.empty:
        return pd.DataFrame()
    
    # Filter to existing columns
    valid_group_cols = [c for c in group_cols if c in df.columns]
    valid_agg_spec = {c: spec for c, spec in agg_spec.items() if c in df.columns}
    
    if not valid_group_cols:
        return pd.DataFrame()
    
    if not valid_agg_spec:
        # Just count if no agg columns
        return df.groupby(valid_group_cols, as_index=False).size().rename(columns={"size": "n_records"})
    
    result = df.groupby(valid_group_cols, as_index=False).agg(valid_agg_spec)
    
    # Flatten multi-level column names if needed
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = ["_".join(filter(None, map(str, col))) for col in result.columns]
    
    return result


def explode_text_to_items(
    value: Any,
    delimiters: str = r"[,;|/\n]",
    min_len: int = 2,
) -> List[str]:
    """
    Split a text value by delimiters, strip, deduplicate.
    
    Args:
        value: Text value to split
        delimiters: Regex pattern for delimiters
        min_len: Minimum length for items to keep
        
    Returns:
        List of unique, cleaned items
    """
    if pd.isna(value):
        return []
    
    text = str(value).strip()
    if not text:
        return []
    
    # Split by delimiters
    items = re.split(delimiters, text)
    
    # Clean and filter
    cleaned = []
    seen = set()
    for item in items:
        item_clean = item.strip()
        item_lower = item_clean.lower()
        if len(item_clean) >= min_len and item_lower not in seen:
            cleaned.append(item_clean)
            seen.add(item_lower)
    
    return cleaned


def frequency_table(
    series: pd.Series,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Create a frequency table from a series of values.
    
    Args:
        series: Series of values (can include lists)
        top_n: Maximum number of items to return
        
    Returns:
        DataFrame with 'item' and 'count' columns
    """
    # Flatten if series contains lists
    items = []
    for val in series.dropna():
        if isinstance(val, list):
            items.extend(val)
        else:
            items.append(val)
    
    if not items:
        return pd.DataFrame(columns=["item", "count"])
    
    freq = pd.Series(items).value_counts().reset_index()
    freq.columns = ["item", "count"]
    
    return freq.head(top_n)
