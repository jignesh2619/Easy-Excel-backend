"""
Excel File Summarizer

Analyzes Excel files and provides comprehensive summaries including:
- Column types and statistics
- Sample rows
- Data quality metrics
- Missing value analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path


class ExcelSummarizer:
    """Summarizes Excel files with detailed analysis"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize summarizer with a dataframe
        
        Args:
            df: The dataframe to summarize
        """
        self.df = df
        self.summary = {}
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary of the dataframe
        
        Returns:
            Dictionary containing all summary information
        """
        return {
            'shape': self._get_shape(),
            'columns': self._get_column_info(),
            'sample_rows': self._get_sample_rows(),
            'statistics': self._get_statistics(),
            'data_quality': self._get_data_quality(),
            'missing_values': self._get_missing_values(),
            'duplicates': self._get_duplicate_info()
        }
    
    def _get_shape(self) -> Dict[str, int]:
        """Get dataframe shape"""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns)
        }
    
    def _get_column_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about each column"""
        column_info = []
        
        for col in self.df.columns:
            col_data = self.df[col]
            dtype = str(col_data.dtype)
            
            # Infer type category
            type_category = self._infer_type_category(col_data)
            
            # Get unique count
            unique_count = col_data.nunique()
            
            # Get null count
            null_count = col_data.isna().sum()
            
            # Get sample values
            sample_values = col_data.dropna().head(5).tolist()
            
            info = {
                'name': str(col),
                'dtype': dtype,
                'type_category': type_category,
                'unique_count': int(unique_count),
                'null_count': int(null_count),
                'null_percentage': float(null_count / len(self.df) * 100) if len(self.df) > 0 else 0.0,
                'sample_values': [str(v) for v in sample_values[:5]]
            }
            
            # Add type-specific info
            if type_category == 'numeric':
                info['min'] = float(col_data.min()) if pd.api.types.is_numeric_dtype(col_data) else None
                info['max'] = float(col_data.max()) if pd.api.types.is_numeric_dtype(col_data) else None
                info['mean'] = float(col_data.mean()) if pd.api.types.is_numeric_dtype(col_data) else None
            elif type_category == 'datetime':
                info['min_date'] = str(col_data.min()) if pd.api.types.is_datetime64_any_dtype(col_data) else None
                info['max_date'] = str(col_data.max()) if pd.api.types.is_datetime64_any_dtype(col_data) else None
            
            column_info.append(info)
        
        return column_info
    
    def _infer_type_category(self, series: pd.Series) -> str:
        """Infer the category of a column"""
        # Check numeric
        numeric_count = pd.to_numeric(series, errors='coerce').notna().sum()
        if numeric_count == len(series) and numeric_count > 0:
            return 'numeric'
        
        # Check datetime
        datetime_count = pd.to_datetime(series, errors='coerce').notna().sum()
        if datetime_count > len(series) * 0.8 and datetime_count > 0:
            return 'datetime'
        
        # Check boolean
        if series.dtype == 'bool' or series.dtype.name == 'bool':
            return 'boolean'
        
        # Default to text
        return 'text'
    
    def _get_sample_rows(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from the dataframe"""
        sample_df = self.df.head(n)
        return sample_df.to_dict('records')
    
    def _get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        stats = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'numeric_columns': len(numeric_cols),
            'text_columns': len(self.df.select_dtypes(include=['object']).columns),
            'datetime_columns': len(self.df.select_dtypes(include=['datetime64']).columns)
        }
        
        if numeric_cols:
            stats['numeric_column_names'] = numeric_cols
        
        return stats
    
    def _get_data_quality(self) -> Dict[str, Any]:
        """Get data quality metrics"""
        total_cells = len(self.df) * len(self.df.columns)
        null_cells = self.df.isna().sum().sum()
        
        return {
            'total_cells': int(total_cells),
            'null_cells': int(null_cells),
            'null_percentage': float(null_cells / total_cells * 100) if total_cells > 0 else 0.0,
            'complete_rows': int((~self.df.isna().any(axis=1)).sum()),
            'complete_rows_percentage': float((~self.df.isna().any(axis=1)).sum() / len(self.df) * 100) if len(self.df) > 0 else 0.0
        }
    
    def _get_missing_values(self) -> Dict[str, Any]:
        """Get detailed missing value information"""
        missing_by_column = {}
        for col in self.df.columns:
            null_count = self.df[col].isna().sum()
            if null_count > 0:
                missing_by_column[col] = {
                    'count': int(null_count),
                    'percentage': float(null_count / len(self.df) * 100) if len(self.df) > 0 else 0.0
                }
        
        return {
            'by_column': missing_by_column,
            'columns_with_missing': list(missing_by_column.keys()),
            'total_missing_columns': len(missing_by_column)
        }
    
    def _get_duplicate_info(self) -> Dict[str, Any]:
        """Get duplicate row information"""
        duplicate_mask = self.df.duplicated(keep=False)
        duplicate_count = duplicate_mask.sum()
        
        # Check for duplicates in specific columns
        column_duplicates = {}
        for col in self.df.columns:
            col_duplicates = self.df[col].duplicated(keep=False).sum()
            if col_duplicates > 0:
                column_duplicates[col] = int(col_duplicates)
        
        return {
            'duplicate_rows': int(duplicate_count),
            'duplicate_percentage': float(duplicate_count / len(self.df) * 100) if len(self.df) > 0 else 0.0,
            'column_duplicates': column_duplicates
        }
    
    def get_quick_summary(self) -> str:
        """Get a quick text summary"""
        shape = self._get_shape()
        stats = self._get_statistics()
        quality = self._get_data_quality()
        
        return (
            f"Excel file with {shape['rows']} rows and {shape['columns']} columns. "
            f"Contains {stats['numeric_columns']} numeric, {stats['text_columns']} text columns. "
            f"Data quality: {100 - quality['null_percentage']:.1f}% complete cells."
        )

