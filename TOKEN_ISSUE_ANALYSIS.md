# Token Usage Issue Analysis

## Problem Identified

**Actual Average: 21,579 tokens per request** (for 5-7 column sheets)
**Expected Average: ~6,000 tokens per request**

**Discrepancy: 3.6x higher than expected!**

## Root Cause

The system is sending **TWO massive prompts**:

1. **System Message**: `ACTION_PLAN_SYSTEM_PROMPT` (~3,000 tokens)
2. **User Message**: `SYSTEM_PROMPT` (from `utils/prompts.py`) + `get_prompt_with_context()` output

The `get_prompt_with_context()` function includes the ENTIRE `SYSTEM_PROMPT` from `utils/prompts.py` which is **1,500+ lines** of instructions, examples, and rules. This is being sent in the USER message, effectively duplicating system instructions.

## Token Breakdown (Actual)

For a 5-7 column sheet with 20 sample rows:

1. **System Message (ACTION_PLAN_SYSTEM_PROMPT)**: ~3,000 tokens
2. **User Message Components**:
   - `SYSTEM_PROMPT` (from utils/prompts.py): **~15,000+ tokens** ⚠️ THIS IS THE PROBLEM
   - Sample data (5-7 cols, 20 rows): ~500-1,250 tokens
   - Column info: ~100 tokens
   - User prompt: ~30 tokens
   - Additional context (KB, examples, etc.): ~1,000 tokens
   - **Total User Message: ~17,630 tokens**
3. **Response**: ~600 tokens

**Total: ~21,230 tokens** (matches the 21,579 average!)

## The Fix

The `SYSTEM_PROMPT` from `utils/prompts.py` should NOT be included in the user message when using ActionPlanBot, because:
- ActionPlanBot already has its own `ACTION_PLAN_SYSTEM_PROMPT`
- The `SYSTEM_PROMPT` is redundant and massive
- It's causing 3x more tokens than necessary

## Solution

Modify `get_prompt_with_context()` to NOT include `SYSTEM_PROMPT` when called from ActionPlanBot, OR create a lightweight version that only includes essential context.

## Expected After Fix

- System Message: ~3,000 tokens
- User Message: ~2,000 tokens (sample data + context, no SYSTEM_PROMPT)
- Response: ~600 tokens
- **Total: ~5,600 tokens per request** ✅

This would reduce token usage by **74%** (from 21,579 to ~5,600 tokens)!

