# EasyExcel Backend - Complete Capabilities List

## Overview
The EasyExcel backend can process Excel/CSV files using natural language prompts. It uses Google Gemini AI to interpret user requests and executes operations using Python pandas.

## Core Tasks Supported

### 1. **Data Cleaning** (`clean`)
- Remove duplicate rows
- Fix formatting (trim whitespace, normalize text)
- Handle missing values (fill with defaults)
- Remove specific characters from columns (e.g., remove dots from phone numbers)
- Replace characters (e.g., replace X with space)
- Normalize text (uppercase, lowercase, proper case)
- **Output**: Cleaned data rows (same structure, fewer/cleaned rows)

**Example Prompts:**
- "remove duplicates"
- "clean the data"
- "remove dot from phone numbers"
- "replace X with space"
- "fix formatting"

---

### 2. **Data Summarization** (`summarize`)
- Generate statistical summary (count, mean, std, min, max, quartiles)
- Describe data distribution
- **Output**: Summary statistics table

**Example Prompts:**
- "give me summary statistics"
- "describe the data"
- "what are the stats"

---

### 3. **Filtering** (`filter`)
- Filter rows based on conditions (>, <, ==, >=, <=, !=)
- Show only specific rows
- **Output**: Filtered data rows (same columns, fewer rows)

**Example Prompts:**
- "show rows where amount > 500"
- "filter rows with status = active"
- "show only sales > 1000"

---

### 4. **Grouping & Aggregation** (`group_by`)
- Group data by column(s)
- Aggregate functions: sum, mean, count, max, min
- Create pivot-like tables
- **Output**: Grouped and aggregated data

**Example Prompts:**
- "group by city and sum revenue"
- "count by category"
- "sum by department"

---

### 5. **Sorting** (`sort`)
- Sort by single or multiple columns
- Ascending/descending order
- Sort text, numbers, dates
- **Output**: Sorted data rows (same structure, reordered)

**Example Prompts:**
- "sort by amount descending"
- "sort from small to big"
- "order by name A to Z"

---

### 6. **Delete Column** (`delete_column`)
- Delete columns by name
- Delete columns by position (first, second, third, last, 2nd, 3rd, etc.)
- **Output**: Data without specified column

**Example Prompts:**
- "delete second column"
- "delete 2nd column"
- "remove column Age"
- "delete last column"

---

### 7. **Delete Rows** (`delete_rows`)
- Delete rows by index range
- Delete rows by position (first, second, etc.)
- Delete specific row indices
- **Output**: Data without specified rows

**Example Prompts:**
- "delete first row"
- "delete rows 1 to 10"
- "remove second row"

---

### 8. **Add Column** (`add_column`)
- Add new columns
- Set default values
- Specify position
- **Output**: Data with new column

**Example Prompts:**
- "add column Status"
- "add new column with default value"

---

### 9. **Add Row** (`add_row`)
- Add new rows to the sheet
- Specify position
- **Output**: Data with new row

**Example Prompts:**
- "add a new row"
- "insert row at position 5"

---

### 10. **Edit Cell** (`edit_cell`)
- Edit specific cell values
- Update by row index and column name
- **Output**: Data with edited cell

**Example Prompts:**
- "edit cell at row 5 column Name"
- "change value in cell"

---

### 11. **Clear Cell** (`clear_cell`)
- Clear specific cells (set to empty)
- **Output**: Data with cleared cell

**Example Prompts:**
- "clear cell at row 5"
- "empty cell"

---

### 12. **Auto Fill** (`auto_fill`)
- Auto-fill cells down a column
- **Output**: Data with auto-filled values

**Example Prompts:**
- "auto fill column"
- "fill down"

---

### 13. **Formatting** (`format`)
- Apply text formatting (bold, italic)
- Set colors (text color, background color)
- Alignment (left, center, right)
- Merge cells
- Wrap text
- **Output**: Data with formatting rules (applied when saving)

**Example Prompts:**
- "make Name column bold"
- "highlight column with red background"
- "center align Amount column"

---

### 14. **Conditional Formatting** (`conditional_format`)
- Highlight duplicates
- Highlight values greater/less than threshold
- **Output**: Data with conditional formatting rules

**Example Prompts:**
- "highlight duplicates"
- "highlight columns with phone numbers"
- "highlight values > 1000"

---

### 15. **Formulas** (`formula`)
Supports extensive formula operations:

#### Math Formulas:
- **sum**: Sum all values in a column
- **average/mean**: Calculate average
- **min**: Find minimum value
- **max**: Find maximum value
- **count**: Count non-null values
- **countif**: Count rows meeting condition
- **counta**: Count all non-empty values
- **unique**: Get unique values
- **round**: Round to decimal places

#### Text Functions:
- **concat**: Combine columns
- **textjoin**: Join with separator
- **left/right/mid**: Extract substrings
- **trim**: Remove whitespace
- **lower/upper/proper**: Change case
- **find/search**: Search text

#### Date Functions:
- **today/now**: Current date/time
- **year/month/day**: Extract date parts
- **datedif**: Calculate date differences

#### Logical Functions:
- **if**: Conditional logic
- **and/or/not**: Boolean operations

#### Lookup Functions:
- **vlookup/xlookup**: Find and return values

**Example Prompts:**
- "what's the sum of all amounts"
- "average of sales column"
- "count rows where status = active"
- "combine first and last name"

---

### 16. **Find Missing** (`find_missing`)
- Identify missing/null values
- **Output**: Report of missing values

**Example Prompts:**
- "find missing values"
- "show empty cells"

---

### 17. **Transform** (`transform`)
- Apply data transformations
- Normalize data
- Pivot operations
- **Output**: Transformed data

**Example Prompts:**
- "transform data"
- "normalize values"
- "pivot table"

---

## Chart Generation

All tasks can be combined with chart generation:
- **bar**: Bar chart (categorical data)
- **line**: Line chart (time series)
- **pie**: Pie chart (proportions)
- **histogram**: Distribution of numeric data
- **scatter**: Relationship between two variables

**Example Prompts:**
- "remove duplicates and create dashboard"
- "group by city and show chart"
- "filter data and visualize"

---

## Advanced Features

### 1. **Natural Language Understanding**
- Handles broken English, typos, slang
- Understands Indian-English patterns
- Fuzzy matching for column names
- Positional reference conversion (2nd → actual column name)

### 2. **Complete Dataset Context**
- Sends full Excel data (up to 1000 rows) to AI
- AI sees all column names, values, and patterns
- Better decision-making based on actual data

### 3. **Error Tolerance**
- Handles typos in column names
- Suggests nearest matches
- Infers meaning from context

### 4. **Token Usage Tracking**
- Accurate token calculation from Gemini API
- Per-user token tracking
- Token limits enforcement

---

## Current Limitations

1. **File Size**: Limited to 1000 rows sent to AI (for token management)
2. **File Formats**: Supports CSV, XLSX, XLS
3. **Charts**: Generated as images (PNG format)
4. **Formatting**: Stored but applied when saving Excel file

---

## Example Use Cases

1. **Data Cleaning**: "remove duplicates and fix formatting"
2. **Analysis**: "group by category and sum revenue, then create chart"
3. **Data Manipulation**: "delete second column, sort by amount, filter > 100"
4. **Formatting**: "highlight duplicates in email column"
5. **Calculations**: "what's the average sales by region"

---

## Technical Stack

- **Backend**: FastAPI (Python)
- **Data Processing**: Pandas, NumPy
- **AI**: Google Gemini 2.5 Flash Lite
- **Charts**: Matplotlib
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth

---

Last Updated: November 27, 2025

