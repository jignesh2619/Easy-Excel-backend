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
from services.extraction_pattern_analyzer import ExtractionPatternAnalyzer

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

⚠️ CRITICAL: CODE MUST BE VALID PYTHON - NO LINE BREAKS IN METHOD CHAINS ⚠️
- Method chains MUST be on ONE line: df.groupby(['A'])['B'].sum().reset_index()
- NEVER split method chains: df.groupby(['A'])\n['B'].sum() ❌ (INVALID)
- Use semicolons to separate statements on one line
- Only use newlines for for/if/elif/else blocks (with proper indentation)

**OUTPUT FORMAT (STRICT JSON - NO MARKDOWN):**

{
  "operations": [
    {
      "python_code": "df = df.drop_duplicates().reset_index(drop=True)",
      "description": "Remove duplicate rows",
      "result_type": "dataframe"
    }
  ],
  "conditional_format": [
    {
      "format_type": "text_equals",
      "config": {
        "column": "ColumnName",
        "text": "HR",
        "bg_color": "#FF0000"
      }
    },
    {
      "format_type": "text_equals",
      "config": {
        "column": "ColumnName",
        "text": "IT",
        "bg_color": "#FFFF00"
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

⚠️ CRITICAL: INTERPRET USER REQUESTS CAREFULLY ⚠️
- Pay close attention to ALL words in the user's request - every word matters
- "new column" means HORIZONTAL combination (axis=1) - adds columns side by side
- "stack" or "stacked" without "new column" usually means VERTICAL combination (axis=0) - adds rows
- "give them in new column" / "put in new columns" → horizontal (axis=1)
- "combine vertically" / "stack vertically" → vertical (axis=0)
- "merge side by side" → horizontal (axis=1)
- If user says BOTH "stack" AND "new column", prioritize "new column" (horizontal)
- Always verify your interpretation matches what the user actually requested

⚠️ CRITICAL: SAMPLE vs FULL DATASET (APPLIES TO ALL OPERATIONS) ⚠️
- You receive a SAMPLE of rows (shown in the prompt) but the code executes on the FULL dataset (total rows shown in prompt)
- The prompt will tell you: "SAMPLE of X rows from a TOTAL of Y rows" - your code must work on ALL Y rows
- This applies to ALL operations: grouping, filtering, sorting, cleaning, formulas, calculations, aggregations, etc.
- When grouping by categories (Month, Item, etc.), there may be MORE rows with that category in the full dataset
- When filtering by conditions, there may be MORE matching rows in the full dataset than shown in the sample
- When calculating totals/sums/averages, they must include ALL rows in the full dataset, not just the sample
- Your code MUST work on ALL rows in the full dataset, not just the sample shown
- Always use DataFrame operations (df.groupby, df.filter, df.sort_values, df.apply, df.sum, df.mean, etc.) that process the entire dataset automatically
- DO NOT assume the sample shows all unique values, all matching rows, or complete data - there may be many more in the full dataset
- The number of rows can be ANY number (23, 50, 100, 1000, etc.) - your code must handle all of them

**CRITICAL - CODE FORMATTING RULES (MUST FOLLOW):**
6. KEEP METHOD CHAINS ON SINGLE LINE - Never split method calls across lines
   - WRONG: "df.groupby(['A'])\n['B'].sum()" (invalid - method chain split)
   - CORRECT: "df.groupby(['A'])['B'].sum()" (all on one line)
   - CORRECT: "grouped = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index()"
   
7. FOR LOOPS - Must be on separate lines with proper indentation
   - WRONG: "statement1; for col in cols: statement2" (invalid syntax)
   - CORRECT: "statement1\nfor col in cols:\n    statement2"
   - If you need multiple statements, use semicolons for simple statements, but for loops need separate lines

8. MULTIPLE STATEMENTS - Use semicolons to separate simple statements on one line
   - CORRECT: "df = df.dropna(); df = df.reset_index(drop=True)"
   - CORRECT: "grouped = df.groupby(['A'])['B'].sum(); df = grouped.reset_index()"

**CRITICAL - PRESERVE ALL COLUMNS:**
⚠️ DO NOT drop or remove columns unless the user EXPLICITLY asks to remove them.
- Preserve ALL columns from the original file, even if they are empty (all NaN)
- Only drop columns if user explicitly says "remove column X", "delete column Y", "drop empty columns", etc.
- DO NOT automatically drop empty columns during general cleaning operations
- Empty columns may be needed for data structure or future data entry

**CRITICAL - DO NOT AUTO-FILL EMPTY VALUES:**
⚠️ DO NOT automatically fill empty cells with 0 or empty strings unless user EXPLICITLY requests it.
- Empty cells should remain empty (NaN) unless user says "fill missing values", "fill empty cells", etc.
- DO NOT add operations like "fillna(0)" or "fillna('')" unless user explicitly asks for it
- Preserve the original data structure - empty means empty, not 0 or blank string

**CRITICAL - CONDITIONAL FORMATTING (HIGHLIGHT CELLS):**
⚠️ DO NOT create temporary columns for conditional formatting - conditional formatting ONLY applies visual formatting, it does NOT modify data.
- Conditional formatting does NOT require Python operations - ONLY return conditional_format JSON
- For multiple formats (e.g., "highlight HR red and IT yellow"), use conditional_format as an ARRAY with multiple entries
- DO NOT add columns like "_hr_contains_hr_" or any temporary flag columns for conditional formatting
- Example: "Highlight cells HR with Red and IT with yellow" → Return conditional_format array with two entries (HR=red, IT=yellow), NO operations

**AVAILABLE IN EXECUTION CONTEXT:**
- df: Current pandas DataFrame
- pd: Pandas library
- np: NumPy library
- DateCleaner, TextCleaner, CurrencyCleaner: Cleaning utilities (use static methods)
- datetime: Date/time functions
- Basic functions: abs, round, min, max, sum, str, len, list, range

**PHONE NUMBER FORMATTING (CRITICAL - MUST USE TextCleaner.format_phone_numbers):**
When user requests phone number formatting (e.g., "format phone numbers to (XXX) XXX-XXXX", "standardize phone numbers", "format phone numbers"):
- ALWAYS use TextCleaner.format_phone_numbers() method - This is the ONLY correct way
- CORRECT: df = TextCleaner.format_phone_numbers(df, 'Phone Number')
- CORRECT: df = TextCleaner.format_phone_numbers(df, ['Phone', 'Mobile', 'Phone Number'])
- CORRECT: df = TextCleaner.format_phone_numbers(df, 'Phone')  # Use actual column name from dataset
- This method automatically handles ALL formats: 555-123-4567, 555.123.4567, (555) 123-4567, +1-555-123-4567, +15554445566, 5551234567, 555 123 4567, etc.
- DO NOT write custom code with str.replace() or regex for phone formatting
- DO NOT use apply() with lambda for phone formatting
- DO NOT assign to 're' variable (causes scoping errors)
- The method extracts digits and formats to (XXX) XXX-XXXX automatically

**HOW TO USE CLEANING UTILITIES (CRITICAL - USE STATIC METHODS):**

TextCleaner - Use static methods, returns modified DataFrame:
- CORRECT: df = TextCleaner.trim_whitespace(df, 'ColumnName')
- CORRECT: df = TextCleaner.trim_whitespace(df, ['Col1', 'Col2'])  # Multiple columns
- CORRECT: df = TextCleaner.normalize_case(df, 'ColumnName', case='lower')
- CORRECT: df = TextCleaner.remove_special_characters(df, 'ColumnName')
- CORRECT: df = TextCleaner.format_phone_numbers(df, 'Phone Number')  # Format to (XXX) XXX-XXXX
- CORRECT: df = TextCleaner.format_phone_numbers(df, ['Phone', 'Mobile'])  # Multiple columns

**TEXT SPLITTING (CRITICAL - USE TextCleaner.split_column OR pandas str.split):**
When user requests to split text from one column into multiple columns (e.g., "split column A into D and E", "split text of col a and fill in D and e"):
- ALWAYS use TextCleaner.split_column() method OR pandas str.split() - DO NOT use re module
- CORRECT: df = TextCleaner.split_column(df, 'ColumnA', ' ', ['ColumnD', 'ColumnE'])
- CORRECT: df[['D', 'E']] = df['A'].astype(str).str.split(' ', n=1, expand=True)  # Split on space into 2 columns
- CORRECT: split_cols = df['A'].astype(str).str.split(' ', expand=True); df['D'] = split_cols[0]; df['E'] = split_cols[1]
- DO NOT use re.split() or re module for text splitting - use str.split() instead
- DO NOT assign to 're' variable anywhere in the code
- If separator is not specified, assume space ' ' as default separator

- WRONG: df['ColumnName'] = TextCleaner(df['ColumnName'])  # DON'T DO THIS
- WRONG: for c in cols: df[c] = TextCleaner(df[c])  # DON'T DO THIS

DateCleaner - Use static methods, returns modified DataFrame:
- CORRECT: df = DateCleaner.parse_dates(df, 'DateColumn')
- CORRECT: df = DateCleaner.normalize_dates(df, 'DateColumn', target_format='%m/%d/%Y')  # For MM/DD/YYYY format
- CORRECT: df = DateCleaner.normalize_dates(df, 'DateColumn', target_format='%Y-%m-%d')  # For YYYY-MM-DD format

CurrencyCleaner - Use static methods, returns modified DataFrame:
- CORRECT: df = CurrencyCleaner.extract_numeric(df, 'PriceColumn')

**RESULT TYPES:**
- "dataframe": Operation modifies dataframe (filter, sort, clean, etc.)
- "single_value": Operation returns single value (SUM, AVERAGE, COUNT)
- "new_column": Operation creates new column (IF, calculations per row)

**EXAMPLES:**

Example 1: "Clean text columns" or "Clean all text data"
{
  "operations": [{
    "python_code": "text_cols = df.select_dtypes(include=['object']).columns.tolist(); df = TextCleaner.trim_whitespace(df, text_cols); df = TextCleaner.normalize_case(df, text_cols, case='lower')",
    "description": "Clean all text columns: trim whitespace and normalize to lowercase",
    "result_type": "dataframe"
  }]
}

Example 1b: "Format phone numbers to (XXX) XXX-XXXX" or "standardize phone numbers"
{
  "operations": [{
    "python_code": "phone_cols = [col for col in df.columns if 'phone' in col.lower() or 'mobile' in col.lower() or 'contact' in col.lower()]; df = TextCleaner.format_phone_numbers(df, phone_cols[0]) if phone_cols else TextCleaner.format_phone_numbers(df, df.columns[1] if len(df.columns) > 1 else df.columns[0])",
    "description": "Format phone numbers to (XXX) XXX-XXXX format",
    "result_type": "dataframe"
  }]
}

Example 1c: "split text of col a and fill in D and e" or "split column A into D and E"
{
  "operations": [{
    "python_code": "split_data = df[df.columns[0]].astype(str).str.split(' ', n=1, expand=True); df['D'] = split_data[0]; df['E'] = split_data[1] if len(split_data.columns) > 1 else ''",
    "description": "Split first column by space into columns D and E using pandas str.split()",
    "result_type": "dataframe"
  }]
}
Note: For text splitting, ALWAYS use pandas str.split() method (e.g., df['Col'].astype(str).str.split(' ', expand=True)) - NEVER use re.split() or re module. DO NOT assign to 're' variable.

Example 1d: "Convert all dates to MM/DD/YYYY format" or "format dates in column B to MM/DD/YYYY"
{
  "operations": [{
    "python_code": "date_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]; df = DateCleaner.normalize_dates(df, date_col, target_format='%m/%d/%Y')",
    "description": "Convert all dates in Date column to MM/DD/YYYY format",
    "result_type": "dataframe"
  }]
}
Note: For date formatting, ALWAYS use DateCleaner.normalize_dates() with target_format parameter. Use '%m/%d/%Y' for MM/DD/YYYY, '%Y-%m-%d' for YYYY-MM-DD, etc. The method handles all date formats automatically and preserves original values if parsing fails.

Example 1e: "extract emails from column B and fill in new columns" or "extract email addresses from Notes column"
{
  "add_column": {
    "name": "Email",
    "position": -1,
    "default_value": ""
  },
  "operations": [{
    "python_code": "notes_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]; df['Email'] = df[notes_col].astype(str).str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})', expand=False)",
    "description": "Extract first email address from Notes column using regex with capture group",
    "result_type": "dataframe"
  }]
}
⚠️ CRITICAL: str.extract() REQUIRES capture groups (parentheses) in the regex pattern ⚠️
- WRONG: df['Email'] = df['Notes'].str.extract(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}') ❌ (no capture group - will fail with "pattern contains no capture groups")
- CORRECT: df['Email'] = df['Notes'].astype(str).str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})', expand=False) ✓ (has capture group)
- The pattern MUST be wrapped in parentheses: r'(PATTERN)' not r'PATTERN'
- Use expand=False to get a Series directly (no need for [0])
- Always use .astype(str) before str.extract() to handle NaN/None values
- If cell has multiple emails, str.extract() returns the FIRST match (this is correct behavior)
- If cell has no email, result will be NaN (this is acceptable)

**CORRECT way to clean text columns:**
- Get text columns: text_cols = df.select_dtypes(include=['object']).columns.tolist()
- Clean them: df = TextCleaner.trim_whitespace(df, text_cols)
- Always assign back to df: df = TextCleaner.method(df, columns)

**WRONG way (DO NOT DO THIS):**
- WRONG: for c in text_cols: df[c] = TextCleaner(df[c])
- WRONG: df[c] = TextCleaner.trim_whitespace(df[c])
- TextCleaner methods return the ENTIRE DataFrame, not just the column

Example 2: "Remove duplicates"
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

Example 4: "If revenue > 1000, mark as High" (single column condition)
{
  "operations": [{
    "python_code": "df['Status'] = df['Revenue'].apply(lambda x: 'High' if x > 1000 else 'Low')",
    "description": "Mark status based on revenue",
    "result_type": "new_column"
  }]
}

Example 4b: "Fill column based on multiple column conditions" (GENERAL PATTERN)
{
  "operations": [{
    "python_code": "df['Result'] = df.apply(lambda row: 'Value1' if (condition_on_col1) or (condition_on_col2) else 'Value2', axis=1)",
    "description": "Fill column based on multiple column conditions",
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

Example 6: "Group similar items in columns E, F, G" (preserve original data, add grouped results to new columns)
{
  "operations": [{
    "python_code": "grouped = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index(); grouped.columns = ['Item.1', 'Size.1', 'Quantity.1']; original_len = len(df); grouped_len = len(grouped); if grouped_len < original_len: empty_data = {col: [None] * (original_len - grouped_len) for col in grouped.columns}; empty_df = pd.DataFrame(empty_data); grouped = pd.concat([grouped, empty_df], ignore_index=True); df = pd.concat([df, grouped], axis=1)",
    "description": "Group by Item and Size, sum quantities, add results to new columns preserving original rows",
    "result_type": "dataframe"
  }]
}

Example 6b: "Group similar items in columns E, F, G" (alternative: add grouped results as new rows at bottom)
{
  "operations": [{
    "python_code": "grouped = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index(); grouped.columns = ['Item.1', 'Size.1', 'Quantity.1']; original_cols = df.columns.tolist(); missing_cols = [col for col in original_cols if col not in grouped.columns]; for col in missing_cols: grouped[col] = None; grouped = grouped.reindex(columns=original_cols + ['Item.1', 'Size.1', 'Quantity.1']); df = pd.concat([df, grouped], ignore_index=True)",
    "description": "Group by Item and Size, add grouped results as new rows at bottom with original columns",
    "result_type": "dataframe"
  }]
}

Example 7: "Group similar items" (if user wants to replace data with grouped results only)
{
  "operations": [{
    "python_code": "df = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index()",
    "description": "Group by Item and Size, sum quantities for each group",
    "result_type": "dataframe"
  }]
}

Example 8: "Highlight cells HR with Red and IT with yellow" (multiple conditional formats - NO operations, NO temporary columns)
{
  "operations": [],
  "conditional_format": [
    {
      "format_type": "text_equals",
      "config": {
        "column": "Title",
        "text": "HR",
        "bg_color": "#FF0000"
      }
    },
    {
      "format_type": "text_equals",
      "config": {
        "column": "Title",
        "text": "IT",
        "bg_color": "#FFFF00"
      }
    }
  ]
}

CRITICAL FOR CONDITIONAL FORMATTING:
- Conditional formatting is VISUAL ONLY - it does NOT modify the dataframe
- DO NOT create temporary columns (like "_hr_contains_hr_") for conditional formatting
- DO NOT add Python operations to create flag columns
- ONLY return conditional_format JSON (as single object or array for multiple formats)
- The system automatically detects matching cells and applies formatting - no columns needed

**IMPORTANT - GROUPING SIMILAR ROWS:**
When user says "group similar items", "total quantity of each product", "combine duplicate rows", "group data of similar ones", etc.:

CRITICAL FORMATTING: Keep ALL method chains on ONE LINE - never split across lines
- WRONG: "grouped = df.groupby(['Item', 'Size'])\n['Quantity'].sum()" (INVALID - method chain split)
- CORRECT: "grouped = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index()" (all on one line)

CRITICAL: Check if user specifies target columns (e.g., "in E, F, G", "in columns E F G"):
- If YES: PRESERVE original data and ADD grouped results
  - Option 1: Add as new columns (pad with None to match row count)
    - CORRECT FORMAT: "grouped = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index(); grouped.columns = ['Item.1', 'Size.1', 'Quantity.1']; original_len = len(df); grouped_len = len(grouped); empty_rows = pd.DataFrame({col: [None] * (original_len - grouped_len) for col in grouped.columns}) if grouped_len < original_len else pd.DataFrame(); grouped = pd.concat([grouped, empty_rows], ignore_index=True) if len(empty_rows) > 0 else grouped; df = pd.concat([df, grouped], axis=1)"
  
  - Option 2: Add as new rows at bottom (preserve all original rows, append grouped summary)
    - CORRECT FORMAT: "grouped = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index(); grouped.columns = ['Item.1', 'Size.1', 'Quantity.1']; original_cols = df.columns.tolist(); missing_cols = [col for col in original_cols if col not in grouped.columns]; for col in missing_cols: grouped[col] = None; df = pd.concat([df, grouped], ignore_index=True)"
  
  - DEFAULT: Use Option 2 (add as new rows) to preserve all original data clearly

- If NO target columns specified: User wants to REPLACE data with grouped results only
  - CORRECT FORMAT: "df = df.groupby(['Item', 'Size'])['Quantity'].sum().reset_index()"
  - This creates a new dataframe with only grouped results

KEY RULE: When user says "group in column X, Y, Z", ALWAYS preserve ALL original rows and columns, then add grouped results.

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

═══════════════════════════════════════════════════════════════════════════════
📊 ADDING ROWS AND COLUMNS - CRITICAL INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════════════

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

**CORRECT - Adding total row using BOTH operations AND JSON format:**

Pattern: 
1. Use operations with Python code to CALCULATE values
2. Use add_row JSON format to ADD the row
3. BOTH are required - don't skip operations!

Example - Adding total row for Jan column:
{
  "operations": [{
    "python_code": "df['_temp_jan_sum'] = df['Jan'].sum()",
    "description": "Calculate sum of Jan column and store in temp column",
    "result_type": "dataframe"
  }],
  "add_row": {
    "position": -1,
    "data": {
      "Jan": "df['_temp_jan_sum'].iloc[0]"
    }
  },
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_jan_sum'])",
    "description": "Remove temporary column",
    "result_type": "dataframe"
  }]
}

**CRITICAL:** 
- You MUST include operations with Python code to calculate values
- You MUST include add_row/add_column JSON format to add the row/column
- In add_row.data, use string expressions like "df['ColumnName'].iloc[0]" to reference calculated values
- The system evaluates these expressions safely

**CORRECT - Adding total row with label in first column:**
{
  "operations": [{
    "python_code": "df['_temp_first_col'] = df.columns[0]; df['_temp_jan_sum'] = df['Jan'].sum()",
    "description": "Store first column name and calculate Jan sum",
    "result_type": "dataframe"
  }],
  "add_row": {
    "position": -1,
    "data": {
      "df['_temp_first_col'].iloc[0]": "Total",
      "Jan": "df['_temp_jan_sum'].iloc[0]"
    }
  },
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_first_col', '_temp_jan_sum'])",
    "description": "Clean up temporary columns",
    "result_type": "dataframe"
  }]
}

**BETTER - Adding total row with label (simpler approach):**
{
  "operations": [{
    "python_code": "df['_temp_jan_sum'] = df['Jan'].sum()",
    "description": "Calculate Jan sum",
    "result_type": "dataframe"
  }],
  "add_row": {
    "position": -1,
    "data": {
      df.columns[0]: "Total",
      "Jan": "df['_temp_jan_sum'].iloc[0]"
    }
  },
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_jan_sum'])",
    "description": "Clean up temporary column",
    "result_type": "dataframe"
  }]
}

