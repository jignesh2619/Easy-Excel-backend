# Training Data Directory

This directory contains training datasets for improving LLM performance.

## Dataset Files

Place your training datasets here:

1. **dataset_realistic_500.xlsx** - Realistic examples with typos, slang, messy human messages
2. **dataset_multicategory_500.xlsx** - Multi-category examples (cleaning, sorting, filters, pivots, charts, formulas, etc.)
3. **dataset_jsonheavy_500.xlsx** - JSON-heavy, tool-focused examples for training tool-calling consistency

## File Format

Each Excel file should contain examples with:
- **Column A**: User prompts (natural language requests)
- **Column B**: Expected action plans (JSON format)
- **Column C**: Execution instructions (optional, detailed execution steps)

Or any format that can be parsed - we'll create a loader script to handle different formats.

## Usage

The training data will be:
1. Loaded into the knowledge base
2. Used for few-shot learning in prompts
3. Exported for fine-tuning (if needed)

