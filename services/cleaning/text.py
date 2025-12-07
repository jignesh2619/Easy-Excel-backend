"""
Text Cleaning Functions

Clean and normalize text data including whitespace, case, and special characters.
"""

import pandas as pd
import re
from typing import Union, List, Optional


class TextCleaner:
    """Handles text cleaning and normalization"""
    
    @staticmethod
    def trim_whitespace(df: pd.DataFrame, columns: Union[str, List[str]]) -> pd.DataFrame:
        """
        Remove leading and trailing whitespace from text columns
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to trim
        
        Returns:
            DataFrame with trimmed text
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    @staticmethod
    def normalize_case(df: pd.DataFrame, columns: Union[str, List[str]], 
                       case: str = 'lower') -> pd.DataFrame:
        """
        Normalize text case
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to normalize
            case: 'lower', 'upper', 'title', 'sentence'
        
        Returns:
            DataFrame with normalized case
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                if case == 'lower':
                    df[col] = df[col].astype(str).str.lower()
                elif case == 'upper':
                    df[col] = df[col].astype(str).str.upper()
                elif case == 'title':
                    df[col] = df[col].astype(str).str.title()
                elif case == 'sentence':
                    df[col] = df[col].astype(str).str.capitalize()
        
        return df
    
    @staticmethod
    def remove_special_characters(df: pd.DataFrame, columns: Union[str, List[str]], 
                                 keep: Optional[str] = None) -> pd.DataFrame:
        """
        Remove special characters from text columns
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to clean
            keep: Optional regex pattern of characters to keep (default: alphanumeric and spaces)
        
        Returns:
            DataFrame with cleaned text
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        if keep is None or keep == '':
            # Default: keep alphanumeric, spaces, and common punctuation
            pattern = r'[^a-zA-Z0-9\s.,!?;:\-()]'
        else:
            # Escape special regex characters in keep pattern
            try:
                # Test if keep is a valid regex pattern
                re.compile(keep)
                pattern = f'[^{keep}]'
            except re.error:
                # If invalid regex, escape special characters
                escaped_keep = re.escape(keep)
                pattern = f'[^{escaped_keep}]'
        
        for col in columns:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.replace(pattern, '', regex=True)
                except re.error:
                    # Fallback to non-regex replace if pattern is invalid
                    df[col] = df[col].astype(str).str.replace(pattern, '', regex=False)
        
        return df
    
    @staticmethod
    def remove_extra_spaces(df: pd.DataFrame, columns: Union[str, List[str]]) -> pd.DataFrame:
        """
        Remove extra whitespace (multiple spaces to single space)
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to clean
        
        Returns:
            DataFrame with normalized spacing
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
                except re.error:
                    # Fallback if regex fails
                    df[col] = df[col].astype(str).str.replace('  ', ' ', regex=False)
                    while df[col].str.contains('  ', regex=False).any():
                        df[col] = df[col].str.replace('  ', ' ', regex=False)
                    df[col] = df[col].str.strip()
        
        return df
    
    @staticmethod
    def replace_text(df: pd.DataFrame, columns: Union[str, List[str]], 
                    old_text: str, new_text: str, case_sensitive: bool = False) -> pd.DataFrame:
        """
        Replace text in columns
        
        Args:
            df: DataFrame to clean
            columns: Column name(s) to modify
            old_text: Text to replace
            new_text: Replacement text
            case_sensitive: Whether replacement is case sensitive
        
        Returns:
            DataFrame with replaced text
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in df.columns:
                try:
                    if case_sensitive:
                        df[col] = df[col].astype(str).str.replace(old_text, new_text, regex=False)
                    else:
                        df[col] = df[col].astype(str).str.replace(old_text, new_text, case=False, regex=False)
                except Exception:
                    # Fallback: use simple string replace
                    df[col] = df[col].astype(str).str.replace(old_text, new_text, regex=False)
        
        return df
    
    @staticmethod
    def split_column(df: pd.DataFrame, column: str, separator: str, 
                     new_column_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Split a column into multiple columns
        
        Args:
            df: DataFrame
            column: Column to split
            separator: Separator string
            new_column_names: Optional names for new columns
        
        Returns:
            DataFrame with split columns
        """
        df = df.copy()
        
        if column not in df.columns:
            return df
        
        split_df = df[column].astype(str).str.split(separator, expand=True)
        
        if new_column_names:
            split_df.columns = new_column_names[:len(split_df.columns)]
        else:
            split_df.columns = [f'{column}_{i+1}' for i in range(len(split_df.columns))]
        
        # Drop original column and add split columns
        df = df.drop(columns=[column])
        df = pd.concat([df, split_df], axis=1)
        
        return df
    
    @staticmethod
    def merge_columns(df: pd.DataFrame, columns: List[str], new_column: str, 
                     separator: str = ' ') -> pd.DataFrame:
        """
        Merge multiple columns into one
        
        Args:
            df: DataFrame
            columns: Columns to merge
            new_column: Name for merged column
            separator: Separator string
        
        Returns:
            DataFrame with merged column
        """
        df = df.copy()
        
        # Filter to existing columns
        existing_cols = [col for col in columns if col in df.columns]
        if not existing_cols:
            return df
        
        # Merge columns
        df[new_column] = df[existing_cols].astype(str).agg(separator.join, axis=1)
        
        return df
    
    @staticmethod
    def normalize_text(df: pd.DataFrame, column: Union[str, List[str]], 
                       case: str = 'lower') -> pd.DataFrame:
        """
        Normalize text: trim whitespace and normalize case
        
        Args:
            df: DataFrame to clean
            column: Column name(s) to normalize
            case: 'lower', 'upper', 'title', 'sentence' (default: 'lower')
        
        Returns:
            DataFrame with normalized text
        """
        df = df.copy()
        
        # First trim whitespace
        df = TextCleaner.trim_whitespace(df, column)
        
        # Then normalize case
        df = TextCleaner.normalize_case(df, column, case=case)
        
        return df

