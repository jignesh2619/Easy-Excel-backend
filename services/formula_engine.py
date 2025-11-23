"""
Formula Engine

Provides reusable functions for Excel-like formula operations.
Each function operates on pandas DataFrames and returns computed results.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date


class FormulaEngine:
    """Engine for executing Excel-like formulas on DataFrames"""
    
    @staticmethod
    def SUM(df: pd.DataFrame, column: str) -> float:
        """Sum all values in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        return float(numeric_col.sum())
    
    @staticmethod
    def AVERAGE(df: pd.DataFrame, column: str) -> float:
        """Calculate average of values in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        return float(numeric_col.mean())
    
    @staticmethod
    def MIN(df: pd.DataFrame, column: str) -> float:
        """Find minimum value in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        return float(numeric_col.min())
    
    @staticmethod
    def MAX(df: pd.DataFrame, column: str) -> float:
        """Find maximum value in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        return float(numeric_col.max())
    
    @staticmethod
    def COUNT(df: pd.DataFrame, column: str) -> int:
        """Count non-null numeric values in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        return int(numeric_col.notna().sum())
    
    @staticmethod
    def COUNTIF(df: pd.DataFrame, column: str, condition: str, value: Any) -> int:
        """Count rows where column meets condition"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        
        if condition == "==":
            return int((df[column] == value).sum())
        elif condition == "!=":
            return int((df[column] != value).sum())
        elif condition == ">":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return int((numeric_col > value).sum())
        elif condition == ">=":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return int((numeric_col >= value).sum())
        elif condition == "<":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return int((numeric_col < value).sum())
        elif condition == "<=":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return int((numeric_col <= value).sum())
        elif condition == "contains":
            return int(df[column].astype(str).str.contains(str(value), case=False, na=False).sum())
        else:
            raise ValueError(f"Unsupported condition: {condition}")
    
    @staticmethod
    def COUNTA(df: pd.DataFrame, column: str) -> int:
        """Count all non-empty values in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        return int(df[column].notna().sum())
    
    @staticmethod
    def UNIQUE(df: pd.DataFrame, column: str) -> List[Any]:
        """Get unique values from a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        return df[column].dropna().unique().tolist()
    
    @staticmethod
    def ROUND(df: pd.DataFrame, column: str, decimals: int = 0) -> pd.DataFrame:
        """Round values in a column to specified decimal places"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        numeric_col = pd.to_numeric(result_df[column], errors='coerce')
        result_df[column] = numeric_col.round(decimals)
        return result_df
    
    # Text Functions
    @staticmethod
    def CONCAT(df: pd.DataFrame, columns: List[str], separator: str = "") -> pd.DataFrame:
        """Concatenate values from multiple columns"""
        result_df = df.copy()
        new_col_name = "_".join(columns)
        result_df[new_col_name] = df[columns].astype(str).agg(separator.join, axis=1)
        return result_df
    
    @staticmethod
    def TEXTJOIN(df: pd.DataFrame, columns: List[str], separator: str = ", ") -> pd.DataFrame:
        """Join text from multiple columns with separator"""
        result_df = df.copy()
        new_col_name = "_".join(columns) + "_joined"
        result_df[new_col_name] = df[columns].astype(str).agg(separator.join, axis=1)
        return result_df
    
    @staticmethod
    def LEFT(df: pd.DataFrame, column: str, num_chars: int) -> pd.DataFrame:
        """Extract left N characters from a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str[:num_chars]
        return result_df
    
    @staticmethod
    def RIGHT(df: pd.DataFrame, column: str, num_chars: int) -> pd.DataFrame:
        """Extract right N characters from a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str[-num_chars:]
        return result_df
    
    @staticmethod
    def MID(df: pd.DataFrame, column: str, start: int, num_chars: int) -> pd.DataFrame:
        """Extract substring from a column (start position, length)"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str[start-1:start-1+num_chars]
        return result_df
    
    @staticmethod
    def TRIM(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Remove leading/trailing whitespace from a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str.strip()
        return result_df
    
    @staticmethod
    def LOWER(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert text to lowercase"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str.lower()
        return result_df
    
    @staticmethod
    def UPPER(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert text to uppercase"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str.upper()
        return result_df
    
    @staticmethod
    def PROPER(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert text to title case"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str.title()
        return result_df
    
    @staticmethod
    def FIND(df: pd.DataFrame, column: str, search_text: str, case_sensitive: bool = True) -> pd.DataFrame:
        """Find position of search_text in column (returns -1 if not found)"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        new_col_name = f"{column}_find"
        if case_sensitive:
            result_df[new_col_name] = df[column].astype(str).str.find(search_text)
        else:
            result_df[new_col_name] = df[column].astype(str).str.lower().str.find(search_text.lower())
        return result_df
    
    @staticmethod
    def SEARCH(df: pd.DataFrame, column: str, search_text: str) -> pd.DataFrame:
        """Search for text in column (case-insensitive, returns -1 if not found)"""
        return FormulaEngine.FIND(df, column, search_text, case_sensitive=False)
    
    # Date & Time Functions
    @staticmethod
    def TODAY() -> str:
        """Return today's date as string"""
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def NOW() -> str:
        """Return current date and time as string"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def YEAR(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Extract year from date column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        new_col_name = f"{column}_year"
        result_df[new_col_name] = pd.to_datetime(df[column], errors='coerce').dt.year
        return result_df
    
    @staticmethod
    def MONTH(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Extract month from date column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        new_col_name = f"{column}_month"
        result_df[new_col_name] = pd.to_datetime(df[column], errors='coerce').dt.month
        return result_df
    
    @staticmethod
    def DAY(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Extract day from date column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        new_col_name = f"{column}_day"
        result_df[new_col_name] = pd.to_datetime(df[column], errors='coerce').dt.day
        return result_df
    
    @staticmethod
    def DATEDIF(df: pd.DataFrame, start_column: str, end_column: str, unit: str = "days") -> pd.DataFrame:
        """Calculate difference between two date columns"""
        if start_column not in df.columns or end_column not in df.columns:
            raise ValueError(f"One or both date columns not found")
        result_df = df.copy()
        new_col_name = f"datedif_{start_column}_{end_column}"
        
        start_dates = pd.to_datetime(df[start_column], errors='coerce')
        end_dates = pd.to_datetime(df[end_column], errors='coerce')
        
        if unit == "days":
            result_df[new_col_name] = (end_dates - start_dates).dt.days
        elif unit == "months":
            result_df[new_col_name] = ((end_dates.dt.year - start_dates.dt.year) * 12 + 
                                      (end_dates.dt.month - start_dates.dt.month))
        elif unit == "years":
            result_df[new_col_name] = (end_dates.dt.year - start_dates.dt.year)
        else:
            result_df[new_col_name] = (end_dates - start_dates).dt.days
        
        return result_df
    
    # Logical Functions
    @staticmethod
    def IF(df: pd.DataFrame, condition_column: str, condition: str, value: Any, 
           true_value: Any, false_value: Any) -> pd.DataFrame:
        """Apply IF logic: if condition is true, return true_value, else false_value"""
        if condition_column not in df.columns:
            raise ValueError(f"Column '{condition_column}' not found")
        result_df = df.copy()
        new_col_name = f"{condition_column}_if"
        
        # Build condition
        if condition == "==":
            mask = df[condition_column] == value
        elif condition == "!=":
            mask = df[condition_column] != value
        elif condition == ">":
            numeric_col = pd.to_numeric(df[condition_column], errors='coerce')
            mask = numeric_col > value
        elif condition == ">=":
            numeric_col = pd.to_numeric(df[condition_column], errors='coerce')
            mask = numeric_col >= value
        elif condition == "<":
            numeric_col = pd.to_numeric(df[condition_column], errors='coerce')
            mask = numeric_col < value
        elif condition == "<=":
            numeric_col = pd.to_numeric(df[condition_column], errors='coerce')
            mask = numeric_col <= value
        else:
            raise ValueError(f"Unsupported condition: {condition}")
        
        result_df[new_col_name] = np.where(mask, true_value, false_value)
        return result_df
    
    @staticmethod
    def AND(df: pd.DataFrame, columns: List[str], conditions: List[str], values: List[Any]) -> pd.DataFrame:
        """Apply AND logic across multiple conditions"""
        if len(columns) != len(conditions) or len(conditions) != len(values):
            raise ValueError("Columns, conditions, and values must have same length")
        
        result_df = df.copy()
        new_col_name = "_".join(columns) + "_and"
        
        mask = pd.Series([True] * len(df))
        for col, cond, val in zip(columns, conditions, values):
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
            
            if cond == "==":
                mask = mask & (df[col] == val)
            elif cond == "!=":
                mask = mask & (df[col] != val)
            elif cond == ">":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask & (numeric_col > val)
            elif cond == ">=":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask & (numeric_col >= val)
            elif cond == "<":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask & (numeric_col < val)
            elif cond == "<=":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask & (numeric_col <= val)
        
        result_df[new_col_name] = mask
        return result_df
    
    @staticmethod
    def OR(df: pd.DataFrame, columns: List[str], conditions: List[str], values: List[Any]) -> pd.DataFrame:
        """Apply OR logic across multiple conditions"""
        if len(columns) != len(conditions) or len(conditions) != len(values):
            raise ValueError("Columns, conditions, and values must have same length")
        
        result_df = df.copy()
        new_col_name = "_".join(columns) + "_or"
        
        mask = pd.Series([False] * len(df))
        for col, cond, val in zip(columns, conditions, values):
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
            
            if cond == "==":
                mask = mask | (df[col] == val)
            elif cond == "!=":
                mask = mask | (df[col] != val)
            elif cond == ">":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask | (numeric_col > val)
            elif cond == ">=":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask | (numeric_col >= val)
            elif cond == "<":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask | (numeric_col < val)
            elif cond == "<=":
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                mask = mask | (numeric_col <= val)
        
        result_df[new_col_name] = mask
        return result_df
    
    @staticmethod
    def NOT(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Negate boolean values in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        new_col_name = f"{column}_not"
        result_df[new_col_name] = ~df[column].astype(bool)
        return result_df
    
    # Lookup Functions
    @staticmethod
    def VLOOKUP(df: pd.DataFrame, lookup_value: Any, lookup_column: str, 
                return_column: str, exact_match: bool = True) -> Any:
        """VLOOKUP: Find value in lookup_column and return corresponding value from return_column"""
        if lookup_column not in df.columns or return_column not in df.columns:
            raise ValueError("Lookup or return column not found")
        
        if exact_match:
            matches = df[df[lookup_column] == lookup_value]
        else:
            # Approximate match (finds closest value <= lookup_value, requires sorted data)
            matches = df[df[lookup_column] <= lookup_value]
            if len(matches) > 0:
                matches = matches.iloc[[-1]]  # Get last (closest) match
        
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[return_column].iloc[0]
        else:
            # Multiple matches - return first
            return matches[return_column].iloc[0]
    
    @staticmethod
    def XLOOKUP(df: pd.DataFrame, lookup_value: Any, lookup_column: str, 
                return_column: str, not_found: Any = None) -> Any:
        """XLOOKUP: Modern lookup function (similar to VLOOKUP but more flexible)"""
        if lookup_column not in df.columns or return_column not in df.columns:
            raise ValueError("Lookup or return column not found")
        
        matches = df[df[lookup_column] == lookup_value]
        
        if len(matches) == 0:
            return not_found
        elif len(matches) == 1:
            return matches[return_column].iloc[0]
        else:
            # Multiple matches - return first
            return matches[return_column].iloc[0]
    
    # Data Cleaning Functions
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Remove duplicate rows"""
        if columns:
            return df.drop_duplicates(subset=columns)
        return df.drop_duplicates()
    
    @staticmethod
    def highlight_duplicates(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Mark duplicate values (returns DataFrame with is_duplicate column)"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[f"{column}_is_duplicate"] = df[column].duplicated(keep=False)
        return result_df
    
    @staticmethod
    def remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows where all values are empty/null"""
        return df.dropna(how='all')
    
    @staticmethod
    def normalize_text(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Normalize text formatting (trim, lowercase)"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = df[column].astype(str).str.strip().str.lower()
        return result_df
    
    @staticmethod
    def fix_date_formats(df: pd.DataFrame, column: str, target_format: str = "%Y-%m-%d") -> pd.DataFrame:
        """Fix date formats in a column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = pd.to_datetime(df[column], errors='coerce').dt.strftime(target_format)
        return result_df
    
    @staticmethod
    def convert_text_to_numbers(df: pd.DataFrame, column: str) -> pd.DataFrame:
        """Convert text numbers to actual numeric values"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df[column] = pd.to_numeric(df[column], errors='coerce')
        return result_df
    
    # Grouping & Summaries
    @staticmethod
    def group_by_category(df: pd.DataFrame, group_column: str, 
                         agg_function: str = "count", agg_column: Optional[str] = None) -> pd.DataFrame:
        """Group by category and aggregate"""
        if group_column not in df.columns:
            raise ValueError(f"Group column '{group_column}' not found")
        
        if agg_function == "count":
            if agg_column:
                result = df.groupby(group_column)[agg_column].count().reset_index()
                result.columns = [group_column, f"count_{agg_column}"]
            else:
                result = df.groupby(group_column).size().reset_index(name='count')
        elif agg_function == "sum":
            if not agg_column:
                raise ValueError("agg_column required for sum")
            if agg_column not in df.columns:
                raise ValueError(f"Aggregate column '{agg_column}' not found")
            result = df.groupby(group_column)[agg_column].sum().reset_index()
            result.columns = [group_column, f"sum_{agg_column}"]
        elif agg_function == "average" or agg_function == "mean":
            if not agg_column:
                raise ValueError("agg_column required for average")
            if agg_column not in df.columns:
                raise ValueError(f"Aggregate column '{agg_column}' not found")
            result = df.groupby(group_column)[agg_column].mean().reset_index()
            result.columns = [group_column, f"avg_{agg_column}"]
        elif agg_function == "max":
            if not agg_column:
                raise ValueError("agg_column required for max")
            if agg_column not in df.columns:
                raise ValueError(f"Aggregate column '{agg_column}' not found")
            result = df.groupby(group_column)[agg_column].max().reset_index()
            result.columns = [group_column, f"max_{agg_column}"]
        elif agg_function == "min":
            if not agg_column:
                raise ValueError("agg_column required for min")
            if agg_column not in df.columns:
                raise ValueError(f"Aggregate column '{agg_column}' not found")
            result = df.groupby(group_column)[agg_column].min().reset_index()
            result.columns = [group_column, f"min_{agg_column}"]
        else:
            raise ValueError(f"Unsupported aggregate function: {agg_function}")
        
        return result
    
    # Additional Formula Operations
    @staticmethod
    def SORT(df: pd.DataFrame, column: str, ascending: bool = True, limit: Optional[int] = None) -> pd.DataFrame:
        """Sort dataframe by column"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        result_df = df.copy()
        result_df = result_df.sort_values(by=column, ascending=ascending, na_position='last').reset_index(drop=True)
        if limit:
            result_df = result_df.head(limit)
        return result_df
    
    @staticmethod
    def FILTER(df: pd.DataFrame, column: str, condition: str, value: Any) -> pd.DataFrame:
        """Filter dataframe based on condition"""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        
        if condition == "==":
            return df[df[column] == value].copy()
        elif condition == "!=":
            return df[df[column] != value].copy()
        elif condition == ">":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col > value].copy()
        elif condition == ">=":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col >= value].copy()
        elif condition == "<":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col < value].copy()
        elif condition == "<=":
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col <= value].copy()
        elif condition == "contains":
            return df[df[column].astype(str).str.contains(str(value), case=False, na=False)].copy()
        else:
            raise ValueError(f"Unsupported condition: {condition}")

