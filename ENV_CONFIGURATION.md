# Environment Configuration Guide

This document explains all environment variables used in the EasyExcel backend.

## Quick Reference

### Current Setup (OpenAI)
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### Alternative Setup (Gemini - if you want to switch)
```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

**⚠️ IMPORTANT:** The backend currently uses **OpenAI** by default. If you have Gemini configured, it won't be used unless you modify the code.

---

## Complete Environment Variables

### OpenAI Configuration (Currently Active)

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Default model for simple operations
# The system uses hybrid routing:
#   - Simple operations → OPENAI_MODEL (default: gpt-4o-mini)
#   - Complex operations → gpt-4o (automatic)
# 
# Options:
#   - gpt-4o-mini (recommended - cost-effective, ~$0.20-0.30 per 1M tokens)
#   - gpt-4o (more accurate but expensive, ~$5-7 per 1M tokens)
#   - gpt-4-turbo (good for long context)
OPENAI_MODEL=gpt-4o-mini
```

### Gemini Configuration (Not Currently Used)

```bash
# Google Gemini API Key (if you want to use Gemini instead of OpenAI)
GEMINI_API_KEY=your_gemini_api_key_here

# Gemini Model Selection
# Options:
#   - gemini-2.5-flash-lite (cheapest, fastest)
#   - gemini-2.5-flash (better accuracy, still cheap)
#   - gemini-1.5-pro (best accuracy, more expensive)
GEMINI_MODEL=gemini-2.5-flash-lite
```

**Note:** The backend code currently only supports OpenAI. Gemini configuration won't work unless you modify the codebase.

---

## Server Configuration

```bash
# Server port (default: 8000)
PORT=8000

# Server host (default: 0.0.0.0 for all interfaces)
HOST=0.0.0.0
```

---

## File Management

```bash
# Maximum file size in bytes (default: 50MB)
MAX_FILE_SIZE=52428800

# Number of days to keep temporary files (default: 7)
CLEANUP_DAYS=7
```

---

## Supabase Configuration (Authentication & Database)

```bash
# Supabase project URL
SUPABASE_URL=https://your-project-id.supabase.co

# Supabase service role key (for backend operations)
SUPABASE_KEY=your_supabase_service_role_key_here
```

---

## PayPal Configuration (Payment Processing)

```bash
# PayPal API credentials
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here

# PayPal environment (sandbox for testing, live for production)
PAYPAL_MODE=sandbox

# PayPal subscription plan IDs
PAYPAL_PLAN_ID_STARTER=P-XXXXXXXXXX
PAYPAL_PLAN_ID_PRO=P-XXXXXXXXXX

# PayPal redirect URLs
PAYPAL_RETURN_URL=http://localhost:5173/payment/success
PAYPAL_CANCEL_URL=http://localhost:5173/payment/cancel

# Optional: PayPal webhook ID for webhook verification
PAYPAL_WEBHOOK_ID=your_webhook_id_here
```

---

## Model Cost Comparison

### OpenAI Models (Currently Used)

| Model | Input (per 1M) | Output (per 1M) | Typical Cost | Use Case |
|-------|----------------|-----------------|--------------|----------|
| **gpt-4o-mini** | $0.15 | $0.60 | ~$0.20-0.30 | Simple operations (default) |
| **gpt-4o** | $2.50 | $10.00 | ~$5-7 | Complex operations (auto-selected) |
| gpt-4-turbo | $10.00 | $30.00 | ~$15-20 | Long context needs |

### Gemini Models (Not Currently Used)

| Model | Input (per 1M) | Output (per 1M) | Typical Cost | Use Case |
|-------|----------------|-----------------|--------------|----------|
| gemini-2.5-flash-lite | $0.075 | $0.30 | ~$0.10-0.15 | Cheapest option |
| gemini-2.5-flash | $0.15 | $0.60 | ~$0.20-0.30 | Better accuracy |
| gemini-1.5-pro | $1.25 | $5.00 | ~$2-3 | Best accuracy |

---

## Hybrid Model Routing

The system automatically routes requests to the appropriate model:

### Simple Operations → gpt-4o-mini
- Single column operations (add, delete, rename)
- Simple formatting
- Basic cell editing
- Single conditional format
- Simple formulas

### Complex Operations → gpt-4o
- Multiple operations in one prompt ("add column and then sort")
- Complex formulas (VLOOKUP, nested IF)
- Advanced conditional formatting (multiple conditions)
- Data analysis operations
- Ambiguous column references in large datasets

**Cost Impact:**
- ~80% of requests use gpt-4o-mini (cheap)
- ~20% of requests use gpt-4o (expensive but necessary)
- **Overall savings: ~60-70% vs. using gpt-4o for everything**

---

## How to Check Current Configuration

### On Local Machine
```bash
# Check if .env file exists
cat .env

# Or check specific variable
grep OPENAI_MODEL .env
```

### On Server (DigitalOcean Droplet)
```bash
# SSH into server
ssh root@your-server-ip

# Check .env file
cat /opt/easyexcel-backend/.env

# Check specific variable
grep OPENAI_MODEL /opt/easyexcel-backend/.env
```

---

## Troubleshooting

### Issue: Still using gpt-4o even though OPENAI_MODEL=gpt-4o-mini

**Solution:** The code has been updated to:
1. Default to `gpt-4o-mini` in all classes
2. Use hybrid routing (simple → mini, complex → gpt-4o)
3. Properly read from environment variables

**Check:**
1. Restart the backend service after updating .env
2. Check logs to see which model is being used
3. Verify .env file is in the correct location

### Issue: Want to use Gemini instead of OpenAI

**Solution:** The backend currently only supports OpenAI. To use Gemini:
1. You would need to modify the codebase to use Gemini API
2. Or wait for future updates that add Gemini support

---

## Example .env File (OpenAI Setup)

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Server Configuration
PORT=8000
HOST=0.0.0.0

# File Management
MAX_FILE_SIZE=52428800
CLEANUP_DAYS=7

# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# PayPal Configuration
PAYPAL_CLIENT_ID=xxxxx
PAYPAL_CLIENT_SECRET=xxxxx
PAYPAL_MODE=sandbox
PAYPAL_PLAN_ID_STARTER=P-XXXXX
PAYPAL_PLAN_ID_PRO=P-XXXXX
PAYPAL_RETURN_URL=http://localhost:5173/payment/success
PAYPAL_CANCEL_URL=http://localhost:5173/payment/cancel
```

---

## Summary

- **Current Setup:** OpenAI with hybrid model routing
- **Default Model:** gpt-4o-mini (for simple operations)
- **Complex Operations:** Automatically use gpt-4o
- **Gemini:** Not currently supported (code only uses OpenAI)
- **Cost Savings:** ~60-70% with hybrid routing vs. all gpt-4o

