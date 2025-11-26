# Training Data Directory

This directory contains training datasets for improving LLM performance.

## Dataset Files

Place your training datasets here:

1. **dataset_realistic_500.xlsx** - Realistic examples with typos, slang, messy human messages
2. **dataset_multicategory_500.xlsx** - Multi-category examples (cleaning, sorting, filters, pivots, charts, formulas, etc.)
3. **dataset_jsonheavy_500.xlsx** - JSON-heavy, tool-focused examples for training tool-calling consistency

## File Format

### Standard Format (Recommended):
Each Excel file should contain examples with:
- **Column A**: `user_message` - User prompts (natural language requests)
- **Column B**: `model_response` - Action plans in JSON format (can include JSON + explanation)
- **Column C**: Execution instructions (optional, detailed execution steps)

### Supported Column Names:
The loader automatically detects these column names:
- **Prompts**: `user_message`, `prompt`, `user_prompt`, `input`, `query`, `request`
- **Responses**: `model_response`, `action_plan`, `response`, `output`, `json`, `plan`
- **Instructions**: `execution`, `instructions`, `execution_instructions`, `steps`

### Response Format:
The `model_response` column can contain:
- Pure JSON: `{"task": "clean", "chart_type": "bar", ...}`
- JSON + explanation: `{"task": "clean", ...} This cleans the data and creates a bar chart.`
- JSON in code blocks: `` ```json {"task": "clean", ...} ``` ``

The loader will automatically extract the JSON part.

## Usage

The training data will be:
1. Loaded into the knowledge base
2. Used for few-shot learning in prompts
3. Exported for fine-tuning (if needed)

