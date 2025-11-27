"""
Currency Cleaning Functions

Extract numeric values from currency strings and normalize currency formats.
"""

import pandas as pd
import numpy as np
import re
from typing import Union, List, Optional


class CurrencyCleaner:
    """Handles currency parsing and cleaning"""
    
    # Common currency symbols
    CURRENCY_SYMBOLS = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '₹': 'INR',
        'USD': 'USD',
        'EUR': 'EUR',
        'GBP': 'GBP',
        'JPY': 'JPY',
        'INR': 'INR',
    }
    
    @staticmethod
    def extract_numeric(series: pd.Series) -> pd.Series:
        """
        Extract numeric values from currency strings
        
        Examples:
            "$1,234.56" -> 1234.56
            "€ 500" -> 500.0
            "USD 1,000" -> 1000.0
            "(500)" -> -500.0  (negative in parentheses)
        
        Args:
            series: Series containing currency strings
        
        Returns:
            Series with numeric values
        """
        def extract_value(value):
            if pd.isna(value):
                return np.nan
            
            value_str = str(value)
            
            # Check for negative in parentheses
            is_negative = value_str.strip().startswith('(') and value_str.strip().endswith(')')
            
            # Remove currency symbols, commas, spaces
            cleaned = re.sub(r'[^\d.]', '', value_str)
            
            try:
                numeric_value = float(cleaned) if cleaned else np.nan
                if is_negative:
                    numeric_value = -abs(numeric_value)
                return numeric_value
            except:
                return np.nan
        
        return series.apply(extract_value)
    
    @staticmethod
    def normalize_currency(df: pd.DataFrame, columns: Union[str, List[str]], 
                           currency_symbol: str = '$', decimal_places: int = 2) -> pd.DataFrame:
        """
        Normalize currency columns to numeric values
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to normalize
            currency_symbol: Currency symbol to use
            decimal_places: Number of decimal places
        
        Returns:
            DataFrame with normalized currency values
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                # Extract numeric values
                df[col] = CurrencyCleaner.extract_numeric(df[col])
                # Round to specified decimal places
                df[col] = df[col].round(decimal_places)
        
        return df
    
    @staticmethod
    def format_as_currency(series: pd.Series, currency_symbol: str = '$', 
                          decimal_places: int = 2) -> pd.Series:
        """
        Format numeric values as currency strings
        
        Args:
            series: Series with numeric values
            currency_symbol: Currency symbol to use
            decimal_places: Number of decimal places
        
        Returns:
            Series with formatted currency strings
        """
        def format_value(value):
            if pd.isna(value):
                return ''
            
            formatted = f"{value:,.{decimal_places}f}"
            return f"{currency_symbol}{formatted}"
        
        return series.apply(format_value)
    
    @staticmethod
    def detect_currency_type(series: pd.Series) -> Optional[str]:
        """
        Detect currency type from a series
        
        Args:
            series: Series containing currency strings
        
        Returns:
            Currency code (USD, EUR, etc.) or None
        """
        sample_values = series.dropna().head(10).astype(str)
        
        for value in sample_values:
            for symbol, code in CurrencyCleaner.CURRENCY_SYMBOLS.items():
                if symbol in value:
                    return code
        
        return None

