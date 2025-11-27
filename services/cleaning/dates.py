"""
Date Cleaning Functions

Robust date parsing and normalization for various date formats.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Union
from datetime import datetime
import re


class DateCleaner:
    """Handles date parsing and cleaning"""
    
    # Common date formats to try
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%Y.%m.%d',
        '%d.%m.%Y',
        '%m.%d.%Y',
        '%B %d, %Y',
        '%d %B %Y',
        '%b %d, %Y',
        '%d %b %Y',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
    ]
    
    @staticmethod
    def parse_dates(series: pd.Series, format: Optional[str] = None, errors: str = 'coerce') -> pd.Series:
        """
        Parse dates from a series with multiple format attempts
        
        Args:
            series: Series containing date strings
            format: Optional specific format to use
            errors: How to handle errors ('coerce', 'raise', 'ignore')
        
        Returns:
            Series with parsed datetime values
        """
        if format:
            return pd.to_datetime(series, format=format, errors=errors)
        
        # Try multiple formats
        result = pd.Series([None] * len(series), dtype='datetime64[ns]')
        
        for fmt in DateCleaner.DATE_FORMATS:
            try:
                parsed = pd.to_datetime(series, format=fmt, errors='coerce')
                # Fill in values that were successfully parsed
                mask = parsed.notna() & result.isna()
                result[mask] = parsed[mask]
            except:
                continue
        
        # If still have unparsed values, try pandas auto-detection
        if result.isna().any():
            remaining = series[result.isna()]
            if len(remaining) > 0:
                auto_parsed = pd.to_datetime(remaining, errors='coerce')
                result[result.isna()] = auto_parsed
        
        return result
    
    @staticmethod
    def normalize_dates(df: pd.DataFrame, columns: Union[str, List[str]], 
                       target_format: str = '%Y-%m-%d') -> pd.DataFrame:
        """
        Normalize date columns to a standard format
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to normalize
            target_format: Target date format string
        
        Returns:
            DataFrame with normalized dates
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                # Parse dates
                df[col] = DateCleaner.parse_dates(df[col])
                # Format to target format (as string)
                df[col] = df[col].dt.strftime(target_format)
        
        return df
    
    @staticmethod
    def extract_date_components(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """
        Extract year, month, day from a date column
        
        Args:
            df: DataFrame
            date_column: Name of date column
        
        Returns:
            DataFrame with added year, month, day columns
        """
        df = df.copy()
        
        if date_column not in df.columns:
            return df
        
        # Parse dates first
        dates = DateCleaner.parse_dates(df[date_column])
        
        df[f'{date_column}_year'] = dates.dt.year
        df[f'{date_column}_month'] = dates.dt.month
        df[f'{date_column}_day'] = dates.dt.day
        df[f'{date_column}_weekday'] = dates.dt.day_name()
        
        return df
    
    @staticmethod
    def fix_invalid_dates(df: pd.DataFrame, columns: Union[str, List[str]], 
                         strategy: str = 'drop') -> pd.DataFrame:
        """
        Fix or remove invalid dates
        
        Args:
            df: DataFrame
            columns: Column name(s) to fix
            strategy: 'drop' to remove rows, 'fill' to fill with NaT, 'coerce' to set to NaT
        
        Returns:
            DataFrame with fixed dates
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                dates = DateCleaner.parse_dates(df[col])
                
                if strategy == 'drop':
                    df = df[dates.notna()]
                elif strategy == 'fill':
                    df[col] = dates.fillna(pd.NaT)
                elif strategy == 'coerce':
                    df[col] = dates
        
        return df

