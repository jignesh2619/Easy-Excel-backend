"""
Shared utilities for dataframe operations
"""

from typing import Any, List, Optional
import pandas as pd


def infer_column_type(series: pd.Series) -> str:
    """
    Infer the data type of a pandas Series
    
    Returns:
        One of: 'numeric', 'datetime', 'text', 'boolean', 'mixed'
    """
    # Check if all values are numeric
    numeric_count = pd.to_numeric(series, errors='coerce').notna().sum()
    if numeric_count == len(series):
        return 'numeric'
    
    # Check if all values are datetime
    datetime_count = pd.to_datetime(series, errors='coerce').notna().sum()
    if datetime_count == len(series):
        return 'datetime'
    
    # Check if all values are boolean
    if series.dtype == 'bool' or series.dtype.name == 'bool':
        return 'boolean'
    
    # Check if mostly numeric (mixed)
    if numeric_count > len(series) * 0.8:
        return 'mixed'
    
    return 'text'


def safe_convert_numeric(series: pd.Series) -> pd.Series:
    """Safely convert series to numeric, keeping non-numeric as NaN"""
    return pd.to_numeric(series, errors='coerce')


def safe_convert_datetime(series: pd.Series) -> pd.Series:
    """Safely convert series to datetime, keeping non-datetime as NaT"""
    return pd.to_datetime(series, errors='coerce')


def normalize_column_name(name: str) -> str:
    """Normalize column name (strip, lowercase, replace spaces)"""
    return str(name).strip().lower().replace(' ', '_')


def detect_duplicates(series: pd.Series) -> pd.Series:
    """Detect duplicate values in a series"""
    return series.duplicated(keep=False)

