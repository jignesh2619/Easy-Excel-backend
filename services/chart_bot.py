"""
Chart Bot

Specialized bot for generating chart configurations.
Handles all chart/visualization requests.
"""

import json
import os
import logging
import re
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from services.feedback_learner import FeedbackLearner
from services.training_data_loader import TrainingDataLoader
from utils.knowledge_base import get_chart_knowledge_base_summary
from utils.prompts import get_column_mapping_info, resolve_column_reference

load_dotenv()

logger = logging.getLogger(__name__)

CHART_BOT_SYSTEM_PROMPT = """You are a Chart Generation Specialist. Generate chart configurations as JSON.

RULES:
- Generic requests ("dashboard", "graphs", "visualize"): Return {"charts": [...]} with 2-4 charts
- Specific requests: Return single chart config
- Use ACTUAL column names from available_columns (not Excel letters)
- Chart types: bar (categories), line (time), pie (proportions), scatter (numeric pairs), histogram (distribution)

EXCEL COLUMN REFERENCES:
- "graph between A and B" → A = first column, B = second column (use actual names from available_columns)
- "chart of column A" → A = available_columns[0]
- "column B vs C" → B = available_columns[1], C = available_columns[2]
- Always resolve Excel letters (A, B, C, etc.) to actual column names from available_columns

BAR CHART RULES:
- X-axis: Can be categorical (products, names, categories) - stored as strings/objects
- Y-axis: Must be numeric (sales, revenue, counts) - can be stored as numbers or numeric strings
- Example: Products (A) vs Sales (B) → {"chart_type": "bar", "x_column": "Product", "y_column": "Sales"}

OUTPUT FORMATS:
Single: {"chart_type": "bar", "x_column": "Name", "y_column": "Value", "title": "Title", "description": "Desc"}
Multiple: {"charts": [{"chart_type": "bar", "x_column": "X", "y_column": "Y", "title": "T", "description": "D"}, ...]}

EXAMPLES:
"bar chart of revenue by country" → {"chart_type": "bar", "x_column": "Country", "y_column": "Revenue", "title": "Revenue by Country", "description": "Bar chart"}
"graph between A and B" → {"chart_type": "bar", "x_column": "ColumnA", "y_column": "ColumnB", "title": "ColumnB by ColumnA", "description": "Bar chart"}
"create dashboard" → {"charts": [{"chart_type": "bar", ...}, {"chart_type": "line", ...}]}

Return ONLY valid JSON, no markdown or explanations.
"""


