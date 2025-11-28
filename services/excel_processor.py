"""
Excel Processor Service

Executes data operations based on LLM action plans using pandas.
Handles all data modifications deterministically.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import re
import xlsxwriter
from datetime import datetime
from services.formula_engine import FormulaEngine
# New modular imports
from services.excel_writer.write_xlsx import XlsxWriter
from services.summarizer.excel_summary import ExcelSummarizer
from services.cleaning.dates import DateCleaner
from services.cleaning.currency import CurrencyCleaner
from services.cleaning.text import TextCleaner
from services.dflib import default_engine, DataFrameWrapper
from services.python_executor import PythonExecutor
from services.chart_executor import ChartExecutor


class ExcelProcessor:
    """Processes Excel/CSV files based on action plans"""
    
    def __init__(self, file_path: str):
        """
        Initialize Excel Processor
        
        Args:
            file_path: Path to input Excel/CSV file
        """
        self.file_path = file_path
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None
        self.summary: List[str] = []
        self.formatting_rules: List[Dict] = []  # Store formatting instructions
        self.formula_result: Optional[Any] = None  # Store formula computation result
        self.file_summary: Optional[Dict] = None  # Store file summary from ExcelSummarizer

    def _extract_text_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract quoted or keyword text from user prompt."""
        if not prompt:
            return None
        match = re.search(r'"([^"]+)"', prompt)
        if match:
            return match.group(1).strip()
        match = re.search(r"'([^']+)'", prompt)
        if match:
            return match.group(1).strip()
        match = re.search(r'keyword\s+([A-Za-z0-9 \-\._]+)', prompt, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip('"').strip("'")
        return None

    def _infer_column_from_prompt(self, prompt: str) -> Optional[str]:
        """Infer column name from user prompt via letters, ordinals, or direct mention."""
        if not prompt or self.df is None:
            return None
        prompt_lower = prompt.lower()
        
        # Direct column name mention
        for col in self.df.columns:
            col_lower = str(col).lower()
            if col_lower and col_lower in prompt_lower:
                return col
        
        # Column letter (e.g., column L)
        letter_match = re.search(r'column\s+([A-Z]{1,3})', prompt, re.IGNORECASE)
        if letter_match:
            letters = letter_match.group(1).upper()
            col_idx = 0
            for ch in letters:
                col_idx = col_idx * 26 + (ord(ch) - ord('A') + 1)
            col_idx -= 1
            if 0 <= col_idx < len(self.df.columns):
                return self.df.columns[col_idx]
        
        # Positional references (e.g., 2nd column)
        ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+column', prompt_lower)
        if ordinal_match:
            idx = int(ordinal_match.group(1)) - 1
            if 0 <= idx < len(self.df.columns):
                return self.df.columns[idx]
        
        return None

    def _find_column_with_text(self, text: str) -> Optional[str]:
        """Find first column that contains the given text in any cell."""
        if not text or self.df is None:
            return None
        for col in self.df.columns:
            try:
                if self.df[col].astype(str).str.contains(str(text), case=False, na=False).any():
                    return col
            except Exception:
                continue
        return None

    def _prompt_implies_conditional_format(self, prompt: str) -> bool:
        """Detect if user prompt asks for conditional formatting/highlighting."""
        if not prompt:
            return False
        keywords = [
            "highlight", "mark", "color", "colour", "flag", "shade",
            "make it yellow", "bold cells", "format cells", "highlight cells", "highlight rows",
            "paint", "background", "bg color", "background color"
        ]
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in keywords)

    def _extract_color_from_prompt(self, prompt: str) -> Optional[str]:
        """Extract color name from prompt and convert to hex code."""
        if not prompt:
            return None
        prompt_lower = prompt.lower()
        
        color_map = {
            "green": "#90EE90",  # Light green
            "yellow": "#FFFF00",
            "red": "#FF0000",
            "blue": "#0000FF",
            "orange": "#FFA500",
            "pink": "#FFC0CB",
            "purple": "#800080",
            "cyan": "#00FFFF",
            "grey": "#808080",
            "gray": "#808080",
        }
        
        for color_name, hex_code in color_map.items():
            if color_name in prompt_lower:
                return hex_code
        
        return None

    def _build_conditional_format_fallback(self, action_plan: Dict) -> Optional[Dict[str, Any]]:
        """Construct conditional format configuration directly from the user prompt."""
        prompt = action_plan.get("user_prompt", "") or ""
        target_text = self._extract_text_from_prompt(prompt)
        if not target_text:
            return None
        
        column = self._infer_column_from_prompt(prompt)
        if not column:
            column = self._find_column_with_text(target_text)
        if not column:
            return None
        
        # Extract color from prompt
        bg_color = self._extract_color_from_prompt(prompt) or "#FFF3CD"  # Default yellow
        
        return {
            "format_type": "contains_text",
            "config": {
                "column": column,
                "text": target_text,
                "bg_color": bg_color,
                "text_color": "#000000",
                "bold": False
            }
        }

    def _build_filter_fallback(self, action_plan: Dict) -> Optional[Dict[str, Any]]:
        """Construct filter configuration directly from the user prompt."""
        prompt = action_plan.get("user_prompt", "") or ""
        if not prompt:
            return None
        prompt_lower = prompt.lower()
        
        value = self._extract_text_from_prompt(prompt)
        if not value:
            return None
        
        column = self._infer_column_from_prompt(prompt)
        if not column:
            column = self._find_column_with_text(value)
        if not column:
            return None
        
        if any(keyword in prompt_lower for keyword in ["remove", "delete", "exclude"]):
            condition = "not_contains"
        else:
            condition = "contains"
        
        return {
            "column": column,
            "condition": condition,
            "value": value
        }
        
    def load_data(self, sheet_name: Optional[str] = None) -> bool:
        """
        Load data from file
        
        Args:
            sheet_name: Sheet name for Excel files (None for CSV or first sheet)
            
        Returns:
            True if loaded successfully
        """
        try:
            file_ext = Path(self.file_path).suffix.lower()
            
            if file_ext == '.csv':
                # Try different encodings for CSV files
                encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                self.df = None
                last_error = None
                for encoding in encodings:
                    try:
                        self.df = pd.read_csv(self.file_path, encoding=encoding, on_bad_lines='skip')
                        break
                    except (UnicodeDecodeError, Exception) as e:
                        last_error = e
                        continue
                
                if self.df is None:
                    raise RuntimeError(f"Failed to read CSV file with multiple encodings. Last error: {str(last_error)}")
                    
            elif file_ext in ['.xlsx', '.xls']:
                # Always specify sheet_name to avoid getting a dict
                # If sheet_name is None, use 0 to get first sheet
                try:
                    if sheet_name is None:
                        loaded_data = pd.read_excel(
                            self.file_path, 
                            sheet_name=0,
                            engine='openpyxl' if file_ext == '.xlsx' else None
                        )
                    else:
                        loaded_data = pd.read_excel(
                            self.file_path, 
                            sheet_name=sheet_name,
                            engine='openpyxl' if file_ext == '.xlsx' else None
                        )
                except Exception as e:
                    # Try without engine specification for .xls files
                    if file_ext == '.xls':
                        try:
                            if sheet_name is None:
                                loaded_data = pd.read_excel(self.file_path, sheet_name=0)
                            else:
                                loaded_data = pd.read_excel(self.file_path, sheet_name=sheet_name)
                        except Exception as e2:
                            raise RuntimeError(f"Failed to read Excel file. The file may be corrupted. Error: {str(e2)}")
                    else:
                        raise RuntimeError(f"Failed to read Excel file. The file may be corrupted. Error: {str(e)}")
                
                # Check if we got a dict (shouldn't happen with sheet_name specified, but double-check)
                if isinstance(loaded_data, dict):
                    # If it's a dict, get the first sheet
                    if len(loaded_data) > 0:
                        self.df = list(loaded_data.values())[0]
                    else:
                        raise ValueError("Excel file has no sheets")
                else:
                    self.df = loaded_data
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Ensure we have a DataFrame
            if not isinstance(self.df, pd.DataFrame):
                raise ValueError(f"Expected DataFrame, got {type(self.df)}")
            
            # Keep original copy
            self.original_df = self.df.copy()
            self.summary.append(f"Loaded {len(self.df)} rows and {len(self.df.columns)} columns")
            
            # Generate summary using new summarizer module
            try:
                summarizer = ExcelSummarizer(self.df)
                self.file_summary = summarizer.generate_summary()
            except Exception as e:
                # If summarizer fails, continue without it
                self.file_summary = None
            
            return True
            
        except pd.errors.EmptyDataError:
            raise RuntimeError("File appears to be empty or corrupted. Please check the file and try again.")
        except pd.errors.ParserError as e:
            raise RuntimeError(f"Error parsing file structure. Please ensure the file is properly formatted. Details: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to load data: {str(e)}. Please ensure the file is not corrupted and is in a supported format.")
    
    def execute_action_plan(self, action_plan: Dict) -> Dict:
        """
        Execute action plan - unified execution using PythonExecutor and ChartExecutor
        
        Args:
            action_plan: Structured action plan from LLM
            
        Returns:
            Dictionary with processed dataframe and summary
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        task = action_plan.get("task", "execute")
        chart_path = None
        
        try:
            # Handle chart requests
            if task == "chart" or "chart_config" in action_plan:
                chart_config = action_plan.get("chart_config", {})
                if chart_config:
                    chart_executor = ChartExecutor(self.df)
                    chart_path = chart_executor.execute(chart_config)
                    self.summary.extend(chart_executor.get_execution_log())
                    chart_type = chart_config.get("chart_type", "chart")
                    self.summary.append(f"Generated {chart_type} chart")
            
            # Handle data operations (Python code execution)
            operations = action_plan.get("operations", [])
            if operations:
                python_executor = PythonExecutor(self.df)
                execution_result = python_executor.execute_multiple(operations)
                self.df = python_executor.get_dataframe()
                self.summary.extend(python_executor.get_execution_log())
                
                # Store formula result if present
                if execution_result.get("results"):
                    for result in execution_result["results"]:
                        if result.get("result") is not None:
                            self.formula_result = result["result"]
                            break
            
            # Handle conditional formatting (still needs special handling)
            if "conditional_format" in action_plan:
                self._execute_conditional_format(action_plan)
            
            # Handle formatting (still needs special handling)
            if "format" in action_plan:
                self._execute_format(action_plan)
            
            return {
                "df": self.df,
                "summary": self.summary,
                "chart_path": chart_path,
                "chart_needed": chart_path is not None,
                "chart_type": action_plan.get("chart_config", {}).get("chart_type", "none") if chart_path else "none",
                "formula_result": self.formula_result,
                "task": task
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to execute action plan: {str(e)}")
    
    def _execute_clean(self, action_plan: Dict):
        """Execute cleaning operations - ONLY what user requests"""
        initial_rows = len(self.df)
        
        # Check if user explicitly requested general cleaning
        # If operations array is empty or only contains specific operations, don't run default cleaning
        operations = action_plan.get("operations", [])
        user_requested_general_cleaning = False
        
        # Check if user explicitly asked for general cleaning keywords
        user_prompt_lower = action_plan.get("user_prompt", "").lower() if action_plan.get("user_prompt") else ""
        if any(keyword in user_prompt_lower for keyword in ["clean", "cleaning", "clean the data", "clean data", "remove duplicates", "fix formatting", "handle missing"]):
            user_requested_general_cleaning = True
        
        # Process operations array if provided (for specific cleaning tasks)
        operation_executed = False
        for op in operations:
            op_type = op.get("type", "")
            params = op.get("params", {})
            exec_instructions = op.get("execution_instructions", {})
            
            # Handle character removal/replacement operations
            if op_type in ["remove_characters", "replace_text", "clean_text"] or "remove" in op_type.lower() or "replace" in op_type.lower():
                column = params.get("column") or exec_instructions.get("kwargs", {}).get("column")
                # Try to find column with case-insensitive matching - improved matching for phone numbers
                if column:
                    matching_column = None
                    column_lower = column.lower().strip()
                    for col in self.df.columns:
                        col_lower = col.lower().strip()
                        # Exact match
                        if col_lower == column_lower:
                            matching_column = col
                            break
                        # Partial match (e.g., "phone number" matches "phone numbers")
                        if column_lower in col_lower or col_lower in column_lower:
                            matching_column = col
                            break
                        # Check for common variations (phone, phone number, phone numbers, etc.)
                        if "phone" in column_lower and "phone" in col_lower:
                            matching_column = col
                            break
                    if matching_column:
                        column = matching_column
                
                if column and column in self.df.columns:
                    # Get the character/pattern to remove or replace
                    char_to_remove = params.get("character") or params.get("pattern") or params.get("value") or params.get("old") or ""
                    # Get replacement value (empty string for "remove", space for "replace with space", or specified value)
                    replace_with = params.get("replace_with") or params.get("new") or params.get("replacement") or ""
                    # Check if user wants to replace with space/blank
                    if replace_with == "" and (params.get("replace_with_space") or params.get("with_blank") or params.get("with_space")):
                        replace_with = " "  # Replace with space
                    remove_from = params.get("position", "all")  # start, end, all
                    
                    # For phone numbers, try common patterns if not specified
                    if not char_to_remove and ("phone" in column.lower() or "number" in column.lower()):
                        # Try common phone number patterns: middle dot "· ", regular dot ". ", or just "."
                        # Check what's actually in the data first
                        sample_value = str(self.df[column].iloc[0]) if len(self.df) > 0 else ""
                        if "· " in sample_value:
                            char_to_remove = "· "  # Middle dot + space
                        elif ". " in sample_value:
                            char_to_remove = ". "  # Regular dot + space
                        elif "·" in sample_value:
                            char_to_remove = "·"  # Middle dot only
                        elif "." in sample_value and sample_value.startswith("."):
                            char_to_remove = "."  # Regular dot at start
                        else:
                            char_to_remove = "."  # Default fallback
                    elif not char_to_remove:
                        char_to_remove = "."
                    
                    if char_to_remove:
                        if remove_from == "start":
                            # Remove/replace from beginning - handles multi-char patterns
                            if len(char_to_remove) > 1:
                                # For multi-character patterns, use replace with count=1 and start check
                                self.df[column] = self.df[column].astype(str).apply(
                                    lambda x: x[len(char_to_remove):] if x.startswith(char_to_remove) else x
                                ) if replace_with == "" else self.df[column].astype(str).apply(
                                    lambda x: replace_with + x[len(char_to_remove):] if x.startswith(char_to_remove) else x
                                )
                            else:
                                if replace_with == "":
                                    self.df[column] = self.df[column].astype(str).str.lstrip(char_to_remove)
                                else:
                                    self.df[column] = self.df[column].astype(str).apply(
                                        lambda x: replace_with + x.lstrip(char_to_remove) if x.startswith(char_to_remove) else x
                                    )
                            action = "Replaced" if replace_with != "" else "Removed"
                            replacement_text = f" with '{replace_with}'" if replace_with != "" else ""
                            self.summary.append(f"{action} '{char_to_remove}' from start of '{column}' column{replacement_text}")
                            operation_executed = True
                        elif remove_from == "end":
                            # Remove/replace from end - handles multi-char patterns
                            if len(char_to_remove) > 1:
                                self.df[column] = self.df[column].astype(str).apply(
                                    lambda x: x[:-len(char_to_remove)] if x.endswith(char_to_remove) else x
                                ) if replace_with == "" else self.df[column].astype(str).apply(
                                    lambda x: x[:-len(char_to_remove)] + replace_with if x.endswith(char_to_remove) else x
                                )
                            else:
                                if replace_with == "":
                                    self.df[column] = self.df[column].astype(str).str.rstrip(char_to_remove)
                                else:
                                    self.df[column] = self.df[column].astype(str).apply(
                                        lambda x: x.rstrip(char_to_remove) + replace_with if x.endswith(char_to_remove) else x
                                    )
                            action = "Replaced" if replace_with != "" else "Removed"
                            replacement_text = f" with '{replace_with}'" if replace_with != "" else ""
                            self.summary.append(f"{action} '{char_to_remove}' from end of '{column}' column{replacement_text}")
                            operation_executed = True
                        else:
                            # Remove/replace all occurrences - works for both single and multi-char patterns
                            self.df[column] = self.df[column].astype(str).str.replace(char_to_remove, replace_with, regex=False)
                            action = "Replaced" if replace_with != "" else "Removed"
                            replacement_text = f" with '{replace_with}'" if replace_with != "" else ""
                            self.summary.append(f"{action} all '{char_to_remove}' from '{column}' column{replacement_text}")
                            operation_executed = True
                else:
                    # Try to find column by partial name match
                    if column:
                        possible_columns = [col for col in self.df.columns if "phone" in col.lower() or "number" in col.lower()]
                        if possible_columns:
                            # Use first matching column
                            column = possible_columns[0]
                            char_to_remove = params.get("character") or params.get("pattern") or params.get("value", "")
                            remove_from = params.get("position", "all")
                            
                            # Auto-detect phone number pattern
                            if not char_to_remove and len(self.df) > 0:
                                sample_value = str(self.df[column].iloc[0])
                                if "· " in sample_value:
                                    char_to_remove = "· "
                                elif ". " in sample_value:
                                    char_to_remove = ". "
                                elif "·" in sample_value:
                                    char_to_remove = "·"
                                elif sample_value.startswith("."):
                                    char_to_remove = "."
                                else:
                                    char_to_remove = "."
                            
                            # Get replacement value
                            replace_with = params.get("replace_with") or params.get("new") or params.get("replacement") or ""
                            if replace_with == "" and (params.get("replace_with_space") or params.get("with_blank") or params.get("with_space")):
                                replace_with = " "
                            
                            if char_to_remove:
                                # Remove/replace all occurrences (most common for phone numbers)
                                self.df[column] = self.df[column].astype(str).str.replace(char_to_remove, replace_with, regex=False)
                                action = "Replaced" if replace_with != "" else "Removed"
                                replacement_text = f" with '{replace_with}'" if replace_with != "" else ""
                                self.summary.append(f"{action} all '{char_to_remove}' from '{column}' column{replacement_text}")
                                operation_executed = True
            
            # Handle execution instructions for pandas operations
            if exec_instructions.get("method"):
                method_path = exec_instructions.get("method", "")
                if "pandas" in method_path or "str" in method_path:
                    column = exec_instructions.get("kwargs", {}).get("column") or params.get("column")
                    # Improved column matching
                    if column:
                        matching_column = None
                        column_lower = column.lower().strip()
                        for col in self.df.columns:
                            col_lower = col.lower().strip()
                            if col_lower == column_lower or column_lower in col_lower or col_lower in column_lower:
                                matching_column = col
                                break
                            if "phone" in column_lower and "phone" in col_lower:
                                matching_column = col
                                break
                        if matching_column:
                            column = matching_column
                    
                    if column and column in self.df.columns:
                        # Handle string operations
                        if "lstrip" in method_path or "remove_start" in method_path.lower():
                            char = exec_instructions.get("kwargs", {}).get("char", ".")
                            self.df[column] = self.df[column].astype(str).str.lstrip(char)
                            self.summary.append(f"Removed '{char}' from start of '{column}' column")
                            operation_executed = True
                        elif "rstrip" in method_path or "remove_end" in method_path.lower():
                            char = exec_instructions.get("kwargs", {}).get("char", ".")
                            self.df[column] = self.df[column].astype(str).str.rstrip(char)
                            self.summary.append(f"Removed '{char}' from end of '{column}' column")
                            operation_executed = True
                        elif "replace" in method_path:
                            old = exec_instructions.get("kwargs", {}).get("old", ".")
                            new = exec_instructions.get("kwargs", {}).get("new", "")
                            self.df[column] = self.df[column].astype(str).str.replace(old, new, regex=False)
                            self.summary.append(f"Replaced '{old}' with '{new}' in '{column}' column")
                            operation_executed = True
        
        # Only run default cleaning steps if:
        # 1. User explicitly requested general cleaning, OR
        # 2. No specific operations were executed
        if user_requested_general_cleaning or (not operation_executed and len(operations) == 0):
            # Remove duplicates
            rows_before_dup = len(self.df)
            self.df = self.df.drop_duplicates()
            duplicates_removed = rows_before_dup - len(self.df)
            if duplicates_removed > 0:
                self.summary.append(f"Removed {duplicates_removed} duplicate rows")
            
            # Fix formatting - trim whitespace from string columns
            string_columns = self.df.select_dtypes(include=['object']).columns
            for col in string_columns:
                self.df[col] = self.df[col].astype(str).str.strip()
                self.df[col] = self.df[col].replace('nan', np.nan)
            
            if len(string_columns) > 0:
                self.summary.append(f"Fixed formatting in {len(string_columns)} text columns")
            
            # Handle missing values - fill with appropriate defaults
            missing_counts = self.df.isnull().sum()
            for col in missing_counts[missing_counts > 0].index:
                if self.df[col].dtype in ['int64', 'float64']:
                    self.df[col] = self.df[col].fillna(0)
                else:
                    self.df[col] = self.df[col].fillna('')
            
            total_missing = missing_counts.sum()
            if total_missing > 0:
                self.summary.append(f"Handled {total_missing} missing values")
        
        # Always show final row count
        self.summary.append(f"Final data: {len(self.df)} rows, {len(self.df.columns)} columns")
    
    def _execute_group_by(self, action_plan: Dict):
        """Execute group by operations"""
        group_by_col = action_plan.get("group_by_column")
        agg_func = action_plan.get("aggregate_function", "sum")
        agg_col = action_plan.get("aggregate_column")
        
        if not group_by_col:
            self.summary.append("Group by: No column specified")
            return
        
        if group_by_col not in self.df.columns:
            raise ValueError(f"Column '{group_by_col}' not found")
        
        if agg_col and agg_col not in self.df.columns:
            raise ValueError(f"Column '{agg_col}' not found")
        
        # Map aggregate functions
        agg_map = {
            "sum": "sum",
            "mean": "mean",
            "avg": "mean",
            "average": "mean",
            "count": "count",
            "max": "max",
            "min": "min"
        }
        
        agg_func = agg_map.get(agg_func.lower(), "sum")
        
        if agg_col:
            # Group by and aggregate specific column
            grouped = self.df.groupby(group_by_col)[agg_col].agg(agg_func).reset_index()
            grouped.columns = [group_by_col, f"{agg_func.capitalize()}_{agg_col}"]
        else:
            # Group by and aggregate all numeric columns
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric columns to aggregate")
            
            grouped = self.df.groupby(group_by_col)[numeric_cols].agg(agg_func).reset_index()
        
        self.df = grouped
        self.summary.append(f"Grouped by '{group_by_col}' with {agg_func} aggregation")
        self.summary.append(f"Result: {len(self.df)} groups")
    
    def _execute_summarize(self, action_plan: Dict):
        """Execute summary operations
        
        NOTE: This creates summary statistics (count, mean, std, etc.)
        If user wants actual data after cleaning, use task: "clean" instead.
        """
        columns_needed = action_plan.get("columns_needed", [])
        
        if columns_needed:
            # Summarize specific columns
            available_cols = [col for col in columns_needed if col in self.df.columns]
            if available_cols:
                numeric_cols = self.df[available_cols].select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    summary = self.df[numeric_cols].describe()
                    self.df = summary.reset_index()
                    self.summary.append(f"Generated summary statistics for {len(numeric_cols)} columns")
                else:
                    self.summary.append("No numeric columns found for summary")
            else:
                self.summary.append("None of the specified columns found")
        else:
            # Summarize all numeric columns
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                summary = self.df[numeric_cols].describe()
                self.df = summary.reset_index()
                self.summary.append(f"Generated summary statistics for all {len(numeric_cols)} numeric columns")
            else:
                self.summary.append("No numeric columns found for summary")
    
    def _execute_filter(self, action_plan: Dict):
        """Execute filter operations"""
        filters = action_plan.get("filters", {})
        
        if not filters:
            fallback = self._build_filter_fallback(action_plan)
            if fallback:
                filters = fallback
                self.summary.append("Filter: Applied fallback configuration from user prompt.")
            else:
                self.summary.append("Filter: No filter conditions specified")
                return
        
        column = filters.get("column")
        condition = filters.get("condition", "==")
        value = filters.get("value")
        
        if not column or column not in self.df.columns:
            raise ValueError(f"Filter column '{column}' not found")
        
        initial_rows = len(self.df)
        
        # Apply filter
        if condition == ">":
            self.df = self.df[self.df[column] > value]
        elif condition == ">=":
            self.df = self.df[self.df[column] >= value]
        elif condition == "<":
            self.df = self.df[self.df[column] < value]
        elif condition == "<=":
            self.df = self.df[self.df[column] <= value]
        elif condition == "==":
            self.df = self.df[self.df[column] == value]
        elif condition == "!=":
            self.df = self.df[self.df[column] != value]
        elif condition == "contains":
            # Filter rows where column contains the text (case-insensitive)
            self.df = self.df[self.df[column].astype(str).str.contains(str(value), case=False, na=False)]
        elif condition == "not_contains":
            # Filter rows where column does NOT contain the text (case-insensitive)
            self.df = self.df[~self.df[column].astype(str).str.contains(str(value), case=False, na=False)]
        else:
            raise ValueError(f"Unsupported filter condition: {condition}")
        
        filtered_rows = len(self.df)
        removed = initial_rows - filtered_rows
        self.summary.append(f"Filtered '{column}' {condition} {value}")
        self.summary.append(f"Result: {filtered_rows} rows (removed {removed})")
    
    def _execute_find_missing(self, action_plan: Dict):
        """Find and report missing values"""
        missing_counts = self.df.isnull().sum()
        missing_cols = missing_counts[missing_counts > 0]
        
        if len(missing_cols) == 0:
            self.summary.append("No missing values found")
        else:
            self.summary.append(f"Found missing values in {len(missing_cols)} columns:")
            for col, count in missing_cols.items():
                percentage = (count / len(self.df)) * 100
                self.summary.append(f"  - {col}: {count} ({percentage:.1f}%)")
        
        # Create a summary dataframe
        if len(missing_cols) > 0:
            missing_df = pd.DataFrame({
                'Column': missing_cols.index,
                'Missing_Count': missing_cols.values,
                'Missing_Percentage': [(count / len(self.df)) * 100 for count in missing_cols.values]
            })
            self.df = missing_df
    
    def _execute_transform(self, action_plan: Dict):
        """Execute transformation operations"""
        steps = action_plan.get("steps", [])
        
        for step in steps:
            step_lower = step.lower()
            if "pivot" in step_lower:
                # Simple pivot - would need more context in real implementation
                self.summary.append("Transform: Pivot operation (not fully implemented)")
            elif "normalize" in step_lower:
                # Normalize numeric columns
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    self.df[col] = (self.df[col] - self.df[col].min()) / (self.df[col].max() - self.df[col].min())
                self.summary.append(f"Normalized {len(numeric_cols)} numeric columns")
            else:
                self.summary.append(f"Transform step: {step}")
    
    def save_processed_file(self, output_path: str) -> str:
        """
        Save processed dataframe to Excel file
        
        Args:
            output_path: Path to save output file
            
        Returns:
            Path to saved file
        """
        if self.df is None:
            raise ValueError("No data to save")
        
        try:
            # Use new modular XlsxWriter
            writer = XlsxWriter(output_path)
            
            # Separate formatting and conditional formatting rules
            formatting_rules = [r for r in self.formatting_rules if r.get("type") == "format"]
            conditional_rules = [r for r in self.formatting_rules if r.get("type") == "conditional"]
            
            # Write with formatting
            writer.write(
                df=self.df,
                sheet_name='Processed Data',
                formatting_rules=formatting_rules if formatting_rules else None,
                conditional_formatting=conditional_rules if conditional_rules else None
            )
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to save processed file: {str(e)}")
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get current dataframe"""
        if self.df is None:
            raise ValueError("Data not loaded")
        return self.df
    
    def get_summary(self) -> List[str]:
        """Get processing summary"""
        return self.summary
    
    def _apply_formatting_rules(self, workbook, worksheet):
        """Apply stored formatting rules to worksheet"""
        for rule in self.formatting_rules:
            if rule.get("type") != "format":
                continue
            
            fmt_config = rule.get("formatting", {})
            range_info = rule.get("range", {})
            
            # Create format object
            cell_format = workbook.add_format()
            
            if fmt_config.get("bold"):
                cell_format.set_bold()
            if fmt_config.get("italic"):
                cell_format.set_italic()
            if fmt_config.get("text_color"):
                cell_format.set_font_color(fmt_config["text_color"])
            if fmt_config.get("bg_color"):
                cell_format.set_bg_color(fmt_config["bg_color"])
            if fmt_config.get("font_size"):
                cell_format.set_font_size(fmt_config["font_size"])
            if fmt_config.get("borders"):
                cell_format.set_border(1)
            if fmt_config.get("wrap_text"):
                cell_format.set_text_wrap()
            
            align = fmt_config.get("align", "left")
            if align == "center":
                cell_format.set_align("center")
            elif align == "right":
                cell_format.set_align("right")
            else:
                cell_format.set_align("left")
            
            # Apply formatting to range
            if "column" in range_info:
                col_name = range_info["column"]
                if col_name in self.df.columns:
                    col_idx = list(self.df.columns).index(col_name)
                    # Format entire column (skip header row)
                    for row_idx in range(1, len(self.df) + 1):
                        worksheet.write(row_idx, col_idx, self.df.iloc[row_idx - 1, col_idx], cell_format)
            
            elif "row" in range_info:
                row_idx = range_info["row"]
                if 0 <= row_idx < len(self.df):
                    # Format entire row (add 1 for header)
                    excel_row = row_idx + 1
                    for col_idx in range(len(self.df.columns)):
                        worksheet.write(excel_row, col_idx, self.df.iloc[row_idx, col_idx], cell_format)
            
            elif "cells" in range_info:
                cells = range_info["cells"]
                for cell in cells:
                    row_idx = cell.get("row")
                    col_name = cell.get("column")
                    if col_name in self.df.columns and 0 <= row_idx < len(self.df):
                        col_idx = list(self.df.columns).index(col_name)
                        excel_row = row_idx + 1
                        worksheet.write(excel_row, col_idx, self.df.iloc[row_idx, col_idx], cell_format)
            
            # Handle merge cells
            if fmt_config.get("merge_cells") and "cells" in range_info:
                cells = range_info["cells"]
                if len(cells) >= 2:
                    # Get first and last cell positions
                    first_cell = cells[0]
                    last_cell = cells[-1]
                    first_row = first_cell.get("row", 0) + 1  # +1 for header
                    first_col = list(self.df.columns).index(first_cell.get("column")) if first_cell.get("column") in self.df.columns else 0
                    last_row = last_cell.get("row", 0) + 1
                    last_col = list(self.df.columns).index(last_cell.get("column")) if last_cell.get("column") in self.df.columns else len(self.df.columns) - 1
                    worksheet.merge_range(first_row, first_col, last_row, last_col, "", cell_format)
    
    def _apply_conditional_formatting(self, workbook, worksheet):
        """Apply conditional formatting rules"""
        if not self.formatting_rules:
            return
        
        for rule in self.formatting_rules:
            if rule.get("type") != "conditional":
                continue
            
            format_type = rule.get("format_type")
            config = rule.get("config", {})
            
            # Debug: Log what we're trying to apply
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Applying conditional formatting: type={format_type}, config={config}")
            
            if format_type == "duplicates":
                column = config.get("column")
                bg_color = config.get("bg_color", "#FFFF00")
                if column in self.df.columns:
                    col_idx = list(self.df.columns).index(column)
                    # Find duplicate values
                    duplicates = self.df[column].duplicated(keep=False)
                    for row_idx in range(len(self.df)):
                        if duplicates.iloc[row_idx]:
                            excel_row = row_idx + 1
                            dup_format = workbook.add_format({'bg_color': bg_color})
                            worksheet.write(excel_row, col_idx, self.df.iloc[row_idx, col_idx], dup_format)
            
            elif format_type == "greater_than":
                column = config.get("column")
                value = config.get("value")
                bg_color = config.get("bg_color", "#FF0000")
                if column in self.df.columns:
                    col_idx = list(self.df.columns).index(column)
                    # Convert to numeric if possible
                    try:
                        numeric_col = pd.to_numeric(self.df[column], errors='coerce')
                        for row_idx in range(len(self.df)):
                            if pd.notna(numeric_col.iloc[row_idx]) and numeric_col.iloc[row_idx] > value:
                                excel_row = row_idx + 1
                                gt_format = workbook.add_format({'bg_color': bg_color})
                                worksheet.write(excel_row, col_idx, self.df.iloc[row_idx, col_idx], gt_format)
                    except:
                        pass  # Skip if can't convert to numeric
            
            elif format_type in ["contains_text", "text_equals", "regex_match"]:
                # Handle text-based conditional formatting
                target_text = config.get("text", "")
                pattern = config.get("pattern", target_text)
                column_spec = config.get("column")
                
                # Resolve columns: if "all_columns" or None, use all columns; otherwise use specified column
                if column_spec is None or str(column_spec).lower() == "all_columns":
                    columns = list(self.df.columns)
                elif column_spec in self.df.columns:
                    columns = [column_spec]
                else:
                    columns = []
                
                if not columns or not target_text:
                    continue
                
                # Build cell format
                bg_color = config.get("bg_color") or config.get("background_color", "#FFF3CD")
                text_color = config.get("text_color") or config.get("font_color", "#000000")
                format_config = {"bg_color": bg_color}
                if text_color:
                    format_config["font_color"] = text_color
                if config.get("bold"):
                    format_config["bold"] = True
                cell_format = workbook.add_format(format_config)
                
                # Apply formatting to matching cells
                # We need to write cells AFTER to_excel() has written them, so we overwrite with format
                for column in columns:
                    if column not in self.df.columns:
                        continue
                    col_idx = list(self.df.columns).index(column)
                    series = self.df[column].astype(str)
                    
                    try:
                        if format_type == "contains_text":
                            matches = series.str.contains(str(target_text), case=False, na=False)
                        elif format_type == "text_equals":
                            matches = series.str.lower() == str(target_text).lower()
                        else:  # regex_match
                            matches = series.str.contains(pattern, na=False, regex=True)
                        
                        match_count = 0
                        for row_idx, match in enumerate(matches):
                            if match:
                                excel_row = row_idx + 1  # +1 for header row
                                cell_value = self.df.iloc[row_idx, col_idx]
                                
                                # Determine value type and write accordingly
                                if pd.isna(cell_value):
                                    worksheet.write_blank(excel_row, col_idx, cell_format)
                                elif isinstance(cell_value, (int, float)):
                                    worksheet.write_number(excel_row, col_idx, cell_value, cell_format)
                                elif isinstance(cell_value, bool):
                                    worksheet.write_boolean(excel_row, col_idx, cell_value, cell_format)
                                else:
                                    worksheet.write_string(excel_row, col_idx, str(cell_value), cell_format)
                                
                                match_count += 1
                        
                        # Log how many cells were formatted
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Formatted {match_count} cells in column '{column}' with text '{target_text}'")
                    except Exception as e:
                        # Log error but continue
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error applying conditional formatting to column '{column}': {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                        continue
    
    def _execute_delete_rows(self, action_plan: Dict):
        """Execute delete rows operation"""
        delete_rows = action_plan.get("delete_rows", {})
        
        initial_rows = len(self.df)
        
        if "start_row" in delete_rows and "end_row" in delete_rows:
            # Delete range of rows (0-indexed)
            start = delete_rows["start_row"]
            end = delete_rows["end_row"] + 1  # +1 because end is inclusive
            # Ensure valid range
            start = max(0, min(start, len(self.df)))
            end = max(start, min(end, len(self.df)))
            self.df = self.df.drop(self.df.index[start:end])
            self.summary.append(f"Deleted rows {start + 1} to {end} (0-indexed: {start} to {end - 1})")
        elif "row_indices" in delete_rows:
            # Delete specific row indices (0-indexed)
            indices = delete_rows["row_indices"]
            # Filter out invalid indices
            valid_indices = [idx for idx in indices if 0 <= idx < len(self.df)]
            if valid_indices:
                self.df = self.df.drop(self.df.index[valid_indices])
                self.summary.append(f"Deleted {len(valid_indices)} row(s) at indices: {valid_indices}")
            else:
                self.summary.append("No valid row indices to delete")
        else:
            self.summary.append("Delete rows: No valid row specification provided")
        
        deleted_count = initial_rows - len(self.df)
        if deleted_count > 0:
            self.summary.append(f"Result: {len(self.df)} rows remaining (deleted {deleted_count})")
    
    def _execute_add_row(self, action_plan: Dict):
        """Execute add row operation"""
        add_row = action_plan.get("add_row", {})
        
        position = add_row.get("position", -1)  # -1 means append at end
        row_data = add_row.get("data", {})
        
        # Create new row with default values for all columns
        new_row = {}
        for col in self.df.columns:
            new_row[col] = row_data.get(col, "")
        
        # Insert at specified position or append
        if position == -1 or position >= len(self.df):
            # Append at end
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            self.summary.append(f"Added new row at the end with {len(row_data)} specified values")
        else:
            # Insert at position
            position = max(0, min(position, len(self.df)))
            self.df = pd.concat([
                self.df.iloc[:position],
                pd.DataFrame([new_row]),
                self.df.iloc[position:]
            ], ignore_index=True)
            self.summary.append(f"Added new row at position {position + 1} (0-indexed: {position})")
        
        self.summary.append(f"Total rows: {len(self.df)}")
    
    def _execute_add_column(self, action_plan: Dict):
        """Execute add column operation"""
        add_column = action_plan.get("add_column", {})
        
        column_name = add_column.get("name", "NewColumn")
        position = add_column.get("position", -1)  # -1 means append at end
        default_value = add_column.get("default_value", "")
        
        # Check if column already exists
        if column_name in self.df.columns:
            # If exists, just fill with default value
            self.df[column_name] = default_value
            self.summary.append(f"Column '{column_name}' already exists, filled with default value")
        else:
            # Add new column
            if position == -1 or position >= len(self.df.columns):
                # Append at end
                self.df[column_name] = default_value
                self.summary.append(f"Added new column '{column_name}' at the end")
            else:
                # Insert at position
                position = max(0, min(position, len(self.df.columns)))
                cols = list(self.df.columns)
                cols.insert(position, column_name)
                self.df = self.df.reindex(columns=cols)
                self.df[column_name] = default_value
                self.summary.append(f"Added new column '{column_name}' at position {position + 1}")
        
        self.summary.append(f"Total columns: {len(self.df.columns)}")
    
    def _execute_delete_column(self, action_plan: Dict):
        """Execute delete column operation with positional reference fallback"""
        delete_column = action_plan.get("delete_column", {})
        
        column_name = delete_column.get("column_name")
        column_index = delete_column.get("column_index")
        
        # If no column name but we have user prompt, try to extract column name or positional reference
        if not column_name:
            user_prompt = action_plan.get("user_prompt", "")
            user_prompt_lower = user_prompt.lower()
            
            import re
            
            # FIRST: Try to extract direct column name from patterns like:
            # "remove column name UY7F9", "delete column UY7F9", "remove UY7F9 column", etc.
            direct_name_patterns = [
                r'(?:remove|delete|drop)\s+column\s+name\s+([A-Za-z0-9_\-\.\s]+?)(?:\s|$|column)',  # "remove column name UY7F9"
                r'(?:remove|delete|drop)\s+column\s+([A-Za-z0-9_\-\.\s]+?)(?:\s|$|column)',  # "delete column UY7F9"
                r'(?:remove|delete|drop)\s+([A-Za-z0-9_\-\.\s]+?)\s+column',  # "remove UY7F9 column"
            ]
            
            for pattern in direct_name_patterns:
                match = re.search(pattern, user_prompt, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip()
                    # Check if this matches any column name (case-insensitive)
                    for col in self.df.columns:
                        if col.lower() == potential_name.lower():
                            column_name = col  # Use exact case from DataFrame
                            self.summary.append(f"Extracted column name '{column_name}' from user prompt")
                            break
                    if column_name:
                        break
            
            # SECOND: If no direct name found, try to extract Excel column letters (A, B, C, etc.)
            if not column_name:
                # Match Excel column letters: A=0, B=1, C=2, ..., Z=25, AA=26, AB=27, etc.
                excel_letter_pattern = r'\bcolumn\s+([A-Z]+)\b'
                match = re.search(excel_letter_pattern, user_prompt, re.IGNORECASE)
                if match:
                    excel_letter = match.group(1).upper()
                    try:
                        # Convert Excel column letter to index (A=0, B=1, ..., Z=25, AA=26, etc.)
                        col_idx = 0
                        for char in excel_letter:
                            col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                        col_idx = col_idx - 1  # Convert to 0-indexed
                        
                        if 0 <= col_idx < len(self.df.columns):
                            column_name = self.df.columns[col_idx]
                            self.summary.append(f"Identified '{column_name}' as column {excel_letter} (index {col_idx})")
                    except:
                        pass
            
            # THIRD: If still no column name, try to extract positional reference
            if not column_name:
                # Match patterns like "1st", "2nd", "3rd", "first", "second", "third", "last"
                position_patterns = [
                    (r'\b(\d+)(?:st|nd|rd|th)\s+col', lambda m: int(m.group(1)) - 1),  # "2nd col", "3rd col"
                    (r'\b(\d+)\s+col', lambda m: int(m.group(1)) - 1),  # "2 col", "3 col"
                    (r'\bfirst\s+col', lambda m: 0),
                    (r'\bsecond\s+col', lambda m: 1),
                    (r'\bthird\s+col', lambda m: 2),
                    (r'\bfourth\s+col', lambda m: 3),
                    (r'\bfifth\s+col', lambda m: 4),
                    (r'\blast\s+col', lambda m: len(self.df.columns) - 1),
                ]
                
                for pattern, index_func in position_patterns:
                    match = re.search(pattern, user_prompt_lower)
                    if match:
                        try:
                            col_idx = index_func(match)
                            if 0 <= col_idx < len(self.df.columns):
                                column_name = self.df.columns[col_idx]
                                self.summary.append(f"Identified '{column_name}' as the column to delete from positional reference")
                                break
                        except:
                            continue
        
        # Fallback: use column_index if provided
        if not column_name and column_index is not None:
            if 0 <= column_index < len(self.df.columns):
                column_name = self.df.columns[column_index]
        
        if not column_name:
            self.summary.append("Delete column: No column name specified. Please specify column name or position (e.g., 'delete second column', 'delete column Name').")
            return
        
        if column_name not in self.df.columns:
            raise ValueError(f"Column '{column_name}' not found")
        
        self.df = self.df.drop(columns=[column_name])
        self.summary.append(f"Deleted column '{column_name}'")
        self.summary.append(f"Total columns: {len(self.df.columns)}")
    
    def _execute_edit_cell(self, action_plan: Dict):
        """Execute edit cell operation"""
        edit_cell = action_plan.get("edit_cell", {})
        
        row_index = edit_cell.get("row_index")
        column_name = edit_cell.get("column_name")
        value = edit_cell.get("value")
        
        if row_index is None or column_name is None:
            self.summary.append("Edit cell: Row index or column name not specified")
            return
        
        if column_name not in self.df.columns:
            raise ValueError(f"Column '{column_name}' not found")
        
        if row_index < 0 or row_index >= len(self.df):
            raise ValueError(f"Row index {row_index} is out of range (0 to {len(self.df) - 1})")
        
        old_value = self.df.at[row_index, column_name]
        self.df.at[row_index, column_name] = value
        self.summary.append(f"Edited cell at row {row_index + 1}, column '{column_name}': '{old_value}' -> '{value}'")
    
    def _execute_clear_cell(self, action_plan: Dict):
        """Execute clear cell operation"""
        clear_cell = action_plan.get("clear_cell", {})
        
        row_index = clear_cell.get("row_index")
        column_name = clear_cell.get("column_name")
        
        if row_index is None or column_name is None:
            self.summary.append("Clear cell: Row index or column name not specified")
            return
        
        if column_name not in self.df.columns:
            raise ValueError(f"Column '{column_name}' not found")
        
        if row_index < 0 or row_index >= len(self.df):
            raise ValueError(f"Row index {row_index} is out of range (0 to {len(self.df) - 1})")
        
        old_value = self.df.at[row_index, column_name]
        self.df.at[row_index, column_name] = ""
        self.summary.append(f"Cleared cell at row {row_index + 1}, column '{column_name}' (was: '{old_value}')")
    
    def _execute_auto_fill(self, action_plan: Dict):
        """Execute auto-fill operation (fill cells down a column)"""
        auto_fill = action_plan.get("auto_fill", {})
        
        column_name = auto_fill.get("column_name")
        start_row = auto_fill.get("start_row", 0)
        end_row = auto_fill.get("end_row", len(self.df) - 1)
        
        if not column_name:
            self.summary.append("Auto-fill: No column name specified")
            return
        
        if column_name not in self.df.columns:
            raise ValueError(f"Column '{column_name}' not found")
        
        # Ensure valid range
        start_row = max(0, min(start_row, len(self.df) - 1))
        end_row = max(start_row, min(end_row, len(self.df) - 1))
        
        # Get the source value (from start_row)
        source_value = self.df.at[start_row, column_name]
        
        # Fill down from start_row to end_row
        for i in range(start_row + 1, end_row + 1):
            self.df.at[i, column_name] = source_value
        
        filled_count = end_row - start_row
        self.summary.append(f"Auto-filled column '{column_name}' from row {start_row + 1} to {end_row + 1} with value '{source_value}' ({filled_count} cells filled)")
    
    def _execute_sort(self, action_plan: Dict):
        """Execute sort operation (A→Z, Z→A, numbers, dates, multi-column)"""
        sort_config = action_plan.get("sort", {})
        columns = sort_config.get("columns", [])
        
        if not columns:
            self.summary.append("Sort: No columns specified for sorting")
            return
        
        # Validate all columns exist
        for col_config in columns:
            col_name = col_config.get("column_name")
            if col_name not in self.df.columns:
                raise ValueError(f"Column '{col_name}' not found for sorting")
        
        # Build sort parameters
        sort_by = []
        ascending = []
        
        for col_config in columns:
            col_name = col_config.get("column_name")
            order = col_config.get("order", "asc").lower()
            data_type = col_config.get("data_type", "auto").lower()
            
            # Determine ascending/descending
            is_ascending = order in ["asc", "ascending", "a→z", "a-z", "small to big", "small→big"]
            
            # Handle data type conversion if needed
            if data_type == "date":
                # Try to convert to datetime
                try:
                    self.df[col_name] = pd.to_datetime(self.df[col_name], errors='coerce')
                except:
                    pass  # If conversion fails, sort as-is
            elif data_type == "number":
                # Try to convert to numeric
                try:
                    self.df[col_name] = pd.to_numeric(self.df[col_name], errors='coerce')
                except:
                    pass  # If conversion fails, sort as-is
            
            sort_by.append(col_name)
            ascending.append(is_ascending)
        
        # Perform multi-column sort
        self.df = self.df.sort_values(by=sort_by, ascending=ascending, na_position='last').reset_index(drop=True)
        
        # Build summary message
        sort_descriptions = []
        for i, col_config in enumerate(columns):
            col_name = col_config.get("column_name")
            order = col_config.get("order", "asc").lower()
            data_type = col_config.get("data_type", "auto").lower()
            
            if order in ["asc", "ascending", "a→z", "a-z", "small to big", "small→big"]:
                if data_type == "number":
                    order_desc = "small to big"
                elif data_type == "date":
                    order_desc = "oldest to newest"
                else:
                    order_desc = "A to Z"
            else:
                if data_type == "number":
                    order_desc = "big to small"
                elif data_type == "date":
                    order_desc = "newest to oldest"
                else:
                    order_desc = "Z to A"
            
            sort_descriptions.append(f"'{col_name}' {order_desc}")
        
        if len(sort_descriptions) == 1:
            self.summary.append(f"Sorted by {sort_descriptions[0]}")
        else:
            self.summary.append(f"Multi-column sorted by: {', '.join(sort_descriptions)}")
        
        self.summary.append(f"Total rows: {len(self.df)}")
    
    def _execute_format(self, action_plan: Dict):
        """Execute format operation - store formatting rules to apply when saving"""
        format_config = action_plan.get("format", {})
        
        if not format_config:
            self.summary.append("Format: No format configuration specified")
            return
        
        # Handle both structures:
        # 1. Nested: {"formatting": {...}, "range": {...}}
        # 2. Flat: {"range": {...}, "bold": true, "italic": false, ...}
        
        if "formatting" in format_config:
            # Nested structure
            formatting = format_config.get("formatting", {})
            range_info = format_config.get("range", {})
        else:
            # Flat structure - extract formatting from root level
            formatting = {}
            range_info = format_config.get("range", {})
            
            # Extract all formatting properties (including font_size, bold, italic, colors, etc.)
            for key in ["bold", "italic", "text_color", "font_color", "bg_color", 
                       "background_color", "font_size", "align", "borders", "wrap_text"]:
                if key in format_config:
                    if key == "font_color":
                        formatting["text_color"] = format_config[key]
                    elif key == "background_color":
                        formatting["bg_color"] = format_config[key]
                    else:
                        formatting[key] = format_config[key]
        
        # Store formatting rule to apply when saving
        rule = {
            "type": "format",
            "formatting": formatting,
            "range": range_info
        }
        self.formatting_rules.append(rule)
        
        # Build summary message
        format_parts = []
        if formatting.get("bold"):
            format_parts.append("bold")
        if formatting.get("italic"):
            format_parts.append("italic")
        if formatting.get("text_color"):
            format_parts.append(f"text color: {formatting['text_color']}")
        if formatting.get("bg_color"):
            format_parts.append(f"background: {formatting['bg_color']}")
        if formatting.get("font_size"):
            format_parts.append(f"font size: {formatting['font_size']}")
        if formatting.get("align"):
            format_parts.append(f"align: {formatting['align']}")
        
        range_desc = ""
        if "column" in range_info:
            range_desc = f"column '{range_info['column']}'"
        elif "row" in range_info:
            range_desc = f"row {range_info['row'] + 1}"
        elif "cells" in range_info:
            range_desc = f"{len(range_info['cells'])} cell(s)"
        
        if format_parts:
            self.summary.append(f"Applied formatting ({', '.join(format_parts)}) to {range_desc}")
        else:
            self.summary.append(f"Formatting rule stored for {range_desc}")
    
    def _execute_conditional_format(self, action_plan: Dict):
        """Execute conditional format operation - store conditional formatting rules"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 _execute_conditional_format called with action_plan keys: {list(action_plan.keys())}")
        conditional_format = action_plan.get("conditional_format", {})
        
        logger.info(f"🔍 Extracted conditional_format: {conditional_format}")
        
        if not conditional_format:
            logger.warning(f"⚠️ conditional_format is empty, trying fallback...")
            fallback = self._build_conditional_format_fallback(action_plan)
            if fallback:
                conditional_format = fallback
                logger.info(f"✅ Using fallback: {fallback}")
                self.summary.append("Conditional format: Applied fallback configuration from user prompt.")
            else:
                logger.error(f"❌ No conditional_format and no fallback available!")
                self.summary.append("Conditional format: No configuration specified")
                return
        
        # Extract conditional formatting details
        format_type = conditional_format.get("format_type", "")
        config = conditional_format.get("config", {})
        
        logger.info(f"✅ Format type: {format_type}, Config: {config}")
        
        # Store conditional formatting rule to apply when saving
        rule = {
            "type": "conditional",
            "format_type": format_type,
            "config": config
        }
        self.formatting_rules.append(rule)
        logger.info(f"✅ Added conditional format rule to formatting_rules. Total rules: {len(self.formatting_rules)}")
        
        # Build summary message
        if format_type == "duplicates":
            column = config.get("column", "unknown")
            self.summary.append(f"Conditional formatting: Highlight duplicates in column '{column}'")
        elif format_type == "greater_than":
            column = config.get("column", "unknown")
            value = config.get("value", "unknown")
            self.summary.append(f"Conditional formatting: Highlight values > {value} in column '{column}'")
        elif format_type == "less_than":
            column = config.get("column", "unknown")
            value = config.get("value", "unknown")
            self.summary.append(f"Conditional formatting: Highlight values < {value} in column '{column}'")
        elif format_type == "between":
            column = config.get("column", "unknown")
            min_val = config.get("min_value", "unknown")
            max_val = config.get("max_value", "unknown")
            self.summary.append(f"Conditional formatting: Highlight values between {min_val} and {max_val} in column '{column}'")
        elif format_type == "contains_text":
            column = config.get("column", "unknown")
            text = config.get("text", "unknown")
            self.summary.append(f"Conditional formatting: Highlight cells containing '{text}' in column '{column}'")
        elif format_type == "text_equals":
            column = config.get("column", "unknown")
            text = config.get("text", "unknown")
            self.summary.append(f"Conditional formatting: Highlight cells equal to '{text}' in column '{column}'")
        else:
            self.summary.append(f"Conditional formatting rule stored: {format_type}")
    
    def _execute_formula(self, action_plan: Dict):
        """Execute formula operations using FormulaEngine"""
        formula_config = action_plan.get("formula", {})
        
        if not formula_config:
            self.summary.append("Formula: No formula configuration specified")
            return
        
        formula_type = formula_config.get("type", "").lower()
        params = formula_config.get("parameters", {})
        column = formula_config.get("column")
        columns = formula_config.get("columns", [])
        
        try:
            # Basic Math Formulas
            if formula_type == "sum":
                if not column:
                    raise ValueError("Column required for SUM")
                result = FormulaEngine.SUM(self.df, column)
                self.formula_result = result
                self.summary.append(f"SUM({column}) = {result}")
            
            elif formula_type == "average":
                if not column:
                    raise ValueError("Column required for AVERAGE")
                # Apply filter if specified
                df_to_use = self.df
                if params.get("filter_column") and params.get("condition") and params.get("value"):
                    filter_col = params["filter_column"]
                    condition = params["condition"]
                    value = params["value"]
                    if condition == "==":
                        df_to_use = self.df[self.df[filter_col] == value]
                    elif condition == "!=":
                        df_to_use = self.df[self.df[filter_col] != value]
                result = FormulaEngine.AVERAGE(df_to_use, column)
                self.formula_result = result
                self.summary.append(f"AVERAGE({column}) = {result}")
            
            elif formula_type == "min":
                if not column:
                    raise ValueError("Column required for MIN")
                result = FormulaEngine.MIN(self.df, column)
                self.formula_result = result
                self.summary.append(f"MIN({column}) = {result}")
            
            elif formula_type == "max":
                if not column:
                    raise ValueError("Column required for MAX")
                result = FormulaEngine.MAX(self.df, column)
                self.formula_result = result
                self.summary.append(f"MAX({column}) = {result}")
            
            elif formula_type == "count":
                if not column:
                    raise ValueError("Column required for COUNT")
                result = FormulaEngine.COUNT(self.df, column)
                self.formula_result = result
                self.summary.append(f"COUNT({column}) = {result}")
            
            elif formula_type == "countif":
                if not column:
                    raise ValueError("Column required for COUNTIF")
                condition = params.get("condition", "==")
                value = params.get("value")
                result = FormulaEngine.COUNTIF(self.df, column, condition, value)
                self.formula_result = result
                self.summary.append(f"COUNTIF({column} {condition} {value}) = {result}")
            
            elif formula_type == "counta":
                if not column:
                    raise ValueError("Column required for COUNTA")
                result = FormulaEngine.COUNTA(self.df, column)
                self.formula_result = result
                self.summary.append(f"COUNTA({column}) = {result}")
            
            elif formula_type == "unique":
                if not column:
                    raise ValueError("Column required for UNIQUE")
                result = FormulaEngine.UNIQUE(self.df, column)
                self.formula_result = result
                self.summary.append(f"UNIQUE({column}) = {len(result)} unique values")
            
            elif formula_type == "round":
                if not column:
                    raise ValueError("Column required for ROUND")
                decimals = params.get("decimals", 0)
                self.df = FormulaEngine.ROUND(self.df, column, decimals)
                self.summary.append(f"ROUND({column}, {decimals}) applied")
            
            # Text Functions
            elif formula_type == "concat":
                if not columns:
                    raise ValueError("Columns required for CONCAT")
                separator = params.get("separator", "")
                self.df = FormulaEngine.CONCAT(self.df, columns, separator)
                self.summary.append(f"CONCAT({', '.join(columns)}) applied")
            
            elif formula_type == "textjoin":
                if not columns:
                    raise ValueError("Columns required for TEXTJOIN")
                separator = params.get("separator", ", ")
                self.df = FormulaEngine.TEXTJOIN(self.df, columns, separator)
                self.summary.append(f"TEXTJOIN({', '.join(columns)}) applied")
            
            elif formula_type == "left":
                if not column:
                    raise ValueError("Column required for LEFT")
                num_chars = params.get("num_chars", 1)
                self.df = FormulaEngine.LEFT(self.df, column, num_chars)
                self.summary.append(f"LEFT({column}, {num_chars}) applied")
            
            elif formula_type == "right":
                if not column:
                    raise ValueError("Column required for RIGHT")
                num_chars = params.get("num_chars", 1)
                self.df = FormulaEngine.RIGHT(self.df, column, num_chars)
                self.summary.append(f"RIGHT({column}, {num_chars}) applied")
            
            elif formula_type == "mid":
                if not column:
                    raise ValueError("Column required for MID")
                start = params.get("start", 1)
                num_chars = params.get("num_chars", 1)
                self.df = FormulaEngine.MID(self.df, column, start, num_chars)
                self.summary.append(f"MID({column}, {start}, {num_chars}) applied")
            
            elif formula_type == "trim":
                if not column:
                    raise ValueError("Column required for TRIM")
                self.df = FormulaEngine.TRIM(self.df, column)
                self.summary.append(f"TRIM({column}) applied")
            
            elif formula_type == "lower":
                if not column:
                    raise ValueError("Column required for LOWER")
                self.df = FormulaEngine.LOWER(self.df, column)
                self.summary.append(f"LOWER({column}) applied")
            
            elif formula_type == "upper":
                if not column:
                    raise ValueError("Column required for UPPER")
                self.df = FormulaEngine.UPPER(self.df, column)
                self.summary.append(f"UPPER({column}) applied")
            
            elif formula_type == "proper":
                if not column:
                    raise ValueError("Column required for PROPER")
                self.df = FormulaEngine.PROPER(self.df, column)
                self.summary.append(f"PROPER({column}) applied")
            
            elif formula_type == "find":
                if not column:
                    raise ValueError("Column required for FIND")
                search_text = params.get("search_text", "")
                case_sensitive = params.get("case_sensitive", True)
                self.df = FormulaEngine.FIND(self.df, column, search_text, case_sensitive)
                self.summary.append(f"FIND({column}, '{search_text}') applied")
            
            elif formula_type == "search":
                if not column:
                    raise ValueError("Column required for SEARCH")
                search_text = params.get("search_text", "")
                self.df = FormulaEngine.SEARCH(self.df, column, search_text)
                self.summary.append(f"SEARCH({column}, '{search_text}') applied")
            
            # Date & Time Functions
            elif formula_type == "today":
                result = FormulaEngine.TODAY()
                self.formula_result = result
                self.summary.append(f"TODAY() = {result}")
            
            elif formula_type == "now":
                result = FormulaEngine.NOW()
                self.formula_result = result
                self.summary.append(f"NOW() = {result}")
            
            elif formula_type == "year":
                if not column:
                    raise ValueError("Column required for YEAR")
                self.df = FormulaEngine.YEAR(self.df, column)
                self.summary.append(f"YEAR({column}) applied")
            
            elif formula_type == "month":
                if not column:
                    raise ValueError("Column required for MONTH")
                self.df = FormulaEngine.MONTH(self.df, column)
                self.summary.append(f"MONTH({column}) applied")
            
            elif formula_type == "day":
                if not column:
                    raise ValueError("Column required for DAY")
                self.df = FormulaEngine.DAY(self.df, column)
                self.summary.append(f"DAY({column}) applied")
            
            elif formula_type == "datedif":
                start_column = params.get("start_column") or column
                end_column = params.get("end_column")
                if not start_column or not end_column:
                    raise ValueError("start_column and end_column required for DATEDIF")
                unit = params.get("unit", "days")
                self.df = FormulaEngine.DATEDIF(self.df, start_column, end_column, unit)
                self.summary.append(f"DATEDIF({start_column}, {end_column}, {unit}) applied")
            
            # Logical Functions
            elif formula_type == "if":
                if not column:
                    raise ValueError("Column required for IF")
                condition = params.get("condition", "==")
                value = params.get("value")
                true_value = params.get("true_value")
                false_value = params.get("false_value")
                self.df = FormulaEngine.IF(self.df, column, condition, value, true_value, false_value)
                self.summary.append(f"IF({column} {condition} {value}) applied")
            
            elif formula_type == "and":
                if not columns:
                    raise ValueError("Columns required for AND")
                conditions = params.get("conditions", [])
                values = params.get("values", [])
                self.df = FormulaEngine.AND(self.df, columns, conditions, values)
                self.summary.append(f"AND({', '.join(columns)}) applied")
            
            elif formula_type == "or":
                if not columns:
                    raise ValueError("Columns required for OR")
                conditions = params.get("conditions", [])
                values = params.get("values", [])
                self.df = FormulaEngine.OR(self.df, columns, conditions, values)
                self.summary.append(f"OR({', '.join(columns)}) applied")
            
            elif formula_type == "not":
                if not column:
                    raise ValueError("Column required for NOT")
                self.df = FormulaEngine.NOT(self.df, column)
                self.summary.append(f"NOT({column}) applied")
            
            # Lookup Functions
            elif formula_type == "vlookup":
                lookup_value = params.get("lookup_value")
                lookup_column = params.get("lookup_column")
                return_column = params.get("return_column")
                exact_match = params.get("exact_match", True)
                if not all([lookup_value, lookup_column, return_column]):
                    raise ValueError("lookup_value, lookup_column, and return_column required for VLOOKUP")
                result = FormulaEngine.VLOOKUP(self.df, lookup_value, lookup_column, return_column, exact_match)
                self.formula_result = result
                self.summary.append(f"VLOOKUP({lookup_value}, {lookup_column}, {return_column}) = {result}")
            
            elif formula_type == "xlookup":
                lookup_value = params.get("lookup_value")
                lookup_column = params.get("lookup_column")
                return_column = params.get("return_column")
                not_found = params.get("not_found")
                if not all([lookup_value, lookup_column, return_column]):
                    raise ValueError("lookup_value, lookup_column, and return_column required for XLOOKUP")
                result = FormulaEngine.XLOOKUP(self.df, lookup_value, lookup_column, return_column, not_found)
                self.formula_result = result
                self.summary.append(f"XLOOKUP({lookup_value}, {lookup_column}, {return_column}) = {result}")
            
            # Data Cleaning
            elif formula_type == "remove_duplicates":
                if columns:
                    self.df = FormulaEngine.remove_duplicates(self.df, columns)
                    self.summary.append(f"Removed duplicates based on {', '.join(columns)}")
                else:
                    self.df = FormulaEngine.remove_duplicates(self.df)
                    self.summary.append("Removed duplicate rows")
            
            elif formula_type == "highlight_duplicates":
                if not column:
                    raise ValueError("Column required for highlight_duplicates")
                self.df = FormulaEngine.highlight_duplicates(self.df, column)
                self.summary.append(f"Highlighted duplicates in {column}")
            
            elif formula_type == "remove_empty_rows":
                initial_rows = len(self.df)
                self.df = FormulaEngine.remove_empty_rows(self.df)
                removed = initial_rows - len(self.df)
                self.summary.append(f"Removed {removed} empty rows")
            
            elif formula_type == "normalize_text":
                if not column:
                    raise ValueError("Column required for normalize_text")
                # Use new TextCleaner module
                self.df = TextCleaner.trim_whitespace(self.df, column)
                self.df = TextCleaner.normalize_case(self.df, column, case='lower')
                self.summary.append(f"Normalized text in {column}")
            
            elif formula_type == "fix_date_formats":
                if not column:
                    raise ValueError("Column required for fix_date_formats")
                target_format = params.get("target_format", "%Y-%m-%d")
                # Use new DateCleaner module
                self.df = DateCleaner.normalize_dates(self.df, column, target_format)
                self.summary.append(f"Fixed date formats in {column}")
            
            elif formula_type == "convert_text_to_numbers":
                if not column:
                    raise ValueError("Column required for convert_text_to_numbers")
                self.df = FormulaEngine.convert_text_to_numbers(self.df, column)
                self.summary.append(f"Converted text to numbers in {column}")
            
            # Grouping & Summaries
            elif formula_type == "group_by_category":
                if not column:
                    raise ValueError("Column required for group_by_category")
                agg_function = params.get("agg_function", "count")
                agg_column = params.get("agg_column")
                self.df = FormulaEngine.group_by_category(self.df, column, agg_function, agg_column)
                self.summary.append(f"Grouped by {column} with {agg_function} aggregation")
            
            # Additional Operations
            elif formula_type == "sort":
                if not column:
                    raise ValueError("Column required for SORT")
                ascending = params.get("ascending", True)
                if isinstance(ascending, str):
                    ascending = ascending.lower() in ["asc", "ascending", "true", "1"]
                limit = params.get("limit")
                self.df = FormulaEngine.SORT(self.df, column, ascending, limit)
                order = "ascending" if ascending else "descending"
                limit_text = f" (top {limit})" if limit else ""
                self.summary.append(f"Sorted by {column} {order}{limit_text}")
            
            elif formula_type == "filter":
                if not column:
                    raise ValueError("Column required for FILTER")
                condition = params.get("condition", "==")
                value = params.get("value")
                initial_rows = len(self.df)
                self.df = FormulaEngine.FILTER(self.df, column, condition, value)
                filtered_rows = len(self.df)
                removed = initial_rows - filtered_rows
                self.summary.append(f"Filtered '{column}' {condition} {value}: {filtered_rows} rows (removed {removed})")
            
            else:
                raise ValueError(f"Unsupported formula type: {formula_type}")
        
        except Exception as e:
            raise RuntimeError(f"Formula execution failed: {str(e)}")


