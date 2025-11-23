# Knowledge Base Guide for Gemini

This guide explains different approaches to provide a comprehensive knowledge base to Gemini.

## Current Implementation

### 1. **Structured Knowledge Base Module** (`knowledge_base.py`)
- ✅ Created structured knowledge base with:
  - Task definitions
  - Common patterns
  - Validation rules
  - Edge cases
  - Formula mappings
  - Chart type selection

### 2. **Integration with LLM Agent**
- Knowledge base summary is included in every prompt
- Task decision hints are provided as guidance
- Validation rules are enforced

## Advanced Approaches

### Approach 1: Enhanced Prompt with Knowledge Base (Current)
**Pros:**
- Simple to implement
- Works with all Gemini models
- No additional API calls

**Cons:**
- Limited by context window size
- Knowledge base is sent with every request

**Usage:**
```python
from utils.knowledge_base import get_knowledge_base_summary
kb_summary = get_knowledge_base_summary()
# Include in prompt
```

### Approach 2: Gemini File API (For Large Knowledge Bases)
**Pros:**
- Can handle very large knowledge bases
- Files are cached by Gemini
- More efficient for repeated use

**Cons:**
- Requires file upload
- Additional API setup

**Implementation:**
```python
import google.generativeai as genai

# Upload knowledge base file
kb_file = genai.upload_file(path="knowledge_base.json")
# Use in prompt
response = model.generate_content([
    "Use this knowledge base:",
    kb_file,
    user_prompt
])
```

### Approach 3: RAG (Retrieval Augmented Generation)
**Pros:**
- Most scalable
- Can search relevant chunks
- Works with very large knowledge bases

**Cons:**
- More complex implementation
- Requires vector database
- Additional infrastructure

**Implementation:**
```python
# 1. Create embeddings of knowledge base chunks
# 2. Store in vector database (Pinecone, Weaviate, etc.)
# 3. Search for relevant chunks based on user query
# 4. Include only relevant chunks in prompt
```

### Approach 4: Few-Shot Learning with Examples
**Pros:**
- Very effective for pattern recognition
- Easy to add new examples
- Works well with Gemini

**Cons:**
- Can make prompts very long
- Need to curate good examples

**Implementation:**
```python
examples = [
    {
        "input": "remove duplicates and create dashboard",
        "output": {"task": "clean", "chart_type": "bar"}
    },
    # ... more examples
]
# Include in prompt as few-shot examples
```

## Recommended Approach for Your Use Case

**Hybrid Approach:**
1. **Structured Knowledge Base** (current) - For rules and definitions
2. **Few-Shot Examples** - For common patterns
3. **File API** (optional) - If knowledge base grows very large

## Best Practices

1. **Keep Knowledge Base Focused**
   - Only include relevant information
   - Update regularly based on common mistakes

2. **Use Structured Format**
   - JSON/YAML for easy parsing
   - Clear categories and hierarchies

3. **Include Examples**
   - Show correct vs incorrect patterns
   - Cover edge cases

4. **Validate Against Knowledge Base**
   - Check LLM response against rules
   - Override if needed (current implementation)

5. **Monitor and Update**
   - Track common errors
   - Add new patterns to knowledge base
   - Refine based on real usage

## Next Steps

1. ✅ Structured knowledge base created
2. ✅ Integrated with LLM agent
3. 🔄 Add more examples based on real usage
4. 🔄 Consider file API if knowledge base grows
5. 🔄 Implement RAG if needed for very large scale


