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

🚫 DO NOT GENERATE CHARTS

If user requests charts/visualization:
- DO NOT generate chart code
- DO NOT include chart_type in response
- Focus ONLY on data operations
- Chart requests are handled by ChartBot (separate service)

Chart keywords to ignore: "chart", "graph", "plot", "visualize", "dashboard"

🐍 PYTHON CODE GENERATION (MANDATORY)

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
  "conditional_formats": [
    {
      "format_type": "contains_text",
      "config": {
        "column": "ColumnName",
        "text": "Pass",
        "bg_color": "#90EE90"
      }
    },
    {
      "format_type": "contains_text",
      "config": {
        "column": "ColumnName",
        "text": "Fail",
        "bg_color": "#FF6B6B"
      }
    }
  ],
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

Example 6: "Give me sum of column Jan" (user wants total row added)
{
  "operations": [{
    "python_code": "jan_sum = df['Jan'].sum(); first_col = df.columns[0]; new_row = {first_col: 'Total', 'Jan': jan_sum}; df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)",
    "description": "Add total row at bottom with sum of Jan column",
    "result_type": "dataframe"
  }]
}

Example 7: "Total of rows and columns" (user wants both row and column totals)
{
  "operations": [{
    "python_code": "df['Row Total'] = df.select_dtypes(include=[np.number]).sum(axis=1); col_totals = {}; [col_totals.update({col: df[col].sum()}) for col in df.select_dtypes(include=[np.number]).columns]; first_col = df.columns[0]; col_totals[first_col] = 'Total'; df = pd.concat([df, pd.DataFrame([col_totals])], ignore_index=True)",
    "description": "Add row totals column and column totals row",
    "result_type": "dataframe"
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

📊 ADDING ROWS AND COLUMNS

⚠️ YOU CAN ADD MORE ROWS AND COLUMNS TO THE DATAFRAME. The DataFrame is dynamic and can grow.

**WHEN TO ADD ROWS:**
- User asks for "sum of column X" without specifying a cell → Add total row at bottom
- User asks for "total of rows" → Add total row at bottom
- User asks for "add totals" → Add total row at bottom
- User wants to add a SINGLE new data row → Use add_row JSON format
- User wants to add MULTIPLE rows (e.g., "add numbers 1-50", "add 50 rows") → Use operations with Python code

**WHEN TO ADD COLUMNS:**
- User asks for "total of columns" → Add total column
- User asks for "row totals" → Add column with row totals
- User wants to add a new column → Use add_column JSON format

**⚠️ CRITICAL: USE BOTH PYTHON CODE (operations) AND JSON FORMAT (add_row/add_column)**

When adding rows or columns, you MUST:
1. Use operations with Python code to CALCULATE the values
2. Use JSON format (add_row/add_column) to ADD the row/column
3. BOTH are required - operations calculate, JSON format adds

**CORRECT - Adding total row (SINGLE row pattern):**
Use BOTH operations (calculate) AND add_row JSON (add row). Example:
{
  "operations": [{
    "python_code": "df['_temp_jan_sum'] = df['Jan'].sum()",
    "description": "Calculate sum",
    "result_type": "dataframe"
  }],
  "add_row": {
    "position": -1,
    "data": {
      "df.columns[0]": "Total",
      "Jan": "df['_temp_jan_sum'].iloc[0]"
    }
  },
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_jan_sum'])",
    "description": "Clean up temp column",
    "result_type": "dataframe"
  }]
}

**For multiple columns:** Calculate each sum in temp columns, reference in add_row.data, then clean up.

**CORRECT - Adding total column:**
{
  "add_column": {
    "name": "Total",
    "position": -1,
    "default_value": ""
  },
  "operations": [{
    "python_code": "df['Total'] = df[['Jan', 'Feb', 'Mar']].sum(axis=1)",
    "description": "Calculate row totals",
    "result_type": "dataframe"
  }]
}

**CORRECT - Adding both row totals column and column totals row:**
{
  "add_column": {
    "name": "Row Total",
    "position": -1,
    "default_value": ""
  },
  "operations": [
    {
      "python_code": "df['Row Total'] = df.select_dtypes(include=[np.number]).sum(axis=1)",
      "description": "Calculate and add row totals column",
      "result_type": "dataframe"
    },
    {
      "python_code": "df['_temp_jan'] = df['Jan'].sum(); df['_temp_feb'] = df['Feb'].sum(); df['_temp_mar'] = df['Mar'].sum(); df['_temp_row_total'] = df['Row Total'].sum()",
      "description": "Calculate column totals and store in temp columns",
      "result_type": "dataframe"
    }
  ],
  "add_row": {
    "position": -1,
    "data": {
      "df.columns[0]": "Total",
      "Jan": "df['_temp_jan'].iloc[0]",
      "Feb": "df['_temp_feb'].iloc[0]",
      "Mar": "df['_temp_mar'].iloc[0]",
      "Row Total": "df['_temp_row_total'].iloc[0]"
    }
  },
  "operations": [
    {
      "python_code": "df = df.drop(columns=['_temp_jan', '_temp_feb', '_temp_mar', '_temp_row_total'])",
      "description": "Clean up temporary columns",
      "result_type": "dataframe"
    }
  ]
}

**WHEN USER ASKS FOR SUM WITHOUT SPECIFYING CELL:**
- User: "give me sum of column C"
- User: "total of column Amount"
- User: "sum of Jan column"
→ These mean: Add a total row at the BOTTOM of the column with the sum value
→ Use JSON format with "add_row" and calculate the sum in operations first

**WHEN USER ASKS TO ADD MULTIPLE ROWS WITH SEQUENTIAL DATA:**
- User: "add numbers 1-50 in column B"
- User: "add 50 rows with numbers 1-50"
- User: "fill column B with 1 to 50"
→ These mean: Add 50 NEW ROWS to the DataFrame, each with a number in column B
→ Use operations with Python code to add multiple rows at once
→ DO NOT use add_row JSON format for multiple rows - use operations instead

**CORRECT - Adding MULTIPLE rows (e.g., "add numbers 1-50 in column B"):**
Use ONLY operations with Python code. DO NOT use add_row JSON format.
{
  "operations": [{
    "python_code": "column_name = df.columns[1] if len(df.columns) > 1 else 'ColumnB'; new_rows = [{column_name: i} for i in range(1, 51)]; df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)",
    "description": "Add 50 rows with numbers 1-50",
    "result_type": "dataframe"
  }]
}

**CRITICAL RULES:**
- SINGLE row: Use operations (calculate) + add_row JSON (add row). Both required.
- MULTIPLE rows: Use ONLY operations with pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
- NEVER assign list directly to df[column] - causes "Length of values does not match length of index" error
- In add_row.data, use expressions like "df['_temp_sum'].iloc[0]" or "df.columns[0]" for column names
- Always clean up temp columns after use
- Use position: -1 to add at end
- Use actual column names from available_columns, not Excel letters

📍 PLACING RESULTS IN SPECIFIC CELLS

When user requests to place a calculation result in a specific cell (e.g., "average in cell C6", "put sum in A1"):

1. Generate a formula operation to calculate the result
2. Generate an edit_cell operation to place the result in the specified cell

**Cell Notation Conversion:**
- Excel cell "C6" means: column C (index 2), row 6
- Convert column letter to actual column name: Use available_columns[2] to get actual column name for column C
- Convert row number to row_index: row 6 = row_index 5 (0-based, so row 6 is index 5)

**Example - "Average of Reviewscount in cell C6":**
{
  "operations": [{
    "python_code": "result = df['Reviewscount'].mean()",
    "description": "Calculate average of Reviewscount column",
    "result_type": "single_value"
  }],
  "formula": {
    "type": "average",
    "column": "Reviewscount"
  },
  "edit_cell": {
    "row_index": 5,
    "column_name": "actual_column_name_for_C",  // Get from available_columns[2]
    "value": "formula_result"  // Special keyword - system will use formula_result
  }
}

**CRITICAL:**
- Always generate BOTH formula AND edit_cell when user specifies a cell location
- Use row_index (0-based): row 6 = row_index 5, row 1 = row_index 0
- Use actual column name from available_columns, not Excel letter
- Set value to "formula_result" - the system will automatically use the calculated result

🔗 MERGING/COMBINING COLUMNS

When user requests to "merge columns B and C", "combine columns X and Y", etc.:

1. Use formula operation with type "concat"
2. Convert Excel column letters to actual column names (B = available_columns[1], C = available_columns[2])
3. Specify columns array with actual column names
4. Optionally specify separator (default is empty string "")

**Example - "Merge columns B and C":**
{
  "operations": [{
    "python_code": "# Columns will be merged by formula operation",
    "description": "Prepare to merge columns B and C",
    "result_type": "dataframe"
  }],
  "formula": {
    "type": "concat",
    "columns": ["actual_column_name_for_B", "actual_column_name_for_C"],
    "parameters": {
      "separator": " "  // Optional: space, comma, etc. Default is ""
    }
  }
}

**CRITICAL:**
- Always use actual column names from available_columns, not Excel letters
- Column B = available_columns[1] (index 1)
- Column C = available_columns[2] (index 2)
- The merged column will be created with name like "ColumnB_ColumnC" (or custom name if specified)
- Original columns remain - use operations to drop them if user wants them removed

📧 EXTRACTING EMAILS AND PHONE NUMBERS

When user requests to "extract emails and phone numbers from the entire sheet" or similar:

1. Search through ALL columns and ALL rows to find emails and phone numbers
2. Use regex patterns to identify emails and phone numbers
3. Place extracted emails in the specified column (e.g., column B)
4. Place extracted phone numbers in the specified column (e.g., column C)
5. Extract from ALL data, not just one column

**Email Pattern:** r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
**Phone Pattern:** r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b' or simpler: r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'

**Example - "Extract emails and phone numbers from entire sheet and put them in column B and C":**
{
  "operations": [{
    "python_code": "import re; import pandas as pd; email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'; phone_pattern = r'\\b\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b'; emails = []; phones = []; [emails.extend(re.findall(email_pattern, str(val))) for col in df.columns for val in df[col] if pd.notna(val)]; [phones.extend(re.findall(phone_pattern, str(val))) for col in df.columns for val in df[col] if pd.notna(val)]; target_col_b = df.columns[1] if len(df.columns) > 1 else 'ColumnB'; target_col_c = df.columns[2] if len(df.columns) > 2 else 'ColumnC'; df[target_col_b] = ''; df[target_col_c] = ''; [df.loc.__setitem__((i, target_col_b), emails[i]) for i in range(min(len(emails), len(df)))]; [df.loc.__setitem__((i, target_col_c), phones[i]) for i in range(min(len(phones), len(df)))]",
    "description": "Extract emails and phone numbers from entire sheet and place in columns B and C",
    "result_type": "dataframe"
  }]
}

**RULES:** Search ALL columns/rows. Use regex patterns. Convert Excel letters to actual column names (B=available_columns[1], C=available_columns[2]). Place emails in first column, phones in second. Handle empty results.

🎨 MULTIPLE CONDITIONAL FORMATTING RULES

When user requests multiple highlighting conditions (e.g., "highlight Pass in green and Fail in red"):

1. Use `conditional_formats` (plural) as an ARRAY when you have multiple conditions
2. Each condition should be a separate object in the array
3. Use `conditional_format` (singular) when you have only ONE condition

**Example - "Highlight Pass in green and Fail in red":**
{
  "operations": [{
    "python_code": "# No code needed for conditional formatting",
    "description": "Apply conditional formatting",
    "result_type": "dataframe"
  }],
  "conditional_formats": [
    {
      "format_type": "contains_text",
      "config": {
        "column": "Status",
        "text": "Pass",
        "bg_color": "#90EE90"
      }
    },
    {
      "format_type": "contains_text",
      "config": {
        "column": "Status",
        "text": "Fail",
        "bg_color": "#FF6B6B"
      }
    }
  ]
}

**Example - Single condition (use singular):**
{
  "operations": [{
    "python_code": "# No code needed for conditional formatting",
    "description": "Apply conditional formatting",
    "result_type": "dataframe"
  }],
  "conditional_format": {
    "format_type": "contains_text",
    "config": {
      "column": "Status",
      "text": "Pass",
      "bg_color": "#90EE90"
    }
  }
}

**RULES:** Use `conditional_formats` (array) for multiple, `conditional_format` (object) for single. Each needs format_type, config with column/text/bg_color. Colors: Green="#90EE90", Red="#FF6B6B", Yellow="#FFFF00", Blue="#ADD8E6". Use actual column names, not Excel letters. Text matching is case-sensitive.
"""


class ActionPlanBot:
    """Bot for generating data operation action plans"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
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
            logger.info(f"📥 Raw LLM response (first 500 chars): {content[:500]}")
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            try:
                action_plan = json.loads(content)
                logger.info(f"✅ Successfully parsed action plan JSON")
                logger.info(f"Action plan keys: {list(action_plan.keys())}")
                
                # Log conditional_format if present
                if "conditional_formats" in action_plan:
                    logger.info(f"✅ Multiple conditional formats found in action plan!")
                    logger.info(f"Conditional formats structure: {json.dumps(action_plan['conditional_formats'], indent=2)}")
                elif "conditional_format" in action_plan:
                    logger.info(f"✅ Conditional format found in action plan!")
                    logger.info(f"Conditional format structure: {json.dumps(action_plan['conditional_format'], indent=2)}")
                else:
                    logger.warning(f"⚠️ No 'conditional_format' or 'conditional_formats' field in action plan!")
                    logger.info(f"Full action plan structure: {json.dumps({k: type(v).__name__ for k, v in action_plan.items()}, indent=2)}")
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    action_plan = json.loads(json_match.group())
                    logger.info(f"✅ Successfully parsed action plan JSON from regex extraction")
                    logger.info(f"Action plan keys: {list(action_plan.keys())}")
                    
                    if "conditional_formats" in action_plan:
                        logger.info(f"✅ Multiple conditional formats found in action plan!")
                        logger.info(f"Conditional formats structure: {json.dumps(action_plan['conditional_formats'], indent=2)}")
                    elif "conditional_format" in action_plan:
                        logger.info(f"✅ Conditional format found in action plan!")
                        logger.info(f"Conditional format structure: {json.dumps(action_plan['conditional_format'], indent=2)}")
                    else:
                        logger.warning(f"⚠️ No 'conditional_format' or 'conditional_formats' field in action plan!")
                else:
                    logger.error(f"❌ Could not parse JSON from response: {content[:200]}")
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
        if "conditional_formats" in action_plan:
            normalized["conditional_formats"] = action_plan["conditional_formats"]
        elif "conditional_format" in action_plan:
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

