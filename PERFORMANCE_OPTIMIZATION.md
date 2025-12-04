# Performance Optimization for File Upload and Preview

## Current Bottlenecks

1. **Sample Selection** (`sample_selector.build_sample()`)
   - Complex quantile calculations
   - Categorical diversity analysis
   - Outlier detection
   - **Impact**: Can take 1-3 seconds for large files (10k+ rows)

2. **LLM API Call** (`llm_agent.interpret_prompt()`)
   - OpenAI API call with large context
   - Network latency
   - **Impact**: 2-5 seconds depending on prompt complexity

3. **Data Processing** (`ExcelProcessor.execute_action_plan()`)
   - Pandas operations on full dataset
   - Formula evaluation
   - Conditional formatting
   - **Impact**: 1-2 seconds for large files

4. **Data Serialization** (Converting DataFrame to JSON)
   - Converting entire processed DataFrame to JSON
   - **Impact**: 0.5-2 seconds for large datasets

## Total Expected Time
- Small files (< 100 rows): 3-5 seconds
- Medium files (100-1000 rows): 5-8 seconds
- Large files (1000-10000 rows): 8-15 seconds
- Very large files (> 10000 rows): 15-30+ seconds

## Optimization Strategies

### 1. Optimize Sample Selection
- Cache sample results for similar files
- Reduce max_rows from 20 to 15 for faster processing
- Simplify quantile calculations

### 2. Add Progress Indicators
- Show loading states during each phase
- Frontend should display: "Uploading...", "Processing...", "Analyzing...", "Generating preview..."

### 3. Stream Responses (Future)
- Stream partial results as they become available
- Show preview data before full processing completes

### 4. Optimize Data Serialization
- Only send necessary columns to frontend
- Compress JSON responses
- Paginate large datasets

### 5. Parallel Processing
- Run sample selection and file validation in parallel
- Process data while LLM call is in progress (if possible)

## Quick Wins

1. **Reduce sample size**: Change `max_rows=20` to `max_rows=15` in SampleSelector
2. **Add timeout**: Set reasonable timeout for LLM calls (30 seconds)
3. **Optimize JSON serialization**: Use faster JSON library or reduce data sent
4. **Frontend loading states**: Show progress messages to users







