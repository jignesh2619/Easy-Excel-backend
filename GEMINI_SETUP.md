# Google Gemini API Setup Guide

## ✅ Code Updated Successfully!

I've updated the backend to use **Google Gemini 2.5 Flash Lite** instead of OpenAI. Here's what changed:

### Changes Made:

1. **Updated `requirements.txt`**:
   - Removed: `openai==1.3.7`
   - Added: `google-generativeai==0.3.2`

2. **Updated `services/llm_agent.py`**:
   - Changed from OpenAI API to Google Gemini API
   - Model: `gemini-2.0-flash-exp` (or `gemini-1.5-flash` for stable version)
   - Updated API initialization and response handling

3. **Updated Configuration**:
   - Environment variable changed from `OPENAI_API_KEY` to `GEMINI_API_KEY`
   - Updated all documentation files

## 📋 Installation Steps

### Step 1: Install Python (if not installed)

1. Download Python from: https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```bash
   python --version
   ```

### Step 2: Install Dependencies

Navigate to the backend folder and install all dependencies:

```bash
cd "C:\Users\manda\excel bot\backend"
pip install -r requirements.txt
```

Or if `pip` doesn't work:
```bash
python -m pip install -r requirements.txt
```

Or with Python 3:
```bash
python3 -m pip install -r requirements.txt
```

### Step 3: Get Google Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### Step 4: Create .env File

Create a `.env` file in the `backend` folder with:

```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
HOST=0.0.0.0
```

**Important**: Replace `your_gemini_api_key_here` with your actual API key!

### Step 5: Test the Setup

Once you have the API key and dependencies installed:

```bash
cd "C:\Users\manda\excel bot\backend"
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔍 Model Options

You can change the Gemini model in `services/llm_agent.py`:

- `gemini-2.0-flash-exp` - Latest experimental (fastest)
- `gemini-1.5-flash` - Stable version (recommended for production)
- `gemini-1.5-pro` - More powerful (slower, more expensive)

Current setting: `gemini-2.0-flash-exp`

## 📝 Quick Test

Once everything is set up, test with:

```bash
python test_example.py
```

## 🔧 Troubleshooting

**Issue: "Python was not found"**
- Install Python from python.org
- Make sure "Add Python to PATH" is checked during installation

**Issue: "Module not found"**
- Run: `pip install -r requirements.txt`
- Make sure you're in the `backend` directory

**Issue: "GEMINI_API_KEY not found"**
- Create `.env` file in `backend` folder
- Add: `GEMINI_API_KEY=your_actual_key`

**Issue: "Failed to initialize Gemini model"**
- Check your API key is correct
- Verify you have internet connection
- Check API quota/limits at: https://makersuite.google.com/app/apikey

## ✨ What's Different from OpenAI?

- **Cost**: Gemini Flash is generally more cost-effective
- **Speed**: Optimized for low-latency responses
- **Context**: Supports up to 1 million tokens context window
- **Multimodal**: Can handle images, audio, video (though we're using text-only)

## 🚀 Ready to Go!

Once you:
1. ✅ Install Python
2. ✅ Install dependencies: `pip install -r requirements.txt`
3. ✅ Get Gemini API key
4. ✅ Create `.env` file with your key

You're all set! Run `python app.py` to start the server.








