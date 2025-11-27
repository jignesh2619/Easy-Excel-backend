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
    Builds representative samples that:
        - Preserve ALL columns
        - Cover categorical variety
        - Capture numeric extremes/median/outliers
        - Include rare rows or edge cases
        - Provide a short explanation of the chosen rows
    """

    def __init__(self, max_rows: int = 20, min_rows: int = 10):
        self.max_rows = max_rows
        self.min_rows = min_rows

    def build_sample(self, df: pd.DataFrame) -> SampleResult:
        """Return a representative sample DataFrame and explanation."""
        if df.empty:
            return SampleResult(df.copy(), "Dataset is empty. Returning empty sample.", {})

        if len(df) <= self.min_rows:
            return SampleResult(df.copy(), "Dataset contains <=30 rows; returning all rows.", {
                "total_rows": len(df),
                "strategy": "full_dataset"
            })

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

        selected_indices = set()
        rationale: List[str] = []

        # 1. Numeric variation: min/median/max (+ optional outliers)
        for col in numeric_cols:
            col_data = df[col].dropna()
            if col_data.empty:
                continue
            quantiles = {
                "min": col_data.idxmin(),
                "median": col_data.sub(col_data.median()).abs().idxmin(),
                "max": col_data.idxmax()
            }
            for label, idx in quantiles.items():
                selected_indices.add(int(idx))
            # Outliers (beyond 1.5 IQR)
            q1, q3 = np.percentile(col_data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
            if not outliers.empty:
                selected_indices.update(outliers.index[:2])
            rationale.append(f"Captured numeric spread for '{col}' (min/median/max + outliers).")

        # 2. Categorical coverage: ensure all major categories appear
        for col in categorical_cols:
            value_counts = df[col].fillna("<NULL>").value_counts()
            top_categories = value_counts.index.tolist()
            for category in top_categories:
                idx = df[df[col].fillna("<NULL>") == category].index[0]
                selected_indices.add(int(idx))
            rationale.append(f"Included representatives for categories in '{col}'.")

        # 3. Date coverage
        for col in datetime_cols:
            col_data = df[col].dropna()
            if col_data.empty:
                continue
            sorted_idx = col_data.sort_values()
            first_idx = sorted_idx.index[0]
            last_idx = sorted_idx.index[-1]
            mid_idx = sorted_idx.index[len(sorted_idx) // 2]
            selected_indices.update([first_idx, mid_idx, last_idx])
            rationale.append(f"Covered date range extremes for '{col}'.")

        # 4. Rare rows: include rows with high missing values or unique combos
        missing_counts = df.isna().sum(axis=1)
        top_missing = missing_counts.sort_values(ascending=False).head(2).index.tolist()
        selected_indices.update(top_missing)
        rationale.append("Captured rows with high missing values.")

        # 5. If still under limit, add random diverse rows using stratified sampling
        if len(selected_indices) < self.max_rows:
            remaining_slots = self.max_rows - len(selected_indices)
            additional_indices = self._stratified_fill(
                df,
                exclude_indices=selected_indices,
                target_count=remaining_slots,
                categorical_cols=categorical_cols
            )
            selected_indices.update(additional_indices)
            if additional_indices:
                rationale.append("Added stratified rows to cover remaining diversity.")

        # Ensure index bounds
        selected_indices = [idx for idx in selected_indices if 0 <= idx < len(df)]

        sample_df = df.loc[sorted(selected_indices)].copy()
        explanation = self._build_explanation(len(df), sample_df, rationale)
        details = {
            "total_rows": len(df),
            "sample_rows": len(sample_df),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols
        }
        return SampleResult(sample_df, explanation, details)

    def _stratified_fill(
        self,
        df: pd.DataFrame,
        exclude_indices: set,
        target_count: int,
        categorical_cols: List[str]
    ) -> List[int]:
        """Add rows to reach target_count using simple stratified sampling."""
        remaining_indices = [idx for idx in df.index if idx not in exclude_indices]
        if not remaining_indices or target_count <= 0:
            return []

        selected: List[int] = []
        if categorical_cols:
            cat_col = categorical_cols[0]
            grouped = df.loc[remaining_indices].groupby(cat_col)
            per_group = max(1, target_count // max(1, len(grouped)))
            for _, group in grouped:
                sample_indices = group.index[:per_group].tolist()
                selected.extend(sample_indices)
                if len(selected) >= target_count:
                    break

        # If still short, fill with first remaining rows
        if len(selected) < target_count:
            remaining_pool = [idx for idx in remaining_indices if idx not in selected]
            selected.extend(remaining_pool[: target_count - len(selected)])

        return selected

    def _build_explanation(self, total_rows: int, sample_df: pd.DataFrame, rationale: List[str]) -> str:
        explanation_parts = [
            f"Selected {len(sample_df)} rows out of {total_rows} total to balance numeric ranges, categories, dates, and missing-value edge cases."
        ]
        explanation_parts.extend(rationale)
        return " ".join(explanation_parts)

