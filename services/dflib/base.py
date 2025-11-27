"""
Abstract Base Class for DataFrame Engines

Defines the interface that all dataframe engines must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import pandas as pd


class DataFrameWrapper:
    """Wrapper around a dataframe that provides engine-agnostic operations"""
    
    def __init__(self, engine: 'DataFrameEngine', data: Any):
        """
        Initialize wrapper
        
        Args:
            engine: The dataframe engine instance
            data: The underlying dataframe (engine-specific)
        """
        self.engine = engine
        self._data = data
    
    @property
    def data(self):
        """Get the underlying dataframe"""
        return self._data
    
    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame (for compatibility)"""
        return self.engine.to_pandas(self._data)
    
    def filter(self, condition: Dict) -> 'DataFrameWrapper':
        """Filter rows based on condition"""
        return DataFrameWrapper(self.engine, self.engine.filter(self._data, condition))
    
    def sort(self, columns: List[Dict], ascending: Optional[List[bool]] = None) -> 'DataFrameWrapper':
        """Sort by columns"""
        return DataFrameWrapper(self.engine, self.engine.sort(self._data, columns, ascending))
    
    def group_by(self, columns: List[str], aggregations: Dict) -> 'DataFrameWrapper':
        """Group by columns and aggregate"""
        return DataFrameWrapper(self.engine, self.engine.group_by(self._data, columns, aggregations))
    
    def add_column(self, name: str, values: Any) -> 'DataFrameWrapper':
        """Add a new column"""
        return DataFrameWrapper(self.engine, self.engine.add_column(self._data, name, values))
    
    def delete_column(self, name: str) -> 'DataFrameWrapper':
        """Delete a column"""
        return DataFrameWrapper(self.engine, self.engine.delete_column(self._data, name))
    
    def rename_column(self, old_name: str, new_name: str) -> 'DataFrameWrapper':
        """Rename a column"""
        return DataFrameWrapper(self.engine, self.engine.rename_column(self._data, old_name, new_name))
    
    def drop_duplicates(self, subset: Optional[List[str]] = None) -> 'DataFrameWrapper':
        """Remove duplicate rows"""
        return DataFrameWrapper(self.engine, self.engine.drop_duplicates(self._data, subset))
    
    def fillna(self, value: Any = None, method: Optional[str] = None, columns: Optional[List[str]] = None) -> 'DataFrameWrapper':
        """Fill missing values"""
        return DataFrameWrapper(self.engine, self.engine.fillna(self._data, value, method, columns))
    
    def dropna(self, subset: Optional[List[str]] = None, how: str = 'any') -> 'DataFrameWrapper':
        """Drop rows with missing values"""
        return DataFrameWrapper(self.engine, self.engine.dropna(self._data, subset, how))
    
    @property
    def columns(self) -> List[str]:
        """Get column names"""
        return self.engine.get_columns(self._data)
    
    @property
    def shape(self) -> tuple:
        """Get shape (rows, columns)"""
        return self.engine.get_shape(self._data)
    
    def head(self, n: int = 5) -> 'DataFrameWrapper':
        """Get first n rows"""
        return DataFrameWrapper(self.engine, self.engine.head(self._data, n))
    
    def tail(self, n: int = 5) -> 'DataFrameWrapper':
        """Get last n rows"""
        return DataFrameWrapper(self.engine, self.engine.tail(self._data, n))
    
    def sample(self, n: int) -> 'DataFrameWrapper':
        """Get random sample of n rows"""
        return DataFrameWrapper(self.engine, self.engine.sample(self._data, n))
    
    def get_value(self, row_idx: int, col_name: str) -> Any:
        """Get value at specific row and column"""
        return self.engine.get_value(self._data, row_idx, col_name)
    
    def set_value(self, row_idx: int, col_name: str, value: Any) -> 'DataFrameWrapper':
        """Set value at specific row and column"""
        return DataFrameWrapper(self.engine, self.engine.set_value(self._data, row_idx, col_name, value))


class DataFrameEngine(ABC):
    """Abstract base class for dataframe engines"""
    
    @abstractmethod
    def from_file(self, file_path: str, **kwargs) -> Any:
        """Load dataframe from file"""
        pass
    
    @abstractmethod
    def to_pandas(self, data: Any) -> pd.DataFrame:
        """Convert to pandas DataFrame"""
        pass
    
    @abstractmethod
    def filter(self, data: Any, condition: Dict) -> Any:
        """Filter rows based on condition"""
        pass
    
    @abstractmethod
    def sort(self, data: Any, columns: List[Dict], ascending: Optional[List[bool]] = None) -> Any:
        """Sort by columns"""
        pass
    
    @abstractmethod
    def group_by(self, data: Any, columns: List[str], aggregations: Dict) -> Any:
        """Group by columns and aggregate"""
        pass
    
    @abstractmethod
    def add_column(self, data: Any, name: str, values: Any) -> Any:
        """Add a new column"""
        pass
    
    @abstractmethod
    def delete_column(self, data: Any, name: str) -> Any:
        """Delete a column"""
        pass
    
    @abstractmethod
    def rename_column(self, data: Any, old_name: str, new_name: str) -> Any:
        """Rename a column"""
        pass
    
    @abstractmethod
    def drop_duplicates(self, data: Any, subset: Optional[List[str]] = None) -> Any:
        """Remove duplicate rows"""
        pass
    
    @abstractmethod
    def fillna(self, data: Any, value: Any = None, method: Optional[str] = None, columns: Optional[List[str]] = None) -> Any:
        """Fill missing values"""
        pass
    
    @abstractmethod
    def dropna(self, data: Any, subset: Optional[List[str]] = None, how: str = 'any') -> Any:
        """Drop rows with missing values"""
        pass
    
    @abstractmethod
    def get_columns(self, data: Any) -> List[str]:
        """Get column names"""
        pass
    
    @abstractmethod
    def get_shape(self, data: Any) -> tuple:
        """Get shape (rows, columns)"""
        pass
    
    @abstractmethod
    def head(self, data: Any, n: int = 5) -> Any:
        """Get first n rows"""
        pass
    
    @abstractmethod
    def tail(self, data: Any, n: int = 5) -> Any:
        """Get last n rows"""
        pass
    
    @abstractmethod
    def sample(self, data: Any, n: int) -> Any:
        """Get random sample of n rows"""
        pass
    
    @abstractmethod
    def get_value(self, data: Any, row_idx: int, col_name: str) -> Any:
        """Get value at specific row and column"""
        pass
    
    @abstractmethod
    def set_value(self, data: Any, row_idx: int, col_name: str, value: Any) -> Any:
        """Set value at specific row and column"""
        pass

