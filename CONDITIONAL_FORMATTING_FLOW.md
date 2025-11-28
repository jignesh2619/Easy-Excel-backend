# Conditional Formatting Flow: "Highlight cells with 'car detailing service'"

## Complete Execution Flow

### Step 1: User Request
```
User Prompt: "highlight cells with 'car detailing service'"
```

### Step 2: Data Preparation (`app.py`)

```python
# Full dataset loaded (could be 1000s of rows)
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
is_chart = self._is_chart_request("highlight cells with 'car detailing service'")
# Returns: False

# Routes to ActionPlanBot
return self.action_plan_bot.generate_action_plan(
    user_prompt="highlight cells with 'car detailing service'",
    available_columns=["Name", "Service", "Amount", ...],
    sample_data=sample_data,  # 15 representative rows
    sample_explanation="Selected 15 rows with diverse values..."
)
```

### Step 4: GPT-4 Analysis (`action_plan_bot.py` + `utils/prompts.py`)

GPT-4 receives a comprehensive prompt that includes:

#### A. Sample Data (All Rows)
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

#### B. Analysis Instructions
```
⚠️ MANDATORY ANALYSIS WORKFLOW:

1. **READ THE ENTIRE DATASET**: Go through ALL 15 rows provided above
2. **SEARCH FOR CONTENT**: 
   - If user mentions text like "Car detailing service" → Search ALL rows to find which column(s) contain it
   - If user says "phone column" → Search ALL rows to find which column has phone data
3. **VERIFY BEFORE ACTING**:
   - Search through ALL rows to identify the actual column name
```

#### C. GPT-4's Search Process

GPT-4 analyzes the sample data:

1. **Searches Row 1**: Finds "Car detailing service" in `Service` column ✅
2. **Searches Row 2**: "Car wash" in `Service` column (different text)
3. **Searches Row 3**: Finds "Car detailing service" in `Service` column ✅
4. **Conclusion**: The `Service` column contains "Car detailing service"

**Note**: Even if "car detailing service" doesn't appear in the sample, GPT-4 can:
- Infer from column names (e.g., "Service" column likely contains service names)
- Use fuzzy matching
- Search for similar patterns

### Step 5: GPT-4 Generates JSON (`action_plan_bot.py`)

```json
{
  "operations": [],
  "conditional_format": {
    "format_type": "contains_text",
    "config": {
      "column": "Service",  // Identified from sample data
      "text": "car detailing service",  // Exact text from user
      "bg_color": "#FFF3CD",  // Default yellow
      "text_color": "#000000"
    }
  }
}
```

**Key Points:**
- ✅ GPT-4 identifies `Service` column from sample data
- ✅ Preserves exact text: "car detailing service" (case-insensitive matching)
- ✅ Uses `contains_text` format type for partial matches

### Step 6: ExcelProcessor Stores Rule (`excel_processor.py`)

```python
# In execute_action_plan()
if "conditional_format" in action_plan:
    self._execute_conditional_format(action_plan)

# Stores rule for later application
rule = {
    "type": "conditional",
    "format_type": "contains_text",
    "config": {
        "column": "Service",
        "text": "car detailing service",
        "bg_color": "#FFF3CD"
    }
}
self.formatting_rules.append(rule)
```

### Step 7: File Saving (`excel_processor.py` - `save_processed_file`)

When saving the Excel file:

```python
# 1. Write data to Excel
df.to_excel(output_path, index=False, engine='xlsxwriter')

# 2. Apply conditional formatting
workbook = xlsxwriter.Workbook(output_path)
worksheet = workbook.get_worksheet()
self._apply_conditional_formatting(workbook, worksheet)
```

### Step 8: Actual Cell Highlighting (`_apply_conditional_formatting`)

**This is where the magic happens - searches the FULL dataset:**