**CORRECT - Adding total row for multiple columns:**
{
  "operations": [{
    "python_code": "df['_temp_jan'] = df['Jan'].sum(); df['_temp_feb'] = df['Feb'].sum(); df['_temp_mar'] = df['Mar'].sum()",
    "description": "Calculate sums for multiple columns",
    "result_type": "dataframe"
  }],
  "add_row": {
    "position": -1,
    "data": {
      "Jan": "df['_temp_jan'].iloc[0]",
      "Feb": "df['_temp_feb'].iloc[0]",
      "Mar": "df['_temp_mar'].iloc[0]"
    }
  },
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_jan', '_temp_feb', '_temp_mar'])",
    "description": "Clean up temporary columns",
    "result_type": "dataframe"
  }]
}

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

**WHEN USER ASKS TO FILL A COLUMN WITH SEQUENTIAL NUMBERS:**
- User: "fill col A with 1-50 numbers"
- User: "fill column B with numbers 1 to 50"
- User: "fill empty cells in column A with 1-50"
→ These mean: Fill the column with sequential numbers (1, 2, 3, ..., up to the requested number)
→ If the DataFrame has fewer rows than needed, AUTOMATICALLY ADD ROWS first
→ Then fill the column with sequential numbers starting from 1

**CORRECT - Filling column with sequential numbers (e.g., fill column A with 1-50, auto-add rows if needed):**
{
  "operations": [{
    "python_code": "target_count = 50\ncurrent_rows = len(df)\nif current_rows < target_count:\n    new_rows = [{} for _ in range(target_count - current_rows)]\n    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)\ndf['A'] = list(range(1, target_count + 1))",
    "description": "Fill column A with numbers 1 to 50, adding rows if needed",
    "result_type": "dataframe"
  }]
}

