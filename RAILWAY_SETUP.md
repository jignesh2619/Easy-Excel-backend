# Railway Setup - Correct Commands

## Setting Environment Variables

Railway CLI has different syntax. Here are the correct ways:

### Option 1: Use Railway Dashboard (Easiest) ✅

1. Go to: https://railway.com/project/3cfc6cac-deaa-41e2-9577-d1884448b361
2. Click on your service/project
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Add each variable:

```
GEMINI_API_KEY = your_gemini_key
PAYPAL_CLIENT_ID = ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL
PAYPAL_CLIENT_SECRET = EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr
PAYPAL_MODE = sandbox
PORT = 8000
```

### Option 2: Use Railway CLI (Correct Syntax)

The correct syntax is:
```bash
railway variables
```

This opens an interactive editor. Or use:
```bash
railway variables --help
```

To see available options.

### Option 3: Create .env file (Railway auto-detects)

Create a `.env` file in the backend folder (Railway will use it):

```env
GEMINI_API_KEY=your_gemini_key
PAYPAL_CLIENT_ID=ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL
PAYPAL_CLIENT_SECRET=EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr
PAYPAL_MODE=sandbox
PORT=8000
```

Then deploy:
```bash
npx @railway/cli up
```

## Recommended: Use Dashboard

The Railway dashboard is the easiest way to set variables. Just go to your project and add them in the Variables tab.






