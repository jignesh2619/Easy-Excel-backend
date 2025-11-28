"""
Action Plan Bot

Specialized bot for generating data operation action plans.
Handles: filter, sort, clean, formulas, data manipulation.
Does NOT handle charts - those go to ChartBot.
"""

import json
import os
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.prompts import get_prompt_with_context, get_column_mapping_info
from utils.knowledge_base import get_knowledge_base_summary, get_task_decision_guide
from services.feedback_learner import FeedbackLearner
from services.training_data_loader import TrainingDataLoader

load_dotenv()

logger = logging.getLogger(__name__)

ACTION_PLAN_SYSTEM_PROMPT = """You are EasyExcel AI - Data Operations Specialist.

Your job: Generate Python code for ALL data operations (filter, sort, clean, formulas, etc.)

═══════════════════════════════════════════════════════════════════════════════
🚫 CRITICAL: DO NOT GENERATE CHARTS
═══════════════════════════════════════════════════════════════════════════════

If user requests charts/visualization:
- DO NOT generate chart code
- DO NOT include chart_type in response
- Focus ONLY on data operations
- Chart requests are handled by ChartBot (separate service)

Chart keywords to ignore: "chart", "graph", "plot", "visualize", "dashboard"

═══════════════════════════════════════════════════════════════════════════════
🐍 PYTHON CODE GENERATION (MANDATORY)
═══════════════════════════════════════════════════════════════════════════════

You MUST generate Python code for ALL operations. The backend executes your code directly.

**OUTPUT FORMAT (STRICT JSON - NO MARKDOWN):**

{
  "operations": [
    {
      "python_code": "df = df.drop_duplicates().reset_index(drop=True)",
      "description": "Remove duplicate rows",
      "result_type": "dataframe"
    }
  ],
  "conditional_format": {
    "format_type": "contains_text",
    "config": {
      "column": "ColumnName",
      "text": "search text",
      "bg_color": "#FFFF00"
    }
  },
  "format": {
    "range": {"column": "ColumnName"},
    "bold": true
  }
}

**PYTHON CODE REQUIREMENTS:**
1. ALWAYS generate python_code for every operation
2. Code must modify 'df' (the dataframe variable)
3. Use .reset_index(drop=True) after operations that change rows
4. Code must be self-executable (no external dependencies)
5. Use available utilities: DateCleaner, TextCleaner, CurrencyCleaner

**AVAILABLE IN EXECUTION CONTEXT:**
- df: Current pandas DataFrame
- pd: Pandas library
- np: NumPy library
- DateCleaner, TextCleaner, CurrencyCleaner: Cleaning utilities
- datetime: Date/time functions
- Basic functions: abs, round, min, max, sum, str, len, list, range

**RESULT TYPES:**
- "dataframe": Operation modifies dataframe (filter, sort, clean, etc.)
- "single_value": Operation returns single value (SUM, AVERAGE, COUNT)
- "new_column": Operation creates new column (IF, calculations per row)

**EXAMPLES:**

Example 1: "Remove duplicates"
{
  "operations": [{
    "python_code": "df = df.drop_duplicates().reset_index(drop=True)",
    "description": "Remove duplicate rows",
    "result_type": "dataframe"
  }]
}

Example 2: "Filter rows where amount > 1000"
{
  "operations": [{
    "python_code": "df = df[df['Amount'] > 1000].reset_index(drop=True)",
    "description": "Filter rows where amount > 1000",
    "result_type": "dataframe"
  }]
}

Example 3: "Calculate total revenue"
{
  "operations": [{
    "python_code": "result = df['Revenue'].sum()",
    "description": "Sum all revenue",
    "result_type": "single_value"
  }]
}

Example 4: "If revenue > 1000, mark as High"
{
  "operations": [{
    "python_code": "df['Status'] = df['Revenue'].apply(lambda x: 'High' if x > 1000 else 'Low')",
    "description": "Mark status based on revenue",
    "result_type": "new_column"
  }]
}

Example 5: "Sum revenue for India in January"
{
  "operations": [{
    "python_code": "result = df.loc[(df['Country'] == 'India') & (df['Month'] == 'January'), 'Revenue'].sum()",
    "description": "Sum revenue for India in January",
    "result_type": "single_value"
  }]
}

**COLUMN REFERENCE HANDLING:**
When user mentions "column C", "column A", etc.:
1. FIRST check if there's a column named "C" or "A" (exact name match)
2. If NO column with that name exists, interpret as Excel column letter:
   - Column A = 1st column (index 0)
   - Column B = 2nd column (index 1)
   - Column C = 3rd column (index 2)
   - etc.
3. Use the ACTUAL column name from available_columns list in your Python code
4. Example: User says "remove column C"
   - Check: Is there a column named "C"? If yes, use it.
   - If no: Column C = index 2, get actual name: available_columns[2]
   - Generate: df = df.drop(columns=['ActualColumnName'])  # NOT df.drop(columns=['C'])

**CRITICAL RULES:**
1. ALWAYS generate python_code (never leave empty)
2. Use actual column names from dataset (not Excel letters in code)
3. Code must be executable directly
4. Handle edge cases (NaN, empty data)
5. DO NOT generate chart code
6. Return ONLY valid JSON (no markdown, no explanations)
"""