**IMPORTANT - When user specifies a range like "1-50":**
- Extract the maximum number (50 in this case) - this is the target_count
- Always check if current_rows < target_count
- If yes, automatically add (target_count - current_rows) new empty rows
- Then fill the column with numbers from 1 to target_count

**ALTERNATIVE - If you want to fill only empty cells (when there are enough rows):**
- Only use this approach if the user explicitly says "fill empty cells" AND there are already enough rows
- Otherwise, use the approach above to auto-add rows

**WHEN USER ASKS TO ADD MULTIPLE NEW ROWS WITH SEQUENTIAL DATA:**
- User: "add numbers 1-50 in column B" (when column is already full)
- User: "add 50 rows with numbers 1-50"
- User: "append 50 rows with numbers 1-50"
→ These mean: Add 50 NEW ROWS to the DataFrame, each with a number in column B
→ Use operations with Python code to add multiple rows at once
→ DO NOT use add_row JSON format for multiple rows - use operations instead

**CORRECT - Adding multiple rows with sequential data (e.g., add 50 new rows with numbers 1-50 in column B):**
{
  "operations": [{
    "python_code": "new_rows = [{'B': i} for i in range(1, 51)]; df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)",
    "description": "Add 50 new rows with numbers 1-50 in column B",
    "result_type": "dataframe"
  }]
}

