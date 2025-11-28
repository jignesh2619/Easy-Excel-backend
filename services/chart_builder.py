"""
Chart Builder Service

Generates charts using matplotlib based on processed data.
Supports bar, line, and pie charts with clean formatting.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


def _extract_numeric_from_string(value):
    """
    Extract numeric value from formatted strings like "4.4 (65)" -> 4.4
    Handles:
    - "4.4 (65)" -> 4.4
    - "5 (387)" -> 5.0
    - "4.1 (1,385)" -> 4.1 (handles commas)
    - "4.9" -> 4.9 (already clean)
    - 4.4 -> 4.4 (already numeric)
    """
    if pd.isna(value):
        return None
    
    # If already numeric, return it
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string
    value_str = str(value).strip()
    
    # Try direct conversion first
    try:
        return float(value_str)
    except ValueError:
        pass
    
    # Extract first number before parentheses: "4.4 (65)" -> "4.4"
    # Pattern: match number at start (can have decimal, can have negative sign)
    match = re.match(r'^([-+]?[\d.]+)', value_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Fallback: find first number in string
    numbers = re.findall(r'[-+]?[\d.]+', value_str)
    if numbers:
        try:
            # Remove commas from number string before conversion
            num_str = numbers[0].replace(',', '')
            return float(num_str)
        except ValueError:
            pass
    
    return None


class ChartBuilder:
    """Builds charts from processed data"""
    
    def __init__(self, output_dir: str = "output/charts"):
        """
        Initialize Chart Builder
        
        Args:
            output_dir: Directory to save charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_chart(
        self, 
        df: pd.DataFrame, 
        chart_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        """
        Create chart from dataframe
        
        Args:
            df: Processed dataframe
            chart_type: Type of chart (bar, line, pie)
            x_column: X-axis column name
            y_column: Y-axis column name
            title: Chart title
            
        Returns:
            Path to saved chart file
        """
        # Ensure df is a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"Expected DataFrame, got {type(df)}")
        
        if df.empty:
            raise ValueError("Cannot create chart from empty dataframe")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chart_{timestamp}.png"
        filepath = self.output_dir / filename
        
        # Determine columns if not specified
        if x_column is None or y_column is None:
            x_column, y_column = self._auto_detect_columns(df, chart_type)
        
        # Validate columns exist
        if x_column and x_column not in df.columns:
            raise ValueError(f"Column '{x_column}' not found in dataframe")
        if y_column and y_column not in df.columns:
            raise ValueError(f"Column '{y_column}' not found in dataframe")
        
        # For histogram, y_column can be None
        if chart_type == "histogram" and y_column is None:
            pass  # This is expected for histogram
        
        # Set style (fallback to default if seaborn not available)
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            try:
                plt.style.use('seaborn-darkgrid')
            except:
                plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 7))
        
        try:
            if chart_type == "bar":
                self._create_bar_chart(ax, df, x_column, y_column, title)
            elif chart_type == "line":
                self._create_line_chart(ax, df, x_column, y_column, title)
            elif chart_type == "pie":
                self._create_pie_chart(ax, df, x_column, y_column, title)
            elif chart_type == "histogram":
                self._create_histogram(ax, df, x_column, y_column, title)
            elif chart_type == "scatter":
                self._create_scatter_plot(ax, df, x_column, y_column, title)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Save chart
            try:
                plt.tight_layout()
            except Exception:
                # If tight_layout fails, continue anyway (just a warning)
                pass
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(filepath)
            
        except Exception as e:
            plt.close()
            raise RuntimeError(f"Failed to create chart: {str(e)}")
    
    def _auto_detect_columns(self, df: pd.DataFrame, chart_type: str) -> Tuple[str, str]:
        """
        Auto-detect appropriate columns for chart
        
        Args:
            df: Dataframe
            chart_type: Type of chart
            
        Returns:
            Tuple of (x_column, y_column)
        """
        if len(df.columns) == 0:
            raise ValueError("Dataframe has no columns")
        
        # For pie charts, use first two columns
        if chart_type == "pie":
            if len(df.columns) < 2:
                raise ValueError("Pie chart requires at least 2 columns")
            return df.columns[0], df.columns[1]
        
        # For histogram, use first numeric column
        if chart_type == "histogram":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("Histogram requires at least one numeric column")
            return numeric_cols[0], None
        
        # For scatter plots, need two numeric columns
        if chart_type == "scatter":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) < 2:
                raise ValueError("Scatter plot requires at least 2 numeric columns")
            return numeric_cols[0], numeric_cols[1]
        
        # For bar/line charts, find categorical and numeric columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Use first categorical as x, first numeric as y
        x_col = categorical_cols[0] if len(categorical_cols) > 0 else df.columns[0]
        y_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[-1]
        
        # If no numeric columns, use count
        if len(numeric_cols) == 0:
            y_col = "Count"
            df[y_col] = 1
        
        return x_col, y_col
    
    def _create_bar_chart(self, ax, df: pd.DataFrame, x_column: str, y_column: str, title: Optional[str]):
        """Create bar chart"""
        # Prepare data
        if y_column == "Count":
            data = df.groupby(x_column).size().reset_index(name=y_column)
            x_data = data[x_column].astype(str)  # Convert to string for labels
            y_data = data[y_column]
        else:
            x_data = df[x_column].astype(str)  # Convert to string for labels
            # Extract numeric values from formatted strings for y_column
            y_data = df[y_column].apply(_extract_numeric_from_string)
            # Remove rows where y_data extraction failed
            valid_mask = pd.Series([y is not None for y in y_data])
            x_data = x_data[valid_mask].astype(str)  # Ensure string type
            y_data = pd.Series([y for y, valid in zip(y_data, valid_mask) if valid])
        
        # Create bar chart
        bars = ax.bar(range(len(x_data)), y_data, color='#00A878', edgecolor='#008c67', linewidth=1.5)
        ax.set_xticks(range(len(x_data)))
        ax.set_xticklabels(x_data, rotation=45 if len(x_data) > 10 else 0, ha='right' if len(x_data) > 10 else 'center')
        
        # Customize
        ax.set_xlabel(x_column, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_column, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{y_column} by {x_column}", fontsize=14, fontweight='bold', pad=20)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        # Grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    def _create_line_chart(self, ax, df: pd.DataFrame, x_column: str, y_column: str, title: Optional[str]):
        """Create line chart"""
        # Prepare data
        if y_column == "Count":
            data = df.groupby(x_column).size().reset_index(name=y_column)
            x_data = data[x_column]
            y_data = data[y_column]
        else:
            x_data = df[x_column]
            # Extract numeric values from formatted strings for y_column
            y_data = df[y_column].apply(_extract_numeric_from_string)
            # Remove rows where y_data extraction failed
            valid_mask = pd.Series([y is not None for y in y_data])
            x_data = x_data[valid_mask]
            y_data = pd.Series([y for y, valid in zip(y_data, valid_mask) if valid])
        
        # Sort by x if numeric or convert to numeric index
        if pd.api.types.is_numeric_dtype(x_data):
            sorted_indices = x_data.argsort()
            x_data = x_data.iloc[sorted_indices]
            y_data = y_data.iloc[sorted_indices]
        
        # Create line chart
        ax.plot(x_data, y_data, marker='o', linewidth=2.5, markersize=8, 
                color='#00A878', markerfacecolor='#00c98c', markeredgecolor='#008c67')
        
        # Customize
        ax.set_xlabel(x_column, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_column, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{y_column} over {x_column}", fontsize=14, fontweight='bold', pad=20)
        
        # Rotate x-axis labels if needed
        if len(x_data) > 10:
            plt.xticks(rotation=45, ha='right')
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')
    
    def _create_pie_chart(self, ax, df: pd.DataFrame, x_column: str, y_column: str, title: Optional[str]):
        """Create pie chart"""
        # Prepare data - use first two columns
        if y_column == "Count":
            data = df.groupby(x_column).size().reset_index(name=y_column)
            labels = data[x_column].astype(str)
            values = data[y_column]
        else:
            labels = df[x_column].astype(str)
            values = df[y_column]
        
        # Limit to top 10 for readability
        if len(labels) > 10:
            sorted_indices = values.argsort()[::-1][:10]
            labels = labels.iloc[sorted_indices]
            values = values.iloc[sorted_indices]
        
        # Color palette matching brand colors
        colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(labels)))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                          colors=colors, startangle=90,
                                          textprops={'fontsize': 10, 'fontweight': 'bold'})
        
        # Customize
        ax.set_title(title or f"Distribution of {y_column} by {x_column}", 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Equal aspect ratio ensures pie is circular
        ax.axis('equal')
    
    def _create_histogram(self, ax, df: pd.DataFrame, x_column: str, y_column: Optional[str], title: Optional[str]):
        """Create histogram chart"""
        # Extract numeric values from formatted strings
        data = df[x_column].apply(_extract_numeric_from_string)
        data = pd.Series([x for x in data if x is not None])
        
        if len(data) == 0:
            raise ValueError(f"No valid numeric data in column '{x_column}'")
        
        # Create histogram
        n, bins, patches = ax.hist(data, bins=30, color='#00A878', edgecolor='#008c67', 
                                   linewidth=1.5, alpha=0.7)
        
        # Customize
        ax.set_xlabel(x_column, fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title(title or f"Distribution of {x_column}", fontsize=14, fontweight='bold', pad=20)
        
        # Grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    def _create_scatter_plot(self, ax, df: pd.DataFrame, x_column: str, y_column: str, title: Optional[str]):
        """Create scatter plot"""
        # Extract numeric values from formatted strings
        x_data = df[x_column].apply(_extract_numeric_from_string)
        y_data = df[y_column].apply(_extract_numeric_from_string)
        
        # Remove None values (where extraction failed)
        valid_mask = pd.Series([x is not None and y is not None 
                               for x, y in zip(x_data, y_data)])
        x_data = pd.Series([x for x, valid in zip(x_data, valid_mask) if valid])
        y_data = pd.Series([y for y, valid in zip(y_data, valid_mask) if valid])
        
        if len(x_data) == 0:
            raise ValueError(f"No valid numeric data in columns '{x_column}' and '{y_column}'")
        
        # Create scatter plot
        ax.scatter(x_data, y_data, color='#00A878', alpha=0.6, s=50, edgecolors='#008c67', linewidth=1)
        
        # Customize
        ax.set_xlabel(x_column, fontsize=12, fontweight='bold')
        ax.set_ylabel(y_column, fontsize=12, fontweight='bold')
        ax.set_title(title or f"{y_column} vs {x_column}", fontsize=14, fontweight='bold', pad=20)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')

