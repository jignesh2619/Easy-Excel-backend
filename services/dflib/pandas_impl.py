"""
Pandas Implementation of DataFrame Engine

Default implementation using pandas for all dataframe operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from .base import DataFrameEngine


class PandasEngine(DataFrameEngine):
    """Pandas-based dataframe engine implementation"""
    
    def from_file(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Load dataframe from file"""
        file_path_str = str(file_path)
        
        if file_path_str.endswith('.csv'):
            return pd.read_csv(file_path_str, **kwargs)
        elif file_path_str.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path_str, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_path_str}")
    
    def to_pandas(self, data: Any) -> pd.DataFrame:
        """Convert to pandas DataFrame (already is)"""
        if isinstance(data, pd.DataFrame):
            return data
        return pd.DataFrame(data)
    
    def filter(self, data: pd.DataFrame, condition: Dict) -> pd.DataFrame:
        """Filter rows based on condition"""
        df = data.copy()
        
        column = condition.get('column')
        operator = condition.get('operator', '==')
        value = condition.get('value')
        
        if column not in df.columns:
            return df
        
        if operator == '==':
            return df[df[column] == value]
        elif operator == '!=':
            return df[df[column] != value]
        elif operator == '>':
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col > value]
        elif operator == '>=':
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col >= value]
        elif operator == '<':
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col < value]
        elif operator == '<=':
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            return df[numeric_col <= value]
        elif operator == 'contains':
            return df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
        elif operator == 'not_contains':
            return df[~df[column].astype(str).str.contains(str(value), case=False, na=False)]
        elif operator == 'in':
            if isinstance(value, list):
                return df[df[column].isin(value)]
        elif operator == 'not_in':
            if isinstance(value, list):
                return df[~df[column].isin(value)]
        elif operator == 'is_null':
            return df[df[column].isna()]
        elif operator == 'is_not_null':
            return df[df[column].notna()]
        
        return df
    
    def sort(self, data: pd.DataFrame, columns: List[Dict], ascending: Optional[List[bool]] = None) -> pd.DataFrame:
        """Sort by columns"""
        df = data.copy()
        
        if not columns:
            return df
        
        sort_by = []
        sort_ascending = []
        
        for col_config in columns:
            col_name = col_config.get('column_name')
            order = col_config.get('order', 'asc').lower()
            
            if col_name in df.columns:
                sort_by.append(col_name)
                is_ascending = order in ['asc', 'ascending', 'a→z', 'a-z', 'small to big', 'small→big']
                sort_ascending.append(is_ascending)
        
        if not sort_by:
            return df
        
        if ascending is not None:
            sort_ascending = ascending
        
        return df.sort_values(by=sort_by, ascending=sort_ascending, na_position='last').reset_index(drop=True)
    
    def group_by(self, data: pd.DataFrame, columns: List[str], aggregations: Dict) -> pd.DataFrame:
        """Group by columns and aggregate"""
        df = data.copy()
        
        # Filter to only existing columns
        group_cols = [col for col in columns if col in df.columns]
        if not group_cols:
            return df
        
        agg_dict = {}
        for agg_col, agg_funcs in aggregations.items():
            if agg_col in df.columns:
                if isinstance(agg_funcs, str):
                    agg_dict[agg_col] = agg_funcs
                elif isinstance(agg_funcs, list):
                    for func in agg_funcs:
                        if func in ['sum', 'mean', 'count', 'min', 'max', 'std', 'median']:
                            agg_dict[agg_col] = agg_dict.get(agg_col, []) + [func]
        
        if not agg_dict:
            # Default to count if no aggregations specified
            result = df.groupby(group_cols).size().reset_index(name='count')
        else:
            result = df.groupby(group_cols).agg(agg_dict).reset_index()
        
        return result
    
    def add_column(self, data: pd.DataFrame, name: str, values: Any) -> pd.DataFrame:
        """Add a new column"""
        df = data.copy()
        df[name] = values
        return df
    
    def delete_column(self, data: pd.DataFrame, name: str) -> pd.DataFrame:
        """Delete a column"""
        df = data.copy()
        if name in df.columns:
            df = df.drop(columns=[name])
        return df
    
    def rename_column(self, data: pd.DataFrame, old_name: str, new_name: str) -> pd.DataFrame:
        """Rename a column"""
        df = data.copy()
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
        return df
    
    def drop_duplicates(self, data: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Remove duplicate rows"""
        df = data.copy()
        if subset:
            subset = [col for col in subset if col in df.columns]
            if subset:
                return df.drop_duplicates(subset=subset).reset_index(drop=True)
        return df.drop_duplicates().reset_index(drop=True)
    
    def fillna(self, data: pd.DataFrame, value: Any = None, method: Optional[str] = None, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Fill missing values"""
        df = data.copy()
        
        if columns:
            columns = [col for col in columns if col in df.columns]
            if not columns:
                return df
        
        if method:
            if columns:
                df[columns] = df[columns].fillna(method=method)
            else:
                df = df.fillna(method=method)
        elif value is not None:
            if columns:
                df[columns] = df[columns].fillna(value)
            else:
                df = df.fillna(value)
        
        return df
    
    def dropna(self, data: pd.DataFrame, subset: Optional[List[str]] = None, how: str = 'any') -> pd.DataFrame:
        """Drop rows with missing values"""
        df = data.copy()
        
        if subset:
            subset = [col for col in subset if col in df.columns]
            if subset:
                return df.dropna(subset=subset, how=how).reset_index(drop=True)
        
        return df.dropna(how=how).reset_index(drop=True)
    
    def get_columns(self, data: pd.DataFrame) -> List[str]:
        """Get column names"""
        return list(data.columns)
    
    def get_shape(self, data: pd.DataFrame) -> tuple:
        """Get shape (rows, columns)"""
        return data.shape
    
    def head(self, data: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """Get first n rows"""
        return data.head(n)
    
    def tail(self, data: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """Get last n rows"""
        return data.tail(n)
    
    def sample(self, data: pd.DataFrame, n: int) -> pd.DataFrame:
        """Get random sample of n rows"""
        if len(data) <= n:
            return data.copy()
        return data.sample(n=n, random_state=42).reset_index(drop=True)
    
    def get_value(self, data: pd.DataFrame, row_idx: int, col_name: str) -> Any:
        """Get value at specific row and column"""
        if col_name not in data.columns:
            return None
        if row_idx < 0 or row_idx >= len(data):
            return None
        return data.iloc[row_idx][col_name]
    
    def set_value(self, data: pd.DataFrame, row_idx: int, col_name: str, value: Any) -> pd.DataFrame:
        """Set value at specific row and column"""
        df = data.copy()
        if col_name in df.columns and 0 <= row_idx < len(df):
            df.iloc[row_idx, df.columns.get_loc(col_name)] = value
        return df

