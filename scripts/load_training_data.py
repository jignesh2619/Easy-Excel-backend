"""
Script to verify training data is loaded correctly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.training_data_loader import TrainingDataLoader

def main():
    print("Training Data Loader Test")
    print("=" * 50)
    
    # Initialize loader
    loader = TrainingDataLoader()
    
    # Get statistics
    stats = loader.get_statistics()
    print(f"\nTotal Examples Loaded: {stats['total_examples']}")
    
    if stats['sources']:
        print("\nSources:")
        for source, count in stats['sources'].items():
            print(f"  - {source}: {count} examples")
    else:
        print("\n⚠️  No training data found!")
        print("\nTo add training data:")
        print("1. Place your Excel files in: backend/data/")
        print("2. Files should be named:")
        print("   - dataset_realistic_500.xlsx")
        print("   - dataset_multicategory_500.xlsx")
        print("   - dataset_jsonheavy_500.xlsx")
        print("3. Each file should have:")
        print("   - Column A: User prompts")
        print("   - Column B: Action plans (JSON)")
        print("   - Column C: Execution instructions (optional)")
        return
    
    # Test example retrieval
    print("\n" + "=" * 50)
    print("Testing Example Retrieval:")
    print("=" * 50)
    
    test_prompts = [
        "remove duplicates and create dashboard",
        "what's the sum of all sales",
        "group by region and calculate average"
    ]
    
    for prompt in test_prompts:
        print(f"\nPrompt: '{prompt}'")
        examples = loader.get_examples_for_prompt(prompt, limit=2)
        print(f"Found {len(examples)} similar examples:")
        for i, ex in enumerate(examples, 1):
            print(f"  {i}. {ex['prompt'][:60]}...")
            if ex.get('source_file'):
                print(f"     (from {ex['source_file']})")
    
    print("\n" + "=" * 50)
    print("✅ Training data loader is working!")
    print("\nThe system will automatically use these examples")
    print("in LLM prompts for better accuracy.")

if __name__ == "__main__":
    main()