**CORRECT - Adding multiple rows with data in specific column:**
If column name is "Id" or "ColumnB" or similar:
{
  "operations": [{
    "python_code": "column_name = 'Id'; new_rows = [{column_name: i} for i in range(1, 51)]; df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)",
    "description": "Add 50 new rows with numbers 1-50 in specified column",
    "result_type": "dataframe"
  }]
}

**CRITICAL RULES FOR ADDING MULTIPLE ROWS:**
1. When adding MULTIPLE rows (more than 1), use operations with Python code
2. Create a list of dictionaries, each dictionary is one row
3. Each dictionary should contain ONLY the columns you need to fill
4. Use pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True) to add all rows at once
5. DO NOT try to assign a list directly to df.loc or df[column] - this causes "Length of values does not match length of index" error
6. DO NOT use add_row JSON format for multiple rows - it's only for single rows

**EXAMPLE - User asks "sum of column Jan":**
{
  "operations": [{
    "python_code": "df['_temp_jan_sum'] = df['Jan'].sum()",
    "description": "Calculate sum of Jan column",
    "result_type": "dataframe"
  }],
  "add_row": {
    "position": -1,
    "data": {
      df.columns[0]: "Total",
      "Jan": "df['_temp_jan_sum'].iloc[0]"
    }
  },
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_jan_sum'])",
    "description": "Remove temporary column",
    "result_type": "dataframe"
  }]
}

