# Comprehensive Fine-Tuning Guide for LLM

This guide covers multiple approaches to fine-tune and improve the LLM's understanding and execution accuracy.

## Table of Contents
1. [Few-Shot Learning](#few-shot-learning)
2. [Feedback Loop System](#feedback-loop-system)
3. [Fine-Tuning Dataset Creation](#fine-tuning-dataset-creation)
4. [Chain of Thought Prompting](#chain-of-thought-prompting)
5. [Structured Output Validation](#structured-output-validation)
6. [RAG (Retrieval Augmented Generation)](#rag-improvements)
7. [Execution Feedback Learning](#execution-feedback-learning)
8. [Prompt Engineering Best Practices](#prompt-engineering)

---

## 1. Few-Shot Learning

### What It Is
Adding more examples directly in the prompt to teach the LLM patterns.

### Implementation

**Current:** Basic examples in prompt
**Enhanced:** Add 10-20 diverse examples covering edge cases

```python
# In utils/prompts.py - Add to SYSTEM_PROMPT

FEW_SHOT_EXAMPLES = """
EXAMPLES OF CORRECT INTERPRETATIONS:

Example 1:
User: "remove duplicates and create dashboard"
Response:
{
    "task": "clean",
    "chart_type": "bar",
    "operations": [
        {
            "type": "remove_duplicates",
            "execution_instructions": {
                "method": "pandas.drop_duplicates",
                "args": [],
                "kwargs": {}
            }
        }
    ]
}

Example 2:
User: "what's the average sales for each region"
Response:
{
    "task": "group_by",
    "group_by_column": "region",
    "aggregate_function": "mean",
    "aggregate_column": "sales",
    "operations": [
        {
            "type": "group_by",
            "execution_instructions": {
                "method": "pandas.groupby",
                "args": ["region"],
                "kwargs": {"agg": {"sales": "mean"}}
            }
        }
    ]
}

Example 3:
User: "clean data, remove empty rows, and show me a chart"
Response:
{
    "task": "clean",
    "chart_type": "bar",
    "operations": [
        {
            "type": "remove_empty_rows",
            "execution_instructions": {
                "method": "pandas.dropna",
                "args": [],
                "kwargs": {"how": "all"}
            }
        },
        {
            "type": "remove_duplicates",
            "execution_instructions": {
                "method": "pandas.drop_duplicates",
                "args": [],
                "kwargs": {}
            }
        }
    ]
}
"""
```

### Benefits
- ✅ Immediate improvement without training
- ✅ Easy to add new examples
- ✅ No model retraining needed

### Limitations
- Token usage increases
- May hit context limits with too many examples

---

## 2. Feedback Loop System

### What It Is
Learn from successful and failed executions to improve future responses.

### Implementation

Create `services/feedback_learner.py`:

```python
"""
Feedback Learning System

Tracks successful/failed executions and uses them to improve prompts.
"""

import json
from typing import Dict, List
from datetime import datetime
from services.supabase_client import SupabaseClient

class FeedbackLearner:
    """Learn from execution feedback"""
    
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.feedback_table = "llm_feedback"
    
    def record_success(self, user_prompt: str, action_plan: Dict, execution_result: Dict):
        """Record successful execution"""
        feedback = {
            "user_prompt": user_prompt,
            "action_plan": json.dumps(action_plan),
            "execution_result": json.dumps(execution_result),
            "success": True,
            "created_at": datetime.now().isoformat()
        }
        self.supabase.table(self.feedback_table).insert(feedback).execute()
    
    def record_failure(self, user_prompt: str, action_plan: Dict, error: str):
        """Record failed execution"""
        feedback = {
            "user_prompt": user_prompt,
            "action_plan": json.dumps(action_plan),
            "error": error,
            "success": False,
            "created_at": datetime.now().isoformat()
        }
        self.supabase.table(self.feedback_table).insert(feedback).execute()
    
    def get_similar_successful_examples(self, user_prompt: str, limit: int = 5) -> List[Dict]:
        """Get similar successful examples for few-shot learning"""
        # Get successful examples
        result = self.supabase.table(self.feedback_table).select("*").eq(
            "success", True
        ).order("created_at", desc=True).limit(limit * 2).execute()
        
        # Simple similarity: check for common keywords
        prompt_lower = user_prompt.lower()
        similar = []
        
        for example in result.data:
            example_prompt = example["user_prompt"].lower()
            # Count common words
            common_words = set(prompt_lower.split()) & set(example_prompt.split())
            if len(common_words) >= 2:  # At least 2 common words
                similar.append({
                    "prompt": example["user_prompt"],
                    "action_plan": json.loads(example["action_plan"])
                })
                if len(similar) >= limit:
                    break
        
        return similar
    
    def get_failure_patterns(self) -> List[Dict]:
        """Analyze failure patterns to improve prompts"""
        result = self.supabase.table(self.feedback_table).select("*").eq(
            "success", False
        ).order("created_at", desc=True).limit(100).execute()
        
        # Group by error type
        error_patterns = {}
        for failure in result.data:
            error = failure.get("error", "unknown")
            if error not in error_patterns:
                error_patterns[error] = []
            error_patterns[error].append({
                "prompt": failure["user_prompt"],
                "action_plan": json.loads(failure["action_plan"])
            })
        
        return error_patterns
```

### Usage in LLM Agent

```python
# In services/llm_agent.py

from services.feedback_learner import FeedbackLearner

class LLMAgent:
    def __init__(self, ...):
        self.feedback_learner = FeedbackLearner()
    
    def interpret_prompt(self, user_prompt: str, available_columns: List[str]) -> Dict:
        # Get similar successful examples
        similar_examples = self.feedback_learner.get_similar_successful_examples(user_prompt)
        
        # Add to prompt
        examples_text = "\n\nSIMILAR SUCCESSFUL EXAMPLES:\n"
        for ex in similar_examples:
            examples_text += f"User: {ex['prompt']}\n"
            examples_text += f"Response: {json.dumps(ex['action_plan'], indent=2)}\n\n"
        
        # ... rest of prompt generation
        
        try:
            # Execute and record success
            result = self._execute_plan(action_plan)
            self.feedback_learner.record_success(user_prompt, action_plan, result)
            return result
        except Exception as e:
            # Record failure
            self.feedback_learner.record_failure(user_prompt, action_plan, str(e))
            raise
```

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS llm_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_prompt TEXT NOT NULL,
    action_plan JSONB NOT NULL,
    execution_result JSONB,
    error TEXT,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_feedback_success ON llm_feedback(success, created_at);
CREATE INDEX idx_llm_feedback_prompt ON llm_feedback USING gin(to_tsvector('english', user_prompt));
```

---

## 3. Fine-Tuning Dataset Creation

### What It Is
Create a training dataset to fine-tune Gemini (if supported) or use for few-shot learning.

### Dataset Format

Create `data/training_dataset.jsonl`:

```jsonl
{"prompt": "remove duplicates and create dashboard", "response": {"task": "clean", "chart_type": "bar", "operations": [...]}}
{"prompt": "what's the sum of all amounts", "response": {"task": "formula", "formula": {"type": "sum", "column": "Amount"}, "operations": [...]}}
{"prompt": "group by city and sum revenue", "response": {"task": "group_by", "group_by_column": "city", "aggregate_function": "sum", "aggregate_column": "revenue", "operations": [...]}}
```

### Dataset Collection Script

Create `scripts/collect_training_data.py`:

```python
"""
Collect training data from user interactions
"""

import json
from services.feedback_learner import FeedbackLearner

def export_training_dataset(output_file: str = "training_dataset.jsonl"):
    """Export successful examples as training dataset"""
    learner = FeedbackLearner()
    
    # Get all successful examples
    result = learner.supabase.table("llm_feedback").select("*").eq(
        "success", True
    ).order("created_at", desc=True).limit(1000).execute()
    
    with open(output_file, 'w') as f:
        for example in result.data:
            training_example = {
                "prompt": example["user_prompt"],
                "response": json.loads(example["action_plan"])
            }
            f.write(json.dumps(training_example) + "\n")
    
    print(f"Exported {len(result.data)} examples to {output_file}")
```

### Using Dataset for Few-Shot Learning

```python
def load_training_examples(file_path: str, user_prompt: str, n: int = 5):
    """Load similar examples from training dataset"""
    examples = []
    with open(file_path, 'r') as f:
        for line in f:
            example = json.loads(line)
            # Simple similarity check
            if any(word in user_prompt.lower() for word in example["prompt"].lower().split()[:3]):
                examples.append(example)
                if len(examples) >= n:
                    break
    return examples
```

---

## 4. Chain of Thought Prompting

### What It Is
Make the LLM think step-by-step before generating the final response.

### Implementation

```python
# In utils/prompts.py

CHAIN_OF_THOUGHT_PROMPT = """
Before generating the action plan, think through these steps:

1. UNDERSTAND THE USER'S INTENT:
   - What is the user trying to accomplish?
   - What keywords indicate the operation type?
   - Is this a cleaning, analysis, or visualization request?

2. IDENTIFY THE TASK:
   - Based on keywords, what task should be used?
   - Check: clean, summarize, filter, group_by, formula, sort?
   - Remember: "remove duplicates" → task: "clean" (NOT "summarize")

3. DETERMINE OPERATIONS:
   - What pandas operations are needed?
   - What formula functions are required?
   - In what order should operations execute?

4. SPECIFY EXECUTION INSTRUCTIONS:
   - For each operation, specify the exact pandas method
   - Provide correct parameters
   - Ensure execution_instructions are complete

5. VALIDATE:
   - Does the action plan match user intent?
   - Are all required columns specified?
   - Is the chart type appropriate?

Now generate the action plan JSON following this thought process.
"""
```

---

## 5. Structured Output Validation

### What It Is
Use JSON schema validation to ensure LLM returns correct format.

### Implementation

Create `utils/schema_validator.py`:

```python
"""
JSON Schema Validation for LLM Responses
"""

import json
from jsonschema import validate, ValidationError

ACTION_PLAN_SCHEMA = {
    "type": "object",
    "required": ["task"],
    "properties": {
        "task": {
            "type": "string",
            "enum": ["clean", "summarize", "filter", "group_by", "formula", "sort", "transform"]
        },
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type", "execution_instructions"],
                "properties": {
                    "type": {"type": "string"},
                    "description": {"type": "string"},
                    "params": {"type": "object"},
                    "execution_instructions": {
                        "type": "object",
                        "required": ["method"],
                        "properties": {
                            "method": {"type": "string"},
                            "args": {"type": "array"},
                            "kwargs": {"type": "object"}
                        }
                    }
                }
            }
        },
        "chart_type": {
            "type": "string",
            "enum": ["bar", "line", "pie", "histogram", "scatter", "none"]
        }
    }
}

def validate_action_plan(action_plan: dict) -> tuple[bool, str]:
    """
    Validate action plan against schema
    
    Returns:
        (is_valid, error_message)
    """
    try:
        validate(instance=action_plan, schema=ACTION_PLAN_SCHEMA)
        return True, ""
    except ValidationError as e:
        return False, str(e)
```

### Usage

```python
# In services/llm_agent.py

from utils.schema_validator import validate_action_plan

def interpret_prompt(self, ...):
    # ... generate response ...
    
    # Validate response
    is_valid, error = validate_action_plan(action_plan)
    if not is_valid:
        # Retry with validation error in prompt
        retry_prompt = f"{prompt}\n\nPREVIOUS RESPONSE WAS INVALID: {error}\nPlease fix and return valid JSON."
        # ... retry ...
```

---

## 6. RAG Improvements

### What It Is
Retrieval Augmented Generation - Use a knowledge base to provide context.

### Enhanced Implementation

Create `services/rag_system.py`:

```python
"""
RAG System for Enhanced Context
"""

from typing import List, Dict
import json
from utils.knowledge_base import KNOWLEDGE_BASE

class RAGSystem:
    """Retrieval Augmented Generation for better context"""
    
    def __init__(self):
        self.knowledge_base = KNOWLEDGE_BASE
    
    def retrieve_relevant_context(self, user_prompt: str) -> str:
        """Retrieve relevant context from knowledge base"""
        prompt_lower = user_prompt.lower()
        context_parts = []
        
        # 1. Find matching task definitions
        for task, info in self.knowledge_base["task_definitions"].items():
            keywords = info["keywords"]
            if any(kw in prompt_lower for kw in keywords):
                context_parts.append(f"TASK: {task.upper()}")
                context_parts.append(f"Description: {info['description']}")
                context_parts.append(f"Output: {info['output']}")
                context_parts.append(f"Examples: {', '.join(info['examples'][:3])}")
        
        # 2. Find matching patterns
        for pattern_name, pattern_info in self.knowledge_base["common_patterns"].items():
            if pattern_info["pattern"].lower() in prompt_lower:
                context_parts.append(f"\nMATCHED PATTERN: {pattern_name}")
                context_parts.append(f"Correct approach: {pattern_info['correct_task']}")
                context_parts.append(f"Reason: {pattern_info['reason']}")
        
        # 3. Find formula mappings
        for category, mappings in self.knowledge_base["formula_mappings"].items():
            for formula_type, keywords in mappings.items():
                if any(kw in prompt_lower for kw in keywords):
                    context_parts.append(f"\nFORMULA: {formula_type}")
                    context_parts.append(f"Category: {category}")
        
        return "\n".join(context_parts)
    
    def get_execution_examples(self, task: str) -> List[Dict]:
        """Get execution examples for a specific task"""
        examples = []
        
        # Get examples from knowledge base
        if task in self.knowledge_base["task_definitions"]:
            task_info = self.knowledge_base["task_definitions"][task]
            for example_prompt in task_info["examples"]:
                examples.append({
                    "prompt": example_prompt,
                    "task": task,
                    "execution_hint": task_info["description"]
                })
        
        return examples
```

---

## 7. Execution Feedback Learning

### What It Is
Learn from execution results to improve future prompts.

### Implementation

```python
# In services/llm_agent.py

def interpret_prompt_with_feedback(self, user_prompt: str, available_columns: List[str], previous_errors: List[str] = None) -> Dict:
    """Interpret prompt with feedback from previous errors"""
    
    feedback_context = ""
    if previous_errors:
        feedback_context = "\n\nPREVIOUS ERRORS TO AVOID:\n"
        for error in previous_errors:
            feedback_context += f"- {error}\n"
        feedback_context += "\nPlease ensure your response avoids these errors.\n"
    
    # Include feedback in prompt
    full_prompt = f"""{SYSTEM_PROMPT}
    
{feedback_context}

{prompt}
"""
    # ... rest of implementation
```

---

## 8. Prompt Engineering Best Practices

### A. Use Clear Structure

```python
PROMPT_STRUCTURE = """
1. SYSTEM ROLE: You are an expert data analyst
2. CONTEXT: Available columns, data structure
3. EXAMPLES: 5-10 diverse examples
4. CONSTRAINTS: Validation rules, edge cases
5. OUTPUT FORMAT: JSON schema
6. THINKING PROCESS: Chain of thought
"""
```

### B. Include Negative Examples

```python
NEGATIVE_EXAMPLES = """
❌ WRONG:
User: "remove duplicates and create dashboard"
Response: {"task": "summarize"}  // WRONG!

✅ CORRECT:
User: "remove duplicates and create dashboard"
Response: {"task": "clean", "chart_type": "bar"}  // CORRECT!
"""
```

### C. Use Temperature Settings

```python
# For deterministic operations
generation_config = {
    "temperature": 0.1,  # Low = more deterministic
    "top_p": 0.95,
    "top_k": 64
}

# For creative operations (if needed)
generation_config = {
    "temperature": 0.3,  # Slightly higher for flexibility
    "top_p": 0.95,
    "top_k": 64
}
```

### D. Progressive Prompting

```python
def interpret_prompt_progressive(self, user_prompt: str, available_columns: List[str]) -> Dict:
    """Try with simple prompt first, then enhance if needed"""
    
    # First attempt: Simple prompt
    simple_prompt = f"Interpret: {user_prompt}\nColumns: {available_columns}"
    action_plan = self._try_interpret(simple_prompt)
    
    # If validation fails, try with enhanced prompt
    if not self._validate_action_plan(action_plan):
        enhanced_prompt = f"""{SYSTEM_PROMPT}
        
        {FEW_SHOT_EXAMPLES}
        
        {user_prompt}
        """
        action_plan = self._try_interpret(enhanced_prompt)
    
    return action_plan
```

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add more few-shot examples (20-30 examples)
2. ✅ Implement feedback loop system
3. ✅ Add chain of thought prompting

### Phase 2: Medium Term (1 week)
4. ✅ Create training dataset collection
5. ✅ Implement RAG improvements
6. ✅ Add structured output validation

### Phase 3: Long Term (2-4 weeks)
7. ✅ Fine-tune model (if Gemini supports it)
8. ✅ Advanced feedback learning
9. ✅ A/B testing different prompt strategies

---

## Measuring Improvement

### Metrics to Track

1. **Accuracy Rate**: % of successful executions
2. **Error Types**: Categorize errors (validation, execution, logic)
3. **User Satisfaction**: Track user corrections/retries
4. **Response Quality**: Validate execution_instructions completeness
5. **Token Efficiency**: Average tokens per request

### Dashboard Query

```sql
-- Success rate over time
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM llm_feedback
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Next Steps

1. **Start with Few-Shot Learning**: Add 20-30 diverse examples
2. **Implement Feedback Loop**: Track successes/failures
3. **Create Training Dataset**: Export successful examples
4. **Iterate**: Use feedback to improve prompts continuously

The key is **iterative improvement** - start simple, measure results, and enhance based on real user interactions.

