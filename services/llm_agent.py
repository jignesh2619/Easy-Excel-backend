"""
LLM Agent Service

Interprets user prompts and returns structured action plans using OpenAI GPT-4.1.
The LLM does NOT modify data directly - it only returns action plans.
"""

import json
import os
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.prompts import get_prompt_with_context
from utils.knowledge_base import get_knowledge_base_summary, get_task_decision_guide
from services.feedback_learner import FeedbackLearner
from services.training_data_loader import TrainingDataLoader
from services.action_plan_bot import ActionPlanBot
from services.chart_bot import ChartBot

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = (
    "You are EasyExcel AI, an expert spreadsheet automation assistant with access to a modular, production-grade backend architecture. "
    "\n\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "🏗️ BACKEND ARCHITECTURE - AVAILABLE MODULES & FUNCTIONS\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "\n"
    "The backend uses a modular architecture with specialized modules:\n"
    "\n"
    "1. **dflib/** - DataFrame operations (filter, sort, group_by, add/delete columns, etc.)\n"
    "2. **summarizer/** - Excel file analysis (column types, statistics, data quality)\n"
    "3. **cleaning/** - Data cleaning functions:\n"
    "   - DateCleaner: parse dates, normalize formats, extract components\n"
    "   - CurrencyCleaner: extract numeric values from currency strings\n"
    "   - TextCleaner: trim, normalize case, remove special chars, split/merge columns\n"
    "4. **excel_writer/** - Safe Excel writing with formatting (XlsxWriter, OpenpyxlWriter)\n"
    "5. **formula/** - Formula evaluation (xlcalculator with fallback)\n"
    "\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "📊 CRITICAL: ANALYZE THE SHEET FIRST, THEN ACT\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "\n"
    "BEFORE generating any action plan, you MUST:\n"
    "\n"
    "1. **ANALYZE THE COMPLETE DATASET** provided to you:\n"
    "   - Understand the structure: How many rows? How many columns?\n"
    "   - Identify column names EXACTLY as they appear (case-sensitive)\n"
    "   - Understand data types: numeric, text, dates, mixed\n"
    "   - Check for patterns: duplicates, missing values, formatting issues\n"
    "   - Note any special characters, unusual formats, or edge cases\n"
    "\n"
    "2. **MAP USER REFERENCES TO ACTUAL DATA**:\n"
    "   - If user says '3rd column' → Find column at index 2, get its ACTUAL name\n"
    "   - If user says 'column with phone numbers' → Search ALL rows to find which column contains phone data\n"
    "   - If user says 'remove column X' → Verify X exists in available_columns, use exact name\n"
    "   - If user says 'highlight cells with Y' → Search dataset to find which column(s) contain Y\n"
    "\n"
    "3. **MAKE INFORMED DECISIONS**:\n"
    "   - Don't blindly follow instructions - understand the data first\n"
    "   - If user says 'remove 3rd column', verify what that column actually contains\n"
    "   - If user says 'clean dates', identify which columns are dates by analyzing the data\n"
    "   - If user says 'remove duplicates', check which columns might have duplicates\n"
    "\n"
    "4. **GENERATE COMPLETE, EXECUTABLE JSON**:\n"
    "   - Use ACTUAL column names from the dataset (never use positions or descriptions)\n"
    "   - Include all required fields for the operation\n"
    "   - Provide execution_instructions when needed\n"
    "   - Ensure the JSON can be directly executed by the backend\n"
    "\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "📋 RESPONSE FORMAT\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "\n"
    "Respond with ONLY valid JSON that our backend can execute directly.\n"
    "Never include markdown, explanations, or extra text.\n"
    "The JSON must use actual column names from the provided dataset.\n"
)


