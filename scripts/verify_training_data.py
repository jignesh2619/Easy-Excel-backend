"""
Detailed verification script for training data
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.training_data_loader import TrainingDataLoader
import json

def main():
    print("=" * 60)
    print("TRAINING DATA VERIFICATION")
    print("=" * 60)
    
    # Initialize loader
    loader = TrainingDataLoader()
    
    # Get statistics
    stats = loader.get_statistics()
    
    print(f"\n📊 STATISTICS:")
    print(f"   Total Examples Loaded: {stats['total_examples']}")
    
    if stats['total_examples'] == 0:
        print("\n❌ No training data found!")
        print("\nPlease check:")
        print("1. Files are in: backend/data/")
        print("2. Files are .xlsx or .xls format")
        print("3. Files have 'user_message' and 'model_response' columns")
        return
    
    print(f"\n📁 SOURCES:")
    for source, count in stats['sources'].items():
        print(f"   ✅ {source}: {count} examples")
    
    # Show sample prompts
    print(f"\n📝 SAMPLE PROMPTS (first 5):")
    for i, prompt in enumerate(stats.get('sample_prompts', [])[:5], 1):
        print(f"   {i}. {prompt}")
    
    # Test example retrieval for different scenarios
    print("\n" + "=" * 60)
    print("TESTING EXAMPLE RETRIEVAL")
    print("=" * 60)
    
    test_cases = [
        ("remove duplicates and create dashboard", ["cleaning", "charts"]),
        ("what's the sum of all sales", ["formulas"]),
        ("group by region and calculate average", ["pivot", "formulas"]),
        ("sort by date descending", ["sorting"]),
        ("filter rows where amount > 1000", ["filtering"])
    ]
    
    for prompt, categories in test_cases:
        print(f"\n🔍 Testing: '{prompt}'")
        examples = loader.get_examples_for_prompt(prompt, limit=2, categories=categories)
        print(f"   Found {len(examples)} similar examples:")
        for i, ex in enumerate(examples, 1):
            print(f"   {i}. {ex['prompt'][:70]}...")
            # Check if action_plan is valid JSON
            if isinstance(ex.get('action_plan'), dict):
                task = ex['action_plan'].get('task', 'unknown')
                print(f"      → Task: {task}")
            if ex.get('source_file'):
                print(f"      → Source: {ex['source_file']}")
    
    # Show detailed example
    if loader.datasets:
        print("\n" + "=" * 60)
        print("DETAILED EXAMPLE (First Entry)")
        print("=" * 60)
        first_ex = loader.datasets[0]
        print(f"\nPrompt: {first_ex['prompt']}")
        print(f"\nAction Plan:")
        print(json.dumps(first_ex['action_plan'], indent=2))
        if first_ex.get('execution_instructions'):
            print(f"\nExecution Instructions: {first_ex['execution_instructions']}")
        print(f"\nSource: {first_ex.get('source_file', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)
    print("\n🎉 Your training data is loaded and ready!")
    print("\nThe system will automatically use these examples")
    print("in LLM prompts for better accuracy.")
    print("\n💡 Next: Restart your backend server to activate the training data.")

if __name__ == "__main__":
    main()

