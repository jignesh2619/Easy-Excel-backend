# Token Usage Estimation Guide

## Overview
This document provides detailed token usage estimates for processing Excel/CSV files with EasyExcel AI.

## Token Calculation Formula
**Total Tokens = System Prompt + User Prompt + Sample Data + Response**

---

## 1. System Prompt Tokens

### ActionPlanBot System Prompt
- **Character Count**: ~12,000 characters (after optimization)
- **Estimated Tokens**: ~3,000 tokens (using ~4 chars/token ratio)
- **Note**: This is the optimized version after reducing redundant examples

### ChartBot System Prompt
- **Character Count**: ~3,000 characters
- **Estimated Tokens**: ~750 tokens

---

## 2. User Prompt Tokens

### Typical User Prompts
- **Short prompts** (e.g., "remove duplicates"): 20-50 characters → **5-12 tokens**
- **Medium prompts** (e.g., "filter rows where amount > 1000"): 50-100 characters → **12-25 tokens**
- **Long prompts** (e.g., "create a dashboard with sales by region and highlight top performers"): 100-200 characters → **25-50 tokens**

### Average User Prompt: **~30 tokens**

---

## 3. Sample Data Tokens (Sheet Data)

### Sample Selection Strategy
- **Maximum rows sent**: 20 rows (configured in `SampleSelector`)
- **All columns preserved**: Yes, all columns from the original sheet are included
- **Data truncation**: Values longer than 300 characters are truncated

### Token Calculation for Sample Data

#### Small Sheet (5 columns, 20 sample rows)
- **Columns**: 5 columns
- **Average value length**: 20 characters per cell
- **Total characters**: 5 columns × 20 rows × 20 chars = 2,000 characters
- **Tokens**: ~500 tokens

#### Medium Sheet (10 columns, 20 sample rows)
- **Columns**: 10 columns
- **Average value length**: 25 characters per cell
- **Total characters**: 10 columns × 20 rows × 25 chars = 5,000 characters
- **Tokens**: ~1,250 tokens

#### Large Sheet (20 columns, 20 sample rows)
- **Columns**: 20 columns
- **Average value length**: 30 characters per cell
- **Total characters**: 20 columns × 20 rows × 30 chars = 12,000 characters
- **Tokens**: ~3,000 tokens

#### Very Large Sheet (50 columns, 20 sample rows)
- **Columns**: 50 columns
- **Average value length**: 35 characters per cell
- **Total characters**: 50 columns × 20 rows × 35 chars = 35,000 characters
- **Tokens**: ~8,750 tokens

### Average Sample Data: **~2,000 tokens** (for typical 10-15 column sheets)

---

## 4. Additional Context Tokens

### Knowledge Base Summary
- **Estimated**: ~200 tokens

### Task Decision Guide
- **Estimated**: ~100 tokens

### Column Mapping Info
- **Estimated**: ~50 tokens per column
- **For 10 columns**: ~500 tokens

### Few-Shot Examples (if enabled)
- **Per example**: ~300 tokens
- **Typical**: 2-3 examples = **600-900 tokens**

### Sample Explanation
- **Estimated**: ~50 tokens

### Total Additional Context: **~1,000-1,500 tokens**

---

## 5. Response Tokens

### Action Plan Response
- **Simple operations** (e.g., remove duplicates): 200-400 tokens
- **Medium operations** (e.g., filter + sort): 400-800 tokens
- **Complex operations** (e.g., multiple formulas + formatting): 800-1,500 tokens

### Average Response: **~600 tokens**

---

## 6. Total Token Usage Estimates

### Scenario 1: Simple Operation (Small Sheet)
- System Prompt: 3,000 tokens
- User Prompt: 30 tokens
- Sample Data (5 cols): 500 tokens
- Additional Context: 1,000 tokens
- Response: 400 tokens
- **Total: ~4,930 tokens**

### Scenario 2: Medium Operation (Medium Sheet) ⭐ MOST COMMON
- System Prompt: 3,000 tokens
- User Prompt: 30 tokens
- Sample Data (10 cols): 1,250 tokens
- Additional Context: 1,200 tokens
- Response: 600 tokens
- **Total: ~6,080 tokens**

### Scenario 3: Complex Operation (Large Sheet)
- System Prompt: 3,000 tokens
- User Prompt: 50 tokens
- Sample Data (20 cols): 3,000 tokens
- Additional Context: 1,500 tokens
- Response: 1,200 tokens
- **Total: ~8,750 tokens**

