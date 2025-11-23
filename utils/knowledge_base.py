"""
Knowledge Base for LLM Agent

Structured knowledge base containing:
- Task definitions and use cases
- Common patterns and examples
- Edge cases and solutions
- Validation rules
"""

KNOWLEDGE_BASE = {
    "task_definitions": {
        "clean": {
            "description": "Remove duplicates, fix formatting, handle missing values",
            "output": "Actual cleaned data rows (same structure, fewer/cleaned rows)",
            "use_when": [
                "User wants to modify/clean the actual data rows",
                "User mentions: remove duplicates, clean, fix formatting, handle missing, remove empty, normalize",
                "User wants cleaned data + visualization (dashboard/chart)"
            ],
            "never_use_when": [
                "User explicitly asks for summary statistics",
                "User wants statistical analysis only"
            ],
            "keywords": ["remove duplicates", "clean", "fix formatting", "handle missing", "duplicate", "remove empty", "normalize"],
            "examples": [
                "remove duplicates and create dashboard",
                "clean the data",
                "fix formatting issues",
                "remove empty rows"
            ]
        },
        "summarize": {
            "description": "Create summary statistics (count, mean, std, min, max, quartiles)",
            "output": "Summary statistics table (different structure - index column + stat columns)",
            "use_when": [
                "User explicitly asks for summary statistics",
                "User mentions: summary, statistics, describe, statistical analysis",
                "User wants to know: count, mean, std, min, max, quartiles"
            ],
            "never_use_when": [
                "User wants to see actual data after cleaning/filtering",
                "User requests cleaning operations",
                "User wants dashboard after cleaning"
            ],
            "keywords": ["summary", "statistics", "describe", "statistical analysis", "what are the stats"],
            "examples": [
                "give me summary statistics of sales data",
                "what are the statistics for amount column",
                "describe the data statistically"
            ]
        },
        "filter": {
            "description": "Show only specific rows based on conditions",
            "output": "Filtered data rows (same structure, fewer rows)",
            "use_when": [
                "User wants to show only specific rows",
                "User mentions: filter, show only, where, find rows, rows where"
            ],
            "keywords": ["filter", "show only", "where", "find rows", "rows where"],
            "examples": [
                "show rows where amount > 500",
                "filter by city equals NYC",
                "find rows where status is active"
            ]
        },
        "group_by": {
            "description": "Group data and aggregate (like pivot table)",
            "output": "Grouped and aggregated data (different structure - group column + aggregate columns)",
            "use_when": [
                "User wants to group data and aggregate",
                "User mentions: group by, by category, sum by, count by category"
            ],
            "keywords": ["group by", "by category", "sum by", "count by category"],
            "examples": [
                "group by city and sum revenue",
                "count by category",
                "sum sales by region"
            ]
        },
        "formula": {
            "description": "Calculate a single value or apply formula transformations",
            "output": "Depends on formula type (single value or transformed data)",
            "use_when": [
                "User wants to calculate a single value",
                "User mentions: sum all, average, count, find, lookup"
            ],
            "keywords": ["sum all", "average", "count", "find", "lookup"],
            "examples": [
                "what's the sum of all amounts",
                "calculate average sales",
                "find email for ID 123"
            ]
        },
        "sort": {
            "description": "Reorder rows",
            "output": "Sorted data rows (same structure, reordered)",
            "use_when": [
                "User wants to reorder rows",
                "User mentions: sort, order, arrange, top N"
            ],
            "keywords": ["sort", "order", "arrange", "top N"],
            "examples": [
                "sort by amount descending",
                "order by name A to Z",
                "show top 10 rows"
            ]
        }
    },
    
    "common_patterns": {
        "clean_and_dashboard": {
            "pattern": "remove duplicates and create dashboard",
            "correct_task": "clean",
            "correct_chart_type": "bar",
            "incorrect_task": "summarize",
            "reason": "User wants cleaned data + visualization, not statistics"
        },
        "clean_and_chart": {
            "pattern": "clean the data and show me a chart",
            "correct_task": "clean",
            "correct_chart_type": "bar",
            "incorrect_task": "summarize",
            "reason": "Cleaning operations should use 'clean' task"
        },
        "explicit_statistics": {
            "pattern": "give me summary statistics",
            "correct_task": "summarize",
            "correct_chart_type": "none",
            "incorrect_task": "clean",
            "reason": "Explicit request for statistics"
        },
        "just_clean": {
            "pattern": "remove duplicates",
            "correct_task": "clean",
            "correct_chart_type": "none",
            "incorrect_task": "summarize",
            "reason": "Data cleaning operation"
        },
        "group_and_dashboard": {
            "pattern": "group by city and create dashboard",
            "correct_task": "group_by",
            "correct_chart_type": "bar",
            "incorrect_task": "clean",
            "reason": "Grouping operation with visualization"
        },
        "filter_and_chart": {
            "pattern": "filter rows where amount > 500 and show chart",
            "correct_task": "filter",
            "correct_chart_type": "bar",
            "incorrect_task": "group_by",
            "reason": "Filtering operation with visualization"
        }
    },
    
    "validation_rules": [
        {
            "rule": "If user mentioned cleaning keywords, task MUST be 'clean' (not 'summarize')",
            "keywords": ["remove duplicates", "clean", "fix formatting", "handle missing", "duplicate", "remove empty", "normalize"],
            "enforce_task": "clean"
        },
        {
            "rule": "If user wants dashboard/chart after cleaning, task is 'clean' with chart_type",
            "keywords": ["dashboard", "chart", "visualize", "graph", "plot"],
            "with_cleaning": True,
            "enforce_task": "clean"
        },
        {
            "rule": "If user explicitly asks for summary statistics, task is 'summarize'",
            "keywords": ["summary", "statistics", "describe", "statistical analysis"],
            "enforce_task": "summarize"
        },
        {
            "rule": "Chart type must match data type",
            "bar": "categorical data, comparisons, grouped data",
            "line": "time series, trends over time",
            "pie": "proportions, percentages, distributions",
            "histogram": "distribution of single numeric variable",
            "scatter": "relationship between two numeric variables"
        }
    ],
    
    "edge_cases": [
        {
            "scenario": "User says 'clean and show dashboard'",
            "solution": {
                "task": "clean",
                "chart_type": "bar",
                "columns_needed": [],
                "output": "Actual cleaned data rows + chart"
            }
        },
        {
            "scenario": "User says 'remove duplicates'",
            "solution": {
                "task": "clean",
                "chart_type": "none",
                "output": "Actual cleaned data rows (duplicates removed)"
            }
        },
        {
            "scenario": "User says 'give me statistics'",
            "solution": {
                "task": "summarize",
                "chart_type": "none",
                "output": "Summary statistics table"
            }
        },
        {
            "scenario": "User says 'clean data and visualize sales by region'",
            "solution": {
                "task": "clean",
                "chart_type": "bar",
                "group_by_column": "region",
                "output": "Cleaned data + chart"
            }
        },
        {
            "scenario": "User says 'remove duplicates then group by city'",
            "solution": {
                "task": "clean",
                "note": "Grouping might need separate operation, but prioritize 'clean' for main task"
            }
        }
    ],
    
    "formula_mappings": {
        "math_operations": {
            "sum": ["sum", "total", "add up", "sum all"],
            "average": ["average", "mean", "what's the average", "avg"],
            "min": ["minimum", "min", "lowest"],
            "max": ["maximum", "max", "highest"],
            "count": ["how many", "count", "number of"],
            "countif": ["count where", "how many where", "count if"],
            "unique": ["unique", "distinct", "how many unique"]
        },
        "text_operations": {
            "concat": ["combine", "join", "merge"],
            "left": ["extract left", "first N characters"],
            "right": ["extract right", "last N characters"],
            "trim": ["remove spaces", "trim", "strip"],
            "lower": ["lowercase", "lower", "small letters"],
            "upper": ["uppercase", "upper", "capital letters"],
            "proper": ["title case", "proper case", "capitalize"]
        },
        "date_operations": {
            "year": ["extract year", "what year"],
            "month": ["extract month", "what month"],
            "day": ["extract day", "what day"],
            "datedif": ["days between", "difference", "datedif"]
        },
        "lookup_operations": {
            "vlookup": ["find", "lookup", "get value for"],
            "xlookup": ["find", "lookup", "get value for"]
        }
    },
    
    "chart_type_selection": {
        "bar": {
            "use_for": ["categorical data", "comparisons", "grouped data", "counts by category"],
            "keywords": ["compare", "by category", "grouped", "counts"]
        },
        "line": {
            "use_for": ["time series", "trends over time", "changes over time"],
            "keywords": ["over time", "trend", "time series", "changes"]
        },
        "pie": {
            "use_for": ["proportions", "percentages", "distributions", "parts of whole"],
            "keywords": ["proportion", "percentage", "distribution", "parts"]
        },
        "histogram": {
            "use_for": ["distribution of single numeric variable"],
            "keywords": ["distribution", "frequency", "histogram"]
        },
        "scatter": {
            "use_for": ["relationship between two numeric variables", "correlation"],
            "keywords": ["relationship", "correlation", "scatter", "vs"]
        }
    }
}


