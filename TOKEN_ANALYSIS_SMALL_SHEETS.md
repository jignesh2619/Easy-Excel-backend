# Token Usage Analysis: Small Sheets (5-7 Columns)

## User Information
- **Sheet Size**: Typically 5-7 columns (small sheets)
- **Current Stats**: 188 requests, 4,056,809 tokens
- **Average**: 21,579 tokens per request

## Expected Token Usage for Small Sheets

### For 5-7 Column Sheets:
- **Sample Data**: 5-7 cols × 20 rows × 20 chars = 2,000-2,800 chars = **500-700 tokens**
- **System Prompt**: **3,000 tokens** (optimized)
- **User Prompt**: **30 tokens**
- **Additional Context**: 
  - Knowledge base: 200 tokens
  - Task guide: 100 tokens
  - Column mapping: 250-350 tokens (5-7 columns)
  - Sample explanation: 50 tokens
  - Few-shot examples: 600-900 tokens (if enabled)
  - **Total**: ~1,200-1,700 tokens
- **Response**: **600 tokens** (JSON action plan)

### Expected Total: ~5,500-6,000 tokens per request

## Actual vs Expected

- **Expected**: ~5,500-6,000 tokens
- **Actual**: 21,579 tokens
- **Difference**: **3.6x - 3.9x higher than expected!**

## Possible Causes

### 1. Multiple LLM Calls Per Request? ❌ NO
- Code shows only ONE LLM call per request
- Either ChartBot OR ActionPlanBot, not both
- Not the issue

### 2. System Prompt Size? ❌ NO
- System prompt is ~3,000 tokens (optimized)
- This is correct

### 3. Sample Data Size? ❌ NO
- With 5-7 columns, sample data should be ~500-700 tokens
- Not the issue

### 4. Additional Context Bloat? ⚠️ POSSIBLE
- Check if `get_prompt_with_context` is including too much
- Check if few-shot examples are adding excessive tokens
- Check if knowledge base summary is too large

### 5. Token Counting Issue? ⚠️ POSSIBLE
- Are we counting tokens correctly?
- Is there double counting?
- Are we including tokens from multiple operations in one request?

### 6. Old Stats Were Different? ⚠️ POSSIBLE
- Old: 179 requests, ~3.6M tokens = 20,112 tokens/request
- New: 188 requests, 4.056M tokens = 21,579 tokens/request
- Both are similarly high, suggesting this is the actual usage pattern

## Investigation Needed

### Check 1: Prompt Size
Look at what's actually being sent to OpenAI:
- System prompt: ~3,000 tokens ✓
- User prompt: Should include full context from `get_prompt_with_context`
- Check if `get_prompt_with_context` is adding excessive data

### Check 2: Actual Prompt Content
The `get_prompt_with_context` function includes:
- Full SYSTEM_PROMPT (very large, ~12,000 characters = ~3,000 tokens)
- User prompt
- Available columns info
- **Full sample data** (all 20 rows with all columns)
- Additional context (knowledge base, examples, etc.)

### Check 3: SYSTEM_PROMPT in prompts.py
The `get_prompt_with_context` function prepends `SYSTEM_PROMPT` which is HUGE:
- Contains extensive examples and instructions
- This might be adding significant tokens

### Check 4: Are We Sending System Prompt Twice?
- ActionPlanBot sends: `ACTION_PLAN_SYSTEM_PROMPT` (~3,000 tokens)
- `get_prompt_with_context` also includes `SYSTEM_PROMPT` (~3,000 tokens)
- **Are we sending BOTH?** This would double the system prompt!

## Critical Finding: Double System Prompt?

Looking at the code flow:
1. `app.py` calls `llm_agent.interpret_prompt()`
2. `llm_agent` routes to `action_plan_bot.generate_action_plan()`
3. `action_plan_bot` calls `get_prompt_with_context()` which includes `SYSTEM_PROMPT`
4. `action_plan_bot` then sends:
   - System message: `ACTION_PLAN_SYSTEM_PROMPT` (~3,000 tokens)
   - User message: `full_prompt` which includes `SYSTEM_PROMPT` again (~3,000 tokens)

**This could be sending the system prompt twice!**

## Revised Calculation

If system prompt is sent twice:
- System prompt (in system message): 3,000 tokens
- System prompt (in user message): 3,000 tokens
- Sample data: 500-700 tokens
- Additional context: 1,200-1,700 tokens
- User prompt: 30 tokens
- Response: 600 tokens
- **Total**: ~8,500-9,000 tokens

Still not 21,579, but closer. There might be:
- More context being added
- Larger responses
- Additional operations

## Next Steps

1. **Check if SYSTEM_PROMPT is being included in user message**
   - Look at `get_prompt_with_context` output
   - Check if it's duplicating system instructions

2. **Log actual prompt sizes**
   - Add logging to see actual token counts
   - Log prompt_tokens and completion_tokens separately

3. **Check if few-shot examples are too large**
   - Each example might be adding 300+ tokens
   - 3-5 examples = 900-1,500 tokens

4. **Verify token counting**
   - Ensure we're only counting one API call per request
   - Check if tokens are being accumulated incorrectly

## Recommendation

**Immediate Action**: Check if `SYSTEM_PROMPT` from `prompts.py` is being included in the user message when it shouldn't be. The `ACTION_PLAN_SYSTEM_PROMPT` should be the only system prompt, and the user message should NOT include the full `SYSTEM_PROMPT` again.

