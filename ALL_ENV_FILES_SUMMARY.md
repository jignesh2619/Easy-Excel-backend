# All Environment Variable Files Summary

This document clarifies all .env configurations to resolve confusion between OpenAI and Gemini setups.

---

## Current Status

**✅ ACTIVE:** OpenAI with hybrid model routing (gpt-4o-mini + gpt-4o)  
**❌ NOT USED:** Gemini (code doesn't support it, even if env vars are set)

---

## Complete .env File Template

### For Production (OpenAI - Currently Active)

```bash
# ============================================
# OpenAI API Configuration (ACTIVE)
# ============================================
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# ============================================
# Server Configuration
# ============================================
PORT=8000
HOST=0.0.0.0

# ============================================
# File Management
# ============================================
MAX_FILE_SIZE=52428800
CLEANUP_DAYS=7

# ============================================
# Supabase Configuration (Authentication & Database)
# ============================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_service_role_key_here

# ============================================
# PayPal Configuration (Payment Processing)
# ============================================
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here
PAYPAL_MODE=sandbox
PAYPAL_PLAN_ID_STARTER=P-XXXXXXXXXX
PAYPAL_PLAN_ID_PRO=P-XXXXXXXXXX
PAYPAL_RETURN_URL=http://localhost:5173/payment/success
PAYPAL_CANCEL_URL=http://localhost:5173/payment/cancel
PAYPAL_WEBHOOK_ID=your_webhook_id_here
```

---

## Gemini Configuration (NOT USED - For Reference Only)

**⚠️ WARNING:** These variables won't work because the backend code only uses OpenAI API.

```bash
# ============================================
# Gemini API Configuration (NOT ACTIVE)
# ============================================
# These are ignored by the current codebase
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

**Why it's confusing:**
- Some documentation mentions Gemini
- Some old .env files might have Gemini variables
- But the code only calls OpenAI API

**Solution:** 
- Remove Gemini variables if present
- They won't cause errors, just won't be used
- Focus on OpenAI configuration only

---

## Environment Variable Reference

### OpenAI Variables (REQUIRED - Currently Used)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | None | Your OpenAI API key |
| `OPENAI_MODEL` | ❌ No | `gpt-4o-mini` | Default model for simple operations |

**Note:** Complex operations automatically use `gpt-4o` regardless of `OPENAI_MODEL`.

### Gemini Variables (NOT USED - Ignored by Code)

| Variable | Status | Description |
|----------|--------|-------------|
| `GEMINI_API_KEY` | ❌ Ignored | Won't be used by current code |
| `GEMINI_MODEL` | ❌ Ignored | Won't be used by current code |

### Server Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | ❌ No | `8000` | Server port |
| `HOST` | ❌ No | `0.0.0.0` | Server host |

### File Management Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAX_FILE_SIZE` | ❌ No | `52428800` | Max file size in bytes (50MB) |
| `CLEANUP_DAYS` | ❌ No | `7` | Days to keep temp files |

### Supabase Variables (Required for Auth)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ Yes | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ Yes | Supabase service role key |

### PayPal Variables (Required for Payments)

| Variable | Required | Description |
|----------|----------|-------------|
| `PAYPAL_CLIENT_ID` | ✅ Yes | PayPal API client ID |
| `PAYPAL_CLIENT_SECRET` | ✅ Yes | PayPal API secret |
| `PAYPAL_MODE` | ❌ No | `sandbox` or `live` |
| `PAYPAL_PLAN_ID_STARTER` | ✅ Yes | Starter plan ID |
| `PAYPAL_PLAN_ID_PRO` | ✅ Yes | Pro plan ID |
| `PAYPAL_RETURN_URL` | ❌ No | Success redirect URL |
| `PAYPAL_CANCEL_URL` | ❌ No | Cancel redirect URL |
| `PAYPAL_WEBHOOK_ID` | ❌ No | Webhook ID (optional) |

---

## Location of .env Files

### Local Development
```
backend/.env
```

### Production Server (DigitalOcean)
```
/opt/easyexcel-backend/.env
```

### How to Check Current Configuration

**On Server:**
```bash
ssh root@your-server-ip
cat /opt/easyexcel-backend/.env
```

**Check Specific Variable:**
```bash
grep OPENAI_MODEL /opt/easyexcel-backend/.env
```

---

## Model Configuration Explained

### Hybrid Model Routing (Current Implementation)

The system uses **two models** automatically:

1. **gpt-4o-mini** (default)
   - Used for: Simple operations
   - Cost: ~$0.20-0.30 per 1M tokens
   - Examples: "Delete column A", "Rename column", "Make header bold"

2. **gpt-4o** (automatic for complex)
   - Used for: Complex operations
   - Cost: ~$5-7 per 1M tokens
   - Examples: "Add column and then sort and highlight", "Create VLOOKUP formula"

**How it works:**
- System analyzes the prompt
- Routes to appropriate model automatically
- No manual configuration needed
- `OPENAI_MODEL` only sets the default (mini)

---

## Common Confusion Points

### ❌ "I have Gemini configured but it's not working"

**Answer:** The backend code only uses OpenAI. Gemini variables are ignored.

**Solution:** Use OpenAI configuration instead.

### ❌ "Why is it still using gpt-4o when I set OPENAI_MODEL=gpt-4o-mini?"

**Answer:** Complex operations automatically use gpt-4o for better accuracy.

**Solution:** This is intentional and correct behavior. Simple operations use mini.

### ❌ "I see both OpenAI and Gemini in my .env, which one is used?"

**Answer:** Only OpenAI is used. Gemini variables can be removed.

**Solution:** Keep only OpenAI variables, remove Gemini ones.

---

## Quick Setup Checklist

### Minimum Required Variables
```bash
✅ OPENAI_API_KEY
✅ SUPABASE_URL
✅ SUPABASE_KEY
✅ PAYPAL_CLIENT_ID
✅ PAYPAL_CLIENT_SECRET
✅ PAYPAL_PLAN_ID_STARTER
✅ PAYPAL_PLAN_ID_PRO
```

### Recommended Variables
```bash
✅ OPENAI_MODEL=gpt-4o-mini
✅ PORT=8000
✅ HOST=0.0.0.0
✅ MAX_FILE_SIZE=52428800
✅ CLEANUP_DAYS=7
```

### Optional Variables
```bash
PAYPAL_MODE=sandbox
PAYPAL_RETURN_URL=...
PAYPAL_CANCEL_URL=...
PAYPAL_WEBHOOK_ID=...
```

---

## Summary

### What You Need
- ✅ OpenAI API key and model setting
- ✅ Supabase credentials
- ✅ PayPal credentials

### What You DON'T Need
- ❌ Gemini variables (code doesn't use them)
- ❌ Complex model routing configuration (automatic)

### Current Setup
- **Model:** Hybrid routing (gpt-4o-mini + gpt-4o)
- **Default:** gpt-4o-mini (set via OPENAI_MODEL)
- **Complex:** gpt-4o (automatic, no config needed)
- **Cost Savings:** ~60-70% vs. all gpt-4o

---

## Need Help?

1. Check `ENV_CONFIGURATION.md` for detailed explanations
2. Check `HYBRID_MODEL_IMPLEMENTATION.md` for technical details
3. Check server logs: `journalctl -u easyexcel-backend -f`
4. Verify .env file location and permissions

