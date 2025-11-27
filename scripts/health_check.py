"""
Comprehensive Health Check Script

Checks all systems are working correctly.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def check_training_data():
    """Check training data is loaded"""
    print("📚 Checking Training Data...")
    try:
        from services.training_data_loader import TrainingDataLoader
        loader = TrainingDataLoader()
        stats = loader.get_statistics()
        
        if stats['total_examples'] > 0:
            print(f"   ✅ Loaded {stats['total_examples']} examples")
            for source, count in stats['sources'].items():
                print(f"      - {source}: {count} examples")
            return True
        else:
            print("   ⚠️  No training data found")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_feedback_system():
    """Check feedback system is working"""
    print("\n📊 Checking Feedback System...")
    try:
        from services.feedback_learner import FeedbackLearner
        learner = FeedbackLearner()
        
        if learner.supabase:
            stats = learner.get_success_rate(days=7)
            print(f"   ✅ Feedback system active")
            print(f"      - Total: {stats['total']}")
            print(f"      - Success rate: {stats['success_rate']}%")
            return True
        else:
            print("   ⚠️  Supabase not configured")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_llm_agent():
    """Check LLM agent is configured"""
    print("\n🤖 Checking LLM Agent...")
    try:
        from services.llm_agent import LLMAgent
        agent = LLMAgent()
        
        print(f"   ✅ LLM Agent initialized")
        print(f"      - Model: {agent.model}")
        print(f"      - Training data loader: {'✅' if agent.training_data_loader else '❌'}")
        print(f"      - Feedback learner: {'✅' if agent.feedback_learner else '❌'}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_user_service():
    """Check user service is working"""
    print("\n👤 Checking User Service...")
    try:
        from services.user_service import UserService
        service = UserService()
        
        if service.supabase:
            print("   ✅ User service active")
            print("      - Supabase connected")
            return True
        else:
            print("   ⚠️  Supabase not configured")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("\n🔐 Checking Environment...")
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required = [
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]
    
    all_present = True
    for var in required:
        if os.getenv(var):
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing")
            all_present = False
    
    return all_present

def main():
    print("=" * 60)
    print("EASYEXCEL HEALTH CHECK")
    print("=" * 60)
    
    results = {
        "Training Data": check_training_data(),
        "Feedback System": check_feedback_system(),
        "LLM Agent": check_llm_agent(),
        "User Service": check_user_service(),
        "Environment": check_environment()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_ok = all(results.values())
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component}")
    
    if all_ok:
        print("\n🎉 All systems operational!")
    else:
        print("\n⚠️  Some issues found. Please review above.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

