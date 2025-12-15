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
    },
    
    "chart_knowledge": {
        "chart_type_rules": {
            "bar": {
                "description": "Use for comparing categories, showing counts, or grouped data",
                "data_requirements": "X-axis: categorical column, Y-axis: numeric column",
                "examples": ["revenue by country", "sales by region", "count by category"],
                "when_to_use": [
                    "User mentions 'by' (e.g., 'by country', 'by category')",
                    "Comparing values across categories",
                    "Showing counts or totals per group"
                ]
            },
            "line": {
                "description": "Use for showing trends over time or sequential data",
                "data_requirements": "X-axis: date/time or sequential column, Y-axis: numeric column",
                "examples": ["revenue over time", "sales trend", "growth over months"],
                "when_to_use": [
                    "User mentions 'over time', 'trend', 'changes'",
                    "X-axis column contains dates or sequential values",
                    "Showing progression or trends"
                ]
            },
            "pie": {
                "description": "Use for showing proportions or parts of a whole",
                "data_requirements": "X-axis: categories, Y-axis: values (percentages or counts)",
                "examples": ["market share", "distribution", "percentage breakdown"],
                "when_to_use": [
                    "User mentions 'share', 'percentage', 'distribution', 'parts'",
                    "Showing how parts relate to whole",
                    "Limited number of categories (typically < 10)"
                ]
            },
            "histogram": {
                "description": "Use for showing distribution of a single numeric variable",
                "data_requirements": "X-axis: numeric column (Y is auto-generated frequency)",
                "examples": ["age distribution", "price distribution", "score frequency"],
                "when_to_use": [
                    "User mentions 'distribution', 'frequency', 'histogram'",
                    "Single numeric column to analyze",
                    "Understanding data spread or patterns"
                ]
            },
            "scatter": {
                "description": "Use for showing relationship between two numeric variables",
                "data_requirements": "X-axis: numeric column, Y-axis: numeric column",
                "examples": ["sales vs profit", "price vs quantity", "correlation analysis"],
                "when_to_use": [
                    "User mentions 'vs', 'relationship', 'correlation', 'scatter'",
                    "Both X and Y are numeric columns",
                    "Finding patterns or relationships"
                ]
            }
        },
        "column_identification": {
            "x_axis_rules": [
                "For bar charts: Use categorical column (country, category, region, etc.)",
                "For line charts: Use date/time column or sequential column",
                "For pie charts: Use category column",
                "For scatter/histogram: Use numeric column"
            ],
            "y_axis_rules": [
                "For bar/line charts: Use numeric column (revenue, sales, count, etc.)",
                "For pie charts: Use value column (count, percentage, amount)",
                "For scatter: Use numeric column",
                "For histogram: Y-axis is auto-generated (frequency)"
            ],
            "column_matching": [
                "Match column names from user request to actual column names (case-insensitive)",
                "If user says 'revenue by country', find 'Revenue' and 'Country' columns",
                "If column not found, use closest match or first numeric/categorical column",
                "For time series, look for date/time column names"
            ]
        },
        "common_chart_patterns": {
            "revenue_by_category": {
                "pattern": "revenue by [category]",
                "chart_type": "bar",
                "x_column": "[category column]",
                "y_column": "revenue or amount or sales"
            },
            "trend_over_time": {
                "pattern": "[metric] over time",
                "chart_type": "line",
                "x_column": "date or time column",
                "y_column": "[metric column]"
            },
            "distribution": {
                "pattern": "distribution of [numeric]",
                "chart_type": "histogram",
                "x_column": "[numeric column]",
                "y_column": None
            },
            "comparison": {
                "pattern": "[metric1] vs [metric2]",
                "chart_type": "scatter",
                "x_column": "[metric1 column]",
                "y_column": "[metric2 column]"
            },
            "share_or_percentage": {
                "pattern": "share of [category] or percentage",
                "chart_type": "pie",
                "x_column": "[category column]",
                "y_column": "value or count column"
            }
        },
        "best_practices": [
            "Always use actual column names from the dataset",
            "Validate that columns exist before generating chart config",
            "Choose chart type based on data type and user intent",
            "Provide descriptive titles that explain what the chart shows",
            "For time series, ensure X-axis is date/time column",
            "For comparisons, ensure both axes are appropriate data types",
            "If user request is unclear, analyze sample data to infer columns"
        ],
        "edge_cases": [
            {
                "scenario": "User says 'chart' without specifying type",
                "solution": "Analyze data and user request to infer best chart type (usually bar for categorical, line for time)"
            },
            {
                "scenario": "Column names don't match user request exactly",
                "solution": "Use fuzzy matching or find closest column name, validate with user if possible"
            },
            {
                "scenario": "User requests chart but no appropriate columns found",
                "solution": "Use first numeric column for Y-axis, first categorical/numeric for X-axis"
            },
            {
                "scenario": "User says 'show me data' (ambiguous)",
                "solution": "If visualization keywords present, create bar chart of first categorical vs first numeric column"
            }
        ]
    }
}