**EXAMPLE - User asks "total of rows and columns":**
{
  "add_column": {
    "name": "Row Total",
    "position": -1,
    "default_value": ""
  },
  "operations": [{
    "python_code": "df['Row Total'] = df.select_dtypes(include=[np.number]).sum(axis=1)",
    "description": "Add row totals column",
    "result_type": "dataframe"
  }],
  "operations": [{
    "python_code": "df['_temp_jan'] = df['Jan'].sum(); df['_temp_feb'] = df['Feb'].sum(); df['_temp_mar'] = df['Mar'].sum(); df['_temp_row_total'] = df['Row Total'].sum()",
    "description": "Calculate column totals",
    "result_type": "dataframe"
  }],
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
  "operations": [{
    "python_code": "df = df.drop(columns=['_temp_jan', '_temp_feb', '_temp_mar', '_temp_row_total'])",
    "description": "Clean up temporary columns",
    "result_type": "dataframe"
  }]
}

**KEY PRINCIPLES:**
1. For SINGLE row: Use BOTH operations (with Python code) AND add_row JSON format
2. For MULTIPLE rows: Use ONLY operations with Python code (do NOT use add_row JSON format)
3. Operations calculate values and store in temporary columns (e.g., df['_temp_sum'] = df['Column'].sum())
4. add_row JSON format is ONLY for adding ONE row at a time
5. For multiple rows, create a list of dictionaries in operations and use pd.concat
6. Reference temporary columns in add_row.data using string expressions (e.g., "df['_temp_sum'].iloc[0]")
   - CRITICAL: Temporary columns MUST be created in operations BEFORE add_row references them
   - If you create a temporary column, make sure it exists in the DataFrame before using it in add_row
   - Example: operations creates df['_temp_sum'] = df['Column'].sum(), then add_row can use "df['_temp_sum'].iloc[0]"
7. Clean up temporary columns after adding the row (add another operation to drop them)
8. Use position: -1 to add at the end (bottom for rows, right for columns)
9. In add_row.data, only specify the columns you need to fill - other columns will be empty
10. The DataFrame CAN have more rows/columns - it's not fixed size
11. You can use expressions like "df.columns[0]" for column names in add_row.data keys

**REMEMBER:** 
- Single row = Operations + add_row JSON format
- Multiple rows = Operations ONLY (with list of dictionaries)
- NEVER try to assign a list of values directly to a column - always use pd.concat with DataFrame

**CRITICAL RULES FOR TEMPORARY COLUMNS:**
- ALWAYS create temporary columns in operations BEFORE referencing them in add_row.data
- Temporary columns must exist in the DataFrame when add_row tries to use them
- If you create df['_temp_X'] in operations, make sure it's not dropped before add_row runs
- Verify column names match exactly (case-sensitive, no typos)

**REMEMBER:** The system evaluates DataFrame expressions in add_row.data values, so you can use:
- "df['ColumnName'].iloc[0]" to get a value from a column
- "df.columns[0]" to get the first column name
- Any valid DataFrame expression that returns a value

**TEXT REPLACEMENT AND CHARACTER REMOVAL:**
When removing or replacing special characters (asterisk, question mark, plus, parentheses, brackets, braces, caret, dollar, pipe, backslash, etc.):
- ALWAYS use regex=False for simple character removal/replacement
- Example: df['Column'] = df['Column'].str.replace('*', '', regex=False)
- Example: df['Column'] = df['Column'].str.replace('"', '', regex=False)
- Example: df['Column'] = df['Column'].str.replace('?', '', regex=False)
- Only use regex=True when you need pattern matching (e.g., r'\\d+' for digits)
- For removing multiple characters, use multiple str.replace() calls with regex=False
- Example: df['Column'] = df['Column'].str.replace('*', '', regex=False).str.replace('?', '', regex=False)

**EXTRACTION OPERATIONS (GENERALIZED PATTERN RECOGNITION):**

⚠️⚠️⚠️ CRITICAL: str.extract() REQUIRES CAPTURE GROUPS ⚠️⚠️⚠️
- str.extract() will FAIL with error "pattern contains no capture groups" if regex has no parentheses
- ALL extraction patterns MUST have capture groups: r'(PATTERN)' not r'PATTERN'
- WRONG: df['Email'] = df['Notes'].str.extract(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}') ❌
- CORRECT: df['Email'] = df['Notes'].str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})')[0] ✓
- Always use [0] after str.extract() to get the first capture group as a Series
- This applies to ALL extractions: emails, phone numbers, dates, currency, numbers, text, etc.

When extracting values between columns, follow this pattern recognition workflow:

STEP 1: ANALYZE SOURCE COLUMN FORMAT (from sample data)
- Scan sample rows to identify: separators (|, :, -, space, parentheses), value position (before/after separator), format type (currency, number, text, date)
- Pattern types: "Text | Value", "Label: Value", "Value (Text)", "Text-Value", "Value$", "Text Value", etc.
- Identify value characteristics: numeric (with/without commas/decimals), currency ($, €, ₹, £, ¥), text, date, mixed

STEP 2: DETERMINE TARGET SEMANTICS (from column name)
- Column name hints at expected type:
  * Numeric indicators: "Sales", "Amount", "Price", "Cost", "Revenue", "Profit", "Total", "Sum", "Value", "Number", "Qty", "Quantity"
  * Text indicators: "Name", "Description", "Label", "Title", "Category", "Type"
  * Date indicators: "Date", "Time", "Created", "Updated"
- If target name suggests numeric but source has formatted string → extract numeric part only
- If target name suggests text but source has mixed → extract text part only
- If target name suggests date but source has mixed → extract date part only

