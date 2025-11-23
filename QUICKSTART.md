# Quick Start Guide

Get EasyExcel backend running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Set Google Gemini API Key

Create a `.env` file in the `backend` directory:

```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

Get your API key from: https://makersuite.google.com/app/apikey

## Step 3: Start the Server

```bash
python app.py
```

Or with auto-reload:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Test the API

### Using curl:

```bash
# Health check
curl http://localhost:8000/health

# Process a file
curl -X POST "http://localhost:8000/process-file" \
  -F "file=@path/to/your/file.csv" \
  -F "prompt=Group by Region and sum Revenue"
```

### Using Python test script:

```bash
python test_example.py
```

This will:
- Create a sample CSV file
- Test multiple prompts
- Download processed files and charts

### Using Python requests:

```python
import requests

# Upload and process
with open('sample.csv', 'rb') as f:
    files = {'file': ('sample.csv', f, 'text/csv')}
    data = {'prompt': 'Group by Region and sum Revenue, create bar chart'}
    response = requests.post('http://localhost:8000/process-file', files=files, data=data)
    print(response.json())
```

## Example Prompts

Try these prompts with your Excel/CSV files:

1. **"Group by Region and sum Revenue, then create a bar chart"**
2. **"Clean the data - remove duplicates and fix formatting"**
3. **"Show me summary statistics for Revenue and Quantity"**
4. **"Filter rows where Revenue > 20000 and create a line chart"**
5. **"Find and report all missing values"**

## Project Structure Created

```
backend/
├── app.py                    ✓ FastAPI server
├── requirements.txt          ✓ Dependencies
├── services/
│   ├── llm_agent.py         ✓ LLM interpretation
│   ├── excel_processor.py   ✓ Data processing
│   ├── chart_builder.py     ✓ Chart generation
│   └── file_manager.py      ✓ File handling
├── utils/
│   ├── prompts.py           ✓ LLM prompts
│   └── validator.py         ✓ Validation
├── temp/                     ✓ Uploads (auto-created)
└── output/                   ✓ Results (auto-created)
    └── charts/
```

## Next Steps

1. ✅ Backend is ready!
2. Connect your frontend to `http://localhost:8000`
3. Use the `/process-file` endpoint
4. Download processed files and charts from returned URLs

## Troubleshooting

**Error: "LLM service not available"**
- Make sure `GEMINI_API_KEY` is set in `.env` file
- Get your key from: https://makersuite.google.com/app/apikey

**Error: "Module not found"**
- Run `pip install -r requirements.txt`

**Error: Port already in use**
- Change port in `app.py` or use: `uvicorn app:app --port 8001`

**Charts not generating**
- Make sure matplotlib backend is working
- Check that data has appropriate columns for chart type

## API Documentation

Once server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

