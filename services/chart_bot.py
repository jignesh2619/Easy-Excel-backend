"""
Chart Bot

Specialized bot for generating chart configurations.
Handles all chart/visualization requests.
"""

import json
import os
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CHART_BOT_SYSTEM_PROMPT = """You are a Chart Generation Specialist for Excel automation.

Your ONLY job: Generate chart configurations for visualization requests.

═══════════════════════════════════════════════════════════════════════════════
📊 CHART GENERATION RULES
═══════════════════════════════════════════════════════════════════════════════

**OUTPUT FORMAT (STRICT JSON - NO MARKDOWN):**

{
  "chart_type": "bar|line|pie|histogram|scatter",
  "x_column": "ColumnName",
  "y_column": "ColumnName",
  "title": "Chart Title",
  "description": "Chart description"
}

**CHART TYPE SELECTION:**
- bar: Categorical comparison (e.g., revenue by country)
- line: Time series data (e.g., revenue over time)
- pie: Proportions/percentages (e.g., market share)
- histogram: Distribution of numeric data (e.g., age distribution)
- scatter: Relationship between two numeric variables (e.g., sales vs profit)

**COLUMN IDENTIFICATION:**
1. Analyze the dataset provided
2. Identify X and Y columns based on user request
3. Use ACTUAL column names from available_columns
4. For pie charts: X = categories, Y = values
5. For scatter: X and Y = both numeric columns
6. For histogram: X = numeric column (Y is auto-generated)

**EXAMPLES:**

Example 1: "Create a bar chart of revenue by country"
{
  "chart_type": "bar",
  "x_column": "Country",
  "y_column": "Revenue",
  "title": "Revenue by Country",
  "description": "Bar chart showing revenue for each country"
}

Example 2: "Show revenue over time"
{
  "chart_type": "line",
  "x_column": "Date",
  "y_column": "Revenue",
  "title": "Revenue Over Time",
  "description": "Line chart showing revenue trends"
}

Example 3: "Pie chart of market share"
{
  "chart_type": "pie",
  "x_column": "Category",
  "y_column": "MarketShare",
  "title": "Market Share by Category",
  "description": "Pie chart showing market share distribution"
}

Example 4: "Histogram of ages"
{
  "chart_type": "histogram",
  "x_column": "Age",
  "y_column": null,
  "title": "Age Distribution",
  "description": "Histogram showing age distribution"
}

Example 5: "Scatter plot of sales vs profit"
{
  "chart_type": "scatter",
  "x_column": "Sales",
  "y_column": "Profit",
  "title": "Sales vs Profit",
  "description": "Scatter plot showing relationship between sales and profit"
}

**CRITICAL RULES:**
1. ALWAYS use actual column names from dataset
2. Analyze dataset to identify appropriate columns
3. Choose chart type based on data and user request
4. Provide clear, descriptive title
5. Return ONLY valid JSON (no markdown, no explanations)
6. If columns not clear, make best inference from dataset
"""


class ChartBot:
    """Bot for generating chart configurations"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize Chart Bot
        
        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.model = os.getenv("OPENAI_MODEL", model)
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_chart_plan(
        self,
        user_prompt: str,
        available_columns: List[str],
        sample_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate chart configuration
        
        Args:
            user_prompt: User's chart request
            available_columns: Available column names
            sample_data: Sample data rows
        
        Returns:
            Chart configuration dict
        """
        try:
            prompt = self._build_chart_prompt(user_prompt, available_columns, sample_data)
            
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
            
            # Validate chart config
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
    
    def _build_chart_prompt(self, user_prompt: str, columns: List[str], sample_data: Optional[List[Dict]]) -> str:
        """Build prompt for chart generation"""
        columns_info = f"Available columns: {', '.join(columns)}"
        
        sample_text = ""
        if sample_data:
            sample_text = "\n\nSample data (first 5 rows):\n"
            for i, row in enumerate(sample_data[:5], 1):
                sample_text += f"Row {i}: {row}\n"
        
        return f"""
User Request: {user_prompt}

{columns_info}
{sample_text}

Analyze the request and generate chart configuration.
Identify the appropriate chart type and columns from the dataset.
Use actual column names from the available columns list.
Return ONLY valid JSON with chart_type, x_column, y_column, title, and description.
"""
    
    def _validate_chart_config(self, chart_config: Dict, available_columns: List[str]) -> Dict:
        """Validate and fix chart configuration"""
        chart_type = chart_config.get("chart_type", "bar")
        x_column = chart_config.get("x_column")
        y_column = chart_config.get("y_column")
        
        # Validate chart type
        valid_types = ["bar", "line", "pie", "histogram", "scatter"]
        if chart_type not in valid_types:
            chart_type = "bar"  # Default
        
        # Validate columns exist
        if x_column and x_column not in available_columns:
            # Try to find closest match
            x_column_lower = str(x_column).lower()
            for col in available_columns:
                if x_column_lower in str(col).lower() or str(col).lower() in x_column_lower:
                    x_column = col
                    break
            else:
                x_column = available_columns[0] if available_columns else None
        
        if y_column and y_column not in available_columns:
            y_column_lower = str(y_column).lower()
            for col in available_columns:
                if y_column_lower in str(col).lower() or str(col).lower() in y_column_lower:
                    y_column = col
                    break
            else:
                y_column = available_columns[1] if len(available_columns) > 1 else None
        
        return {
            "chart_type": chart_type,
            "x_column": x_column,
            "y_column": y_column,
            "title": chart_config.get("title", "Chart"),
            "description": chart_config.get("description", f"{chart_type} chart")
        }

