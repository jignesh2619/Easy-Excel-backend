"""
LLM Agent Service

Interprets user prompts and returns structured action plans using Google Gemini 2.5 Flash Lite.
The LLM does NOT modify data directly - it only returns action plans.
"""

import json
import os
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.prompts import get_prompt_with_context
from utils.knowledge_base import get_knowledge_base_summary, get_task_decision_guide
from services.feedback_learner import FeedbackLearner
from services.training_data_loader import TrainingDataLoader

load_dotenv()


class LLMAgent:
    """Handles LLM interpretation of user prompts using Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash-lite"):
        """
        Initialize LLM Agent with Google Gemini
        
        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model to use (default: gemini-2.5-flash-lite - Gemini 2.5 Flash-Lite)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        
        # Get model from environment or use default
        # Default: gemini-2.5-flash-lite (Gemini 2.5 Flash-Lite)
        # Can override with GEMINI_MODEL environment variable
        self.model = os.getenv("GEMINI_MODEL", model)
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        try:
            self.client = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent outputs
                    "top_p": 0.95,
                    "top_k": 64,
                }
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini model: {str(e)}")
        
        # Initialize feedback learner for continuous improvement
        try:
            self.feedback_learner = FeedbackLearner()
        except Exception as e:
            # If feedback learner fails to initialize, continue without it
            self.feedback_learner = None
        
        # Initialize training data loader for few-shot learning
        try:
            self.training_data_loader = TrainingDataLoader()
        except Exception as e:
            # If training data loader fails, continue without it
            self.training_data_loader = None
    
    def interpret_prompt(
        self, 
        user_prompt: str, 
        available_columns: List[str],
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Interpret user prompt and return structured action plan with token usage
        
        Args:
            user_prompt: Natural language user request
            available_columns: List of available column names in the data
            user_id: Optional user ID for feedback tracking
            
        Returns:
            Dictionary with:
            - action_plan: Structured action plan dictionary with:
              - task: Operation to perform
              - columns_needed: Required columns
              - chart_type: Type of chart if needed
              - steps: List of steps to execute
              - Additional fields based on operation type
            - tokens_used: Actual token count from Gemini API (prompt + response)
        """
        try:
            prompt = get_prompt_with_context(user_prompt, available_columns)
            
            # Get knowledge base summary for enhanced context
            kb_summary = get_knowledge_base_summary()
            
            # Get task decision suggestions (for validation, not enforcement)
            task_suggestions = get_task_decision_guide(user_prompt)
            
            # Get similar examples for few-shot learning
            similar_examples_text = ""
            all_examples = []
            
            # 1. Get examples from training datasets (GPT-generated)
            if self.training_data_loader:
                try:
                    training_examples = self.training_data_loader.get_examples_for_prompt(user_prompt, limit=3)
                    all_examples.extend(training_examples)
                except Exception as e:
                    pass
            
            # 2. Get similar successful examples from feedback (real user interactions)
            if self.feedback_learner:
                try:
                    feedback_examples = self.feedback_learner.get_similar_successful_examples(user_prompt, limit=2)
                    # Convert feedback format to match training format
                    for ex in feedback_examples:
                        all_examples.append({
                            "prompt": ex["prompt"],
                            "action_plan": ex["action_plan"]
                        })
                except Exception as e:
                    pass
            
            # Combine and format examples
            if all_examples:
                similar_examples_text = "\n\nFEW-SHOT LEARNING EXAMPLES (from training data and past executions):\n"
                for i, ex in enumerate(all_examples[:5], 1):  # Limit to 5 total examples
                    similar_examples_text += f"\nExample {i}:\n"
                    similar_examples_text += f"User: {ex['prompt']}\n"
                    similar_examples_text += f"Response: {json.dumps(ex['action_plan'], indent=2)}\n"
                    if ex.get('execution_instructions'):
                        similar_examples_text += f"Execution: {ex['execution_instructions']}\n"
            
            # Create full prompt with system instructions and knowledge base
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

{prompt}

Return your response as a valid JSON object with no additional formatting.
Include "operations" array with "execution_instructions" for each operation."""

            # Generate response using Gemini
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "top_k": 64,
                }
            )
            
            # Extract actual token usage from Gemini API response
            tokens_used = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                # Gemini API provides usage_metadata with token counts
                if hasattr(response.usage_metadata, 'prompt_token_count'):
                    prompt_tokens = response.usage_metadata.prompt_token_count or 0
                else:
                    prompt_tokens = 0
                
                if hasattr(response.usage_metadata, 'candidates_token_count'):
                    response_tokens = response.usage_metadata.candidates_token_count or 0
                elif hasattr(response.usage_metadata, 'total_token_count'):
                    # Some versions use total_token_count
                    total_tokens = response.usage_metadata.total_token_count or 0
                    response_tokens = total_tokens - prompt_tokens if total_tokens > prompt_tokens else 0
                else:
                    response_tokens = 0
                
                tokens_used = prompt_tokens + response_tokens
            
            # If usage_metadata is not available, estimate based on prompt length (fallback)
            if tokens_used == 0:
                # Rough estimate: ~4 characters per token, plus response tokens
                prompt_tokens_estimate = len(full_prompt) // 4
                response_tokens_estimate = len(response.text) // 4 if hasattr(response, 'text') and response.text else 0
                tokens_used = prompt_tokens_estimate + response_tokens_estimate
            
            # Extract text from response
            content = response.text.strip()
            
            # Clean up content if it has markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON response
            try:
                action_plan = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                if json_match:
                    action_plan = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            # Validate and normalize action plan
            normalized_plan = self._normalize_action_plan(action_plan)
            
            # Return both action plan and token usage
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

