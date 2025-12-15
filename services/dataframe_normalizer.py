"""
Unified DataFrame Normalization

Single source of truth for normalizing DataFrame structure after operations.
This replaces multiple validation layers scattered across the codebase.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unified function to normalize DataFrame structure.
    
    Ensures:
    1. All columns are proper Series (not nested structures)
    2. All cell values are scalars (not arrays, DataFrames, or Series)
    3. Index is reset to RangeIndex
    
    Args:
        df: DataFrame to normalize
        
    Returns:
        Normalized DataFrame
    """
    if df is None or df.empty:
        return df
    
    # Work on copy to avoid side effects
    df = df.copy()
    
    # 1. Ensure all columns are Series
    for col in df.columns:
        if not isinstance(df[col], pd.Series):
            logger.warning(f"Column '{col}' is not a Series, converting...")
            df[col] = pd.Series(df[col], index=df.index, dtype=object)
    
    # 2. Convert all non-scalar values to scalars
    for col in df.columns:
        for idx in df.index:
            value = df.at[idx, col]
            
            # Skip if already scalar or None/NaN
            if value is None or pd.isna(value):
                continue
            
            # Handle non-scalar types
            if isinstance(value, pd.Series):
                # Series in cell - take first value
                if len(value) > 0:
                    df.at[idx, col] = value.iloc[0] if not pd.isna(value.iloc[0]) else None
                else:
                    df.at[idx, col] = None
            elif isinstance(value, pd.DataFrame):
                # DataFrame in cell - convert to string
                logger.warning(f"Cell ({idx}, {col}) contains DataFrame, converting to string")
                df.at[idx, col] = str(value)
            elif isinstance(value, np.ndarray):
                # Numpy array - flatten 1D, convert multi-D to string
                if value.ndim == 1 and len(value) > 0:
                    df.at[idx, col] = value[0]
                else:
                    logger.warning(f"Cell ({idx}, {col}) contains ndarray of shape {value.shape}, converting to string")
                    df.at[idx, col] = str(value)
    
    # 3. Reset index to RangeIndex
    if not df.index.equals(pd.RangeIndex(len(df))):
        df = df.reset_index(drop=True)
    
    return df