def get_knowledge_base_summary() -> str:
    """
    Get a formatted summary of the knowledge base for inclusion in prompts
    Optimized for token efficiency - only essential information
    
    Returns:
        Formatted string with key knowledge base information
    """
    # Ultra-concise summary - only critical task mappings
    # Format: "task: keywords" (one line per task)
    tasks = []
    common_tasks = ["clean", "filter", "group_by", "formula"]
    for task in common_tasks:
        if task in KNOWLEDGE_BASE["task_definitions"]:
            info = KNOWLEDGE_BASE["task_definitions"][task]
            keywords = ', '.join(info['keywords'][:2])  # Only top 2 keywords
            tasks.append(f"{task}: {keywords}")
    
    # Single line format for maximum efficiency
    return "Tasks: " + " | ".join(tasks) if tasks else ""


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
    Optimized for token efficiency - minimal output
    
    Args:
        user_prompt: User's natural language request
        
    Returns:
        Dictionary with suggested task (simplified)
    """
    prompt_lower = user_prompt.lower()
    
    # Quick keyword checks (most common patterns first)
    # Check for cleaning keywords
    cleaning_keywords = ["clean", "remove duplicates", "fix formatting", "duplicate", "remove empty"]
    has_cleaning = any(keyword in prompt_lower for keyword in cleaning_keywords)
    
    # Check for statistics keywords
    stats_keywords = ["summary", "statistics", "describe", "statistical"]
    has_stats = any(keyword in prompt_lower for keyword in stats_keywords)
    
    # Check for grouping keywords
    group_keywords = ["group", "group by", "sum by", "count by"]
    has_group = any(keyword in prompt_lower for keyword in group_keywords)
    
    # Decision logic (simplified - only return task, no verbose reasoning)
    if has_cleaning:
        return {"suggested_task": "clean"}
    elif has_stats:
        return {"suggested_task": "summarize"}
    elif has_group:
        return {"suggested_task": "group_by"}
    else:
        return {"suggested_task": "auto-detect"}


def get_chart_knowledge_base_summary() -> str:
    """
    Get chart-specific knowledge base summary for ChartBot
    
    Returns:
        Formatted string with chart generation knowledge
    """
    if "chart_knowledge" not in KNOWLEDGE_BASE:
        return "Chart knowledge base not available. Use default chart generation rules."
    
    chart_kb = KNOWLEDGE_BASE["chart_knowledge"]
    summary = []
    
    # Chart type rules
    summary.append("📊 CHART TYPE SELECTION RULES:")
    for chart_type, rules in chart_kb.get("chart_type_rules", {}).items():
        summary.append(f"\n**{chart_type.upper()} Chart:**")
        summary.append(f"  Description: {rules.get('description', 'N/A')}")
        summary.append(f"  Data Requirements: {rules.get('data_requirements', 'N/A')}")
        summary.append(f"  When to Use:")
        for use_case in rules.get("when_to_use", [])[:3]:
            summary.append(f"    - {use_case}")
        summary.append(f"  Examples: {', '.join(rules.get('examples', [])[:3])}")
    
    # Column identification rules
    summary.append("\n\n📋 COLUMN IDENTIFICATION:")
    col_id = chart_kb.get("column_identification", {})
    summary.append("\n**X-Axis Rules:**")
    for rule in col_id.get("x_axis_rules", [])[:4]:
        summary.append(f"  - {rule}")
    summary.append("\n**Y-Axis Rules:**")
    for rule in col_id.get("y_axis_rules", [])[:4]:
        summary.append(f"  - {rule}")
    summary.append("\n**Column Matching:**")
    for rule in col_id.get("column_matching", [])[:3]:
        summary.append(f"  - {rule}")
    
    # Common chart patterns
    summary.append("\n\n🔍 COMMON CHART PATTERNS:")
    for pattern_name, pattern_info in chart_kb.get("common_chart_patterns", {}).items():
        summary.append(f"\nPattern: '{pattern_info.get('pattern', 'N/A')}'")
        summary.append(f"  Chart Type: {pattern_info.get('chart_type', 'N/A')}")
        summary.append(f"  X-Column: {pattern_info.get('x_column', 'N/A')}")
        summary.append(f"  Y-Column: {pattern_info.get('y_column', 'N/A')}")
    
    # Best practices
    summary.append("\n\n✅ BEST PRACTICES:")
    for practice in chart_kb.get("best_practices", [])[:5]:
        summary.append(f"  - {practice}")
    
    # Edge cases
    summary.append("\n\n⚠️ EDGE CASES:")
    for edge_case in chart_kb.get("edge_cases", [])[:3]:
        summary.append(f"\nScenario: {edge_case.get('scenario', 'N/A')}")
        summary.append(f"  Solution: {edge_case.get('solution', 'N/A')}")
    
    return "\n".join(summary)

