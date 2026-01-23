"""
Action Plan Bot - OPTIMIZED VERSION
Minimal prompt for faster LLM calls
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
from services.extraction_pattern_analyzer import ExtractionPatternAnalyzer

load_dotenv()
logger = logging.getLogger(__name__)

# SIMPLIFIED PROMPT - Essential rules only (~80 lines)
ACTION_PLAN_SYSTEM_PROMPT = """You are EasyExcel AI. Generate Python code for data operations.

**OUTPUT:** JSON with operations array containing python_code for each operation.

⚠️⚠️⚠️ CRITICAL CODE FORMATTING RULES - MUST FOLLOW EXACTLY ⚠️⚠️⚠️

**RULE 1: ALWAYS use \\n for line breaks in python_code string**
- The python_code is a STRING - you MUST use \\n (backslash-n) for newlines
- NEVER put multiple statements on one line
- NEVER use actual newlines in the JSON string (they break JSON parsing)

**RULE 2: Control flow MUST be on separate lines**
- ✅ CORRECT: "col_a_idx = 0\\nfor i in range(len(df)):\\n    if pd.isna(df.loc[i, 'A']):\\n        df.loc[i, 'A'] = value"
- ❌ WRONG: "col_a_idx = 0 for i in range(len(df)):" (NO - must have \\n)
- ❌ WRONG: "if x: if y:" (NO - must have \\n between)

**RULE 3: Template format for multi-column filling:**
When filling multiple columns, use this EXACT pattern:
"sales = df[df['Dept'] == 'Sales']['Name'].tolist()\\ncol_a_idx = 0\\nfor i in range(len(df)):\\n    if pd.isna(df.loc[i, 'A']) or df.loc[i, 'A'] == '':\\n        if col_a_idx < len(sales):\\n            df.loc[i, 'A'] = sales[col_a_idx]\\n            col_a_idx += 1\\ncol_b_idx = 0\\nfor i in range(len(df)):\\n    if pd.isna(df.loc[i, 'B']) or df.loc[i, 'B'] == '':\\n        if col_b_idx < len(finance):\\n            df.loc[i, 'B'] = finance[col_b_idx]\\n            col_b_idx += 1"

**REQUIREMENTS:**
- Code modifies 'df' (dataframe variable)
- Use .reset_index(drop=True) after operations that change rows
- Available: pd, np, re, DateCleaner, TextCleaner, CurrencyCleaner
- Method chains: keep on ONE line (df.groupby()['col'].sum())
- Use semicolons (;) ONLY for simple statements on same line, NEVER before for/if/while

**VALIDATION CHECKLIST before returning:**
1. ✓ Every for/if/while is on its own line (separated by \\n)
2. ✓ No variable assignment immediately followed by for/if/while on same line
3. ✓ All control flow blocks are properly indented (use spaces after \\n)
4. ✓ python_code is a valid JSON string (escape quotes, use \\n for newlines)

**KEY RULES:**
- Code executes on FULL dataset, not just sample
- Use actual column names from available_columns list
- Map positional refs: first=0, second=1, third=2, last=-1
- Map Excel letters: A=0, B=1, C=2, etc.

Generate concise, correct code with proper \\n line breaks."""


class ActionPlanBot:
    """Bot for generating data operation action plans - OPTIMIZED"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize Action Plan Bot
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost savings)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
        # DISABLED for performance
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
        Generate action plan with Python code - OPTIMIZED
        
        Args:
            user_prompt: User's request
            available_columns: Available column names
            sample_data: Sample data rows
            sample_explanation: Explanation of sample data
        
        Returns:
            Action plan dict with operations
        """
        try:
            # Extract total rows from sample_explanation if available
            total_rows = None
            if sample_explanation:
                import re
                match = re.search(r'(\d+)\s+rows?\s+selected\s+from\s+(\d+)\s+total', sample_explanation, re.IGNORECASE)
                if match:
                    total_rows = int(match.group(2))
            
            # Build prompt with total row count
            prompt = get_prompt_with_context(user_prompt, available_columns, sample_data, total_rows=total_rows)
            
            # Get knowledge base summary (simplified)
            kb_summary = get_knowledge_base_summary()
            
            # Get task suggestions (simplified output)
            task_suggestions = get_task_decision_guide(user_prompt)
            task_hint = task_suggestions.get('suggested_task', 'auto-detect')
            
            # Get column mapping info (Excel letters → actual column names)
            column_mapping = get_column_mapping_info(available_columns)
            
            # Build concise prompt - minimal context
            prompt_parts = []
            
            if kb_summary:
                prompt_parts.append(f"Tasks: {kb_summary}")
            
            if task_hint != 'auto-detect':
                prompt_parts.append(f"Task hint: {task_hint}")
            
            if column_mapping:
                prompt_parts.append(column_mapping)
            
            prompt_parts.append(prompt)
            
            # Build final prompt
            full_prompt = "\n\n".join(prompt_parts) + "\n\nReturn ONLY valid JSON with operations array containing python_code for each operation."

            # Use faster model and shorter response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ACTION_PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,  # Lower temperature for consistency
                max_tokens=2000,  # Reduced from default
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
                    logger.error(f"Could not parse JSON from response: {content[:200]}")
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            # Normalize action plan
            normalized_plan = self._normalize_action_plan(action_plan)
            
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            tokens_used = prompt_tokens + completion_tokens
            
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
        for field in ["add_row", "add_column", "delete_column", "delete_rows", "sort", 
                     "conditional_format", "format", "filters", "task"]:
            if field in action_plan:
                normalized[field] = action_plan[field]
        
        # Ensure operations is a list
        if not isinstance(normalized["operations"], list):
            normalized["operations"] = []
        
        # Validate and extract python_code for each operation
        for op in normalized["operations"]:
            if "python_code" not in op or not op.get("python_code", "").strip():
                exec_instructions = op.get("execution_instructions", {})
                if isinstance(exec_instructions, dict) and "code" in exec_instructions:
                    op["python_code"] = exec_instructions["code"]
                elif "python_code" not in op:
                    logger.warning(f"Operation missing python_code: {op}")
        
        return normalized
