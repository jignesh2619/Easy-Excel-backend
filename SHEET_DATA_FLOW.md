# Sheet Data Flow to ActionPlanBot

## Overview

The system uses a **smart sampling strategy** to provide ActionPlanBot with representative sheet data while managing token limits. The complete flow is:

```
Excel File → SampleSelector → ActionPlanBot → GPT-4
```

## Complete Data Flow

### 1. File Upload & Loading (`app.py`)

```python
# User uploads Excel file
file = UploadFile(...)
df = pd.read_excel(temp_file_path)  # Load full dataset
available_columns = list(df.columns)
```

### 2. Smart Sample Selection (`app.py` lines 211-229)

```python
# Create representative sample (10-20 rows, all columns preserved)
sample_result = sample_selector.build_sample(df)
sample_df = sample_result.dataframe
sample_explanation = sample_result.explanation
sample_data = sample_df.to_dict("records")  # Convert to list of dicts
```

**SampleSelector Strategy:**
- **Preserves ALL columns** (no column is dropped)
- **Selects 10-20 diverse rows** (configurable via `max_rows`, `min_rows`)
- **Smart selection includes:**
  - Quantile-based sampling for numeric columns (min, 25%, 50%, 75%, max)
  - Categorical variety (ensures different categories appear)
  - Edge cases and outliers
  - Date range coverage
  - Missing value examples

### 3. Routing to ActionPlanBot (`llm_agent.py` lines 161-180)

```python
# LLMAgent routes non-chart requests to ActionPlanBot
if not is_chart_request:
    return self.action_plan_bot.generate_action_plan(
        user_prompt=user_prompt,
        available_columns=available_columns,  # All column names
        sample_data=sample_data,               # Representative rows
        sample_explanation=sample_explanation  # How sample was selected
    )
```

### 4. Prompt Building (`action_plan_bot.py` lines 200-260)

```python
# ActionPlanBot builds comprehensive prompt
prompt = get_prompt_with_context(
    user_prompt, 
    available_columns,  # All column names with indices
    sample_data         # Representative sample rows
)

# Adds context:
# - Knowledge base summary
# - Task suggestions
# - Few-shot learning examples
# - Sample explanation
```

### 5. Prompt Formatting (`utils/prompts.py` lines 1115-1400)

The `get_prompt_with_context()` function creates a comprehensive prompt that includes:

#### A. Column Information
```
Available columns (with indices for positional references):
0: Name (first column)
1: Age (second column)
2: City (third column)
3: Phone (last column)

Column List: Name, Age, City, Phone
```

#### B. Representative Sample Data
```
╔══════════════════════════════════════════════════════════════════════════════╗
║         📊 REPRESENTATIVE SAMPLE OF THE UPLOADED DATASET PROVIDED 📊          ║
║                                                                                ║
║  You are receiving a curated sample of 15 rows. ALL columns appear.           ║
║  Rows were selected to capture numeric extremes, category coverage, dates,     ║
║  missing-value edge cases, and overall diversity of the dataset.               ║
╚══════════════════════════════════════════════════════════════════════════════╝

REPRESENTATIVE SAMPLE (15 rows shown, 4 columns):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━ ROW 1 ━━━
  [Name]: John Doe
  [Age]: 30
  [City]: New York
  [Phone]: 123-456-7890

━━━ ROW 2 ━━━
  [Name]: Jane Smith
  [Age]: 25
  [City]: Los Angeles
  [Phone]: 987-654-3210

... (all sample rows)
```

#### C. Analysis Instructions
```
═══════════════════════════════════════════════════════════════════════════════
🔍 STEP 1: ANALYZE THE DATASET (DO THIS FIRST, BEFORE ANY ACTION)
═══════════════════════════════════════════════════════════════════════════════

YOU HAVE THE COMPLETE EXCEL DATASET ABOVE WITH ALL 15 ROWS.

⚠️ MANDATORY ANALYSIS WORKFLOW:

1. **READ THE ENTIRE DATASET**: Go through ALL 15 rows provided above
2. **UNDERSTAND THE STRUCTURE**: 
   - Column positions: first=Name (index 0), second=Age (index 1), etc.
   - Excel letters: A=Name, B=Age, C=City, etc.
3. **SEARCH FOR CONTENT**: 
   - If user mentions text like "Car detailing service" → Search ALL rows to find which column(s) contain it
   - If user says "phone column" → Search ALL rows to find which column has phone data
4. **VERIFY BEFORE ACTING**:
   - If user says "remove 3rd column" → Check what the 3rd column actually contains
```

