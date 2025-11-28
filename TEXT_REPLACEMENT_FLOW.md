# Text Replacement Flow: "Replace 'car detailing service' with 'cds'"

## Complete Execution Flow

### Step 1: User Request
```
User Prompt: "replace 'car detailing service' with 'cds'"
```

### Step 2: Data Preparation (`app.py`)

```python
# Full dataset loaded
df = pd.read_excel(file)  # e.g., 5000 rows, 10 columns

# Smart sample created (10-20 rows, ALL columns preserved)
sample_result = sample_selector.build_sample(df)
sample_data = sample_df.to_dict("records")  # 15 rows, all columns
```

**Sample Data Example:**
```python
sample_data = [
    {"Name": "John", "Service": "Car detailing service", "Amount": 100},
    {"Name": "Jane", "Service": "Car wash", "Amount": 50},
    {"Name": "Bob", "Service": "Car detailing service", "Amount": 150},
    # ... 12 more rows
]
available_columns = ["Name", "Service", "Amount", ...]
```

### Step 3: Routing to ActionPlanBot (`llm_agent.py`)

```python
# LLMAgent detects it's NOT a chart request
is_chart = self._is_chart_request("replace 'car detailing service' with 'cds'")
# Returns: False

# Routes to ActionPlanBot
return self.action_plan_bot.generate_action_plan(
    user_prompt="replace 'car detailing service' with 'cds'",
    available_columns=["Name", "Service", "Amount", ...],
    sample_data=sample_data,  # 15 representative rows
    sample_explanation="Selected 15 rows with diverse values..."
)
```

### Step 4: GPT-4 Analysis (`action_plan_bot.py` + `utils/prompts.py`)

GPT-4 receives comprehensive prompt with sample data and analyzes:

#### A. Sample Data Analysis
```
REPRESENTATIVE SAMPLE (15 rows shown, 10 columns):
━━━ ROW 1 ━━━
  [Name]: John
  [Service]: Car detailing service
  [Amount]: 100
  ...

━━━ ROW 2 ━━━
  [Name]: Jane
  [Service]: Car wash
  [Amount]: 50
  ...

━━━ ROW 3 ━━━
  [Name]: Bob
  [Service]: Car detailing service
  [Amount]: 150
  ...
```

#### B. GPT-4's Analysis Process

1. **Identifies Operation**: Text replacement (not filtering, not highlighting)
2. **Finds Column**: Searches sample data to find which column contains "car detailing service"
   - Row 1: `Service = "Car detailing service"` ✅
   - Row 3: `Service = "Car detailing service"` ✅
   - **Conclusion**: Column "Service" contains the text
3. **Understands Replacement**: Replace "car detailing service" with "cds"
4. **Generates Python Code**: Uses pandas `.str.replace()` method

### Step 5: GPT-4 Generates Python Code (`action_plan_bot.py`)

ActionPlanBot generates JSON with Python code:

```json
{
  "operations": [
    {
      "python_code": "df['Service'] = df['Service'].astype(str).str.replace('car detailing service', 'cds', case=False, regex=False)",
      "description": "Replace 'car detailing service' with 'cds' in Service column",
      "result_type": "dataframe"
    }
  ]
}
```

**Key Points:**
- ✅ Uses actual column name: `Service` (identified from sample)
- ✅ Uses `.str.replace()` for text replacement
- ✅ `case=False` for case-insensitive matching
- ✅ `regex=False` for literal string matching
- ✅ Converts to string first with `.astype(str)` to handle mixed types

### Step 6: PythonExecutor Executes Code (`python_executor.py`)

```python
# PythonExecutor receives the operation
executor = PythonExecutor(df)  # Full dataset (5000 rows)

# Executes the Python code
executor.execute(
    python_code="df['Service'] = df['Service'].astype(str).str.replace('car detailing service', 'cds', case=False, regex=False)",
    operation_meta={
        "description": "Replace 'car detailing service' with 'cds' in Service column",
        "result_type": "dataframe"
    }
)
```

**Execution Process:**

1. **Code Validation**: Validates code (no imports, no dangerous operations)
2. **Build Execution Environment**: 
   ```python
   exec_globals = {
       'df': self.df,  # Full dataset (5000 rows)
       'pd': pd,
       'np': np,
       # ... other utilities
   }
   ```
3. **Execute Code**:
   ```python
   exec(python_code, exec_globals)
   # This runs on the FULL dataset:
   # df['Service'] = df['Service'].astype(str).str.replace('car detailing service', 'cds', case=False, regex=False)
   ```
4. **Update DataFrame**:
   ```python
   self.df = exec_globals['df']  # Updated dataframe
   ```

### Step 7: Full Dataset Replacement

The replacement happens on **ALL rows** in the full dataset:

```python
# Before replacement (example rows):
# Row 5:  Service = "Car detailing service"
# Row 12: Service = "car detailing service"  
# Row 45: Service = "CAR DETAILING SERVICE"
# Row 78: Service = "Premium car detailing service package"

# After replacement:
# Row 5:  Service = "cds"
# Row 12: Service = "cds"
# Row 45: Service = "cds"
# Row 78: Service = "Premium cds package"  # Partial match replaced
```

**Pandas `.str.replace()` Behavior:**
- **Case-insensitive**: "Car Detailing Service", "CAR DETAILING SERVICE", "car detailing service" all match
- **Partial matches**: "Premium car detailing service package" → "Premium cds package"
- **All occurrences**: Replaces every occurrence in each cell