class ChartBot:
    """Bot for generating chart configurations"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize Chart Bot
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost savings)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        # Use provided model directly (no env var override) since LLMAgent handles routing
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize feedback learner
        try:
            self.feedback_learner = FeedbackLearner()
        except Exception:
            self.feedback_learner = None
        
        # Initialize training data loader
        try:
            self.training_data_loader = TrainingDataLoader()
        except Exception:
            self.training_data_loader = None
    
    def generate_chart_plan(
        self,
        user_prompt: str,
        available_columns: List[str],
        sample_data: Optional[List[Dict]] = None,
        df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Generate chart configuration
        
        Args:
            user_prompt: User's chart request
            available_columns: Available column names
            sample_data: Sample data rows
            df: DataFrame for data analysis (optional, needed for generic requests)
        
        Returns:
            Chart configuration dict (single chart) or dict with "charts" array (multiple charts)
        """
        try:
            # Detect if request is generic
            generic_keywords = ["dashboard", "graphs", "visualizations", "charts", "visualize", 
                              "show data", "create graphs", "create charts", "make graphs"]
            is_generic = any(keyword in user_prompt.lower() for keyword in generic_keywords)
            
            # Analyze data if generic request and DataFrame provided
            data_analysis = None
            if is_generic and df is not None:
                data_analysis = self.analyze_data_for_charts(df, available_columns, sample_data)
            # Get chart-specific knowledge base summary
            kb_summary = get_chart_knowledge_base_summary()
            
            # Get similar examples from training data and feedback
            similar_examples_text = ""
            all_examples = []
            
            if self.training_data_loader:
                try:
                    training_examples = self.training_data_loader.get_examples_for_prompt(user_prompt, limit=3)
                    all_examples.extend(training_examples)
                except Exception:
                    pass
            
            if self.feedback_learner:
                try:
                    feedback_examples = self.feedback_learner.get_similar_successful_examples(user_prompt, limit=2)
                    for ex in feedback_examples:
                        all_examples.append({
                            "prompt": ex["prompt"],
                            "chart_config": ex.get("chart_config") or ex.get("action_plan", {}).get("chart_config", {})
                        })
                except Exception:
                    pass
            
            if all_examples:
                similar_examples_text = "\n\nFEW-SHOT LEARNING EXAMPLES:\n"
                for i, ex in enumerate(all_examples[:5], 1):
                    similar_examples_text += f"\nExample {i}:\n"
                    similar_examples_text += f"User: {ex['prompt']}\n"
                    chart_config = ex.get("chart_config", {})
                    similar_examples_text += f"Response: {json.dumps(chart_config, indent=2)}\n"
            
            # Get column mapping info (Excel letters → actual column names)
            column_mapping = get_column_mapping_info(available_columns)
            
            # Enhance prompt to handle Excel column references in user request
            # Check if user mentions Excel column letters (A, B, C, etc.)
            excel_ref_pattern = r'\b([A-Z])\b'
            excel_refs = re.findall(excel_ref_pattern, user_prompt.upper())
            if excel_refs and len(excel_refs) >= 2:
                # User likely wants chart between Excel columns
                # Add explicit instruction to resolve these
                excel_instruction = f"\nNOTE: User mentioned Excel columns {', '.join(set(excel_refs[:2]))}. "
                excel_instruction += "Resolve these to actual column names using the column mapping below.\n"
                column_mapping = excel_instruction + column_mapping
            
            # Build prompt with context
            prompt = self._build_chart_prompt(
                user_prompt, 
                available_columns, 
                sample_data, 
                kb_summary, 
                similar_examples_text, 
                column_mapping,
                data_analysis=data_analysis,
                is_generic=is_generic
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CHART_BOT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                top_p=0.95,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                chart_config = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    chart_config = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            # Handle multiple charts (generic requests) or single chart
            if "charts" in chart_config and isinstance(chart_config["charts"], list):
                # Multiple charts - validate each
                validated_charts = []
                for chart in chart_config["charts"]:
                    validated = self._validate_chart_config(chart, available_columns)
                    validated_charts.append(validated)
                chart_config = {"charts": validated_charts}
            else:
                # Single chart - validate normally
                chart_config = self._validate_chart_config(chart_config, available_columns)
            
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            tokens_used = prompt_tokens + completion_tokens
            
            logger.info(f"ChartBot tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={tokens_used}")
            
            return {
                "chart_config": chart_config,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"ChartBot failed: {str(e)}")
            raise RuntimeError(f"Chart configuration generation failed: {str(e)}")
    
    def _build_chart_prompt(self, user_prompt: str, columns: List[str], sample_data: Optional[List[Dict]], 
                           kb_summary: str = "", similar_examples: str = "", column_mapping: str = "",
                           data_analysis: Optional[Dict] = None, is_generic: bool = False) -> str:
        """Build prompt for chart generation"""
        columns_info = f"Available columns: {', '.join(columns)}"
        
        sample_text = ""
        if sample_data:
            # Limit to 3 rows to reduce tokens
            sample_text = "\n\nSample data (first 3 rows):\n"
            for i, row in enumerate(sample_data[:3], 1):
                # Only include key columns to reduce token usage
                sample_row = {k: v for k, v in list(row.items())[:5]}  # Max 5 columns per row
                sample_text += f"Row {i}: {sample_row}\n"
        
        # Add data analysis for generic requests (condensed to reduce tokens)
        analysis_text = ""
        if is_generic and data_analysis:
            numeric = ', '.join(data_analysis.get('numeric_columns', [])[:5]) or 'None'
            categorical = ', '.join(data_analysis.get('categorical_columns', [])[:5]) or 'None'
            datetime_cols = ', '.join(data_analysis.get('datetime_columns', [])[:3]) or 'None'
            
            analysis_text = f"\nDATA ANALYSIS:\nNumeric: {numeric}\nCategorical: {categorical}\nDatetime: {datetime_cols}\n"
            
            # Only include top 3 suggested charts to reduce tokens
            suggested = data_analysis.get('suggested_charts', [])[:3]
            if suggested:
                analysis_text += "Suggested charts:\n"
                for i, chart in enumerate(suggested, 1):
                    analysis_text += f"{i}. {chart.get('chart_type', 'unknown')}: {chart.get('x_column', 'X')} vs {chart.get('y_column', 'Y')}\n"
        
        kb_context = ""
        if kb_summary:
            kb_context = f"\n\nKNOWLEDGE BASE CONTEXT:\n{kb_summary}\n"
        
        examples_context = ""
        if similar_examples:
            examples_context = f"\n{similar_examples}\n"
        
        # Build concise prompt to reduce tokens
        prompt_parts = []
        if analysis_text:
            prompt_parts.append(analysis_text.strip())
        if kb_context:
            prompt_parts.append(kb_context.strip())
        if examples_context:
            prompt_parts.append(examples_context.strip())
        if column_mapping:
            prompt_parts.append(column_mapping.strip())
        
        prompt_parts.append(f"User Request: {user_prompt}")
        prompt_parts.append(columns_info)
        if sample_text:
            prompt_parts.append(sample_text.strip())
        
        prompt_parts.append(f"{'Generate MULTIPLE charts in a charts array. ' if is_generic else 'Generate SINGLE chart config. '}Use actual column names. Return ONLY valid JSON.")
        
        return "\n\n".join(prompt_parts)
    
    def _validate_chart_config(self, chart_config: Dict, available_columns: List[str]) -> Dict:
        """Validate and fix chart configuration"""
        chart_type = chart_config.get("chart_type", "bar")
        x_column = chart_config.get("x_column")
        y_column = chart_config.get("y_column")
        
        # Validate chart type
        valid_types = ["bar", "line", "pie", "histogram", "scatter"]
        if chart_type not in valid_types:
            chart_type = "bar"  # Default
        
        # Validate columns - use column resolution (handles Excel letters)
        if x_column:
            resolved = resolve_column_reference(x_column, available_columns)
            if resolved:
                x_column = resolved
            elif x_column not in available_columns:
                # Try to find closest match (fallback)
                x_column_lower = str(x_column).lower()
                for col in available_columns:
                    if x_column_lower in str(col).lower() or str(col).lower() in x_column_lower:
                        x_column = col
                        break
                else:
                    x_column = available_columns[0] if available_columns else None
            else:
                # Column exists, use it
                pass
        else:
            x_column = available_columns[0] if available_columns else None
        
        if y_column:
            resolved = resolve_column_reference(y_column, available_columns)
            if resolved:
                y_column = resolved
            elif y_column not in available_columns:
                # Try to find closest match (fallback)
                y_column_lower = str(y_column).lower()
                for col in available_columns:
                    if y_column_lower in str(col).lower() or str(col).lower() in y_column_lower:
                        y_column = col
                        break
                else:
                    y_column = available_columns[1] if len(available_columns) > 1 else None
            else:
                # Column exists, use it
                pass
        else:
            y_column = available_columns[1] if len(available_columns) > 1 else None
        
        return {
            "chart_type": chart_type,
            "x_column": x_column,
            "y_column": y_column,
            "title": chart_config.get("title", "Chart"),
            "description": chart_config.get("description", f"{chart_type} chart")
        }
    
    def analyze_data_for_charts(
        self,
        df: pd.DataFrame,
        available_columns: List[str],
        sample_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Analyze data and suggest chart configurations
        
        Args:
            df: DataFrame to analyze
            available_columns: Available column names
            sample_data: Sample data rows
            
        Returns:
            Dictionary with analysis and suggested chart configurations
        """
        import pandas as pd
        import numpy as np
        
        analysis = {
            "numeric_columns": [],
            "categorical_columns": [],
            "datetime_columns": [],
            "suggested_charts": []
        }
        
        # Analyze column types
        for col in available_columns:
            if col not in df.columns:
                continue
                
            col_data = df[col]
            
            # Check if numeric
            if pd.api.types.is_numeric_dtype(col_data):
                analysis["numeric_columns"].append(col)
            # Check if datetime
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                analysis["datetime_columns"].append(col)
            # Check if categorical (low unique count or object type)
            elif col_data.nunique() < len(df) * 0.5 or col_data.dtype == 'object':
                analysis["categorical_columns"].append(col)
        
        # Suggest chart configurations based on data
        numeric_cols = analysis["numeric_columns"]
        categorical_cols = analysis["categorical_columns"]
        datetime_cols = analysis["datetime_columns"]
        
        # 1. Bar chart: categorical x numeric
        if categorical_cols and numeric_cols:
            for cat_col in categorical_cols[:2]:  # Top 2 categorical
                for num_col in numeric_cols[:2]:  # Top 2 numeric
                    analysis["suggested_charts"].append({
                        "chart_type": "bar",
                        "x_column": cat_col,
                        "y_column": num_col,
                        "title": f"{num_col} by {cat_col}",
                        "description": f"Bar chart comparing {num_col} across {cat_col} categories"
                    })
        
        # 2. Line chart: datetime x numeric
        if datetime_cols and numeric_cols:
            for dt_col in datetime_cols[:1]:  # First datetime
                for num_col in numeric_cols[:2]:  # Top 2 numeric
                    analysis["suggested_charts"].append({
                        "chart_type": "line",
                        "x_column": dt_col,
                        "y_column": num_col,
                        "title": f"{num_col} Over Time",
                        "description": f"Line chart showing {num_col} trends over {dt_col}"
                    })
        
        # 3. Pie chart: categorical x numeric (count or sum)
        if categorical_cols and numeric_cols:
            for cat_col in categorical_cols[:1]:  # First categorical
                for num_col in numeric_cols[:1]:  # First numeric
                    analysis["suggested_charts"].append({
                        "chart_type": "pie",
                        "x_column": cat_col,
                        "y_column": num_col,
                        "title": f"Distribution of {num_col} by {cat_col}",
                        "description": f"Pie chart showing {num_col} distribution"
                    })
        
        # 4. Histogram: numeric column distribution
        if numeric_cols:
            for num_col in numeric_cols[:2]:  # Top 2 numeric
                analysis["suggested_charts"].append({
                    "chart_type": "histogram",
                    "x_column": num_col,
                    "y_column": None,
                    "title": f"Distribution of {num_col}",
                    "description": f"Histogram showing {num_col} distribution"
                })
        
        # 5. Scatter plot: numeric x numeric
        if len(numeric_cols) >= 2:
            analysis["suggested_charts"].append({
                "chart_type": "scatter",
                "x_column": numeric_cols[0],
                "y_column": numeric_cols[1],
                "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
                "description": f"Scatter plot showing relationship between {numeric_cols[0]} and {numeric_cols[1]}"
            })
        
        # Limit to top 2 suggestions (to avoid OOM on low-memory servers)
        # For 512MB servers, generating 3+ charts causes OOM kills
        # 2 charts is the safe limit for 512MB RAM
        analysis["suggested_charts"] = analysis["suggested_charts"][:2]
        
        return analysis