### 6. GPT-4 Receives Complete Context

ActionPlanBot sends to GPT-4:

```python
{
    "role": "system",
    "content": ACTION_PLAN_SYSTEM_PROMPT  # Instructions for Python code generation
},
{
    "role": "user", 
    "content": full_prompt  # Contains:
        # - User request
        # - All column names with indices
        # - Representative sample data (all rows)
        # - Analysis instructions
        # - Knowledge base context
        # - Task suggestions
        # - Few-shot examples
}
```

## What ActionPlanBot Receives

### ✅ Complete Column Information
- **All column names** (exact names, case-sensitive)
- **Column indices** (for positional references: first=0, second=1, etc.)
- **Excel column letters** (A=0, B=1, C=2, etc.)

### ✅ Representative Sample Data
- **10-20 rows** (configurable)
- **ALL columns preserved** (no columns dropped)
- **Diverse selection** (min/max values, categories, edge cases)
- **Formatted as readable table** (row-by-row, column-by-column)

### ✅ Context & Instructions
- **Sample explanation** (how rows were selected)
- **Analysis instructions** (how to use the data)
- **Positional mapping** (first/second/third/last → actual column names)
- **Search instructions** (how to find columns by content)

## Example: Complete Flow

### Input
- **File**: `sales_data.xlsx` (1000 rows, 5 columns)
- **User Request**: "Remove duplicates and filter rows where amount > 1000"

### Step 1: Sample Selection
```python
SampleSelector.build_sample(df)
# Returns: 15 representative rows (all 5 columns preserved)
# Includes: min/max amounts, various cities, different dates
```

### Step 2: Data Formatting
```python
sample_data = [
    {"Name": "John", "City": "NYC", "Amount": 500, "Date": "2024-01-01", "Status": "Active"},
    {"Name": "Jane", "City": "LA", "Amount": 1500, "Date": "2024-01-02", "Status": "Active"},
    # ... 13 more rows
]
available_columns = ["Name", "City", "Amount", "Date", "Status"]
```

### Step 3: Prompt to ActionPlanBot
```
User Request: "Remove duplicates and filter rows where amount > 1000"

Available columns:
0: Name (first column)
1: City (second column)
2: Amount (third column)
3: Date (fourth column)
4: Status (last column)

REPRESENTATIVE SAMPLE (15 rows):
━━━ ROW 1 ━━━
  [Name]: John
  [City]: NYC
  [Amount]: 500
  [Date]: 2024-01-01
  [Status]: Active
...
```

### Step 4: ActionPlanBot Generates Python Code
```json
{
  "operations": [
    {
      "python_code": "df = df.drop_duplicates().reset_index(drop=True)",
      "description": "Remove duplicate rows",
      "result_type": "dataframe"
    },
    {
      "python_code": "df = df[df['Amount'] > 1000].reset_index(drop=True)",
      "description": "Filter rows where amount > 1000",
      "result_type": "dataframe"
    }
  ]
}
```

### Step 5: PythonExecutor Executes
```python
executor = PythonExecutor(df)  # Full dataset (1000 rows)
executor.execute_multiple(operations)  # Executes both operations
# Result: Cleaned and filtered dataframe
```

## Key Points

1. **Sample, Not Full Data**: ActionPlanBot receives 10-20 representative rows, not the entire dataset
2. **All Columns Preserved**: Every column appears in the sample
3. **Smart Selection**: Sample includes diverse values (min/max, categories, edge cases)
4. **Full Dataset Execution**: PythonExecutor operates on the complete dataset, not just the sample
5. **Token Efficient**: Sample keeps token usage manageable while providing sufficient context

## Configuration

You can adjust sample size in `SampleSelector`:

```python
# In app.py or sample_selector.py
sample_selector = SampleSelector(max_rows=20, min_rows=10)
```

- **max_rows**: Maximum rows in sample (default: 20)
- **min_rows**: Minimum rows in sample (default: 10)

## Benefits

✅ **Token Efficient**: Only 10-20 rows sent to GPT-4, not thousands
✅ **Complete Context**: All columns preserved, diverse values included
✅ **Accurate Analysis**: GPT-4 can identify columns, understand data types, find patterns
✅ **Scalable**: Works with datasets of any size (100 rows to 1M+ rows)

