"""
Generic Execution Engine

This module provides a generic execution engine that interprets structured JSON
action plans from the LLM and executes them without requiring if-else statements
for every operation type.

The LLM returns detailed JSON with execution instructions, and this engine
interprets and executes them dynamically.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from services.formula_engine import FormulaEngine


class GenericExecutor:
    """
    Generic executor that interprets JSON action plans and executes them.
    
    This reduces the need for if-else statements by having the LLM return
    detailed execution instructions in a structured format.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize executor with a dataframe.
        
        Args:
            df: DataFrame to operate on
        """
        self.df = df.copy()
        self.summary: List[str] = []
        self.formula_result: Optional[Any] = None
    
    def execute(self, action_plan: Dict) -> Dict:
        """
        Execute an action plan from LLM.
        
        The action plan should contain:
        - task: The operation type
        - operations: List of operations to execute in sequence
        - Each operation has: type, params, and execution_instructions
        
        Args:
            action_plan: Structured action plan from LLM
            
        Returns:
            Dictionary with processed dataframe and summary
        """
        if self.df is None:
            raise ValueError("DataFrame not initialized")
        
        task = action_plan.get("task", "summarize")
        operations = action_plan.get("operations", [])
        
        # If operations list is provided, execute them sequentially
        if operations:
            for op in operations:
                self._execute_operation(op)
        else:
            # Fallback to task-based execution for backward compatibility
            self._execute_task(task, action_plan)
        
        return {
            "df": self.df,
            "summary": self.summary,
            "chart_needed": action_plan.get("chart_type", "none") != "none",
            "chart_type": action_plan.get("chart_type", "none"),
            "formula_result": self.formula_result,
            "task": task
        }
    
    def _execute_operation(self, operation: Dict):
        """
        Execute a single operation from the operations list.
        
        Operation format:
        {
            "type": "operation_type",
            "params": {...},
            "execution_instructions": {
                "method": "pandas_method" or "custom_function",
                "args": [...],
                "kwargs": {...}
            }
        }
        """
        op_type = operation.get("type")
        params = operation.get("params", {})
        instructions = operation.get("execution_instructions", {})
        
        try:
            # Use execution instructions if provided (LLM-generated)
            if instructions:
                self._execute_by_instructions(instructions)
            else:
                # Fallback to type-based execution
                self._execute_by_type(op_type, params)
            
            # Add summary
            description = operation.get("description", f"Executed {op_type}")
            self.summary.append(description)
            
        except Exception as e:
            raise RuntimeError(f"Failed to execute operation {op_type}: {str(e)}")
    
    def _execute_by_instructions(self, instructions: Dict):
        """
        Execute operation using LLM-provided execution instructions.
        
        This allows the LLM to specify exactly how to execute the operation,
        reducing the need for hardcoded if-else logic.
        """
        method = instructions.get("method")
        args = instructions.get("args", [])
        kwargs = instructions.get("kwargs", {})
        
        if method.startswith("pandas."):
            # Execute pandas method
            pandas_method = method.replace("pandas.", "")
            if hasattr(pd.DataFrame, pandas_method):
                func = getattr(self.df, pandas_method)
                result = func(*args, **kwargs)
                if isinstance(result, pd.DataFrame):
                    self.df = result
                elif result is not None:
                    self.formula_result = result
        elif method.startswith("formula."):
            # Execute formula engine method
            formula_method = method.replace("formula.", "")
            if hasattr(FormulaEngine, formula_method):
                func = getattr(FormulaEngine, formula_method)
                result = func(self.df, *args, **kwargs)
                if isinstance(result, pd.DataFrame):
                    self.df = result
                else:
                    self.formula_result = result
        elif method == "custom":
            # Custom execution logic specified by LLM
            custom_code = instructions.get("code")
            if custom_code:
                # Execute custom pandas operations
                # Note: In production, you'd want to sandbox this
                exec(custom_code, {"df": self.df, "pd": pd, "np": np})
    
    def _execute_by_type(self, op_type: str, params: Dict):
        """
        Fallback execution by operation type.
        This is still needed for backward compatibility.
        """
        # This can be simplified as LLM provides better instructions
        if op_type == "remove_duplicates":
            self.df = self.df.drop_duplicates()
        elif op_type == "fillna":
            value = params.get("value", "")
            self.df = self.df.fillna(value)
        elif op_type == "dropna":
            self.df = self.df.dropna()
        # Add more as needed, but ideally LLM should provide instructions
    
    def _execute_task(self, task: str, action_plan: Dict):
        """
        Fallback to task-based execution for backward compatibility.
        """
        # This maintains compatibility with existing code
        # But ideally, all operations should come through the operations list
        pass

