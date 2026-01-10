"""
Text Cleaning Functions

Clean and normalize text data including whitespace, case, and special characters.
"""

import pandas as pd
# Note: re module is available but format_phone_numbers uses string methods to avoid scoping issues
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
        
        if keep is None:
            # Default: keep alphanumeric, spaces, and common punctuation
            pattern = r'[^a-zA-Z0-9\s.,!?;:\-()]'
        else:
            pattern = f'[^{keep}]'
        
        for col in columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(pattern, '', regex=True)
        
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
                df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
        
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
                if case_sensitive:
                    df[col] = df[col].astype(str).str.replace(old_text, new_text)
                else:
                    df[col] = df[col].astype(str).str.replace(old_text, new_text, case=False, regex=False)
        
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
    def format_phone_numbers(df: pd.DataFrame, columns: Union[str, List[str]], 
                            format: str = '(XXX) XXX-XXXX') -> pd.DataFrame:
        """
        Format phone numbers to standard format (XXX) XXX-XXXX
        
        Handles various input formats:
        - 5551234567 (10 digits)
        - 555-123-4567
        - 555.123.4567
        - (555) 123-4567
        - +1-555-123-4567
        - 555 123 4567
        - etc.
        
        Args:
            df: DataFrame to format
            columns: Column name(s) containing phone numbers
            format: Target format (default: '(XXX) XXX-XXXX')
        
        Returns:
            DataFrame with formatted phone numbers
        """
        df = df.copy()
        
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col not in df.columns:
                continue
            
            def format_phone(phone_str):
                """Format a single phone number"""
                if pd.isna(phone_str) or phone_str == '':
                    return phone_str
                
                # Convert to string and strip whitespace
                phone_str = str(phone_str).strip()
                
                # Handle empty string after conversion
                if not phone_str or phone_str.lower() in ['nan', 'none', 'null']:
                    return phone_str
                
                # Remove all non-digit characters using string methods (avoids re scoping issues)
                # Use list comprehension and join instead of re for better compatibility
                digits_only = ''.join(char for char in phone_str if char.isdigit())
                
                # Skip if no digits found
                if not digits_only:
                    return phone_str
                
                # Handle different lengths
                if len(digits_only) == 10:
                    # Standard 10-digit US number: (XXX) XXX-XXXX
                    return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
                elif len(digits_only) == 11:
                    # 11-digit: could be country code 1 or extra digit
                    if digits_only[0] == '1':
                        # Country code 1 (US/Canada): format as (XXX) XXX-XXXX
                        return f"({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:11]}"
                    else:
                        # 11 digits but doesn't start with 1, take last 10 digits
                        digits_only = digits_only[-10:]
                        return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
                elif len(digits_only) > 11:
                    # More than 11 digits: take last 10 digits (most likely US number)
                    digits_only = digits_only[-10:]
                    return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
                elif len(digits_only) == 12:
                    # 12 digits: could be country code + 11 digits, take last 10
                    digits_only = digits_only[-10:]
                    return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
                elif len(digits_only) < 10:
                    # Too short, return as-is (might be extension or invalid)
                    return phone_str
                else:
                    # Default: format as 10-digit (shouldn't reach here but safety)
                    return f"({digits_only[0:3]}) {digits_only[3:6]}-{digits_only[6:10]}"
            
            # Apply formatting
            df[col] = df[col].apply(format_phone)
        
        return df

