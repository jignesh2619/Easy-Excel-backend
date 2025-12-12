"""
Extraction Pattern Analyzer

Lightweight pattern analyzer for extraction operations.
Analyzes sample data to identify extraction patterns without heavy token usage.
Helps LLM understand data formats efficiently.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExtractionPatternAnalyzer:
    """Analyzes data patterns to suggest extraction strategies"""
    
    @staticmethod
    def analyze_column_format(sample_values: List[str], max_samples: int = 10) -> Dict:
        """
        Analyze column format to suggest extraction pattern.
        Returns minimal pattern info for LLM to use.
        
        Args:
            sample_values: List of sample values from the column
            max_samples: Maximum number of samples to analyze
            
        Returns:
            Dictionary with pattern information
        """
        if not sample_values:
            return {"type": "unknown", "pattern": None}
        
        samples = [str(v) for v in sample_values[:max_samples] if v is not None and str(v).strip()]
        
        if not samples:
            return {"type": "unknown", "pattern": None}
        
        # Check for common separators
        separators = ['|', ':', '-', '(', ')', '$', '€', '₹', '£', '¥']
        found_separators = []
        for sep in separators:
            if any(sep in s for s in samples):
                found_separators.append(sep)
        
        # Check for numeric patterns
        has_currency = any(any(c in s for c in ['$', '€', '₹', '£', '¥']) for s in samples)
        has_numbers = any(re.search(r'\d+', s) for s in samples)
        has_commas = any(',' in s and re.search(r'\d', s) for s in samples)
        has_decimals = any('.' in s and re.search(r'\d+\.\d+', s) for s in samples)
        
        # Check for text patterns
        has_text = any(re.search(r'[a-zA-Z]', s) for s in samples)
        
        # Determine pattern type
        if found_separators and has_numbers:
            # Formatted string with separator and numbers
            return {
                "type": "formatted_with_separator",
                "separators": found_separators,
                "has_currency": has_currency,
                "has_commas": has_commas,
                "has_decimals": has_decimals,
                "has_text": has_text,
                "suggestion": "extract_numeric" if (has_currency or has_numbers) and not has_text else "extract_based_on_target"
            }
        elif has_numbers and not found_separators:
            # Pure numeric (might have commas)
            return {
                "type": "numeric",
                "pattern": "direct",
                "has_commas": has_commas,
                "has_decimals": has_decimals
            }
        elif has_text and not has_numbers:
            return {"type": "text", "pattern": "direct"}
        else:
            return {"type": "mixed", "pattern": "needs_extraction"}
    
    @staticmethod
    def suggest_extraction_code(source_col: str, target_col: str, pattern_info: Dict) -> Optional[str]:
        """
        Suggest extraction code based on pattern analysis.
        Returns minimal code suggestion.
        
        Args:
            source_col: Source column name
            target_col: Target column name
            pattern_info: Pattern information from analyze_column_format
            
        Returns:
            Suggested Python code string or None
        """
        if pattern_info.get("type") == "formatted_with_separator":
            has_currency = pattern_info.get("has_currency", False)
            has_commas = pattern_info.get("has_commas", False)
            has_decimals = pattern_info.get("has_decimals", False)
            
            # Determine if target suggests numeric (common column names)
            target_lower = target_col.lower()
            is_numeric_target = any(keyword in target_lower for keyword in 
                                   ['sales', 'amount', 'price', 'cost', 'revenue', 'profit', 'total', 'sum', 'value', 'number', 'qty', 'quantity'])
            
            if has_currency and is_numeric_target:
                # Currency extraction
                if has_commas:
                    return f"df['{target_col}'] = df['{source_col}'].str.extract(r'\\$([\\d,]+(?:\\.\\d+)?)')[0].str.replace(',', '', regex=False).astype(float)"
                elif has_decimals:
                    return f"df['{target_col}'] = df['{source_col}'].str.extract(r'\\$([\\d.]+)')[0].astype(float)"
                else:
                    return f"df['{target_col}'] = df['{source_col}'].str.extract(r'\\$([\\d]+)')[0].astype(float)"
            elif is_numeric_target:
                # Generic numeric extraction after separator
                if has_commas:
                    return f"df['{target_col}'] = df['{source_col}'].str.extract(r'[|:-]\\s*([\\d,]+(?:\\.\\d+)?)')[0].str.replace(',', '', regex=False).astype(float)"
                else:
                    return f"df['{target_col}'] = df['{source_col}'].str.extract(r'[|:-]\\s*([\\d.]+)')[0].astype(float)"
        
        return None
    
    @staticmethod
    def get_pattern_hint(source_col: str, target_col: str, sample_data: List[Dict], available_columns: List[str]) -> str:
        """
        Get a minimal pattern hint for the LLM prompt.
        Analyzes sample data to provide extraction guidance.
        
        Args:
            source_col: Source column name
            target_col: Target column name  
            sample_data: Sample data rows
            available_columns: List of available columns
            
        Returns:
            Minimal pattern hint string (token-efficient)
        """
        if not sample_data or source_col not in available_columns:
            return ""
        
        # Extract sample values from source column
        sample_values = []
        for row in sample_data[:5]:  # Only analyze first 5 rows
            value = row.get(source_col, "")
            if value is not None:
                sample_values.append(str(value))
        
        if not sample_values:
            return ""
        
        # Analyze pattern
        pattern_info = ExtractionPatternAnalyzer.analyze_column_format(sample_values)
        
        # Generate minimal hint
        hint_parts = []
        
        if pattern_info.get("type") == "formatted_with_separator":
            separators = pattern_info.get("separators", [])
            has_currency = pattern_info.get("has_currency", False)
            has_commas = pattern_info.get("has_commas", False)
            
            hint_parts.append(f"Source '{source_col}' contains formatted data")
            if separators:
                hint_parts.append(f"with separators: {', '.join(separators[:2])}")
            if has_currency:
                hint_parts.append("(currency detected)")
            if has_commas:
                hint_parts.append("(commas in numbers)")
            
            # Check target column name
            target_lower = target_col.lower()
            if any(keyword in target_lower for keyword in ['sales', 'amount', 'price', 'cost', 'revenue', 'profit']):
                hint_parts.append(f"→ Extract numeric values for '{target_col}'")
        
        if hint_parts:
            return "**PATTERN HINT:** " + ". ".join(hint_parts) + ".\n"
        
        return ""


