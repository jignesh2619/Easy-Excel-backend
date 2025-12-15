"""
XlsxWriter-based Excel Writer

Uses xlsxwriter for writing Excel files with formatting support.
"""

import pandas as pd
import xlsxwriter
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging


class XlsxWriter:
    """Excel writer using xlsxwriter engine"""
    
    def __init__(self, output_path: str):
        """
        Initialize writer
        
        Args:
            output_path: Path to output Excel file
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write(self, df: pd.DataFrame, sheet_name: str = 'Sheet1', 
              formatting_rules: Optional[List[Dict]] = None,
              conditional_formatting: Optional[List[Dict]] = None) -> str:
        """
        Write dataframe to Excel with formatting
        
        Args:
            df: DataFrame to write
            sheet_name: Name of the sheet
            formatting_rules: List of formatting rules to apply
            conditional_formatting: List of conditional formatting rules
        
        Returns:
            Path to written file
        """
        logger = logging.getLogger(__name__)
        
        with pd.ExcelWriter(self.output_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet(sheet_name)
            
            # Build conditional format lookup for fast access
            conditional_formats = {}
            if conditional_formatting:
                logger.info(f"Building conditional format lookup from {len(conditional_formatting)} rules")
                conditional_formats = self._build_conditional_format_lookup(
                    workbook, df, conditional_formatting
                )
                logger.info(f"Conditional format lookup built: {len(conditional_formats)} cells to format")
                if conditional_formats:
                    # Log sample keys for debugging
                    sample_keys = list(conditional_formats.keys())[:5]
                    logger.info(f"Sample lookup keys: {sample_keys}")
                    logger.info(f"Sample lookup values: {[type(v).__name__ for v in [conditional_formats[k] for k in sample_keys]]}")
            
            # Write header row
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BC',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Write data row by row with conditional formatting applied
            logger.info(f"Writing {len(df)} rows with conditional formatting")
            formatted_cell_count = 0
            for row_idx in range(len(df)):
                for col_idx, col_name in enumerate(df.columns):
                    cell_value = df.iloc[row_idx, col_idx]
                    
                    # CRITICAL: Ensure cell_value is a scalar, not an array or DataFrame
                    # Convert arrays/DataFrames to string representation
                    if isinstance(cell_value, (pd.DataFrame, pd.Series, np.ndarray)):
                        logger.warning(f"Cell ({row_idx}, {col_name}) contains {type(cell_value).__name__}, converting to string")
                        if isinstance(cell_value, pd.Series):
                            # For Series, take first value or convert to string
                            if len(cell_value) > 0:
                                cell_value = cell_value.iloc[0] if not pd.isna(cell_value.iloc[0]) else None
                            else:
                                cell_value = None
                        elif isinstance(cell_value, pd.DataFrame):
                            # For DataFrame, convert to string representation
                            cell_value = str(cell_value)
                        elif isinstance(cell_value, np.ndarray):
                            # For numpy array, flatten if 1D, convert to string if multi-dimensional
                            if cell_value.ndim == 1 and len(cell_value) > 0:
                                cell_value = cell_value[0]
                            else:
                                cell_value = str(cell_value)
                    
                    # Check if this cell should have conditional formatting
                    cell_format = None
                    lookup_key = (row_idx, col_name)
                    if lookup_key in conditional_formats:
                        cell_format = conditional_formats[lookup_key]
                        formatted_cell_count += 1
                        if formatted_cell_count <= 10:  # Log first 10 for debugging
                            logger.info(f"✅ Applying format to cell ({row_idx}, {col_name}) = '{cell_value}' (Excel row {row_idx + 1})")
                            logger.info(f"   Format type: {type(cell_format).__name__}, Format object: {cell_format}")
                    
                    # Write cell with format
                    excel_row = row_idx + 1  # +1 for header row
                    try:
                        if pd.isna(cell_value):
                            if cell_format:
                                worksheet.write_blank(excel_row, col_idx, "", cell_format)
                            else:
                                worksheet.write_blank(excel_row, col_idx, "")
                        elif isinstance(cell_value, (int, float)):
                            if cell_format:
                                worksheet.write_number(excel_row, col_idx, cell_value, cell_format)
                            else:
                                worksheet.write_number(excel_row, col_idx, cell_value)
                        elif isinstance(cell_value, bool):
                            if cell_format:
                                worksheet.write_boolean(excel_row, col_idx, cell_value, cell_format)
                            else:
                                worksheet.write_boolean(excel_row, col_idx, cell_value)
                        else:
                            if cell_format:
                                worksheet.write_string(excel_row, col_idx, str(cell_value), cell_format)
                            else:
                                worksheet.write_string(excel_row, col_idx, str(cell_value))
                    except Exception as e:
                        logger.error(f"Error writing cell ({excel_row}, {col_idx}): {e}, value type: {type(cell_value)}, value: {cell_value}")
                        # Fallback: write without format
                        worksheet.write_string(excel_row, col_idx, str(cell_value) if not pd.isna(cell_value) else "")
            
            if conditional_formats:
                logger.info(f"Applied conditional formatting to {formatted_cell_count} cells during write")
            
            # Auto-adjust column widths (do this BEFORE applying static formatting to avoid conflicts)
            for i, col in enumerate(df.columns):
                try:
                    # Ensure we're working with a Series, not a nested structure
                    col_data = df[col]
                    if isinstance(col_data, pd.Series):
                        max_length = max(
                            col_data.astype(str).map(len).max() if len(col_data) > 0 else 0,
                            len(str(col))
                        )
                    else:
                        # Fallback if column is not a Series
                        max_length = len(str(col)) + 2
                    worksheet.set_column(i, i, min(max_length + 2, 50))
                except Exception as e:
                    logger.warning(f"Error setting column width for column '{col}': {e}")
                    worksheet.set_column(i, i, 15)  # Default width
            
            # Apply static formatting rules (non-conditional) - do this last
            if formatting_rules:
                self._apply_formatting_rules(workbook, worksheet, df, formatting_rules)
        
        return str(self.output_path)
    
    def _apply_formatting_rules(self, workbook, worksheet, df: pd.DataFrame, rules: List[Dict]):
        """Apply formatting rules to cells"""
        for rule in rules:
            if rule.get("type") != "format":
                continue
            
            formatting = rule.get("formatting", {})
            range_info = rule.get("range", {})
            
            # Build format
            format_dict = {}
            if formatting.get("bold"):
                format_dict['bold'] = True
            if formatting.get("italic"):
                format_dict['italic'] = True
            if formatting.get("bg_color"):
                format_dict['bg_color'] = formatting['bg_color']
            if formatting.get("text_color"):
                format_dict['font_color'] = formatting['text_color']
            if formatting.get("font_size"):
                format_dict['font_size'] = formatting['font_size']
            
            cell_format = workbook.add_format(format_dict)
            
            # Apply to range
            if "cells" in range_info:
                cells = range_info["cells"]
                for cell in cells:
                    row_idx = cell.get("row", 0)
                    col_name = cell.get("column")
                    if col_name in df.columns and 0 <= row_idx < len(df):
                        col_idx = list(df.columns).index(col_name)
                        excel_row = row_idx + 1
                        cell_value = df.iloc[row_idx, col_idx]
                        worksheet.write(excel_row, col_idx, cell_value, cell_format)
    
    def _apply_conditional_formatting(self, workbook, worksheet, df: pd.DataFrame, rules: List[Dict]):
        """Apply conditional formatting rules"""
        logger = logging.getLogger(__name__)
        
        for rule in rules:
            if rule.get("type") != "conditional":
                continue
            
            format_type = rule.get("format_type")
            config = rule.get("config", {})
            
            # Build cell format
            bg_color = config.get("bg_color") or config.get("background_color", "#FFF3CD")
            text_color = config.get("text_color") or config.get("font_color", "#000000")
            format_config = {
                "bg_color": bg_color,
                "pattern": 1  # Solid pattern - REQUIRED for bg_color to be visible in Excel!
            }
            if text_color:
                format_config["font_color"] = text_color
            if config.get("bold"):
                format_config["bold"] = True
            if config.get("italic"):
                format_config["italic"] = True
            if config.get("font_size"):
                format_config["font_size"] = config.get("font_size")
            cell_format = workbook.add_format(format_config)
            
            # Handle text-based conditional formatting
            if format_type in ["contains_text", "text_equals", "regex_match"]:
                target_text = config.get("text", "")
                column_spec = config.get("column")
                
                # Resolve columns with case-insensitive matching
                if column_spec is None or str(column_spec).lower() == "all_columns":
                    columns = list(df.columns)
                elif column_spec in df.columns:
                    columns = [column_spec]
                else:
                    # Try case-insensitive match
                    matching_cols = [col for col in df.columns if str(col).lower() == str(column_spec).lower()]
                    if matching_cols:
                        columns = matching_cols
                        logger.info(f"Matched column '{column_spec}' to '{matching_cols[0]}' (case-insensitive)")
                    else:
                        columns = []
                        logger.warning(f"Column '{column_spec}' not found. Available: {list(df.columns)[:10]}")
                
                if not columns or not target_text:
                    logger.warning(f"Skipping conditional format: columns={columns}, target_text='{target_text}'")
                    continue
                
                # Apply formatting to matching cells
                matched_count = 0
                for column in columns:
                    if column not in df.columns:
                        continue
                    col_idx = list(df.columns).index(column)
                    series = df[column].astype(str)
                    
                    try:
                        if format_type == "contains_text":
                            matches = series.str.contains(str(target_text), case=False, na=False)
                        elif format_type == "text_equals":
                            matches = series.str.lower() == str(target_text).lower()
                        else:  # regex_match
                            pattern = config.get("pattern", target_text)
                            matches = series.str.contains(pattern, na=False, regex=True)
                        
                        match_count = matches.sum()
                        logger.info(f"Found {match_count} matches for '{target_text}' in column '{column}'")
                        
                        for row_idx, match in enumerate(matches):
                            if match:
                                # Excel rows: 0 = header, 1+ = data rows
                                # DataFrame row_idx: 0 = first data row
                                # So: excel_row = row_idx + 1 (skip header row)
                                excel_row = row_idx + 1
                                cell_value = df.iloc[row_idx, col_idx]
                                
                                # Write with proper type handling - overwrites existing cell with format
                                if pd.isna(cell_value):
                                    worksheet.write_blank(excel_row, col_idx, "", cell_format)
                                elif isinstance(cell_value, (int, float)):
                                    worksheet.write_number(excel_row, col_idx, cell_value, cell_format)
                                elif isinstance(cell_value, bool):
                                    worksheet.write_boolean(excel_row, col_idx, cell_value, cell_format)
                                else:
                                    worksheet.write_string(excel_row, col_idx, str(cell_value), cell_format)
                                matched_count += 1
                    except Exception as e:
                        logger.error(f"Error applying conditional formatting to column '{column}': {e}", exc_info=True)
                        continue
                
                logger.info(f"Applied conditional formatting: {matched_count} cells formatted in column(s) {columns}")
    
    def _build_conditional_format_lookup(self, workbook, df: pd.DataFrame, rules: List[Dict]) -> Dict[Tuple[int, str], Any]:
        """Build a lookup dict: (row_idx, column_name) -> format object"""
        logger = logging.getLogger(__name__)
        format_lookup = {}
        
        for rule in rules:
            if rule.get("type") != "conditional":
                continue
            
            format_type = rule.get("format_type")
            config = rule.get("config", {})
            
            # Build cell format
            bg_color = config.get("bg_color") or config.get("background_color", "#FFF3CD")
            text_color = config.get("text_color") or config.get("font_color", "#000000")
            format_config = {
                "bg_color": bg_color,
                "pattern": 1  # Solid pattern - REQUIRED for bg_color to be visible in Excel!
            }
            if text_color:
                format_config["font_color"] = text_color
            if config.get("bold"):
                format_config["bold"] = True
            if config.get("italic"):
                format_config["italic"] = True
            if config.get("font_size"):
                format_config["font_size"] = config.get("font_size")
            cell_format = workbook.add_format(format_config)
            
            # Handle text-based conditional formatting
            if format_type in ["contains_text", "text_equals", "regex_match"]:
                target_text = config.get("text", "")
                column_spec = config.get("column")
                
                # Resolve columns with case-insensitive matching
                if column_spec is None or str(column_spec).lower() == "all_columns":
                    columns = list(df.columns)
                elif column_spec in df.columns:
                    columns = [column_spec]
                else:
                    matching_cols = [col for col in df.columns if str(col).lower() == str(column_spec).lower()]
                    if matching_cols:
                        columns = matching_cols
                        logger.info(f"Matched column '{column_spec}' to '{matching_cols[0]}' (case-insensitive)")
                    else:
                        columns = []
                        logger.warning(f"Column '{column_spec}' not found. Available: {list(df.columns)[:10]}")
                
                if not columns or not target_text:
                    logger.warning(f"Skipping conditional format: columns={columns}, target_text='{target_text}'")
                    continue
                
                # Find matching cells and add to lookup
                matched_count = 0
                for column in columns:
                    if column not in df.columns:
                        continue
                    series = df[column].astype(str)
                    
                    try:
                        if format_type == "contains_text":
                            matches = series.str.contains(str(target_text), case=False, na=False)
                        elif format_type == "text_equals":
                            matches = series.str.lower() == str(target_text).lower()
                        else:  # regex_match
                            pattern = config.get("pattern", target_text)
                            matches = series.str.contains(pattern, na=False, regex=True)
                        
                        match_count = matches.sum()
                        logger.info(f"Found {match_count} matches for '{target_text}' in column '{column}'")
                        
                        for row_idx, match in enumerate(matches):
                            if match:
                                format_lookup[(row_idx, column)] = cell_format
                                matched_count += 1
                    except Exception as e:
                        logger.error(f"Error building conditional format lookup for column '{column}': {e}", exc_info=True)
                        continue
                
                logger.info(f"Built conditional format lookup: {matched_count} cells will be formatted in column(s) {columns}")
        
        return format_lookup

