"""
Feedback Learning System

Tracks successful/failed executions and uses them to improve prompts.
This enables the system to learn from real user interactions.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class FeedbackLearner:
    """Learn from execution feedback to improve LLM responses"""
    
    def __init__(self):
        """Initialize feedback learner with Supabase connection"""
        try:
            self.supabase = SupabaseClient.get_client()
            self.feedback_table = "llm_feedback"
            logger.info("FeedbackLearner initialized with Supabase.")
        except ValueError as e:
            logger.warning(f"Supabase not configured: {e}. Feedback learning will be disabled.")
            self.supabase = None
    
    def record_success(
        self, 
        user_prompt: str, 
        action_plan: Dict, 
        execution_result: Dict,
        user_id: Optional[str] = None
    ):
        """
        Record successful execution for learning.
        
        Args:
            user_prompt: Original user prompt
            action_plan: Action plan returned by LLM
            execution_result: Result of execution
            user_id: Optional user ID for tracking
        """
        if not self.supabase:
            logger.debug("Supabase not configured. Success not recorded.")
            return
        
        try:
            feedback = {
                "user_prompt": user_prompt,
                "action_plan": json.dumps(action_plan),
                "execution_result": json.dumps(execution_result),
                "success": True,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            self.supabase.table(self.feedback_table).insert(feedback).execute()
            logger.info(f"Recorded successful execution for prompt: {user_prompt[:50]}...")
        except Exception as e:
            logger.error(f"Error recording success: {e}")
    
    def record_failure(
        self, 
        user_prompt: str, 
        action_plan: Dict, 
        error: str,
        user_id: Optional[str] = None
    ):
        """
        Record failed execution for learning.
        
        Args:
            user_prompt: Original user prompt
            action_plan: Action plan returned by LLM
            error: Error message
            user_id: Optional user ID for tracking
        """
        if not self.supabase:
            logger.debug("Supabase not configured. Failure not recorded.")
            return
        
        try:
            feedback = {
                "user_prompt": user_prompt,
                "action_plan": json.dumps(action_plan),
                "error": error,
                "success": False,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
            self.supabase.table(self.feedback_table).insert(feedback).execute()
            logger.warning(f"Recorded failed execution for prompt: {user_prompt[:50]}... Error: {error[:100]}")
        except Exception as e:
            logger.error(f"Error recording failure: {e}")
    
    def get_similar_successful_examples(
        self, 
        user_prompt: str, 
        limit: int = 5
    ) -> List[Dict]:
        """
        Get similar successful examples for few-shot learning.
        
        Uses simple keyword matching. For better results, consider using
        vector similarity search or more advanced matching.
        
        Args:
            user_prompt: User's prompt to find similar examples for
            limit: Maximum number of examples to return
            
        Returns:
            List of similar successful examples
        """
        if not self.supabase:
            return []
        
        try:
            # Get recent successful examples
            result = self.supabase.table(self.feedback_table).select("*").eq(
                "success", True
            ).order("created_at", desc=True).limit(limit * 3).execute()
            
            if not result.data:
                return []
            
            # Simple similarity: check for common keywords
            prompt_lower = user_prompt.lower()
            prompt_words = set(prompt_lower.split())
            
            similar = []
            for example in result.data:
                example_prompt = example["user_prompt"].lower()
                example_words = set(example_prompt.split())
                
                # Count common words (excluding common stop words)
                stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
                common_words = (prompt_words & example_words) - stop_words
                
                # If at least 2 meaningful common words, consider it similar
                if len(common_words) >= 2:
                    try:
                        similar.append({
                            "prompt": example["user_prompt"],
                            "action_plan": json.loads(example["action_plan"]),
                            "similarity_score": len(common_words)
                        })
                    except json.JSONDecodeError:
                        continue
                    
                    if len(similar) >= limit:
                        break
            
            # Sort by similarity score (descending)
            similar.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return similar[:limit]
            
        except Exception as e:
            logger.error(f"Error getting similar examples: {e}")
            return []
    
    def get_failure_patterns(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """
        Analyze failure patterns to improve prompts.
        
        Args:
            limit: Maximum number of failures to analyze
            
        Returns:
            Dictionary mapping error types to lists of failures
        """
        if not self.supabase:
            return {}
        
        try:
            result = self.supabase.table(self.feedback_table).select("*").eq(
                "success", False
            ).order("created_at", desc=True).limit(limit).execute()
            
            if not result.data:
                return {}
            
            # Group by error type
            error_patterns = {}
            for failure in result.data:
                error = failure.get("error", "unknown")
                error_key = error.split(":")[0] if ":" in error else error[:50]  # Use first part of error
                
                if error_key not in error_patterns:
                    error_patterns[error_key] = []
                
                try:
                    error_patterns[error_key].append({
                        "prompt": failure["user_prompt"],
                        "action_plan": json.loads(failure["action_plan"]),
                        "full_error": error
                    })
                except json.JSONDecodeError:
                    continue
            
            return error_patterns
            
        except Exception as e:
            logger.error(f"Error getting failure patterns: {e}")
            return {}
    
    def get_success_rate(self, days: int = 7) -> Dict[str, float]:
        """
        Get success rate statistics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with success rate statistics
        """
        if not self.supabase:
            return {"success_rate": 0.0, "total": 0, "successful": 0, "failed": 0}
        
        try:
            # Get all feedback from last N days
            cutoff_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
            result = self.supabase.table(self.feedback_table).select("success").gte(
                "created_at", cutoff_date
            ).execute()
            
            if not result.data:
                return {"success_rate": 0.0, "total": 0, "successful": 0, "failed": 0}
            
            total = len(result.data)
            successful = sum(1 for item in result.data if item.get("success", False))
            failed = total - successful
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            return {
                "success_rate": round(success_rate, 2),
                "total": total,
                "successful": successful,
                "failed": failed
            }
            
        except Exception as e:
            logger.error(f"Error getting success rate: {e}")
            return {"success_rate": 0.0, "total": 0, "successful": 0, "failed": 0}
    
    def export_training_dataset(self, output_file: str = "training_dataset.jsonl", limit: int = 1000):
        """
        Export successful examples as training dataset.
        
        Args:
            output_file: Path to output file
            limit: Maximum number of examples to export
            
        Returns:
            Path to exported file
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Cannot export training dataset.")
            return None
        
        try:
            # Get all successful examples
            result = self.supabase.table(self.feedback_table).select("*").eq(
                "success", True
            ).order("created_at", desc=True).limit(limit).execute()
            
            if not result.data:
                logger.warning("No successful examples found to export.")
                return None
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in result.data:
                    try:
                        training_example = {
                            "prompt": example["user_prompt"],
                            "response": json.loads(example["action_plan"])
                        }
                        f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Exported {len(result.data)} examples to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting training dataset: {e}")
            return None

