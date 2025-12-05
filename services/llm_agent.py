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
    """Handles LLM interpretation of user prompts using OpenAI with hybrid model routing"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize LLM Agent with hybrid model support (gpt-4o-mini default, gpt-4o for complex)
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Default model to use (default: gpt-4o-mini for cost savings)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        # Get model from env var, default to gpt-4o-mini for cost savings
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.complex_model = "gpt-4o"  # Use for complex operations
        
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
        
        # Initialize specialized bots with both models for hybrid routing
        # Mini bots (default for simple operations)
        self.action_plan_bot_mini = ActionPlanBot(api_key=self.api_key, model=self.default_model)
        self.chart_bot_mini = ChartBot(api_key=self.api_key, model=self.default_model)
        
        # Full bots (for complex operations)
        self.action_plan_bot_full = ActionPlanBot(api_key=self.api_key, model=self.complex_model)
        self.chart_bot_full = ChartBot(api_key=self.api_key, model=self.complex_model)
        
        logger.info(f"🤖 LLMAgent initialized with hybrid model routing:")
        logger.info(f"   Default (simple): {self.default_model}")
        logger.info(f"   Complex: {self.complex_model}")
    
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
    
    def _is_complex_operation(self, user_prompt: str, available_columns: List[str] = None, 
                              sample_data: Optional[List[Dict]] = None) -> bool:
        """
        Hybrid complexity detection - determines if operation needs GPT-4o
        
        Uses two-stage approach:
        1. Fast keyword checks (80-90% of cases, no API call)
        2. LLM classification for ambiguous cases (10-20%, tiny cheap API call)
        
        This handles typos, variations, and different phrasings accurately.
        Runs BEFORE any heavy operations, so it's completely safe.
        
        Args:
            user_prompt: User's request
            available_columns: Available column names (optional, for future use)
            sample_data: Sample data (optional, for future use)
            
        Returns:
            True if complex operation (use gpt-4o), False if simple (use gpt-4o-mini)
        """
        if not user_prompt:
            return False
        
        prompt_lower = user_prompt.lower()
        
        # FAST PATH 1: Obviously simple operations (no API call needed)
        if self._quick_simple_check(prompt_lower):
            return False
        
        # FAST PATH 2: Obviously complex operations (no API call needed)
        if self._quick_complex_check(prompt_lower, sample_data):
            return True
        
        # SLOW PATH: Ambiguous cases - use LLM classification (tiny, cheap call)
        # Only ~10-20% of requests reach here
        return self._llm_classify_complexity(user_prompt)
    
    def _quick_simple_check(self, prompt_lower: str) -> bool:
        """
        Fast check for obviously simple operations
        
        Returns True if operation is definitely simple (single, straightforward task)
        """
        import re
        
        # Simple single-operation patterns (must not have "and", "then", etc.)
        simple_patterns = [
            r"^(delete|remove|drop)\s+column",  # "delete column A"
            r"^rename\s+column",  # "rename column Name"
            r"^add\s+column\s+\w+$",  # "add column Total" (single operation)
            r"^make\s+(bold|italic|color|header)",  # "make bold"
            r"^change\s+cell",  # "change cell A1"
            r"^clear\s+cell",  # "clear cell A1"
        ]
        
        # Check if matches simple pattern AND doesn't have multi-step indicators
        for pattern in simple_patterns:
            if re.match(pattern, prompt_lower):
                # Make sure it's not multi-step
                if not any(kw in prompt_lower for kw in [" and ", " then ", " also ", " after ", " next "]):
                    return True  # Definitely simple
        
        # Single operation keywords (only if no multi-step words)
        single_ops = ["delete column", "remove column", "rename column", "make bold", "make italic"]
        if any(op in prompt_lower for op in single_ops):
            if not any(kw in prompt_lower for kw in [" and ", " then ", " also ", " after ", " next "]):
                return True  # Definitely simple
        
        return False
    
    def _quick_complex_check(self, prompt_lower: str, sample_data: Optional[List[Dict]] = None) -> bool:
        """
        Fast check for obviously complex operations
        
        Returns True if operation is definitely complex (multi-step, complex formulas, etc.)
        """
        # Multi-step operations (most common complexity indicator)
        # Check for variations: "then", "thennn" (typo), "and then", "after that", etc.
        multi_step_patterns = [
            r"\s+and\s+then\s+",  # "add and then sort"
            r"\s+then\s+",  # "add then sort" (handles "thennn" too via fuzzy)
            r"\s+also\s+",  # "add also format"
            r"\s+after\s+that\s+",  # "add after that sort"
            r"\s+next\s+",  # "add next sort"
            r"\s+and\s+\w+\s+and\s+",  # "add and sort and format"
        ]
        
        import re
        for pattern in multi_step_patterns:
            if re.search(pattern, prompt_lower):
                return True  # Definitely complex
        
        # Complex formulas and functions (handles typos via case-insensitive)
        complex_formula_keywords = [
            "vlookup", "index match", "nested", "complex formula",
            "if and", "if or", "sumif", "countif", "sumifs", "countifs",
            "hlookup", "match", "index"
        ]
        if any(kw in prompt_lower for kw in complex_formula_keywords):
            return True
        
        # Advanced conditional formatting with multiple conditions
        if any(kw in prompt_lower for kw in ["multiple conditions", "and condition", "or condition"]):
            return True
        
        # Data analysis operations
        analysis_keywords = ["analyze", "find patterns", "identify", "detect", "correlation", "trend", "outlier"]
        if any(kw in prompt_lower for kw in analysis_keywords):
            return True
        
        # Count number of operations requested
        operation_keywords = [
            "add", "delete", "remove", "rename", "format", "highlight",
            "sort", "filter", "clean", "calculate", "formula", "chart"
        ]
        operation_count = sum(1 for keyword in operation_keywords if keyword in prompt_lower)
        
        # Multiple operations (3+) indicate complexity
        if operation_count >= 3:
            return True
        
        # Ambiguous column references in potentially large datasets
        ambiguous_refs = ["column with", "column containing", "find column", "which column"]
        if any(ref in prompt_lower for ref in ambiguous_refs):
            # Only mark as complex if we have a large dataset
            if sample_data and len(sample_data) > 100:
                return True
        
        return False
    
    def _llm_classify_complexity(self, user_prompt: str) -> bool:
        """
        LLM-based complexity classification for ambiguous cases
        
        Uses gpt-4o-mini for a tiny, cheap classification call (~50-100 tokens).
        Handles typos, variations, and different phrasings accurately.
        
        Args:
            user_prompt: User's request
            
        Returns:
            True if complex, False if simple
        """
        try:
            classification_prompt = f"""Classify this Excel operation request as SIMPLE or COMPLEX.

