"""
Chart Executor

Executes chart generation based on chart configurations from ChartBot.
Creates chart images using ChartBuilder.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from services.chart_builder import ChartBuilder
import logging

logger = logging.getLogger(__name__)


class ChartExecutor:
    """Executes chart generation"""
    
    def __init__(self, df: pd.DataFrame, output_dir: str = "output/charts"):
        """
        Initialize chart executor
        
        Args:
            df: DataFrame to create chart from
            output_dir: Directory to save charts
        """
        self.df = df
        self.chart_builder = ChartBuilder(output_dir=output_dir)
        self.chart_paths: List[str] = []
        self.execution_log: List[str] = []
    
    def execute(self, chart_config: Dict) -> str:
        """
        Execute chart generation
        
        Args:
            chart_config: Chart configuration from ChartBot
                {
                    "chart_type": "bar|line|pie|histogram|scatter",
                    "x_column": "ColumnName",
                    "y_column": "ColumnName",
                    "title": "Chart Title",
                    "description": "Chart description"
                }
        
        Returns:
            Path to generated chart file
        """
        chart_type = chart_config.get("chart_type", "bar")
        x_column = chart_config.get("x_column")
        y_column = chart_config.get("y_column")
        title = chart_config.get("title", "Chart")
        description = chart_config.get("description", "Chart")
        
        try:
            # Validate columns exist
            if x_column and x_column not in self.df.columns:
                raise ValueError(f"Column '{x_column}' not found. Available: {list(self.df.columns)}")
            
            if y_column and y_column not in self.df.columns:
                raise ValueError(f"Column '{y_column}' not found. Available: {list(self.df.columns)}")
            
            # Generate chart using ChartBuilder
            chart_path = self.chart_builder.create_chart(
                df=self.df,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column,
                title=title
            )
            
            self.chart_paths.append(chart_path)
            self.execution_log.append(f"✓ Generated {chart_type} chart: {description}")
            logger.info(f"Generated chart: {description} -> {chart_path}")
            
            return chart_path
            
        except Exception as e:
            error_msg = f"Chart generation failed: {str(e)}"
            self.execution_log.append(f"✗ {error_msg}")
            logger.error(f"Chart error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def execute_multiple(self, chart_configs: List[Dict]) -> List[str]:
        """
        Execute multiple chart generations
        
        Args:
            chart_configs: List of chart configurations
            
        Returns:
            List of chart file paths
        """
        chart_paths = []
        if not chart_configs:
            logger.warning("No chart configurations provided to execute_multiple")
            return chart_paths
        
        logger.info(f"Generating {len(chart_configs)} charts for dashboard")
        
        for i, config in enumerate(chart_configs, 1):
            try:
                logger.info(f"Generating chart {i}/{len(chart_configs)}: {config.get('chart_type', 'unknown')} - {config.get('title', 'Untitled')}")
                path = self.execute(config)
                chart_paths.append(path)
                logger.info(f"✓ Chart {i} generated successfully: {path}")
            except Exception as e:
                logger.error(f"✗ Failed to generate chart {i}: {str(e)}", exc_info=True)
                self.execution_log.append(f"✗ Failed to generate chart {i} ({config.get('chart_type', 'unknown')}): {str(e)}")
                # Continue with other charts even if one fails
        
        if not chart_paths:
            raise RuntimeError(f"Failed to generate any charts. All {len(chart_configs)} chart generations failed.")
        
        logger.info(f"Successfully generated {len(chart_paths)}/{len(chart_configs)} charts")
        return chart_paths
    
    def get_chart_paths(self) -> List[str]:
        """Get all generated chart paths"""
        return self.chart_paths.copy()
    
    def get_execution_log(self) -> List[str]:
        """Get execution log"""
        return self.execution_log.copy()