STEP 3: GENERATE EXTRACTION CODE (pattern-based)
⚠️ CRITICAL: str.extract() REQUIRES CAPTURE GROUPS (parentheses) ⚠️
- str.extract() will FAIL with "pattern contains no capture groups" if pattern has no parentheses
- Pattern MUST have capture groups: r'PATTERN' → r'(PATTERN)' or r'PREFIX(PATTERN)SUFFIX'
- ALWAYS use .astype(str) before str.extract() to handle NaN/None values: df['Source'].astype(str).str.extract(...)
- Use expand=False to get a Series directly (recommended): df['Target'] = df['Source'].astype(str).str.extract(r'(PATTERN)', expand=False)
- Pattern template: df['Target'] = df['Source'].astype(str).str.extract(r'(PATTERN)', expand=False)
- For numeric extraction: df['Target'] = df['Source'].astype(str).str.extract(r'(PATTERN)', expand=False).str.replace(',', '', regex=False).astype(float)
- WRONG: df['Email'] = df['Notes'].str.extract(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}') ❌ (no capture group - will fail)
- CORRECT: df['Email'] = df['Notes'].astype(str).str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', expand=False) ✓ (has capture group)
- If multiple matches exist in one cell, str.extract() returns the FIRST match (this is correct)
- If no match exists, result will be NaN (this is acceptable - don't try to handle it)

**CRITICAL - EXTRACTING NAMES AND CONTACT NUMBERS FROM MIXED DATA:**
- When user says "fill name in C and contact in D from column B" or similar:
  - SMART FILLING: Detect where the last non-empty cell is in each target column, then fill empty cells sequentially
  - Step 1: Extract names and contacts from source column (Data/B)
  - Step 2: Find last non-empty index in each target column (Student Name, Contact No.)
  - Step 3: Fill empty cells sequentially starting from the next position after last filled cell
  - CORRECT approach for smart sequential filling (MUST USE THIS PATTERN):
    * import pandas as pd
    * # Extract names and contacts from source column
    * names = df['Data'].where(df['Data'].str.contains(r'^[A-Za-z\s]+$', na=False)).dropna().tolist()
    * contacts = df['Data'].where(df['Data'].str.match(r'^\d{8,10}$', na=False)).dropna().tolist()
    * # Fill Student Name column - find last non-empty, then fill empty cells sequentially
    * name_idx = 0
    * for i in range(len(df)):
    *     if pd.isna(df.loc[i, 'Student Name']) or df.loc[i, 'Student Name'] == '':
    *         if name_idx < len(names):
    *             df.loc[i, 'Student Name'] = names[name_idx]
    *             name_idx += 1
    * # Fill Contact No. column - find last non-empty, then fill empty cells sequentially
    * contact_idx = 0
    * for i in range(len(df)):
    *     if pd.isna(df.loc[i, 'Contact No.']) or df.loc[i, 'Contact No.'] == '':
    *         if contact_idx < len(contacts):
    *             df.loc[i, 'Contact No.'] = contacts[contact_idx]
    *             contact_idx += 1
  - ALTERNATIVE simpler approach (if data is alternating):
    * df['Student Name'] = df['Data'].where(df['Data'].str.contains(r'^[A-Za-z\s]+$', na=False))
    * df['Contact No.'] = df['Data'].where(df['Data'].str.match(r'^\d{8,10}$', na=False)).shift(1)
  - DO NOT use .str.isalpha() or .str.isnumeric() - these fail for strings with spaces or mixed content
  - NEVER use .str.isalpha() for names (fails on strings with spaces like "am Sandier")
  - NEVER use .str.isnumeric() for contact numbers in mixed data (use regex pattern matching instead)
- Common regex patterns (apply to similar formats) - ALL MUST HAVE CAPTURE GROUPS:
  * Email extraction: df['Email'] = df['Notes'].astype(str).str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})', expand=False)
  * Currency after separator: df['Amount'] = df['Source'].astype(str).str.extract(r'\\$([\\d,]+(?:\\.\\d+)?)', expand=False).str.replace(',', '', regex=False).astype(float)
  * Currency with decimals: df['Price'] = df['Source'].astype(str).str.extract(r'\\$([\\d.]+)', expand=False).astype(float)
  * Number after separator (|, :, -): df['Value'] = df['Source'].astype(str).str.extract(r'[|:-]\\s*([\\d,]+(?:\\.\\d+)?)', expand=False).str.replace(',', '', regex=False).astype(float)
  * Number with commas: df['Number'] = df['Source'].astype(str).str.extract(r'([\\d,]+)', expand=False).str.replace(',', '', regex=False).astype(float)
  * Text before separator: df['Text'] = df['Source'].astype(str).str.extract(r'^([^|:]+)', expand=False) or df['Text'] = df['Source'].astype(str).str.extract(r'(.+?)\\s*[|:]', expand=False)
  * Date extraction: df['Date'] = df['Source'].astype(str).str.extract(r'(\\d{4}-\\d{2}-\\d{2})', expand=False) or df['Date'] = df['Source'].astype(str).str.extract(r'(\\d{1,2}/\\d{1,2}/\\d{4})', expand=False)
  * Phone number: df['Phone'] = df['Source'].astype(str).str.extract(r'(\\d{3}-\\d{3}-\\d{4})', expand=False) or df['Phone'] = df['Source'].astype(str).str.extract(r'(\\(\\d{3}\\)\\s*\\d{3}-\\d{4})', expand=False)
