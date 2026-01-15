#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 2 Transforms Module
Data transformation utilities.
"""

import logging
import re
from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd

from .config import (
    ADMIN0_COL,
    CONTEXT_ID_COL,
    FECHA_COL,
    GEO_ID_COL,
    GRUPO_COL,
    PAISAJE_COL,
    SPANISH_MONTHS,
)

logger = logging.getLogger(__name__)


def canonical_text(x: Any) -> str:
    """
    Normalize a string value for consistent matching.
    
    Args:
        x: Input value (may be None, NaN, or string)
        
    Returns:
        Normalized lowercase stripped string, or empty string for null values
    """
    if pd.isna(x) or x is None:
        return ""
    return str(x).strip().lower()


def minmax(series: pd.Series, fill_constant: float = 0.5) -> pd.Series:
    """
    Apply min-max normalization to a series.
    
    Args:
        series: Input numeric series
        fill_constant: Value to use when series is constant (default 0.5)
        
    Returns:
        Normalized series with values in [0, 1]
    """
    s = pd.to_numeric(series, errors="coerce")
    
    if s.isna().all():
        return pd.Series([fill_constant] * len(s), index=s.index)
    
    min_val = s.min()
    max_val = s.max()
    
    if min_val == max_val:
        return pd.Series([fill_constant] * len(s), index=s.index)
    
    return (s - min_val) / (max_val - min_val)


def attach_geo(
    df: pd.DataFrame,
    dim_context_geo: pd.DataFrame,
    on: str = "context_id",
) -> pd.DataFrame:
    """
    Join a DataFrame to dimensional context/geo table.
    
    Args:
        df: Input DataFrame with context_id column
        dim_context_geo: Dimensional table with geo columns
        on: Join column name (default: context_id)
        
    Returns:
        DataFrame with geo columns attached (admin0, paisaje, grupo, fecha_iso)
    """
    if df.empty:
        return df
    
    if on not in df.columns:
        logger.debug(f"Column '{on}' not in DataFrame, skipping geo attach")
        return df
    
    if dim_context_geo.empty:
        logger.debug("Empty dim_context_geo, skipping geo attach")
        return df
    
    # Select columns to join
    geo_cols = [on]
    for col in [ADMIN0_COL, PAISAJE_COL, GRUPO_COL, FECHA_COL, GEO_ID_COL]:
        if col in dim_context_geo.columns and col not in df.columns:
            geo_cols.append(col)
    
    if len(geo_cols) <= 1:
        return df
    
    geo_subset = dim_context_geo[geo_cols].drop_duplicates()
    
    result = df.merge(geo_subset, on=on, how="left")
    logger.debug(f"Attached geo: {len(result)} rows with {geo_cols}")
    
    return result


def pick_first_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Pick the first column name that exists in a DataFrame.
    
    Args:
        df: Input DataFrame
        candidates: List of candidate column names in priority order
        
    Returns:
        First matching column name, or None if none exist
    """
    for col in candidates:
        if col in df.columns:
            return col
    return None


def coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Coerce columns to numeric, replacing non-numeric values with NaN.
    
    Args:
        df: Input DataFrame
        cols: List of column names to coerce
        
    Returns:
        DataFrame with specified columns as numeric
    """
    result = df.copy()
    for col in cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")
    return result


def safe_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: Union[str, List[str]],
    how: str = "left",
    suffixes: tuple = ("", "_right"),
) -> pd.DataFrame:
    """
    Safely merge two DataFrames, handling empty cases.
    
    Args:
        left: Left DataFrame
        right: Right DataFrame
        on: Join column(s)
        how: Join type (default: left)
        suffixes: Column name suffixes for conflicts
        
    Returns:
        Merged DataFrame
    """
    if left.empty:
        return left
    if right.empty:
        return left
    
    # Ensure join columns exist
    on_list = [on] if isinstance(on, str) else on
    if not all(c in left.columns for c in on_list):
        logger.warning(f"Join columns {on_list} not all in left DataFrame")
        return left
    if not all(c in right.columns for c in on_list):
        logger.warning(f"Join columns {on_list} not all in right DataFrame")
        return left
    
    return left.merge(right, on=on, how=how, suffixes=suffixes)


def safe_group_agg(
    df: pd.DataFrame,
    group_cols: List[str],
    agg_spec: dict,
) -> pd.DataFrame:
    """
    Safely perform a groupby aggregation, handling missing columns.
    
    Args:
        df: Input DataFrame
        group_cols: Columns to group by
        agg_spec: Aggregation specification {col: func or [funcs]}
        
    Returns:
        Aggregated DataFrame
    """
    if df.empty:
        return pd.DataFrame()
    
    # Filter to existing group columns
    existing_group_cols = [c for c in group_cols if c in df.columns]
    if not existing_group_cols:
        logger.warning(f"No group columns found in DataFrame: {group_cols}")
        return pd.DataFrame()
    
    # Filter agg_spec to existing columns
    filtered_agg = {k: v for k, v in agg_spec.items() if k in df.columns}
    if not filtered_agg:
        logger.warning(f"No aggregation columns found in DataFrame")
        return pd.DataFrame()
    
    try:
        result = df.groupby(existing_group_cols, dropna=False).agg(filtered_agg).reset_index()
        return result
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return pd.DataFrame()


def parse_months_to_numbers(value: Any) -> List[int]:
    """
    Parse a month string into a list of month numbers (1-12).
    
    Handles formats like:
    - "enero, febrero"
    - "ene; feb; mar"
    - "1, 2, 3"
    - "Jan, Feb"
    
    Args:
        value: Input value (may be string, number, or None)
        
    Returns:
        Sorted list of unique month integers (1-12)
    """
    if pd.isna(value) or value is None:
        return []
    
    value_str = str(value).strip().lower()
    if not value_str:
        return []
    
    months = set()
    
    # Split by common delimiters
    parts = re.split(r'[,;/\-\s]+', value_str)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Try as a number first
        try:
            num = int(float(part))
            if 1 <= num <= 12:
                months.add(num)
            continue
        except ValueError:
            pass
        
        # Try as month name
        if part in SPANISH_MONTHS:
            months.add(SPANISH_MONTHS[part])
    
    return sorted(months)


def count_months(value: Any) -> int:
    """
    Count the number of months in a month string.
    
    Args:
        value: Month string value
        
    Returns:
        Number of unique months found
    """
    return len(parse_months_to_numbers(value))


def compute_seasonality_fragility(value: Any) -> float:
    """
    Compute seasonality fragility as fraction of year.
    
    Args:
        value: Month string (mes_falta) representing months without the service
        
    Returns:
        Fragility score (0-1), where 1 = all 12 months lacking
    """
    n_months = count_months(value)
    return n_months / 12.0


def explode_months(
    df: pd.DataFrame,
    src_col: str,
    out_col: str = "month_num",
) -> pd.DataFrame:
    """
    Explode a month string column into multiple rows (one per month).
    
    Args:
        df: Input DataFrame
        src_col: Column containing month strings
        out_col: Name for the output month number column
        
    Returns:
        DataFrame with one row per month
    """
    if df.empty or src_col not in df.columns:
        return df
    
    result = df.copy()
    result["_months_list"] = result[src_col].apply(parse_months_to_numbers)
    result = result.explode("_months_list")
    result[out_col] = result["_months_list"]
    result = result.drop(columns=["_months_list"])
    
    return result


def extract_numeric_from_text(value: Any) -> Optional[float]:
    """
    Extract a numeric value from text that may contain numbers.
    
    Handles formats like:
    - "100"
    - "100 users"
    - "approx. 50"
    - "50-100" -> takes first number
    
    Args:
        value: Input value
        
    Returns:
        First numeric value found, or None
    """
    if pd.isna(value) or value is None:
        return None
    
    # If already numeric
    if isinstance(value, (int, float)):
        return float(value)
    
    value_str = str(value).strip()
    
    # Find all numbers
    numbers = re.findall(r'\d+(?:\.\d+)?', value_str)
    if numbers:
        return float(numbers[0])
    
    return None


def normalize_within_groups(
    df: pd.DataFrame,
    value_col: str,
    group_col: str,
    out_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Apply min-max normalization within each group.
    
    Args:
        df: Input DataFrame
        value_col: Column to normalize
        group_col: Column defining groups
        out_col: Output column name (default: {value_col}_norm)
        
    Returns:
        DataFrame with normalized column added
    """
    if out_col is None:
        out_col = f"{value_col}_norm"
    
    if df.empty or value_col not in df.columns:
        return df
    
    result = df.copy()
    
    if group_col in result.columns:
        result[out_col] = result.groupby(group_col)[value_col].transform(
            lambda x: minmax(x)
        )
    else:
        result[out_col] = minmax(result[value_col])
    
    return result
