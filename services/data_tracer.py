"""
Data Tracer Service

Tracks which columns and operations were used in each request.
Helps with debugging, validation, and understanding data flow.
Adapted from excelaiagent's data_trace.py
"""

import logging
from typing import Dict, List, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataTracer:
    """Tracks data usage and operation history"""
    
    def __init__(self):
        self.current_trace: Optional[Dict] = None
        self.reset()
    
    def reset(self):
        """Reset trace for new operation"""
        self.current_trace = {
            "timestamp": datetime.now().isoformat(),
            "columns_used": set(),
            "operations": [],
            "data_sources": [],
            "rows_before": 0,
            "rows_after": 0,
            "columns_before": [],
            "columns_after": []
        }
    
    def track_operation(
        self, 
        operation_type: str, 
        columns: List[str],
        description: str = "",
        rows_affected: int = 0
    ):
        """
        Track an operation and columns used
        
        Args:
            operation_type: Type of operation (e.g., "remove_duplicates", "filter", "sum")
            columns: List of column names used in this operation
            description: Human-readable description
            rows_affected: Number of rows affected (0 if not applicable)
        """
        if not self.current_trace:
            self.reset()
        
        self.current_trace["operations"].append({
            "type": operation_type,
            "columns": columns,
            "description": description,
            "rows_affected": rows_affected,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add columns to used set
        self.current_trace["columns_used"].update(columns)
        
        # Update rows affected
        if rows_affected > 0:
            self.current_trace["rows_after"] = rows_affected
    
    def track_data_source(self, source: str, columns: List[str]):
        """Track data source (file, sheet, etc.)"""
        if not self.current_trace:
            self.reset()
        
        self.current_trace["data_sources"].append({
            "source": source,
            "columns": columns,
            "timestamp": datetime.now().isoformat()
        })
    
    def set_dataframe_state(self, rows: int, columns: List[str], stage: str = "before"):
        """
        Track DataFrame state at different stages
        
        Args:
            rows: Number of rows
            columns: List of column names
            stage: "before" or "after"
        """
        if not self.current_trace:
            self.reset()
        
        if stage == "before":
            self.current_trace["rows_before"] = rows
            self.current_trace["columns_before"] = columns
        elif stage == "after":
            self.current_trace["rows_after"] = rows
            self.current_trace["columns_after"] = columns
    
    def get_trace_report(self) -> Dict:
        """
        Generate traceability report
        
        Returns:
            Dictionary with trace information
        """
        if not self.current_trace:
            return {}
        
        return {
            "timestamp": self.current_trace["timestamp"],
            "total_operations": len(self.current_trace["operations"]),
            "columns_used": sorted(list(self.current_trace["columns_used"])),
            "operation_history": self.current_trace["operations"],
            "data_sources": self.current_trace["data_sources"],
            "rows_before": self.current_trace["rows_before"],
            "rows_after": self.current_trace["rows_after"],
            "columns_before": self.current_trace["columns_before"],
            "columns_after": self.current_trace["columns_after"],
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary"""
        if not self.current_trace:
            return ""
        
        ops = self.current_trace["operations"]
        cols = sorted(list(self.current_trace["columns_used"]))
        rows_before = self.current_trace["rows_before"]
        rows_after = self.current_trace["rows_after"]
        
        summary_parts = []
        
        if ops:
            summary_parts.append(f"Executed {len(ops)} operation(s)")
        
        if cols:
            col_list = ', '.join(cols[:5])
            if len(cols) > 5:
                col_list += f" and {len(cols) - 5} more"
            summary_parts.append(f"Used {len(cols)} column(s): {col_list}")
        
        if rows_before > 0 and rows_after > 0:
            if rows_before != rows_after:
                summary_parts.append(f"Rows: {rows_before} → {rows_after}")
            else:
                summary_parts.append(f"Rows: {rows_after}")
        
        return ". ".join(summary_parts) if summary_parts else "No operations tracked"