- ⚠️ CRITICAL RULE: ALL str.extract() patterns MUST have capture groups (parentheses) ⚠️
- ALWAYS use .astype(str) before str.extract() to handle NaN/None values
- Use expand=False to get a Series directly (cleaner than [0])
- Always handle commas: extract → remove commas → convert to float
- Handle NaN: extraction may fail for some rows (acceptable, will be NaN - don't try to handle it)
- If multiple matches exist in one cell, str.extract() returns the FIRST match (this is correct behavior)

STEP 4: VALIDATION RULE
- If source column contains formatted data (has separators/currency/text mix) AND target column name suggests single type (Sales, Amount, Name, Date) → MUST extract, not copy
- WRONG: df['Sales'] = df['Combined Data'] (copies formatted string like "Name | $Value")
- CORRECT: df['Sales'] = df['Combined Data'].str.extract(r'\\$([\\d,]+)')[0].str.replace(',', '', regex=False).astype(float) (extracts numeric value)

PATTERN RECOGNITION PRINCIPLES:
- Apply pattern recognition to ANY format, not just memorized examples
- Analyze sample data FIRST to determine the correct extraction pattern
- Use column name semantics to guide extraction type
- Handle edge cases: missing values, different formats in same column, special characters

**MULTI-COLUMN CONDITIONAL LOGIC (GENERAL PATTERN):**

When filling a column based on conditions from multiple columns, use this PATTERN:

PATTERN 1 - df.apply with lambda (works for ANY number of columns and complex logic):
df['Result'] = df.apply(lambda row: value_if_true if (condition) else value_if_false, axis=1)
- Use 'or' for "ANY condition is true" (e.g., if ANY score < 60)
- Use 'and' for "ALL conditions are true" (e.g., if BOTH scores >= 60)
- For multiple conditions: (row['Col1'] < 60) or (row['Col2'] < 60)
- Access columns via row['ColumnName'] or row[df.columns[index]]

PATTERN 2 - np.where for simple two-value conditions:
df['Result'] = np.where((df['Col1'] < 60) | (df['Col2'] < 60), 'Value1', 'Value2')

PATTERN 3 - Column letters (B, C, E) to actual names:
col_b = df.columns[1]; col_c = df.columns[2]; target_col = df.columns[4] if len(df.columns) > 4 else 'Result'
Then use: df.apply(lambda row: ..., axis=1) with row[col_b], row[col_c], etc.

KEY RULES:
- ALWAYS use df.apply(lambda row: ..., axis=1) for multi-column row-by-row operations
- Convert to numeric with pd.to_numeric(row['Col'], errors='coerce') if needed
- DO NOT use regex (re) or str methods for numeric comparisons
- Apply this pattern to ANY multi-column conditional task (Pass/Fail, Grade, Status, Category, etc.)

**CRITICAL RULES:**
1. ALWAYS generate python_code in operations (never leave empty)
2. When adding a SINGLE row, you MUST include BOTH:
   - operations with Python code to calculate values
   - add_row JSON format to add the row
3. When adding MULTIPLE rows, use ONLY operations with Python code:
   - Create a list of dictionaries: new_rows = [{'Column': value} for value in range(...)]
   - Use pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
   - DO NOT use add_row JSON format for multiple rows
4. Use actual column names from dataset (not Excel letters in code)
5. Code must be executable directly
6. Handle edge cases (NaN, empty data)
7. DO NOT generate chart code
8. Return ONLY valid JSON (no markdown, no explanations)
9. When using add_row, only specify columns you need in data - other columns will be empty
10. Calculate values in operations first, then reference them in add_row.data using expressions
11. NEVER assign a list of values directly to df[column] or df.loc - always use pd.concat with DataFrame
12. CRITICAL: When removing/replacing special characters (*, ?, +, etc.), ALWAYS use regex=False to avoid regex errors

**WHEN USER ASKS TO COMBINE/STACK MULTIPLE TABLES:**

⚠️ CRITICAL: PAY ATTENTION TO KEYWORDS - "new column" vs "stack" vs "merge" mean DIFFERENT things:

**CASE 1: Vertical stacking (concatenating rows - adds MORE ROWS):**
- User: "combine all 5 tables into one stacked dataset" (no mention of "new column")
- User: "stack all tables vertically"
- User: "merge all tables into one" (if context suggests rows)
→ These mean: Concatenate multiple DataFrames VERTICALLY (axis=0) - adds rows
→ Use: pd.concat([df1, df2, df3, df4, df5], ignore_index=True)
→ Result: More rows, same columns

**CASE 2: Horizontal combination (concatenating columns - adds MORE COLUMNS):**
- User: "combine all 5 tables into one stacked dataset and give them in new column"
- User: "combine tables in new columns"
- User: "put all tables in new columns"
- User: "merge tables side by side"
→ These mean: Concatenate multiple DataFrames HORIZONTALLY (axis=1) - adds columns
→ Use: df = pd.concat([df1, df2, df3, df4, df5], axis=1)
→ Result: Same rows (or aligned), more columns

**⚠️ CRITICAL: EXECUTION ENVIRONMENT ONLY HAS ONE `df` VARIABLE ⚠️**
- The execution environment ONLY has a single `df` variable - there is NO `df1`, `df2`, `df3`, etc.
- Available variables: df (single DataFrame), pd, np, re, DateCleaner, TextCleaner, CurrencyCleaner
- DO NOT generate code that references `df1`, `df2`, `df3`, `df4`, `df5` - these variables DO NOT EXIST
- If user says "combine all 5 tables" and you need multiple DataFrames, you must WORK WITH THE SINGLE `df` that exists

**WHEN USER SAYS "COMBINE ALL 5 TABLES":**
- If the tables are already in different parts of the current `df`, you may need to split and recombine
- If the tables are in separate Excel sheets, they are NOT automatically loaded - only the current sheet is in `df`
- If user wants to combine existing data horizontally (as new columns), check if the data is already in `df` or if it's a restructuring operation
- Most likely: User wants to combine data that's already in `df` horizontally (axis=1) - this might already be done or might require identifying separate "table" regions

**CORRECT - Vertical stacking (if you have separate DataFrames to combine):**
⚠️ THIS REQUIRES FIRST LOADING/IDENTIFYING THE SEPARATE TABLES FROM `df` OR FILE
- If tables are in separate sheets, you cannot access them - only current sheet is in `df`
- If tables are regions in current `df`, split them first, then: df = pd.concat([table1, table2, table3, table4, table5], ignore_index=True)

**CORRECT - Horizontal combination (combining as new columns within same df):**
⚠️ WORK WITH THE SINGLE `df` - cannot reference df1, df2, etc.
- If data is already in `df` as separate column groups, you might just need to reorder: df = df[col_list]
- If you need to combine multiple datasets horizontally but only have one `df`, you may need to clarify with user or assume data is already structured
- Example (if splitting df into parts first): part1 = df.iloc[:, 0:5]; part2 = df.iloc[:, 5:10]; df = pd.concat([part1, part2], axis=1)

**CRITICAL FOR VERTICAL STACKING:**
→ After combining, columns may have mixed types (object dtype) - NEVER apply numeric aggregation functions (.mean(), .sum(), .median(), etc.) to object columns
→ ALWAYS check data type before aggregation: df.select_dtypes(include=[np.number]) for numeric columns
→ If you need to aggregate after combining, use: numeric_cols = df.select_dtypes(include=[np.number]).columns; df.groupby(...)[numeric_cols].mean()
→ WRONG: df.groupby(...).mean() ❌ (may fail on object columns)
→ CORRECT: numeric_cols = df.select_dtypes(include=[np.number]).columns; df.groupby(...)[numeric_cols].mean() ✓ (only numeric columns)

**CORRECT - Aggregating after combining (only numeric columns):**
{
  "operations": [{
    "python_code": "numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist(); grouped = df.groupby(['Region'])[numeric_cols].mean().reset_index()",
    "description": "Calculate mean for each region using only numeric columns",
    "result_type": "dataframe"
  }]
}

**CRITICAL RULES FOR AGGREGATION:**
1. NEVER use .mean(), .sum(), .median(), .std() on entire DataFrame - always select numeric columns first
2. ALWAYS use df.select_dtypes(include=[np.number]) before numeric aggregation
3. When combining tables, columns may become object dtype - check data types before aggregation
4. For groupby aggregation: numeric_cols = df.select_dtypes(include=[np.number]).columns; df.groupby(...)[numeric_cols].agg(...)
"""


class ActionPlanBot:
    """Bot for generating data operation action plans"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize Action Plan Bot
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost savings, optimized for JSON outputs)
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
            # Extract total rows from sample_explanation if available
            total_rows = None
            if sample_explanation:
                import re
                # Extract "X rows selected from Y total" pattern
                match = re.search(r'(\d+)\s+rows?\s+selected\s+from\s+(\d+)\s+total', sample_explanation, re.IGNORECASE)
                if match:
                    total_rows = int(match.group(2))
            
            # Build prompt with total row count
            prompt = get_prompt_with_context(user_prompt, available_columns, sample_data, total_rows=total_rows)
            
            # Get knowledge base summary
            kb_summary = get_knowledge_base_summary()
            
            # Get task suggestions (simplified output)
            task_suggestions = get_task_decision_guide(user_prompt)
            task_hint = task_suggestions.get('suggested_task', 'auto-detect')
            
            # Get column mapping info (Excel letters → actual column names) - simplified
            column_mapping = get_column_mapping_info(available_columns)
            
            # Build concise prompt - remove verbose sections
            # Only include essential context
            prompt_parts = []
            
            # Knowledge base (ultra-concise)
            if kb_summary:
                prompt_parts.append(f"Tasks: {kb_summary}")
            
            # Task hint (one line)
            if task_hint != 'auto-detect':
                prompt_parts.append(f"Task hint: {task_hint}")
            
            # Column mapping (essential for Excel letter references)
            if column_mapping:
                prompt_parts.append(column_mapping)
            
            # Main prompt with sample data
            prompt_parts.append(prompt)
            
            # Build final prompt
            full_prompt = "\n\n".join(prompt_parts) + "\n\nReturn ONLY valid JSON with operations array containing python_code for each operation."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ACTION_PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ],
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
                if "conditional_format" in action_plan:
                    logger.info(f"✅ Conditional format found in action plan!")
                    logger.info(f"Conditional format structure: {json.dumps(action_plan['conditional_format'], indent=2)}")
                else:
                    logger.warning(f"⚠️ No 'conditional_format' field in action plan!")
                    logger.info(f"Full action plan structure: {json.dumps({k: type(v).__name__ for k, v in action_plan.items()}, indent=2)}")
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    action_plan = json.loads(json_match.group())
                    logger.info(f"✅ Successfully parsed action plan JSON from regex extraction")
                    logger.info(f"Action plan keys: {list(action_plan.keys())}")
                    
                    if "conditional_format" in action_plan:
                        logger.info(f"✅ Conditional format found in action plan!")
                        logger.info(f"Conditional format structure: {json.dumps(action_plan['conditional_format'], indent=2)}")
                    else:
                        logger.warning(f"⚠️ No 'conditional_format' field in action plan!")
                else:
                    logger.error(f"❌ Could not parse JSON from response: {content[:200]}")
                    raise ValueError(f"Could not parse JSON from response: {content[:200]}")
            
            # Normalize action plan
            ops_before = action_plan.get('operations', [])
            logger.info(f"🔍 Action plan before normalization - operations count: {len(ops_before)}")
            if ops_before:
                logger.info(f"🔍 Operations before normalization: {json.dumps([{'description': op.get('description', 'No desc'), 'python_code': op.get('python_code', '')[:50]} for op in ops_before], indent=2)}")
            normalized_plan = self._normalize_action_plan(action_plan)
            ops_after = normalized_plan.get('operations', [])
            logger.info(f"🔍 Action plan after normalization - operations count: {len(ops_after)}")
            if ops_after:
                logger.info(f"🔍 Operations after normalization: {json.dumps([{'description': op.get('description', 'No desc'), 'python_code': op.get('python_code', '')[:50]} for op in ops_after], indent=2)}")
            
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
        
        # Add optional fields - preserve ALL fields from action plan
        if "add_row" in action_plan:
            normalized["add_row"] = action_plan["add_row"]
        
        if "add_column" in action_plan:
            normalized["add_column"] = action_plan["add_column"]
        
        if "delete_column" in action_plan:
            normalized["delete_column"] = action_plan["delete_column"]
        
        if "delete_rows" in action_plan:
            normalized["delete_rows"] = action_plan["delete_rows"]
        
        if "sort" in action_plan:
            normalized["sort"] = action_plan["sort"]
        
        if "conditional_format" in action_plan:
            normalized["conditional_format"] = action_plan["conditional_format"]
        
        if "format" in action_plan:
            normalized["format"] = action_plan["format"]
        
        if "filters" in action_plan:
            normalized["filters"] = action_plan["filters"]
        
        if "task" in action_plan:
            normalized["task"] = action_plan["task"]
        
        # Ensure operations is a list
        if not isinstance(normalized["operations"], list):
            normalized["operations"] = []
        
        # Validate and extract python_code for each operation
        for op in normalized["operations"]:
            # If python_code is missing or empty, try to extract from execution_instructions
            if "python_code" not in op or not op.get("python_code", "").strip():
                # Check if execution_instructions has code
                exec_instructions = op.get("execution_instructions", {})
                if isinstance(exec_instructions, dict) and "code" in exec_instructions:
                    op["python_code"] = exec_instructions["code"]
                    logger.info(f"✅ Extracted python_code from execution_instructions.code")
                elif "python_code" not in op:
                    logger.warning(f"Operation missing python_code: {op}")
        
        return normalized