### Scenario 4: Very Complex Operation (Very Large Sheet)
- System Prompt: 3,000 tokens
- User Prompt: 50 tokens
- Sample Data (50 cols): 8,750 tokens
- Additional Context: 1,500 tokens
- Response: 1,500 tokens
- **Total: ~14,800 tokens**

---

## 7. Token Usage by Operation Type

### File Processing (Upload + Process)
- **Average**: ~6,000-8,000 tokens per sheet
- **Range**: 4,000-15,000 tokens depending on sheet size

### Data Processing (Chat-based operations)
- **Average**: ~5,000-7,000 tokens per operation
- **Range**: 3,000-12,000 tokens depending on complexity

### Chart Generation
- **Average**: ~4,000-6,000 tokens per chart
- **Range**: 3,000-10,000 tokens depending on data size

---

## 8. Cost Estimation (GPT-4o-mini)

### Pricing (as of 2024)
- **Input tokens**: $0.15 per 1M tokens
- **Output tokens**: $0.60 per 1M tokens

### Cost per Operation

#### Simple Operation (5,000 tokens total, 4,500 input + 500 output)
- Input cost: (4,500 / 1,000,000) × $0.15 = $0.000675
- Output cost: (500 / 1,000,000) × $0.60 = $0.0003
- **Total: ~$0.001 per operation**

#### Medium Operation (6,000 tokens total, 5,400 input + 600 output)
- Input cost: (5,400 / 1,000,000) × $0.15 = $0.00081
- Output cost: (600 / 1,000,000) × $0.60 = $0.00036
- **Total: ~$0.0012 per operation**

#### Complex Operation (9,000 tokens total, 8,100 input + 900 output)
- Input cost: (8,100 / 1,000,000) × $0.15 = $0.001215
- Output cost: (900 / 1,000,000) × $0.60 = $0.00054
- **Total: ~$0.0018 per operation**

### Cost for 50 Sheets (Average 6,000 tokens each)
- **Total tokens**: 50 × 6,000 = 300,000 tokens
- **Input tokens**: ~270,000 tokens
- **Output tokens**: ~30,000 tokens
- **Input cost**: (270,000 / 1,000,000) × $0.15 = **$0.0405**
- **Output cost**: (30,000 / 1,000,000) × $0.60 = **$0.018**
- **Total cost: ~$0.06 for 50 sheets**

---

## 9. Optimization Impact

### Before Optimization
- **System Prompt**: ~5,000 tokens (estimated)
- **Average Total**: ~8,000-10,000 tokens per operation

### After Optimization (Current)
- **System Prompt**: ~3,000 tokens (reduced by ~40%)
- **Average Total**: ~6,000-8,000 tokens per operation
- **Savings**: ~2,000 tokens per operation (~25% reduction)

### Cost Savings for 50 Sheets
- **Before**: 50 × 9,000 = 450,000 tokens → ~$0.09
- **After**: 50 × 6,000 = 300,000 tokens → ~$0.06
- **Savings: ~$0.03 (33% cost reduction)**

---

## 10. Key Takeaways

1. **System Prompt**: ~3,000 tokens (optimized, was ~5,000)
2. **Sample Data**: ~500-8,750 tokens (depends on columns, max 20 rows)
3. **Average Operation**: ~6,000 tokens
4. **Cost per Operation**: ~$0.001-0.002
5. **Cost for 50 Sheets**: ~$0.06

### Recommendations
- ✅ System prompt optimization complete (saved ~2,000 tokens)
- ✅ Sample size limited to 20 rows (prevents token explosion)
- ✅ Value truncation at 300 chars (prevents very long text bloat)
- ⚠️ Consider further reducing sample rows for very wide sheets (50+ columns)
- ⚠️ Monitor actual token usage vs estimates to fine-tune

---

## 11. Monitoring Token Usage

Use the new `/api/users/token-usage` endpoint to:
- Track actual token usage per operation
- Compare estimates vs actuals
- Identify operations consuming excessive tokens
- Monitor cost trends over time

---

## 12. Example Token Breakdown (Real Operation)

```
Operation: "Remove duplicates and highlight Pass in green"
Sheet: 18 rows, 3 columns

Breakdown:
- System Prompt: 3,000 tokens
- User Prompt: 25 tokens ("Remove duplicates and highlight Pass in green")
- Sample Data: 18 rows × 3 cols × 20 chars = 1,080 chars → 270 tokens
- Additional Context: 1,200 tokens
- Response: 450 tokens (JSON with operations + conditional_format)

Total: ~4,945 tokens
Actual (from API): ~5,200 tokens (includes overhead)
```

---

*Last Updated: After system prompt optimization*
*Model: GPT-4o-mini*

