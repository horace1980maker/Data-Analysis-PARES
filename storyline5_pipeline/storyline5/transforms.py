"""
Transform utilities for Storyline 5.
Shared data manipulation functions.
"""

import hashlib
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
    df_cols_lower = {str(c).lower(): c for c in df.columns}
    
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


def parse_range_to_midpoint(value: Any) -> float:
    """
    Parse a range string like "40-60" to its midpoint (50).
    Also handles plain numbers.
    
    Args:
        value: String like "40-60" or numeric value
        
    Returns:
        Midpoint as float, or NaN if parsing fails
    """
    if pd.isna(value):
        return np.nan
    
    # Try direct numeric conversion first
    try:
        return float(value)
    except (ValueError, TypeError):
        pass
    
    # Try range pattern
    s = str(value).strip()
    match = re.match(r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)", s)
    if match:
        low = float(match.group(1))
        high = float(match.group(2))
        return (low + high) / 2
    
    return np.nan


def compute_response_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add response_numeric and response_0_1 columns to a survey response DataFrame.
    Assumes 'response' column exists with values like 1-5 scale or similar.
    
    Args:
        df: DataFrame with 'response' column
        
    Returns:
        DataFrame with response_numeric and response_0_1 added
    """
    df = df.copy()
    
    if "response" not in df.columns:
        df["response_numeric"] = np.nan
        df["response_0_1"] = np.nan
        return df
    
    # Convert to numeric
    df["response_numeric"] = df["response"].apply(parse_range_to_midpoint)
    
    # Normalize to 0-1 (assuming 1-5 scale is common)
    df["response_0_1"] = minmax(df["response_numeric"], fill_constant=0.5)
    
    return df


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


def stable_hash_id(*fields) -> str:
    """
    Generate a deterministic short ID from input fields.
    Uses SHA1 hash of joined canonical text of all fields.
    
    Args:
        *fields: Any number of fields to hash
        
    Returns:
        8-character hex string
    """
    # Canonicalize and join
    parts = [canonical_text(f) for f in fields]
    combined = "|".join(parts)
    
    # SHA1 hash
    h = hashlib.sha1(combined.encode("utf-8")).hexdigest()
    
    # Return first 8 chars for readability
    return h[:8]


def quantile_tier(
    scores: pd.Series,
    tiers_config: Dict[str, float],
) -> pd.Series:
    """
    Assign tiers (Do now, Do next, Do later) by quantiles of scores.
    
    Args:
        scores: Series of numeric scores (higher = better)
        tiers_config: Dict with do_now_top_pct, do_next_mid_pct, do_later_low_pct
        
    Returns:
        Series of tier labels
    """
    if scores.empty:
        return pd.Series(dtype=str)
    
    # Get thresholds
    do_now_pct = tiers_config.get("do_now_top_pct", 0.33)
    
    # Calculate quantile thresholds
    q_high = scores.quantile(1 - do_now_pct)
    q_low = scores.quantile(do_now_pct)
    
    def assign_tier(score):
        if pd.isna(score):
            return "Do later"
        if score >= q_high:
            return "Do now"
        elif score >= q_low:
            return "Do next"
        else:
            return "Do later"
    
    return scores.apply(assign_tier)


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


def join_as_text(items: List[Any], sep: str = ", ", max_items: int = 5) -> str:
    """
    Join a list of items into a text string, limiting to max_items.
    
    Args:
        items: List of items
        sep: Separator string
        max_items: Maximum items to include
        
    Returns:
        Joined string, with "..." if truncated
    """
    if not items:
        return ""
    
    str_items = [str(x) for x in items if pd.notna(x)]
    
    if len(str_items) > max_items:
        return sep.join(str_items[:max_items]) + "..."
    else:
        return sep.join(str_items)


def normalize_within_group(
    df: pd.DataFrame,
    value_col: str,
    group_col: Optional[str] = None,
    output_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Normalize a value column within groups (or overall if no group).
    
    Args:
        df: DataFrame
        value_col: Column to normalize
        group_col: Optional grouping column
        output_col: Output column name (defaults to {value_col}_norm)
        
    Returns:
        DataFrame with normalized column added
    """
    df = df.copy()
    output_col = output_col or f"{value_col}_norm"
    
    if value_col not in df.columns:
        df[output_col] = 0.5
        return df
    
    if group_col and group_col in df.columns:
        # Normalize within each group
        df[output_col] = df.groupby(group_col)[value_col].transform(lambda x: minmax(x))
    else:
        # Normalize overall
        df[output_col] = minmax(df[value_col])
    
    return df
