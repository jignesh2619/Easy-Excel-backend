"""
Sample Selector Service

Creates representative subsets of uploaded datasets to provide the LLM with
meaningful context without sending the entire file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class SampleResult:
    dataframe: pd.DataFrame
    explanation: str
    strategy_details: Dict[str, any]


class SampleSelector:
    """
    Smart sample selector that:
        - Preserves ALL columns
        - Selects diverse, representative rows (no duplicates)
        - Uses quantile-based sampling for numeric columns
        - Ensures categorical variety
        - Captures edge cases and outliers
    """

    def __init__(self, max_rows: int = 20, min_rows: int = 10):
        self.max_rows = max_rows
        self.min_rows = min_rows

    def build_sample(self, df: pd.DataFrame) -> SampleResult:
        """Return a representative sample DataFrame with ALL columns and diverse rows."""
        if df.empty:
            return SampleResult(df.copy(), "Dataset is empty. Returning empty sample.", {})

        # Performance optimization: For small datasets, skip complex selection
        if len(df) <= self.max_rows * 2:
            sample_df = df.head(self.max_rows).copy()
            return SampleResult(
                sample_df,
                f"Small dataset ({len(df)} rows); returning first {len(sample_df)} rows.",
                {
                    "total_rows": len(df),
                    "sample_rows": len(sample_df),
                    "strategy": "simple_head"
                }
            )

        if len(df) <= self.min_rows:
            return SampleResult(df.copy(), f"Dataset contains <= {self.min_rows} rows; returning all rows.", {
                "total_rows": len(df),
                "strategy": "full_dataset"
            })

        # Identify column types
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

        # Use smart selection that ensures diversity
        selected_indices = self._smart_select_rows(
            df, numeric_cols, categorical_cols, datetime_cols
        )

        # Ensure we have at least min_rows
        if len(selected_indices) < self.min_rows:
            remaining = [idx for idx in df.index if idx not in selected_indices]
            needed = self.min_rows - len(selected_indices)
            selected_indices.extend(remaining[:needed])

        # Ensure index bounds and remove duplicates
        selected_indices = sorted(set([int(idx) for idx in selected_indices if 0 <= idx < len(df)]))

        # Limit to max_rows
        if len(selected_indices) > self.max_rows:
            selected_indices = selected_indices[:self.max_rows]

        sample_df = df.loc[selected_indices].copy()
        
        # Build explanation
        explanation = self._build_explanation(len(df), len(sample_df), numeric_cols, categorical_cols, datetime_cols)
        
        details = {
            "total_rows": len(df),
            "sample_rows": len(sample_df),
            "numeric_columns": len(numeric_cols),
            "categorical_columns": len(categorical_cols),
            "datetime_columns": len(datetime_cols),
            "strategy": "smart_diverse_selection"
        }
        
        return SampleResult(sample_df, explanation, details)

    def _smart_select_rows(
        self,
        df: pd.DataFrame,
        numeric_cols: List[str],
        categorical_cols: List[str],
        datetime_cols: List[str]
    ) -> List[int]:
        """Select diverse rows using quantile-based and categorical sampling."""
        selected = set()
        
        # Strategy 1: Quantile-based sampling for numeric columns (ensures distribution)
        # Performance optimization: For large datasets, sample first before calculating percentiles
        if numeric_cols:
            # Use percentiles: 0%, 25%, 50%, 75%, 100% for each numeric column
            for col in numeric_cols[:5]:  # Limit to first 5 numeric cols to avoid too many selections
                col_data = df[col].dropna()
                if len(col_data) < 2:
                    continue
                
                # Performance: For large datasets, use sample for percentile calculation
                if len(col_data) > 2000:
                    sample_data = col_data.sample(min(2000, len(col_data)), random_state=42)
                    percentiles = [0, 25, 50, 75, 100]
                    for p in percentiles:
                        if len(sample_data) > 0:
                            value = np.percentile(sample_data, p)
                            # Find row closest to this percentile value in full dataset
                            closest_idx = (col_data - value).abs().idxmin()
                            selected.add(int(closest_idx))
                else:
                    # Small dataset: use full data
                    percentiles = [0, 25, 50, 75, 100]
                    for p in percentiles:
                        if len(col_data) > 0:
                            value = np.percentile(col_data, p)
                            # Find row closest to this percentile value
                            closest_idx = (col_data - value).abs().idxmin()
                            selected.add(int(closest_idx))
        
        # Strategy 2: Categorical diversity - one row per unique value (up to reasonable limit)
        if categorical_cols:
            for col in categorical_cols[:3]:  # Limit to first 3 categorical cols
                unique_values = df[col].fillna("<NULL>").unique()
                # Limit to top 10 most common categories to avoid explosion
                value_counts = df[col].fillna("<NULL>").value_counts()
                top_values = value_counts.head(10).index.tolist()
                
                for val in top_values:
                    matching_rows = df[df[col].fillna("<NULL>") == val].index
                    if len(matching_rows) > 0:
                        # Pick first row with this value that we haven't selected
                        for idx in matching_rows:
                            if int(idx) not in selected:
                                selected.add(int(idx))
                                break
        
        # Strategy 3: Date range coverage
        if datetime_cols:
            for col in datetime_cols[:2]:  # Limit to first 2 date cols
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    # Earliest, middle, latest
                    sorted_data = col_data.sort_values()
                    selected.add(int(sorted_data.index[0]))  # Earliest
                    selected.add(int(sorted_data.index[-1]))  # Latest
                    if len(sorted_data) > 1:
                        mid_idx = sorted_data.index[len(sorted_data) // 2]
                        selected.add(int(mid_idx))
        
        # Strategy 4: Edge cases - rows with most/least missing values
        # Performance optimization: For large datasets, sample first
        if len(df) > 2000:
            sample_df = df.sample(min(2000, len(df)), random_state=42)
            missing_counts = sample_df.isna().sum(axis=1)
            if len(missing_counts) > 0:
                # Row with most missing values (from sample)
                most_missing_idx = missing_counts.idxmax()
                selected.add(int(most_missing_idx))
                # Row with least missing values (from sample)
                least_missing_idx = missing_counts.idxmin()
                selected.add(int(least_missing_idx))
        else:
            missing_counts = df.isna().sum(axis=1)
            if len(missing_counts) > 0:
                # Row with most missing values
                most_missing_idx = missing_counts.idxmax()
                selected.add(int(most_missing_idx))
                # Row with least missing values (most complete)
                least_missing_idx = missing_counts.idxmin()
                selected.add(int(least_missing_idx))
        
        # Strategy 5: Outlier detection for numeric columns
        if numeric_cols:
            for col in numeric_cols[:3]:  # Check first 3 numeric cols
                col_data = df[col].dropna()
                if len(col_data) < 4:
                    continue
                
                q1, q3 = np.percentile(col_data, [25, 75])
                iqr = q3 - q1
                if iqr > 0:
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    # Add up to 2 outliers per column
                    for idx in outliers.index[:2]:
                        selected.add(int(idx))
        
        # Strategy 6: Evenly distributed sampling to fill remaining slots
        current_count = len(selected)
        if current_count < self.max_rows:
            remaining_slots = self.max_rows - current_count
            available_indices = [idx for idx in df.index if int(idx) not in selected]
            
            if len(available_indices) > 0:
                # Use systematic sampling (every Nth row) for even distribution
                step = max(1, len(available_indices) // remaining_slots)
                for i in range(0, len(available_indices), step):
                    if len(selected) >= self.max_rows:
                        break
                    selected.add(int(available_indices[i]))
        
        return sorted(list(selected))

    def _build_explanation(
        self,
        total_rows: int,
        sample_rows: int,
        numeric_cols: List[str],
        categorical_cols: List[str],
        datetime_cols: List[str]
    ) -> str:
        """Build explanation of sampling strategy."""
        parts = [
            f"Selected {sample_rows} diverse, representative rows from {total_rows} total rows.",
            "Selection strategy: quantile-based sampling for numeric columns, categorical diversity, date range coverage, edge cases, and systematic distribution.",
            f"All {len(numeric_cols) + len(categorical_cols) + len(datetime_cols)} columns are preserved in the sample."
        ]
        return " ".join(parts)
