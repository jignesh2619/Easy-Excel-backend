# 🔑 Get Your Google Gemini API Key

## Step-by-Step Instructions

### 1. Go to Google AI Studio
Visit: **https://makersuite.google.com/app/apikey**

### 2. Sign In
- Sign in with your Google account
- If you don't have a Google account, create one first

### 3. Create API Key
- Click on **"Create API Key"** or **"Get API Key"**
- You may be asked to create a Google Cloud project (just follow the prompts)
- Your API key will be displayed

### 4. Copy Your Key
- Copy the entire API key (it starts with `AIza...`)
- Keep it secure - don't share it publicly!

### 5. Add to .env File
Open the `.env` file in the `backend` folder and replace:
```
GEMINI_API_KEY=your_gemini_api_key_here
```
with:
```
GEMINI_API_KEY=AIzaSy...your-actual-key-here
```

## ✅ Quick Check

After adding your key, verify it works by running:
```powershell
py start_server.py
```

If the server starts without errors, your API key is working!

## 🔒 Security Note

- Never commit your `.env` file to Git (it's already in .gitignore)
- Don't share your API key publicly
- If your key is compromised, revoke it and create a new one