class LLMAgent:
    """Handles LLM interpretation of user prompts using OpenAI GPT-4"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM Agent with OpenAI GPT-4
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.model = os.getenv("OPENAI_MODEL", model)
        
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Initialize feedback learner for continuous improvement
        try:
            self.feedback_learner = FeedbackLearner()
        except Exception:
            self.feedback_learner = None
        
        # Initialize training data loader for few-shot learning
        try:
            self.training_data_loader = TrainingDataLoader()
        except Exception:
            self.training_data_loader = None
        
        # Initialize specialized bots
        self.action_plan_bot = ActionPlanBot(api_key=self.api_key, model=self.model)
        self.chart_bot = ChartBot(api_key=self.api_key, model=self.model)
    
    def _is_chart_request(self, prompt: str) -> bool:
        """
        Detect if request is for chart generation
        
        Args:
            prompt: User prompt
        
        Returns:
            True if chart request, False otherwise
        """
        prompt_lower = prompt.lower()
        chart_keywords = [
            "chart", "graph", "plot", "visualize", "visualization",
            "bar chart", "line chart", "pie chart", "histogram",
            "scatter plot", "scatter", "dashboard", "show chart",
            "create chart", "generate chart", "make chart",
            "draw chart", "display chart"
        ]
        return any(keyword in prompt_lower for keyword in chart_keywords)
    
    def interpret_prompt(
        self, 
        user_prompt: str, 
        available_columns: List[str],
        user_id: Optional[str] = None,
        sample_data: Optional[List[Dict]] = None,
        sample_explanation: Optional[str] = None,
        df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Interpret user prompt and route to appropriate bot
        
        Routes to:
        - ChartBot: If chart/visualization request
        - ActionPlanBot: For all data operations
        """
        # Check if chart request
        is_chart = self._is_chart_request(user_prompt)
        
        if is_chart:
            # Route to ChartBot
            logger.info("Routing to ChartBot for chart generation")
            result = self.chart_bot.generate_chart_plan(
                user_prompt=user_prompt,
                available_columns=available_columns,
                sample_data=sample_data,
                df=df  # Pass DataFrame for data analysis
            )
            # Handle multiple charts (generic requests) or single chart
            chart_config = result["chart_config"]
            if "charts" in chart_config:
                # Multiple charts - return array
                return {
                    "action_plan": {
                        "task": "chart",
                        "chart_configs": chart_config["charts"]  # Array of charts
                    },
                    "tokens_used": result.get("tokens_used", 0)
                }
            else:
                # Single chart - return single config
                return {
                    "action_plan": {
                        "task": "chart",
                        "chart_config": chart_config  # Single chart
                    },
                    "tokens_used": result.get("tokens_used", 0)
                }
        else:
            # Route to ActionPlanBot
            logger.info("🔄 Routing to ActionPlanBot for data operations")
            logger.info(f"📝 User prompt: {user_prompt}")
            result = self.action_plan_bot.generate_action_plan(
                user_prompt=user_prompt,
                available_columns=available_columns,
                sample_data=sample_data,
                sample_explanation=sample_explanation
            )
            logger.info(f"📤 ActionPlanBot returned action plan with keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            if isinstance(result, dict) and "conditional_format" in result:
                logger.info(f"✅ Conditional format in result: {result['conditional_format']}")
            return result
    
    def _legacy_interpret_prompt(
        self, 
        user_prompt: str, 
        available_columns: List[str],
        user_id: Optional[str] = None,
        sample_data: Optional[List[Dict]] = None,
        sample_explanation: Optional[str] = None
    ) -> Dict:
        """
        Legacy method - kept for backward compatibility
        """
        try:
            prompt = get_prompt_with_context(user_prompt, available_columns, sample_data)
            
            # Get knowledge base summary for enhanced context
            kb_summary = get_knowledge_base_summary()
            
            # Get task decision suggestions (for validation, not enforcement)
            task_suggestions = get_task_decision_guide(user_prompt)
            
            # Get similar examples for few-shot learning
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
                similar_examples_text = "\n\nFEW-SHOT LEARNING EXAMPLES (from training data and past executions):\n"
                for i, ex in enumerate(all_examples[:5], 1):
                    similar_examples_text += f"\nExample {i}:\n"
                    similar_examples_text += f"User: {ex['prompt']}\n"
                    similar_examples_text += f"Response: {json.dumps(ex['action_plan'], indent=2)}\n"
                    if ex.get('execution_instructions'):
                        similar_examples_text += f"Execution: {ex['execution_instructions']}\n"
            
            sample_explanation_text = ""
            if sample_explanation:
                sample_explanation_text = f"\n\nDATA SAMPLE SUMMARY:\n{sample_explanation}\n"
            
            full_prompt = f"""You are a data analysis assistant that returns ONLY valid JSON. 
Do not include any markdown formatting, code blocks, or explanatory text. Return pure JSON only.

CRITICAL: Provide detailed "execution_instructions" in the "operations" array for each operation.
This allows the system to execute your plan dynamically without hardcoded if-else statements.
Think step-by-step about how to execute the user's request using pandas operations or formula functions.

KNOWLEDGE BASE CONTEXT:
{kb_summary}

TASK DECISION HINT (use as guidance, not strict rule):
Based on the user prompt, the suggested task is: {task_suggestions.get('suggested_task', 'auto-detect')}
Reasoning: {', '.join(task_suggestions.get('reasoning', []))}
Confidence: {task_suggestions.get('confidence', 0)}
{similar_examples_text}
{sample_explanation_text}

{prompt}

Return your response as a valid JSON object with no additional formatting.
Include "operations" array with "execution_instructions" for each operation."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.1,
                top_p=0.95,
            )
            
            content = (response.choices[0].message.content or "").strip()
            
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            tokens_used = prompt_tokens + completion_tokens
            logger.info(
                "OpenAI token usage: prompt=%s, completion=%s, total=%s",
                prompt_tokens,
                completion_tokens,
                tokens_used,
            )
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            try:
                action_plan = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                if json_match:
                    action_plan = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            normalized_plan = self._normalize_action_plan(action_plan)
            
            return {
                "action_plan": normalized_plan,
                "tokens_used": tokens_used
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"LLM interpretation failed: {str(e)}")
    
    def _normalize_action_plan(self, action_plan: Dict) -> Dict:
        """
        Normalize and validate action plan structure
        
        Args:
            action_plan: Raw action plan from LLM
            
        Returns:
            Normalized action plan
        """
        # Ensure required fields exist
        normalized = {
            "task": action_plan.get("task", "summarize"),
            "columns_needed": action_plan.get("columns_needed", []),
            "chart_type": action_plan.get("chart_type", "none"),
            "steps": action_plan.get("steps", []),
        }
        
        # Add optional fields if present
        if "filters" in action_plan:
            normalized["filters"] = action_plan["filters"]
        
        if "group_by_column" in action_plan:
            normalized["group_by_column"] = action_plan["group_by_column"]
        
        if "aggregate_function" in action_plan:
            normalized["aggregate_function"] = action_plan["aggregate_function"]
        
        if "aggregate_column" in action_plan:
            normalized["aggregate_column"] = action_plan["aggregate_column"]
        
        # Add editing operation fields if present
        if "delete_rows" in action_plan:
            normalized["delete_rows"] = action_plan["delete_rows"]
        
        if "add_row" in action_plan:
            normalized["add_row"] = action_plan["add_row"]
        
        if "add_column" in action_plan:
            normalized["add_column"] = action_plan["add_column"]
        
        if "delete_column" in action_plan:
            normalized["delete_column"] = action_plan["delete_column"]
        
        if "edit_cell" in action_plan:
            normalized["edit_cell"] = action_plan["edit_cell"]
        
        if "clear_cell" in action_plan:
            normalized["clear_cell"] = action_plan["clear_cell"]
        
        if "auto_fill" in action_plan:
            normalized["auto_fill"] = action_plan["auto_fill"]
        
        if "sort" in action_plan:
            normalized["sort"] = action_plan["sort"]
        
        if "format" in action_plan:
            normalized["format"] = action_plan["format"]
        
        if "conditional_format" in action_plan:
            normalized["conditional_format"] = action_plan["conditional_format"]
        
        # Add formula operation field if present
        if "formula" in action_plan:
            normalized["formula"] = action_plan["formula"]
        
        # Validate task
        valid_tasks = [
            "summarize", "clean", "group_by", "find_missing",
            "filter", "combine_sheets", "generate_chart", "transform",
            "delete_rows", "add_row", "add_column", "delete_column",
            "edit_cell", "clear_cell", "auto_fill", "sort",
            "format", "conditional_format", "formula"
        ]
        if normalized["task"] not in valid_tasks:
            normalized["task"] = "summarize"
        
        # Validate chart_type
        valid_chart_types = ["bar", "line", "pie", "histogram", "scatter", "none"]
        if normalized["chart_type"] not in valid_chart_types:
            normalized["chart_type"] = "none"
        
        return normalized
    
    def get_example_action_plan(self, task_type: str = "group_by") -> Dict:
        """
        Get example action plan for testing
        
        Args:
            task_type: Type of task to generate example for
            
        Returns:
            Example action plan dictionary
        """
        examples = {
            "group_by": {
                "task": "group_by",
                "columns_needed": ["Region", "Revenue"],
                "chart_type": "bar",
                "steps": [
                    "group_by Region sum Revenue",
                    "create_chart bar"
                ],
                "group_by_column": "Region",
                "aggregate_function": "sum",
                "aggregate_column": "Revenue"
            },
            "clean": {
                "task": "clean",
                "columns_needed": [],
                "chart_type": "none",
                "steps": [
                    "remove_duplicates",
                    "fix_formatting",
                    "handle_missing_values"
                ]
            },
            "summarize": {
                "task": "summarize",
                "columns_needed": ["Sales", "Profit"],
                "chart_type": "bar",
                "steps": [
                    "calculate_statistics",
                    "create_summary_chart"
                ]
            },
            "filter": {
                "task": "filter",
                "columns_needed": ["Date", "Amount"],
                "chart_type": "line",
                "steps": [
                    "filter Date >= 2024-01-01",
                    "create_chart line"
                ],
                "filters": {
                    "column": "Date",
                    "condition": ">=",
                    "value": "2024-01-01"
                }
            }
        }
        
        return examples.get(task_type, examples["summarize"])

