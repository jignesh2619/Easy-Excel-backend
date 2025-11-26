"""
Script to enhance few-shot examples in prompts

This script helps add more diverse examples to improve LLM understanding.
"""

import json
from pathlib import Path

# Comprehensive examples covering various scenarios
ENHANCED_EXAMPLES = [
    {
        "user_prompt": "remove duplicates and create dashboard",
        "response": {
            "task": "clean",
            "chart_type": "bar",
            "columns_needed": [],
            "operations": [
                {
                    "type": "remove_duplicates",
                    "description": "Remove duplicate rows",
                    "execution_instructions": {
                        "method": "pandas.drop_duplicates",
                        "args": [],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "what's the sum of all sales amounts",
        "response": {
            "task": "formula",
            "chart_type": "none",
            "columns_needed": ["sales"],
            "formula": {
                "type": "sum",
                "column": "sales"
            },
            "operations": [
                {
                    "type": "sum",
                    "description": "Calculate sum of sales column",
                    "params": {"column": "sales"},
                    "execution_instructions": {
                        "method": "formula.SUM",
                        "args": ["sales"],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "group by region and calculate average revenue",
        "response": {
            "task": "group_by",
            "chart_type": "none",
            "columns_needed": ["region", "revenue"],
            "group_by_column": "region",
            "aggregate_function": "mean",
            "aggregate_column": "revenue",
            "operations": [
                {
                    "type": "group_by",
                    "description": "Group by region and average revenue",
                    "params": {
                        "group_by_column": "region",
                        "aggregate_function": "mean",
                        "aggregate_column": "revenue"
                    },
                    "execution_instructions": {
                        "method": "pandas.groupby",
                        "args": ["region"],
                        "kwargs": {"agg": {"revenue": "mean"}}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "clean the data, remove empty rows, and show me a chart",
        "response": {
            "task": "clean",
            "chart_type": "bar",
            "columns_needed": [],
            "operations": [
                {
                    "type": "remove_empty_rows",
                    "description": "Remove rows with all empty values",
                    "execution_instructions": {
                        "method": "pandas.dropna",
                        "args": [],
                        "kwargs": {"how": "all"}
                    }
                },
                {
                    "type": "remove_duplicates",
                    "description": "Remove duplicate rows",
                    "execution_instructions": {
                        "method": "pandas.drop_duplicates",
                        "args": [],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "filter rows where amount is greater than 1000",
        "response": {
            "task": "filter",
            "chart_type": "none",
            "columns_needed": ["amount"],
            "filters": {
                "column": "amount",
                "condition": ">",
                "value": 1000
            },
            "operations": [
                {
                    "type": "filter",
                    "description": "Filter rows where amount > 1000",
                    "params": {
                        "column": "amount",
                        "condition": ">",
                        "value": 1000
                    },
                    "execution_instructions": {
                        "method": "pandas.query",
                        "args": [],
                        "kwargs": {"expr": "amount > 1000"}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "sort by date descending and show top 10",
        "response": {
            "task": "sort",
            "chart_type": "none",
            "columns_needed": ["date"],
            "sort": {
                "columns": [
                    {
                        "column_name": "date",
                        "order": "desc",
                        "data_type": "date"
                    }
                ]
            },
            "operations": [
                {
                    "type": "sort",
                    "description": "Sort by date descending",
                    "params": {
                        "columns": [{"column_name": "date", "order": "desc", "data_type": "date"}]
                    },
                    "execution_instructions": {
                        "method": "pandas.sort_values",
                        "args": ["date"],
                        "kwargs": {"ascending": False}
                    }
                },
                {
                    "type": "limit",
                    "description": "Show top 10 rows",
                    "params": {"n": 10},
                    "execution_instructions": {
                        "method": "pandas.head",
                        "args": [10],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "combine first name and last name columns",
        "response": {
            "task": "formula",
            "chart_type": "none",
            "columns_needed": ["first_name", "last_name"],
            "formula": {
                "type": "concat",
                "columns": ["first_name", "last_name"],
                "parameters": {
                    "separator": " "
                }
            },
            "operations": [
                {
                    "type": "concat",
                    "description": "Combine first_name and last_name",
                    "params": {
                        "columns": ["first_name", "last_name"],
                        "separator": " "
                    },
                    "execution_instructions": {
                        "method": "formula.CONCAT",
                        "args": [["first_name", "last_name"], " "],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "find duplicate emails and highlight them",
        "response": {
            "task": "formula",
            "chart_type": "none",
            "columns_needed": ["email"],
            "formula": {
                "type": "highlight_duplicates",
                "column": "email"
            },
            "operations": [
                {
                    "type": "highlight_duplicates",
                    "description": "Find and highlight duplicate emails",
                    "params": {"column": "email"},
                    "execution_instructions": {
                        "method": "formula.highlight_duplicates",
                        "args": ["email"],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "give me summary statistics of the sales column",
        "response": {
            "task": "summarize",
            "chart_type": "none",
            "columns_needed": ["sales"],
            "operations": [
                {
                    "type": "summarize",
                    "description": "Generate summary statistics for sales",
                    "params": {"columns": ["sales"]},
                    "execution_instructions": {
                        "method": "pandas.describe",
                        "args": [],
                        "kwargs": {}
                    }
                }
            ]
        }
    },
    {
        "user_prompt": "remove duplicates, fix formatting, and create a bar chart",
        "response": {
            "task": "clean",
            "chart_type": "bar",
            "columns_needed": [],
            "operations": [
                {
                    "type": "remove_duplicates",
                    "description": "Remove duplicate rows",
                    "execution_instructions": {
                        "method": "pandas.drop_duplicates",
                        "args": [],
                        "kwargs": {}
                    }
                },
                {
                    "type": "fix_formatting",
                    "description": "Trim whitespace from text columns",
                    "execution_instructions": {
                        "method": "custom",
                        "code": "df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)"
                    }
                }
            ]
        }
    }
]

def export_examples_to_prompt_format(output_file: str = "few_shot_examples.txt"):
    """Export examples in prompt format"""
    with open(output_file, 'w') as f:
        f.write("FEW-SHOT EXAMPLES FOR LLM PROMPT:\n\n")
        for i, example in enumerate(ENHANCED_EXAMPLES, 1):
            f.write(f"Example {i}:\n")
            f.write(f"User: {example['user_prompt']}\n")
            f.write(f"Response:\n{json.dumps(example['response'], indent=2)}\n\n")
    
    print(f"Exported {len(ENHANCED_EXAMPLES)} examples to {output_file}")

def export_examples_to_json(output_file: str = "few_shot_examples.json"):
    """Export examples as JSON for easy loading"""
    with open(output_file, 'w') as f:
        json.dump(ENHANCED_EXAMPLES, f, indent=2)
    
    print(f"Exported {len(ENHANCED_EXAMPLES)} examples to {output_file}")

if __name__ == "__main__":
    export_examples_to_prompt_format()
    export_examples_to_json()
    print("\n✅ Examples exported successfully!")
    print("Next: Add these examples to utils/prompts.py in FEW_SHOT_EXAMPLES section")

