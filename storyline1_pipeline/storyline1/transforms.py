#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storyline 1 Transforms Module
Data transformation utilities for joining, scaling, and parsing.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def attach_geo(
    df: pd.DataFrame,
    dim_context_geo: pd.DataFrame,
    on: str = "context_id",
) -> pd.DataFrame:
    """
    Attach geographic context columns (admin0, paisaje, grupo, fecha_iso) to a DataFrame.
    
    Args:
        df: Source DataFrame with context_id column
        dim_context_geo: Dimensional table with context_id, geo_id, admin0, paisaje, grupo, fecha_iso
        on: Column to join on (default: context_id)
        
    Returns:
        DataFrame with geographic columns attached
    """
    if df.empty:
        return df
    
    if on not in df.columns:
        logger.warning(f"Column '{on}' not found in DataFrame, cannot attach geo")
        return df
    
    geo_cols = ["admin0", "paisaje", "grupo", "fecha_iso"]
    existing_cols = [c for c in geo_cols if c in df.columns]
    
    # Drop existing geo columns to avoid duplicates
    if existing_cols:
        df = df.drop(columns=existing_cols)
    
    # Select only needed columns from dim table
    dim_cols = [on] + [c for c in geo_cols if c in dim_context_geo.columns]
    dim_subset = dim_context_geo[dim_cols].drop_duplicates()
    
    result = df.merge(dim_subset, on=on, how="left")
    logger.debug(f"Attached geo columns to {len(result)} rows")
    
    return result


def minmax(series: pd.Series, feature_range: tuple = (0, 1)) -> pd.Series:
    """
    Min-max normalize a series to the specified range.
    Handles constant series gracefully by returning 0.5 (midpoint).
    
    Args:
        series: Numeric series to normalize
        feature_range: Tuple of (min, max) for output range
        
    Returns:
        Normalized series
    """
    series = pd.to_numeric(series, errors="coerce")
    min_val = series.min()
    max_val = series.max()
    
    if pd.isna(min_val) or pd.isna(max_val):
        return pd.Series([np.nan] * len(series), index=series.index)
    
    if min_val == max_val:
        # Constant series: return midpoint
        midpoint = (feature_range[0] + feature_range[1]) / 2
        return pd.Series([midpoint] * len(series), index=series.index)
    
    # Standard min-max scaling
    scaled = (series - min_val) / (max_val - min_val)
    scaled = scaled * (feature_range[1] - feature_range[0]) + feature_range[0]
    
    return scaled


def parse_range_to_midpoint(value: Any) -> Optional[float]:
    """
    Parse a range string (e.g., "40-60") to its midpoint.
    
    Args:
        value: Value to parse (string like "0-20", "20-40", etc.)
        
    Returns:
        Midpoint as float, or None if cannot parse
        
    Examples:
        "0-20" -> 10.0
        "20-40" -> 30.0
        "40-60" -> 50.0
        "60-80" -> 70.0
        "80-100" -> 90.0
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    
    # Try to parse as "a-b" format
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*[-–—]\s*(-?\d+(?:\.\d+)?)\s*$", s)
    if match:
        try:
            a = float(match.group(1))
            b = float(match.group(2))
            return (a + b) / 2
        except ValueError:
            pass
    
    # Try to parse as single number
    try:
        return float(s)
    except ValueError:
        pass
    
    return None


def compute_response_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute numeric response values from response_raw.
    
    If response_numeric is missing or NaN, fill by parsing response_raw:
    - If "a-b" format with integers -> mean(a, b)
    - Else try float(response_raw)
    
    Also computes response_0_1 = response_numeric / 100 when response_numeric is in [0, 100].
    
    Args:
        df: DataFrame with response_raw and optionally response_numeric columns
        
    Returns:
        DataFrame with response_numeric and response_0_1 columns
    """
    result = df.copy()
    
    # Ensure response_numeric column exists
    if "response_numeric" not in result.columns:
        result["response_numeric"] = np.nan
    
    # Convert to numeric, coercing errors
    result["response_numeric"] = pd.to_numeric(result["response_numeric"], errors="coerce")
    
    # Fill missing values by parsing response_raw
    if "response_raw" in result.columns:
        mask = result["response_numeric"].isna()
        result.loc[mask, "response_numeric"] = result.loc[mask, "response_raw"].apply(
            parse_range_to_midpoint
        )
    
    # Compute 0-1 scale (assuming response_numeric is in 0-100 range)
    result["response_0_1"] = result["response_numeric"].apply(
        lambda x: x / 100 if pd.notna(x) and 0 <= x <= 100 else np.nan
    )
    
    return result


def safe_group_agg(
    df: pd.DataFrame,
    group_cols: List[str],
    agg_spec: Dict[str, Union[str, List[str], tuple]],
) -> pd.DataFrame:
    """
    Safely aggregate a DataFrame by group columns.
    Handles empty DataFrames and missing columns gracefully.
    
    Args:
        df: DataFrame to aggregate
        group_cols: Columns to group by
        agg_spec: Aggregation specification dict (column -> agg_func)
        
    Returns:
        Aggregated DataFrame, or empty DataFrame if input is empty
    """
    if df.empty:
        # Return empty DataFrame with expected columns
        result_cols = list(group_cols) + list(agg_spec.keys())
        return pd.DataFrame(columns=result_cols)
    
    # Filter to only existing columns
    valid_group_cols = [c for c in group_cols if c in df.columns]
    valid_agg_spec = {k: v for k, v in agg_spec.items() if k in df.columns}
    
    if not valid_group_cols or not valid_agg_spec:
        logger.warning("No valid columns for aggregation")
        return pd.DataFrame()
    
    try:
        result = df.groupby(valid_group_cols, dropna=False).agg(valid_agg_spec).reset_index()
        
        # Flatten MultiIndex columns if present
        if isinstance(result.columns, pd.MultiIndex):
            result.columns = ["_".join(col).strip("_") for col in result.columns.values]
        
        return result
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return pd.DataFrame()


def coerce_numeric_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Coerce specified columns to numeric type.
    
    Args:
        df: DataFrame to process
        columns: List of column names to convert
        
    Returns:
        DataFrame with numeric columns
    """
    result = df.copy()
    for col in columns:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")
    return result


def safe_merge(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: Union[str, List[str]],
    how: str = "left",
    suffixes: tuple = ("", "_y"),
) -> pd.DataFrame:
    """
    Safely merge two DataFrames, handling empty DataFrames.
    
    Args:
        left: Left DataFrame
        right: Right DataFrame
        on: Column(s) to join on
        how: Join type
        suffixes: Suffixes for overlapping columns
        
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
        logger.warning(f"Join columns {on_list} not all present in left DataFrame")
        return left
    if not all(c in right.columns for c in on_list):
        logger.warning(f"Join columns {on_list} not all present in right DataFrame")
        return left
    
    return left.merge(right, on=on, how=how, suffixes=suffixes)
