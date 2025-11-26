"""
Test script to verify the feedback system is working correctly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.feedback_learner import FeedbackLearner

def test_feedback_system():
    """Test the feedback learning system"""
    print("Testing Feedback Learning System...")
    print("=" * 50)
    
    # Initialize feedback learner
    try:
        learner = FeedbackLearner()
        print("✅ FeedbackLearner initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize FeedbackLearner: {e}")
        return False
    
    # Test recording success
    print("\n1. Testing success recording...")
    try:
        test_action_plan = {
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
        test_result = {
            "status": "success",
            "rows_processed": 100,
            "chart_generated": True
        }
        
        learner.record_success(
            user_prompt="remove duplicates and create dashboard",
            action_plan=test_action_plan,
            execution_result=test_result
        )
        print("✅ Success recorded successfully")
    except Exception as e:
        print(f"❌ Failed to record success: {e}")
        return False
    
    # Test recording failure
    print("\n2. Testing failure recording...")
    try:
        learner.record_failure(
            user_prompt="test prompt that failed",
            action_plan=test_action_plan,
            error="Test error message"
        )
        print("✅ Failure recorded successfully")
    except Exception as e:
        print(f"❌ Failed to record failure: {e}")
        return False
    
    # Test getting similar examples
    print("\n3. Testing similar examples retrieval...")
    try:
        examples = learner.get_similar_successful_examples(
            "remove duplicates and create dashboard",
            limit=5
        )
        print(f"✅ Retrieved {len(examples)} similar examples")
        if examples:
            print(f"   First example: {examples[0]['prompt'][:50]}...")
    except Exception as e:
        print(f"❌ Failed to get similar examples: {e}")
        return False
    
    # Test success rate
    print("\n4. Testing success rate calculation...")
    try:
        stats = learner.get_success_rate(days=7)
        print(f"✅ Success rate: {stats['success_rate']}%")
        print(f"   Total: {stats['total']}, Successful: {stats['successful']}, Failed: {stats['failed']}")
    except Exception as e:
        print(f"❌ Failed to get success rate: {e}")
        return False
    
    # Test failure patterns
    print("\n5. Testing failure pattern analysis...")
    try:
        patterns = learner.get_failure_patterns(limit=5)
        print(f"✅ Found {len(patterns)} failure patterns")
        for error_type, failures in list(patterns.items())[:3]:
            print(f"   - {error_type}: {len(failures)} occurrences")
    except Exception as e:
        print(f"❌ Failed to get failure patterns: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Feedback system is working correctly.")
    print("\nNext steps:")
    print("1. Process some files through your API")
    print("2. Check the llm_feedback table in Supabase")
    print("3. The system will automatically learn from successful executions")
    
    return True

if __name__ == "__main__":
    success = test_feedback_system()
    sys.exit(0 if success else 1)

