# EasyExcel Backend API

AI-powered Excel/CSV processing backend service built with FastAPI.

## Features

- 🤖 **AI-Powered Prompt Interpretation**: Uses Google Gemini 2.5 Flash Lite to interpret natural language prompts
- 📊 **Excel/CSV Processing**: Supports XLSX, XLS, and CSV file formats
- 📈 **Chart Generation**: Automatic chart generation (bar, line, pie) using matplotlib
- 🧹 **Data Cleaning**: Remove duplicates, fix formatting, handle missing values
- 📉 **Data Analysis**: Group by, aggregate, filter, summarize operations
- ✅ **Validation**: Comprehensive file and data validation
- 🔒 **File Management**: Secure file handling with automatic cleanup

## Project Structure

```
backend/
├── app.py                 # FastAPI main server
├── requirements.txt       # Python dependencies
├── services/
│   ├── llm_agent.py      # LLM interpretation service
│   ├── excel_processor.py # Data processing engine
│   ├── chart_builder.py  # Chart generation
│   └── file_manager.py   # File handling
├── utils/
│   ├── prompts.py        # LLM prompt templates
│   └── validator.py      # Data validation
├── temp/                 # Temporary uploaded files
└── output/               # Processed files and charts
    └── charts/
```

## Installation

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```
   
   Get your Gemini API key from: https://makersuite.google.com/app/apikey

3. **Run the Server**:
   ```bash
   python app.py
   # Or with uvicorn directly:
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Health Check
```bash
GET /health
```

### Process File
```bash
POST /process-file
Content-Type: multipart/form-data

Parameters:
- file: Excel/CSV file (required)
- prompt: Natural language prompt (required)
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/process-file" \
  -F "file=@sample.csv" \
  -F "prompt=Group by Region and sum Revenue, then create a bar chart"
```

**Example Response**:
```json
{
  "status": "success",
  "processed_file_url": "/download/processed_20241121_123456_sample.xlsx",
  "chart_url": "/download/charts/chart_20241121_123456.png",
  "summary": [
    "Loaded 8 rows and 5 columns",
    "Grouped by 'Region' with sum aggregation",
    "Result: 4 groups",
    "Generated bar chart: chart_20241121_123456.png"
  ],
  "action_plan": {
    "task": "group_by",
    "columns_needed": ["Region", "Revenue"],
    "chart_type": "bar",
    "group_by_column": "Region",
    "aggregate_function": "sum",
    "aggregate_column": "Revenue"
  }
}
```

### Download Files
```bash
GET /download/{filename}
GET /download/charts/{filename}
```

## Usage Examples

### Example Prompts

1. **Group By Operation**:
   ```
   "Group by Region and sum Revenue, then create a bar chart"
   ```

2. **Data Cleaning**:
   ```
   "Clean the data - remove duplicates and fix formatting"
   ```

3. **Summary Statistics**:
   ```
   "Show me summary statistics for Revenue and Quantity"
   ```

4. **Filtering**:
   ```
   "Filter rows where Revenue is greater than 20000 and create a line chart"
   ```

5. **Find Missing Values**:
   ```
   "Find and report all missing values in the dataset"
   ```

## Action Plan Format

The LLM returns structured action plans in this format:

```json
{
  "task": "group_by|clean|summarize|filter|find_missing|transform",
  "columns_needed": ["Column1", "Column2"],
  "chart_type": "bar|line|pie|none",
  "steps": ["step1", "step2"],
  "group_by_column": "ColumnName",
  "aggregate_function": "sum|mean|count|max|min",
  "aggregate_column": "ColumnName",
  "filters": {
    "column": "ColumnName",
    "condition": ">|>=|<|<=|==|!=",
    "value": "filter_value"
  }
}
```

## Testing

Run the example test script:

```bash
python test_example.py
```

This will:
1. Check API health
2. Create a sample CSV file
3. Test various prompts
4. Download processed files and charts

## Architecture

### Data Flow

1. **Upload**: User uploads file + prompt
2. **Validation**: File format, size, and content validation
3. **LLM Interpretation**: Prompt converted to structured action plan
4. **Processing**: Pandas executes operations on data
5. **Chart Generation**: Matplotlib creates charts if needed
6. **Response**: Processed file and chart URLs returned

### Key Principles

- **LLM Never Touches Data**: LLM only generates action plans, Python handles all operations
- **Deterministic**: All operations are reproducible
- **Validated**: Comprehensive validation at each step
- **Secure**: Automatic file cleanup, size limits

## Configuration

Edit `.env` file for configuration:

```env
GEMINI_API_KEY=your_key_here
PORT=8000
HOST=0.0.0.0
MAX_FILE_SIZE=52428800  # 50MB
CLEANUP_DAYS=7
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

## Error Handling

The API returns user-friendly errors:
- `400`: Invalid file format, missing columns, validation errors
- `500`: Processing errors, LLM failures

All errors include descriptive messages.

## Production Considerations

- Set `GEMINI_API_KEY` environment variable securely
- Configure CORS appropriately
- Use proper file storage (S3, etc.) for production
- Implement rate limiting
- Add authentication/authorization
- Set up logging and monitoring
- Use production WSGI server (Gunicorn)

## License

MIT License