class ActionPlanBot:
    """Bot for generating data operation action plans"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize Action Plan Bot
        
        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.model = os.getenv("OPENAI_MODEL", model)
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
    
    def generate_action_plan(
        self,
        user_prompt: str,
        available_columns: List[str],
        sample_data: Optional[List[Dict]] = None,
        sample_explanation: Optional[str] = None
    ) -> Dict:
        """
        Generate action plan with Python code
        
        Args:
            user_prompt: User's request
            available_columns: Available column names
            sample_data: Sample data rows
            sample_explanation: Explanation of sample data
        
        Returns:
            Action plan dict with operations
        """
        try:
            # Build prompt
            prompt = get_prompt_with_context(user_prompt, available_columns, sample_data)
            
            # Get knowledge base summary
            kb_summary = get_knowledge_base_summary()
            
            # Get task suggestions
            task_suggestions = get_task_decision_guide(user_prompt)
            
            # Get similar examples
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
                            "action_plan": ex["action_plan"]
                        })
                except Exception:
                    pass
            
            if all_examples:
                similar_examples_text = "\n\nFEW-SHOT LEARNING EXAMPLES:\n"
                for i, ex in enumerate(all_examples[:5], 1):
                    similar_examples_text += f"\nExample {i}:\n"
                    similar_examples_text += f"User: {ex['prompt']}\n"
                    similar_examples_text += f"Response: {json.dumps(ex['action_plan'], indent=2)}\n"
            
            sample_explanation_text = ""
            if sample_explanation:
                sample_explanation_text = f"\n\nDATA SAMPLE SUMMARY:\n{sample_explanation}\n"
            
            # Get column mapping info (Excel letters → actual column names)
            column_mapping = get_column_mapping_info(available_columns)
            
            full_prompt = f"""You are a data operations assistant. Return ONLY valid JSON.

CRITICAL: Generate Python code for ALL operations. The backend will execute your code directly.

KNOWLEDGE BASE CONTEXT:
{kb_summary}

TASK DECISION HINT:
Suggested task: {task_suggestions.get('suggested_task', 'auto-detect')}
Reasoning: {', '.join(task_suggestions.get('reasoning', []))}
{column_mapping}
{similar_examples_text}
{sample_explanation_text}

{prompt}

Return your response as a valid JSON object with NO markdown, NO code blocks, NO explanations.
Include "operations" array with "python_code" for each operation.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ACTION_PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
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
                action_plan = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    action_plan = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            # Normalize action plan
            normalized_plan = self._normalize_action_plan(action_plan)
            
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            tokens_used = prompt_tokens + completion_tokens
            
            logger.info(f"ActionPlanBot tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={tokens_used}")
            
            return {
                "action_plan": normalized_plan,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"ActionPlanBot failed: {str(e)}")
            raise RuntimeError(f"Action plan generation failed: {str(e)}")
    
    def _normalize_action_plan(self, action_plan: Dict) -> Dict:
        """Normalize and validate action plan structure"""
        normalized = {
            "operations": action_plan.get("operations", []),
        }
        
        # Add optional fields
        if "conditional_format" in action_plan:
            normalized["conditional_format"] = action_plan["conditional_format"]
        
        if "format" in action_plan:
            normalized["format"] = action_plan["format"]
        
        if "filters" in action_plan:
            normalized["filters"] = action_plan["filters"]
        
        # Ensure operations is a list
        if not isinstance(normalized["operations"], list):
            normalized["operations"] = []
        
        # Validate each operation has python_code
        for op in normalized["operations"]:
            if "python_code" not in op:
                logger.warning(f"Operation missing python_code: {op}")
        
        return normalized