def get_knowledge_base_summary() -> str:
    """
    Get a formatted summary of the knowledge base for inclusion in prompts
    
    Returns:
        Formatted string with key knowledge base information
    """
    summary = []
    
    # Task definitions
    summary.append("TASK DEFINITIONS:")
    for task, info in KNOWLEDGE_BASE["task_definitions"].items():
        summary.append(f"\n**{task.upper()}**:")
        summary.append(f"  Description: {info['description']}")
        summary.append(f"  Output: {info['output']}")
        summary.append(f"  Use when: {', '.join(info['use_when'][:3])}")
        summary.append(f"  Keywords: {', '.join(info['keywords'][:5])}")
    
    # Common patterns
    summary.append("\n\nCOMMON PATTERNS:")
    for pattern_name, pattern_info in KNOWLEDGE_BASE["common_patterns"].items():
        summary.append(f"\nPattern: '{pattern_info['pattern']}'")
        summary.append(f"  ✓ CORRECT: task='{pattern_info['correct_task']}', chart_type='{pattern_info['correct_chart_type']}'")
        summary.append(f"  ✗ INCORRECT: task='{pattern_info['incorrect_task']}'")
        summary.append(f"  Reason: {pattern_info['reason']}")
    
    # Validation rules
    summary.append("\n\nVALIDATION RULES:")
    for rule in KNOWLEDGE_BASE["validation_rules"][:3]:  # Top 3 most important
        if "rule" in rule:
            summary.append(f"  - {rule['rule']}")
    
    return "\n".join(summary)