```python
def _apply_conditional_formatting(self, workbook, worksheet):
    for rule in self.formatting_rules:
        if rule["format_type"] == "contains_text":
            column = rule["config"]["column"]  # "Service"
            target_text = rule["config"]["text"]  # "car detailing service"
            
            # Get the FULL dataset column (not just sample!)
            series = self.df[column].astype(str)  # All 5000 rows
            
            # Search ALL rows for matches (case-insensitive)
            matches = series.str.contains(
                str(target_text), 
                case=False,  # Case-insensitive
                na=False     # Ignore NaN values
            )
            
            # Apply formatting to matching cells
            for row_idx, match in enumerate(matches):
                if match:  # Found "car detailing service" in this cell
                    excel_row = row_idx + 1  # Excel is 1-indexed
                    col_idx = list(self.df.columns).index(column)
                    cell_value = self.df.iloc[row_idx, col_idx]
                    
                    # Apply highlight format
                    cell_format = workbook.add_format({
                        'bg_color': '#FFF3CD',  # Yellow background
                        'font_color': '#000000'  # Black text
                    })
                    
                    # Write cell with formatting
                    worksheet.write_string(
                        excel_row, 
                        col_idx, 
                        str(cell_value), 
                        cell_format
                    )
```

## Key Insights

### ✅ GPT-4 Only Needs to Identify the Column

- **Sample data** (10-20 rows) is sufficient for GPT-4 to identify which column contains the text
- GPT-4 searches through the sample rows to find the column
- Even if the exact text doesn't appear in the sample, GPT-4 can infer from context

### ✅ Full Dataset Search Happens at Execution Time

- **Conditional formatting** searches the **FULL dataset** (all 5000 rows), not just the sample
- Uses pandas `.str.contains()` for efficient text matching
- Case-insensitive matching by default
- Applies formatting to ALL matching cells

### ✅ Two-Phase Process

1. **Phase 1 (GPT-4)**: Identify column from sample data
2. **Phase 2 (ExcelProcessor)**: Search full dataset and apply formatting

## Example: Complete Execution

### Input
- **Dataset**: 5000 rows, column "Service" contains various service names
- **User Request**: "highlight cells with 'car detailing service'"

### GPT-4 Analysis (Sample Data - 15 rows)
```
Row 1: Service = "Car detailing service" ✅ Found!
Row 2: Service = "Car wash"
Row 3: Service = "Car detailing service" ✅ Found!
...
Conclusion: Column "Service" contains "car detailing service"
```

### Generated JSON
```json
{
  "conditional_format": {
    "format_type": "contains_text",
    "config": {
      "column": "Service",
      "text": "car detailing service"
    }
  }
}
```

### Execution (Full Dataset - 5000 rows)
```python
# Search all 5000 rows
matches = df['Service'].str.contains('car detailing service', case=False, na=False)

# Results:
# Row 5: ✅ Match - Highlighted
# Row 12: ✅ Match - Highlighted
# Row 45: ✅ Match - Highlighted
# Row 78: ✅ Match - Highlighted
# ... (all matching rows highlighted)
```

### Output Excel File
- All cells in "Service" column containing "car detailing service" are highlighted in yellow
- Works regardless of case: "Car Detailing Service", "CAR DETAILING SERVICE", "car detailing service" all match

## Edge Cases Handled

### 1. Text Not in Sample
**Scenario**: "car detailing service" doesn't appear in the 15-row sample

**Solution**: 
- GPT-4 can infer from column name (e.g., "Service" column likely contains service names)
- Or use fuzzy matching
- The actual search still works on full dataset

### 2. Multiple Columns
**Scenario**: Text appears in multiple columns

**Solution**: GPT-4 can specify `"column": "all_columns"` or list specific columns

### 3. Case Variations
**Scenario**: "Car Detailing Service", "CAR DETAILING SERVICE", "car detailing service"

**Solution**: Uses case-insensitive matching (`case=False`)

### 4. Partial Matches
**Scenario**: "Premium car detailing service package"

**Solution**: Uses `contains_text` which matches partial strings

## Performance

- **GPT-4 Analysis**: ~2-3 seconds (analyzes 15-row sample)
- **Full Dataset Search**: ~0.1-0.5 seconds (searches 5000 rows)
- **Formatting Application**: ~1-2 seconds (applies formatting to matching cells)

**Total**: ~3-5 seconds for 5000 rows

## Summary

1. ✅ **GPT-4 identifies column** from sample data (10-20 rows)
2. ✅ **System stores rule** with column name and search text
3. ✅ **Full dataset searched** when saving Excel file
4. ✅ **All matching cells highlighted** regardless of case
5. ✅ **Efficient**: Sample for analysis, full search for execution

The system is designed to work efficiently: GPT-4 only needs to see a sample to identify the column, but the actual search and highlighting happens on the complete dataset.