SIMPLE = Single operation, straightforward task
Examples: "delete column A", "rename column Name", "make header bold", "add column Total"

COMPLEX = Multiple operations, complex formulas, or requires reasoning
Examples: "add column and sort", "create vlookup formula", "add total then highlight values > 1000"

User request: "{user_prompt}"

Respond with only: SIMPLE or COMPLEX"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheapest model for classification
                messages=[
                    {"role": "system", "content": "You are a classifier. Respond with only SIMPLE or COMPLEX. Handle typos and variations."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=10  # Just need "SIMPLE" or "COMPLEX"
            )
            
            result = response.choices[0].message.content.strip().upper()
            is_complex = "COMPLEX" in result
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            logger.info(f"🔍 LLM complexity classification: '{user_prompt[:50]}...' → {result} ({tokens_used} tokens)")
            
            return is_complex
            
        except Exception as e:
            logger.warning(f"LLM complexity classification failed: {e}. Defaulting to simple (safe fallback).")
            # Fallback: if LLM fails, assume simple (safer for cost)
            return False
    
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
        Interpret user prompt and route to appropriate bot with hybrid model selection
        
        Routes to:
        - ChartBot: If chart/visualization request
        - ActionPlanBot: For all data operations
        
        Uses hybrid model routing:
        - gpt-4o-mini: For simple operations (default, cost-effective)
        - gpt-4o: For complex operations (better accuracy)
        """
        # Check if chart request
        is_chart = self._is_chart_request(user_prompt)
        
        # Detect complexity (ultra-lightweight, runs before any heavy operations)
        is_complex = self._is_complex_operation(user_prompt, available_columns, sample_data)
        
        if is_chart:
            # Route to ChartBot with appropriate model
            chart_bot = self.chart_bot_full if is_complex else self.chart_bot_mini
            model_used = self.complex_model if is_complex else self.default_model
            logger.info(f"📊 Routing to ChartBot ({model_used}) - Complex: {is_complex}")
            
            result = chart_bot.generate_chart_plan(
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
            # Route to ActionPlanBot with appropriate model
            action_bot = self.action_plan_bot_full if is_complex else self.action_plan_bot_mini
            model_used = self.complex_model if is_complex else self.default_model
            logger.info(f"🔄 Routing to ActionPlanBot ({model_used}) - Complex: {is_complex}")
            logger.info(f"📝 User prompt: {user_prompt}")
            
            result = action_bot.generate_action_plan(
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
                model=self.default_model,
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