def export_knowledge_base_to_json(file_path: str = "knowledge_base.json"):
    """
    Export knowledge base to JSON file for use with Gemini File API
    
    Args:
        file_path: Path to save JSON file
    """
    import json
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(KNOWLEDGE_BASE, f, indent=2, ensure_ascii=False)
    return file_path


def add_example_to_knowledge_base(example_type: str, example: dict):
    """
    Dynamically add example to knowledge base
    
    Args:
        example_type: Type of example (e.g., "common_patterns", "edge_cases")
        example: Example dictionary to add
    """
    if example_type in KNOWLEDGE_BASE:
        if isinstance(KNOWLEDGE_BASE[example_type], list):
            KNOWLEDGE_BASE[example_type].append(example)
        elif isinstance(KNOWLEDGE_BASE[example_type], dict):
            # Generate unique key
            key = f"pattern_{len(KNOWLEDGE_BASE[example_type]) + 1}"
            KNOWLEDGE_BASE[example_type][key] = example
    else:
        KNOWLEDGE_BASE[example_type] = [example] if isinstance(example, dict) else example


def get_task_decision_guide(user_prompt: str) -> dict:
    """
    Analyze user prompt and suggest task based on knowledge base
    
    Args:
        user_prompt: User's natural language request
        
    Returns:
        Dictionary with suggested task and reasoning
    """
    prompt_lower = user_prompt.lower()
    suggestions = {
        "suggested_task": None,
        "suggested_chart_type": "none",
        "confidence": 0,
        "reasoning": [],
        "matched_patterns": []
    }
    
    # Check for cleaning keywords
    cleaning_keywords = KNOWLEDGE_BASE["task_definitions"]["clean"]["keywords"]
    has_cleaning = any(keyword in prompt_lower for keyword in cleaning_keywords)
    
    # Check for visualization keywords
    viz_keywords = ["visualize", "dashboard", "chart", "graph", "plot", "show me"]
    has_viz = any(keyword in prompt_lower for keyword in viz_keywords)
    
    # Check for statistics keywords
    stats_keywords = KNOWLEDGE_BASE["task_definitions"]["summarize"]["keywords"]
    has_stats = any(keyword in prompt_lower for keyword in stats_keywords)
    
    # Decision logic
    if has_cleaning:
        suggestions["suggested_task"] = "clean"
        suggestions["confidence"] = 0.9
        suggestions["reasoning"].append("Detected cleaning keywords")
        if has_viz:
            suggestions["suggested_chart_type"] = "bar"
            suggestions["reasoning"].append("Also detected visualization request")
    elif has_stats:
        suggestions["suggested_task"] = "summarize"
        suggestions["confidence"] = 0.9
        suggestions["reasoning"].append("Detected statistics keywords")
    elif has_viz:
        suggestions["suggested_task"] = "group_by"  # Default for visualization
        suggestions["suggested_chart_type"] = "bar"
        suggestions["confidence"] = 0.7
        suggestions["reasoning"].append("Detected visualization request")
    
    # Check common patterns
    for pattern_name, pattern_info in KNOWLEDGE_BASE["common_patterns"].items():
        if pattern_info["pattern"].lower() in prompt_lower:
            suggestions["matched_patterns"].append(pattern_name)
            suggestions["suggested_task"] = pattern_info["correct_task"]
            suggestions["suggested_chart_type"] = pattern_info["correct_chart_type"]
            suggestions["confidence"] = 0.95
            suggestions["reasoning"].append(f"Matched pattern: {pattern_name}")
    
    return suggestions

