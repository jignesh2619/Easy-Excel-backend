"""
XlsxWriter-based Excel Writer

Uses xlsxwriter for writing Excel files with formatting support.
"""

import pandas as pd
import xlsxwriter
from typing import Dict, List, Optional, Any
from pathlib import Path


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
        with pd.ExcelWriter(self.output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Format header row
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BC',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Apply formatting rules
            if formatting_rules:
                self._apply_formatting_rules(workbook, worksheet, df, formatting_rules)
            
            # Apply conditional formatting
            if conditional_formatting:
                self._apply_conditional_formatting(workbook, worksheet, df, conditional_formatting)
            
            # Auto-adjust column widths
            for i, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.set_column(i, i, min(max_length + 2, 50))
        
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
        for rule in rules:
            if rule.get("type") != "conditional":
                continue
            
            format_type = rule.get("format_type")
            config = rule.get("config", {})
            
            # Build cell format
            bg_color = config.get("bg_color") or config.get("background_color", "#FFF3CD")
            text_color = config.get("text_color") or config.get("font_color", "#000000")
            format_config = {"bg_color": bg_color}
            if text_color:
                format_config["font_color"] = text_color
            if config.get("bold"):
                format_config["bold"] = True
            cell_format = workbook.add_format(format_config)
            
            # Handle text-based conditional formatting
            if format_type in ["contains_text", "text_equals", "regex_match"]:
                target_text = config.get("text", "")
                column_spec = config.get("column")
                
                # Resolve columns
                if column_spec is None or str(column_spec).lower() == "all_columns":
                    columns = list(df.columns)
                elif column_spec in df.columns:
                    columns = [column_spec]
                else:
                    columns = []
                
                if not columns or not target_text:
                    continue
                
                # Apply formatting to matching cells
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
                        
                        for row_idx, match in enumerate(matches):
                            if match:
                                excel_row = row_idx + 1
                                cell_value = df.iloc[row_idx, col_idx]
                                
                                # Write with proper type handling
                                if pd.isna(cell_value):
                                    worksheet.write_blank(excel_row, col_idx, cell_format)
                                elif isinstance(cell_value, (int, float)):
                                    worksheet.write_number(excel_row, col_idx, cell_value, cell_format)
                                elif isinstance(cell_value, bool):
                                    worksheet.write_boolean(excel_row, col_idx, cell_value, cell_format)
                                else:
                                    worksheet.write_string(excel_row, col_idx, str(cell_value), cell_format)
                    except Exception as e:
                        continue

