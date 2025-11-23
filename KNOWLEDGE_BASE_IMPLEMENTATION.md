# Knowledge Base Implementation for Gemini

## Overview

We've implemented a comprehensive knowledge base system to improve Gemini's accuracy in generating correct JSON action plans.

## What Was Implemented

### 1. **Structured Knowledge Base Module** (`utils/knowledge_base.py`)

A comprehensive knowledge base containing:

- **Task Definitions**: Detailed descriptions of each task type (clean, summarize, filter, etc.)
  - When to use each task
  - What output each task produces
  - Keywords that map to each task
  - Examples for each task

- **Common Patterns**: Pre-defined patterns with correct/incorrect examples
  - "remove duplicates and create dashboard" → task: "clean" (NOT "summarize")
  - "give me summary statistics" → task: "summarize"
  - And more...

- **Validation Rules**: Rules to enforce correct task selection
  - If cleaning keywords → task MUST be "clean"
  - If dashboard after cleaning → task is "clean" with chart_type
  - If explicit statistics → task is "summarize"

- **Edge Cases**: Solutions for special scenarios
  - Multiple operations in one request
  - Ambiguous requests
  - Complex combinations

- **Formula Mappings**: Keyword mappings for formula operations
  - Math operations
  - Text operations
  - Date operations
  - Lookup operations

- **Chart Type Selection**: Guidelines for choosing chart types

### 2. **Integration with LLM Agent** (`services/llm_agent.py`)

The knowledge base is now automatically included in every prompt:

```python
# Knowledge base summary is added to prompt
kb_summary = get_knowledge_base_summary()

# Task decision hints are provided
task_suggestions = get_task_decision_guide(user_prompt)
```

### 3. **Helper Functions**

- `get_knowledge_base_summary()`: Formats knowledge base for prompts
- `get_task_decision_guide()`: Analyzes prompt and suggests task
- `export_knowledge_base_to_json()`: Export for Gemini File API
- `add_example_to_knowledge_base()`: Dynamically add examples

## How It Works

1. **User sends prompt** → "remove duplicates and create dashboard"

2. **Knowledge base analysis**:
   - Detects cleaning keywords: "remove duplicates"
   - Detects visualization keywords: "dashboard"
   - Matches pattern: "clean_and_dashboard"
   - Suggests: task="clean", chart_type="bar"

3. **Knowledge base included in prompt**:
   - Task definitions
   - Common patterns
   - Validation rules
   - Examples

4. **Gemini receives enhanced prompt**:
   - Full context about tasks
   - Examples of correct responses
   - Validation rules
   - Task decision hints

5. **Response validation**:
   - Backend still validates and overrides if needed
   - But Gemini should be more accurate now

## Benefits

✅ **Better Accuracy**: Gemini has full context about task selection
✅ **Fewer Overrides**: Backend overrides should be less needed
✅ **Consistent Responses**: Knowledge base ensures consistency
✅ **Easy to Update**: Add new patterns/examples easily
✅ **Scalable**: Can export to file API for larger knowledge bases

## Usage Examples

### Basic Usage (Automatic)
The knowledge base is automatically included in every prompt. No changes needed.

### Export Knowledge Base
```python
from utils.knowledge_base import export_knowledge_base_to_json
export_knowledge_base_to_json("kb.json")
# Can upload to Gemini File API if needed
```

### Add New Example
```python
from utils.knowledge_base import add_example_to_knowledge_base

new_pattern = {
    "pattern": "clean and group by category",
    "correct_task": "clean",
    "correct_chart_type": "bar",
    "incorrect_task": "summarize",
    "reason": "Cleaning first, then grouping"
}
add_example_to_knowledge_base("common_patterns", new_pattern)
```

### Get Task Suggestions
```python
from utils.knowledge_base import get_task_decision_guide

suggestions = get_task_decision_guide("remove duplicates and create dashboard")
print(suggestions)
# {
#   "suggested_task": "clean",
#   "suggested_chart_type": "bar",
#   "confidence": 0.95,
#   "reasoning": ["Detected cleaning keywords", "Matched pattern: clean_and_dashboard"]
# }
```

## Advanced Options

### Option 1: Gemini File API (For Very Large Knowledge Bases)

If the knowledge base grows very large, you can:

1. Export to JSON:
```python
export_knowledge_base_to_json("large_kb.json")
```

2. Upload to Gemini:
```python
import google.generativeai as genai
kb_file = genai.upload_file("large_kb.json")
```

3. Use in prompts:
```python
response = model.generate_content([
    "Use this knowledge base:",
    kb_file,
    user_prompt
])
```

### Option 2: RAG (Retrieval Augmented Generation)

For extremely large knowledge bases, implement RAG:

1. Create embeddings of knowledge base chunks
2. Store in vector database (Pinecone, Weaviate, Chroma)
3. Search for relevant chunks based on user query
4. Include only relevant chunks in prompt

## Maintenance

### Adding New Patterns

1. Identify common user request pattern
2. Determine correct task/chart_type
3. Add to `common_patterns` in `knowledge_base.py`
4. Test with real prompts

### Updating Validation Rules

1. Identify new edge case or mistake
2. Add validation rule to `validation_rules`
3. Update task definitions if needed
4. Test thoroughly

### Monitoring

Track:
- Common errors from Gemini
- Cases where backend override is needed
- New user request patterns
- Accuracy improvements

## Next Steps

1. ✅ Knowledge base created and integrated
2. 🔄 Monitor real usage and add more examples
3. 🔄 Consider file API if knowledge base grows
4. 🔄 Implement RAG if needed for scale
5. 🔄 Fine-tune based on error patterns

## Files

- `backend/utils/knowledge_base.py` - Main knowledge base module
- `backend/services/llm_agent.py` - Integration with LLM agent
- `backend/utils/prompts.py` - Enhanced with knowledge base references
- `backend/utils/knowledge_base_guide.md` - Detailed guide
- `backend/KNOWLEDGE_BASE_IMPLEMENTATION.md` - This file