### Step 8: Result

```python
# ExcelProcessor returns updated dataframe
return {
    "df": self.df,  # All 5000 rows with replacements applied
    "summary": ["✓ Replace 'car detailing service' with 'cds' in Service column"],
    "formula_result": None
}
```

### Step 9: Save to Excel (`excel_processor.py`)

```python
# Save processed file with replacements
processed_file_path = processor.save_processed_file(output_path)

# Result: Excel file with all "car detailing service" replaced with "cds"
```

## Complete Example

### Input
- **Dataset**: 5000 rows, column "Service" contains various service names
- **User Request**: "replace 'car detailing service' with 'cds'"

### GPT-4 Analysis (Sample Data - 15 rows)
```
Row 1: Service = "Car detailing service" ✅ Found!
Row 3: Service = "Car detailing service" ✅ Found!
Conclusion: Column "Service" contains "car detailing service"
```

### Generated Python Code
```python
df['Service'] = df['Service'].astype(str).str.replace(
    'car detailing service', 
    'cds', 
    case=False,  # Case-insensitive
    regex=False  # Literal string match
)
```

### Execution (Full Dataset - 5000 rows)
```python
# Before:
Row 5:  "Car detailing service" → "cds"
Row 12: "car detailing service" → "cds"
Row 45: "CAR DETAILING SERVICE" → "cds"
Row 78: "Premium car detailing service package" → "Premium cds package"

# All 5000 rows processed
# All occurrences replaced
```

### Output Excel File
- All cells in "Service" column containing "car detailing service" are replaced with "cds"
- Works regardless of case
- Partial matches also replaced

## Alternative: Using TextCleaner Utility

GPT-4 could also generate code using the `TextCleaner` utility:

```json
{
  "operations": [
    {
      "python_code": "df = TextCleaner.replace_text(df, ['Service'], 'car detailing service', 'cds', case_sensitive=False)",
      "description": "Replace 'car detailing service' with 'cds' using TextCleaner",
      "result_type": "dataframe"
    }
  ]
}
```

**TextCleaner Implementation:**
```python
# In services/cleaning/text.py
@staticmethod
def replace_text(df: pd.DataFrame, columns: Union[str, List[str]], 
                 old_text: str, new_text: str, case_sensitive: bool = True):
    if case_sensitive:
        df[col] = df[col].astype(str).str.replace(old_text, new_text, regex=False)
    else:
        df[col] = df[col].astype(str).str.replace(old_text, new_text, case=False, regex=False)
```

## Key Differences from Conditional Formatting

| Aspect | Conditional Formatting | Text Replacement |
|--------|----------------------|------------------|
| **Operation** | Highlights cells | Modifies cell values |
| **GPT-4 Task** | Identify column | Identify column + generate Python code |
| **Execution** | Stores rule, applies when saving | Executes immediately on full dataset |
| **Result** | Visual highlighting | Actual data modification |
| **Code Generated** | None (just config) | Python code with `.str.replace()` |

## Edge Cases Handled

### 1. Text Not in Sample
**Scenario**: "car detailing service" doesn't appear in the 15-row sample

**Solution**: 
- GPT-4 can infer from column name (e.g., "Service" column likely contains service names)
- Or use fuzzy matching
- The actual replacement still works on full dataset

### 2. Multiple Columns
**Scenario**: Text appears in multiple columns

**Solution**: GPT-4 can generate code for multiple columns:
```python
# Option 1: Replace in specific columns
df['Service'] = df['Service'].astype(str).str.replace('car detailing service', 'cds', case=False, regex=False)
df['Description'] = df['Description'].astype(str).str.replace('car detailing service', 'cds', case=False, regex=False)

# Option 2: Replace in all columns
for col in df.columns:
    df[col] = df[col].astype(str).str.replace('car detailing service', 'cds', case=False, regex=False)
```

### 3. Case Variations
**Scenario**: "Car Detailing Service", "CAR DETAILING SERVICE", "car detailing service"

**Solution**: Uses `case=False` for case-insensitive matching

### 4. Partial Matches
**Scenario**: "Premium car detailing service package"

**Solution**: `.str.replace()` replaces partial matches:
- "Premium car detailing service package" → "Premium cds package"

### 5. Multiple Occurrences in Same Cell
**Scenario**: "car detailing service and car detailing service"

**Solution**: `.str.replace()` replaces all occurrences:
- "car detailing service and car detailing service" → "cds and cds"

## Performance

- **GPT-4 Analysis**: ~2-3 seconds (analyzes 15-row sample)
- **Code Generation**: ~1 second (generates Python code)
- **Full Dataset Replacement**: ~0.5-1 second (replaces in 5000 rows)
- **Total**: ~3-5 seconds for 5000 rows

## Summary

1. ✅ **GPT-4 identifies column** from sample data (10-20 rows)
2. ✅ **GPT-4 generates Python code** using `.str.replace()`
3. ✅ **PythonExecutor executes code** on full dataset (all rows)
4. ✅ **All matching text replaced** regardless of case
5. ✅ **Partial matches handled** automatically
6. ✅ **Efficient**: Sample for analysis, full replacement for execution

The system works efficiently: GPT-4 only needs to see a sample to identify the column and generate code, but the actual replacement happens on the complete dataset using pandas string operations.

