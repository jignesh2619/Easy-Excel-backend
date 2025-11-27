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

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.prompts import get_prompt_with_context
from utils.knowledge_base import get_knowledge_base_summary, get_task_decision_guide
from services.feedback_learner import FeedbackLearner
from services.training_data_loader import TrainingDataLoader
from services.conditional_format_interpreter import ConditionalFormattingInterpreter

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = (
    "You are EasyExcel AI, an expert spreadsheet automation assistant. "
    "Respond with ONLY valid JSON that our backend can execute directly. "
    "Never include markdown, explanations, or extra text."
)


class LLMAgent:
    """Handles LLM interpretation of user prompts using OpenAI GPT-4.1"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-1"):
        """
        Initialize LLM Agent with OpenAI GPT-4.1
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4-1)
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
        
        self.conditional_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "conditional_formatting_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "conditional_formatting": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "apply_to": {"type": "string"},
                                    "condition_type": {"type": "string", "enum": ["contains", "equals", "regex"]},
                                    "condition_value": {"type": "string"},
                                    "format": {
                                        "type": "object",
                                        "properties": {
                                            "background_color": {"type": "string"},
                                            "font_color": {"type": "string"},
                                            "bold": {"type": "boolean"}
                                        },
                                        "required": ["background_color", "font_color", "bold"]
                                    }
                                },
                                "required": ["apply_to", "condition_type", "condition_value", "format"]
                            }
                        }
                    },
                    "required": ["conditional_formatting"]
                }
            }
        }
        self.conditional_helper = ConditionalFormattingInterpreter(
            client=self.client,
            model=self.model,
            schema=self.conditional_schema,
        )
    
    def interpret_prompt(
        self, 
        user_prompt: str, 
        available_columns: List[str],
        user_id: Optional[str] = None,
        sample_data: Optional[List[Dict]] = None,
        sample_explanation: Optional[str] = None
    ) -> Dict:
        """
        Interpret user prompt and return structured action plan with token usage
        """
        try:
            # Dedicated path for conditional-formatting prompts
            if self.conditional_helper.should_handle_prompt(user_prompt):
                helper_payload, helper_tokens = self.conditional_helper.interpret(
                    user_prompt, available_columns
                )
                helper_plan = self._convert_conditional_schema_to_action_plan(
                    helper_payload, available_columns
                )
                helper_plan["user_prompt"] = user_prompt
                return {"action_plan": helper_plan, "tokens_used": helper_tokens}

            general_prompt = get_prompt_with_context(user_prompt, available_columns, sample_data)
            
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

{general_prompt}

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
        
        if "conditional_format_rules" in action_plan:
            normalized["conditional_format_rules"] = action_plan["conditional_format_rules"]
        
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

    def _convert_conditional_schema_to_action_plan(
        self, helper_payload: Dict, available_columns: List[str]
    ) -> Dict:
        """Map helper JSON back into the action plan structure ExcelProcessor expects."""
        rules = []
        requested_rules = helper_payload.get("conditional_formatting", [])
        column_lookup = {col.lower(): col for col in available_columns}

        for entry in requested_rules:
            if not isinstance(entry, dict):
                continue

            apply_to = entry.get("apply_to", "all_columns") or "all_columns"
            if apply_to.lower() != "all_columns":
                normalized_col = column_lookup.get(apply_to.lower())
                if normalized_col:
                    apply_to = normalized_col
                else:
                    apply_to = "all_columns"

            condition_type = entry.get("condition_type", "contains")
            condition_value = entry.get("condition_value", "")
            fmt = entry.get("format", {})

            format_type_map = {
                "contains": "contains_text",
                "equals": "text_equals",
                "regex": "regex_match",
            }
            format_type = format_type_map.get(condition_type, "contains_text")

            rule = {
                "type": "conditional",
                "format_type": format_type,
                "config": {
                    "column": apply_to,
                    "text": condition_value,
                    "pattern": condition_value if format_type == "regex_match" else None,
                    "bg_color": fmt.get("background_color", "#FFF3CD"),
                    "text_color": fmt.get("font_color", "#000000"),
                    "bold": fmt.get("bold", False),
                    "condition_type": condition_type,
                    "condition_value": condition_value,
                },
            }
            # Remove None keys to keep config clean
            rule["config"] = {k: v for k, v in rule["config"].items() if v is not None}
            rules.append(rule)

        action_plan = {
            "task": "conditional_format",
            "columns_needed": [],
            "chart_type": "none",
            "steps": [],
            "conditional_format_rules": rules,
        }

        if rules:
            action_plan["conditional_format"] = rules[0]

        return action_plan
    
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

