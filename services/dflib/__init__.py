"""
DataFrame Library Abstraction Layer

Provides a unified interface for dataframe operations that can work with
pandas, polars, or other engines behind the scenes.
"""

from .base import DataFrameEngine, DataFrameWrapper
from .pandas_impl import PandasEngine

# Default engine
default_engine = PandasEngine()

__all__ = ['DataFrameEngine', 'DataFrameWrapper', 'PandasEngine', 'default_engine']

