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
        # Limit DataFrame size to prevent OOM on low-memory servers
        # For 512MB servers, use sample of data for charts
        MAX_ROWS_FOR_CHART = 1000
        if len(df) > MAX_ROWS_FOR_CHART:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Limiting DataFrame to {MAX_ROWS_FOR_CHART} rows for chart generation (original: {len(df)} rows)")
            self.df = df.head(MAX_ROWS_FOR_CHART).copy()
        else:
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
            logger.info(f"Calling ChartBuilder.create_chart with type={chart_type}, x={x_column}, y={y_column}")
            chart_path = self.chart_builder.create_chart(
                df=self.df,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column,
                title=title
            )
            
            logger.info(f"ChartBuilder returned path: {chart_path}")
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
                
                # Force memory cleanup after each chart to prevent OOM
                import gc
                gc.collect()
                logger.info(f"Memory cleaned after chart {i}")
            except Exception as e:
                logger.error(f"✗ Failed to generate chart {i}: {str(e)}", exc_info=True)
                self.execution_log.append(f"✗ Failed to generate chart {i} ({config.get('chart_type', 'unknown')}): {str(e)}")
                # Continue with other charts even if one fails
                # Clean memory even on failure
                import gc
                gc.collect()
        
        if not chart_paths:
            raise RuntimeError(f"Failed to generate any charts. All {len(chart_configs)} chart generations failed.")
        
        logger.info(f"Successfully generated {len(chart_paths)}/{len(chart_configs)} charts")
        return chart_paths
    
    def get_chart_paths(self) -> List[str]:
        """Get all generated chart paths"""
        return self.chart_paths.copy()
    
    def execute_data(self, chart_config: Dict) -> Dict:
        """
        Execute chart data generation (returns JSON data for interactive charts, not image)
        
        Args:
            chart_config: Chart configuration dictionary
            
        Returns:
            Dictionary with chart data for frontend rendering
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
            
            # Generate chart data using ChartBuilder
            logger.info(f"Calling ChartBuilder.create_chart_data with type={chart_type}, x={x_column}, y={y_column}")
            chart_data = self.chart_builder.create_chart_data(
                df=self.df,
                chart_type=chart_type,
                x_column=x_column,
                y_column=y_column,
                title=title
            )
            
            self.execution_log.append(f"✓ Generated {chart_type} chart data: {description}")
            logger.info(f"Generated chart data: {description}")
            
            return chart_data
            
        except Exception as e:
            error_msg = f"Chart data generation failed: {str(e)}"
            self.execution_log.append(f"✗ {error_msg}")
            logger.error(f"Chart data error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def execute_multiple_data(self, chart_configs: List[Dict]) -> List[Dict]:
        """
        Execute multiple chart data generations
        
        Args:
            chart_configs: List of chart configurations
            
        Returns:
            List of chart data dictionaries for frontend rendering
        """
        chart_data_list = []
        if not chart_configs:
            logger.warning("No chart configurations provided to execute_multiple_data")
            return chart_data_list
        
        logger.info(f"Generating data for {len(chart_configs)} charts")
        
        for i, config in enumerate(chart_configs, 1):
            try:
                logger.info(f"Generating chart data {i}/{len(chart_configs)}: {config.get('chart_type', 'unknown')} - {config.get('title', 'Untitled')}")
                chart_data = self.execute_data(config)
                chart_data_list.append(chart_data)
                logger.info(f"✓ Chart data {i} generated successfully")
            except Exception as e:
                logger.error(f"✗ Failed to generate chart data {i}: {str(e)}", exc_info=True)
                self.execution_log.append(f"✗ Failed to generate chart data {i} ({config.get('chart_type', 'unknown')}): {str(e)}")
                # Continue with other charts even if one fails
        
        if not chart_data_list:
            raise RuntimeError(f"Failed to generate any chart data. All {len(chart_configs)} chart data generations failed.")
        
        logger.info(f"Successfully generated {len(chart_data_list)}/{len(chart_configs)} chart data objects")
        return chart_data_list
    
    def get_execution_log(self) -> List[str]:
        """Get execution log"""
        return self.execution_log.copy()

