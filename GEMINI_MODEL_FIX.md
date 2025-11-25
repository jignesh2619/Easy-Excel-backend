# 🔧 Gemini Model Quota Fix

## Issue: Quota Exceeded Error

You're getting a quota error because `gemini-2.0-flash-exp` is an **experimental model** that may not be available in the free tier or has different quota limits.

## ✅ Solution: Switch to Free-Tier Model

I've updated the default model to **`gemini-1.5-flash`** which is:
- ✅ Available in the free tier
- ✅ Stable and reliable
- ✅ Has generous free quota
- ✅ Fully supported by Google

## Changes Made

**File:** `backend/services/llm_agent.py`
- Changed default model from `gemini-2.0-flash-exp` to `gemini-1.5-flash`

## Next Steps

### 1. Restart Backend (Required)
The change won't take effect until you restart the backend server:

```powershell
# Stop current server (Ctrl+C)
# Then restart:
cd "C:\Users\manda\excel bot\backend"
py start_server.py
```

### 2. Verify It's Working
After restart, try uploading a file again. It should work now!

## Alternative: Use Environment Variable

If you want to use a different model, you can set it in your `.env` file:

```env
GEMINI_MODEL=gemini-1.5-flash
```

Then update the code to read from environment variable.

## Available Models

### Free Tier Models:
- ✅ `gemini-1.5-flash` - **Recommended** (Fast, free, stable)
- ✅ `gemini-1.5-pro` - More capable but slower

### Paid/Experimental Models:
- ⚠️ `gemini-2.0-flash-exp` - Experimental, may require paid tier
- ⚠️ `gemini-2.0-flash-thinking-exp` - Experimental

## Check Your Quota

Visit: https://ai.dev/usage?tab=rate-limit

This will show you:
- Your current usage
- Quota limits
- Available models

## Free Tier Limits (gemini-1.5-flash)

- **Requests per minute:** 15
- **Requests per day:** 1,500
- **Tokens per minute:** 1,000,000
- **Tokens per day:** 50,000,000

These limits are very generous for testing and development!

## If Still Getting Quota Errors

1. **Wait a few minutes** - Rate limits reset
2. **Check your API key** - Make sure it's valid
3. **Check billing** - Ensure your Google Cloud project has billing enabled (free tier still needs billing account)
4. **Try gemini-1.5-pro** - As an alternative

## Questions?

- Gemini API Docs: https://ai.google.dev/gemini-api/docs
- Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits
- Usage Dashboard: https://ai.dev/usage

---

**After restarting, your API should work with the free-tier model!** 🎉







