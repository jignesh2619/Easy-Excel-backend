"""
User and Subscription Management Service

Handles user accounts, API keys, and subscription verification using Supabase.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users and subscriptions."""
    
    def __init__(self):
        """Initialize Supabase connection."""
        try:
            self.supabase = SupabaseClient.get_client()
            logger.info("UserService initialized with Supabase.")
        except ValueError as e:
            logger.warning(f"Supabase not configured: {e}. User features will be disabled.")
            self.supabase = None
    
    def create_user(self, email: str, plan: str = "Free") -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            email: User's email address
            plan: Subscription plan (Free, Starter, Pro)
            
        Returns:
            User data with API key
        """
        if not self.supabase:
            raise ValueError("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_KEY.")
        
        # Generate unique user ID and API key
        user_id = f"user_{secrets.token_urlsafe(16)}"
        api_key = f"ex_{secrets.token_urlsafe(32)}"
        
        try:
            # Check if user already exists
            existing_user = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if existing_user.data:
                # User exists, return existing user
                user = existing_user.data[0]
                return {
                    "user_id": user["id"],
                    "email": user["email"],
                    "api_key": user["api_key"],
                    "plan": user["plan"]
                }
            
            # Create new user
            user_data = {
                "id": user_id,
                "email": email,
                "api_key": api_key,
                "plan": plan,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("users").insert(user_data).execute()
            
            if not result.data:
                raise Exception("Failed to create user")
            
            user = result.data[0]
            
            # Create subscription record
            tokens_limit = self._get_tokens_limit(plan)
            subscription_data = {
                "id": f"sub_{secrets.token_urlsafe(16)}",
                "user_id": user_id,
                "plan_name": plan,
                "status": "active",
                "tokens_used": 0,
                "tokens_limit": tokens_limit,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.supabase.table("subscriptions").insert(subscription_data).execute()
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "api_key": user["api_key"],
                "plan": user["plan"]
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: User's email address
            
        Returns:
            User data or None if not found
        """
        if not self.supabase:
            return None
        
        try:
            user_result = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if not user_result.data:
                return None
            
            user = user_result.data[0]
            user_id = user["id"]
            
            # Get latest ACTIVE subscription for this user
            subscription_result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            subscription = subscription_result.data[0] if subscription_result.data else None
            
            tokens_limit = subscription.get("tokens_limit") if subscription else self._get_tokens_limit(user["plan"])
            tokens_used = subscription.get("tokens_used", 0) if subscription else 0
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "api_key": user.get("api_key"),  # May not exist if using Supabase Auth
                "plan": user["plan"],
                "subscription_status": subscription.get("status", "active") if subscription else "active",
                "tokens_used": tokens_used,
                "tokens_limit": tokens_limit,
                "expires_at": subscription.get("expires_at") if subscription else None
            }
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_supabase_id(self, supabase_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by Supabase Auth user ID.
        
        Args:
            supabase_user_id: Supabase Auth user ID
            
        Returns:
            User data or None if not found
        """
        if not self.supabase:
            return None
        
        try:
            # Check if we have a mapping in users table (supabase_auth_id column)
            user_result = self.supabase.table("users").select("*").eq("supabase_auth_id", supabase_user_id).execute()
            
            if not user_result.data:
                return None
            
            user = user_result.data[0]
            user_id = user["id"]
            
            # Get latest ACTIVE subscription
            subscription_result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            subscription = subscription_result.data[0] if subscription_result.data else None
            
            tokens_limit = subscription.get("tokens_limit") if subscription else self._get_tokens_limit(user["plan"])
            tokens_used = subscription.get("tokens_used", 0) if subscription else 0
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "plan": user["plan"],
                "subscription_status": subscription.get("status", "active") if subscription else "active",
                "tokens_used": tokens_used,
                "tokens_limit": tokens_limit,
                "expires_at": subscription.get("expires_at") if subscription else None
            }
        except Exception as e:
            logger.error(f"Error getting user by Supabase ID: {e}")
            return None
    
    def create_user_from_supabase_auth(self, supabase_user_id: str, email: str, plan: str = "Free") -> Dict[str, Any]:
        """
        Create a new user from Supabase Auth.
        
        Args:
            supabase_user_id: Supabase Auth user ID
            email: User's email address
            plan: Subscription plan (Free, Starter, Pro)
            
        Returns:
            User data
        """
        if not self.supabase:
            raise ValueError("Supabase is not configured.")
        
        # Generate unique user ID
        user_id = f"user_{secrets.token_urlsafe(16)}"
        
        try:
            # Check if user already exists by Supabase Auth ID
            existing_user = self.supabase.table("users").select("*").eq("supabase_auth_id", supabase_user_id).execute()
            
            if existing_user.data:
                user = existing_user.data[0]
                user_id = user["id"]
                # Get ACTIVE subscription data
                subscription_result = self.supabase.table("subscriptions").select("*").eq(
                    "user_id", user_id
                ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
                subscription = subscription_result.data[0] if subscription_result.data else None
                tokens_limit = subscription.get("tokens_limit") if subscription else self._get_tokens_limit(user["plan"])
                tokens_used = subscription.get("tokens_used", 0) if subscription else 0
                return {
                    "user_id": user["id"],
                    "email": user["email"],
                    "plan": user["plan"],
                    "subscription_status": subscription.get("status", "active") if subscription else "active",
                    "tokens_used": tokens_used,
                    "tokens_limit": tokens_limit,
                    "expires_at": subscription.get("expires_at") if subscription else None
                }
            
            # Check if user exists by email
            existing_by_email = self.supabase.table("users").select("*").eq("email", email).execute()
            if existing_by_email.data:
                # Update existing user with Supabase Auth ID
                user = existing_by_email.data[0]
                user_id = user["id"]
                self.supabase.table("users").update({
                    "supabase_auth_id": supabase_user_id,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", user_id).execute()
                # Get ACTIVE subscription data
                subscription_result = self.supabase.table("subscriptions").select("*").eq(
                    "user_id", user_id
                ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
                subscription = subscription_result.data[0] if subscription_result.data else None
                tokens_limit = subscription.get("tokens_limit") if subscription else self._get_tokens_limit(user["plan"])
                tokens_used = subscription.get("tokens_used", 0) if subscription else 0
                return {
                    "user_id": user["id"],
                    "email": user["email"],
                    "plan": user["plan"],
                    "subscription_status": subscription.get("status", "active") if subscription else "active",
                    "tokens_used": tokens_used,
                    "tokens_limit": tokens_limit,
                    "expires_at": subscription.get("expires_at") if subscription else None
                }
            
            # Create new user
            user_data = {
                "id": user_id,
                "supabase_auth_id": supabase_user_id,
                "email": email,
                "plan": plan,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("users").insert(user_data).execute()
            
            if not result.data:
                raise Exception("Failed to create user")
            
            user = result.data[0]
            
            # Create subscription record
            tokens_limit = self._get_tokens_limit(plan)
            subscription_data = {
                "id": f"sub_{secrets.token_urlsafe(16)}",
                "user_id": user_id,
                "plan_name": plan,
                "status": "active",
                "tokens_used": 0,
                "tokens_limit": tokens_limit,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.supabase.table("subscriptions").insert(subscription_data).execute()
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "plan": user["plan"],
                "subscription_status": "active",
                "tokens_used": 0,
                "tokens_limit": tokens_limit,
                "expires_at": None
            }
            
        except Exception as e:
            logger.error(f"Error creating user from Supabase Auth: {e}")
            raise
    
    def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Get user by API key.
        
        Args:
            api_key: User's API key
            
        Returns:
            User data or None if not found
        """
        if not self.supabase:
            return None
        
        try:
            # Get user
            user_result = self.supabase.table("users").select("*").eq("api_key", api_key).execute()
            
            if not user_result.data:
                return None
            
            user = user_result.data[0]
            user_id = user["id"]
            
            # Get latest ACTIVE subscription for this user
            subscription_result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            subscription = subscription_result.data[0] if subscription_result.data else None
            
            tokens_limit = subscription.get("tokens_limit") if subscription else self._get_tokens_limit(user["plan"])
            tokens_used = subscription.get("tokens_used", 0) if subscription else 0
            
            return {
                "user_id": user["id"],
                "email": user["email"],
                "plan": user["plan"],
                "subscription_status": subscription.get("status", "active") if subscription else "active",
                "tokens_used": tokens_used,
                "tokens_limit": tokens_limit,
                "expires_at": subscription.get("expires_at") if subscription else None
            }
        except Exception as e:
            logger.error(f"Error getting user by API key: {e}")
            return None
    
    def update_subscription(self, user_id: str, paypal_subscription_id: str, plan_name: str, status: str):
        """
        Update user subscription from PayPal webhook.
        
        Args:
            user_id: User ID
            paypal_subscription_id: PayPal subscription ID
            plan_name: Plan name (Starter, Pro)
            status: Subscription status
        """
        if not self.supabase:
            raise ValueError("Supabase is not configured.")
        
        try:
            # Update user plan
            self.supabase.table("users").update({
                "plan": plan_name,
                "updated_at": datetime.now().isoformat()
            }).eq("id", user_id).execute()
            
            # Get latest ACTIVE subscription for user (to preserve tokens_used if reactivating)
            result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            tokens_limit = self._get_tokens_limit(plan_name)
            expires_at = None
            if plan_name != "Free":
                # Set expiration to 30 days from now for paid plans
                expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            
            subscription_data = {
                "paypal_subscription_id": paypal_subscription_id,
                "plan_name": plan_name,
                "status": status,
                "tokens_limit": tokens_limit,
                "expires_at": expires_at,
                "updated_at": datetime.now().isoformat()
            }
            
            if result.data and status == "active":
                # Update existing active subscription (preserve tokens_used)
                existing_sub = result.data[0]
                subscription_data["tokens_used"] = existing_sub.get("tokens_used", 0)
                self.supabase.table("subscriptions").update(subscription_data).eq(
                    "id", existing_sub["id"]
                ).execute()
            else:
                # Create new subscription (reset tokens_used to 0 for new subscriptions)
                subscription_data.update({
                    "id": f"sub_{secrets.token_urlsafe(16)}",
                    "user_id": user_id,
                    "tokens_used": 0,
                    "created_at": datetime.now().isoformat()
                })
                self.supabase.table("subscriptions").insert(subscription_data).execute()
                
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            raise
    
    def check_token_limit(self, user_id: str, tokens_needed: int = 0) -> Dict[str, Any]:
        """
        Check if user has enough tokens.
        
        Args:
            user_id: User ID
            tokens_needed: Number of tokens needed for operation
            
        Returns:
            Dictionary with can_proceed, tokens_used, tokens_limit, tokens_remaining
        """
        if not self.supabase:
            return {
                "can_proceed": False,
                "error": "Supabase is not configured"
            }
        
        try:
            # Get latest ACTIVE subscription
            result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            if not result.data:
                return {
                    "can_proceed": False,
                    "error": "No active subscription found"
                }
            
            subscription = result.data[0]
            tokens_used = subscription.get("tokens_used", 0) or 0
            tokens_limit = subscription.get("tokens_limit", 0)
            status = subscription.get("status", "active")
            expires_at = subscription.get("expires_at")
            
            # Check if subscription is active
            if status != "active":
                return {
                    "can_proceed": False,
                    "error": "Subscription is not active"
                }
            
            # Check expiration
            if expires_at:
                expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00") if "Z" in expires_at else expires_at)
                if datetime.now() > expires:
                    return {
                        "can_proceed": False,
                        "error": "Subscription has expired"
                    }
            
            tokens_remaining = tokens_limit - tokens_used
            
            return {
                "can_proceed": tokens_remaining >= tokens_needed,
                "tokens_used": tokens_used,
                "tokens_limit": tokens_limit,
                "tokens_remaining": tokens_remaining,
                "status": status
            }
        except Exception as e:
            logger.error(f"Error checking token limit: {e}")
            return {
                "can_proceed": False,
                "error": f"Error checking token limit: {str(e)}"
            }
    
    def record_token_usage(self, user_id: str, tokens_used: int, operation: str = "file_processing"):
        """
        Record token usage for a user.
        
        Args:
            user_id: User ID
            tokens_used: Number of tokens used (ONLY OpenAI API tokens, not backend operations)
            operation: Type of operation
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Token usage not recorded.")
            return
        
        # Validate token count is reasonable (sanity check)
        if tokens_used < 0:
            logger.error(f"❌ Invalid token count: {tokens_used}. Not recording.")
            return
        if tokens_used > 100000:
            logger.warning(f"⚠️ Suspiciously high token count: {tokens_used} for operation {operation}. Recording anyway but please investigate.")
        
        try:
            logger.info(f"📊 Recording token usage: user_id={user_id}, tokens={tokens_used}, operation={operation}")
            
            # Record usage in token_usage table
            usage_data = {
                "user_id": user_id,
                "tokens_used": tokens_used,
                "operation": operation,
                "created_at": datetime.now().isoformat()
            }
            self.supabase.table("token_usage").insert(usage_data).execute()
            
            # Update subscription tokens_used
            # Get current tokens_used (latest subscription)
            result = self.supabase.table("subscriptions").select("id, tokens_used").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            if result.data:
                subscription = result.data[0]
                subscription_id = subscription["id"]
                current_tokens = subscription.get("tokens_used", 0) or 0
                new_tokens = current_tokens + tokens_used
                
                logger.info(f"📊 Token usage update: current={current_tokens}, adding={tokens_used}, new_total={new_tokens}")
                
                # Update the specific subscription
                self.supabase.table("subscriptions").update({
                    "tokens_used": new_tokens,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", subscription_id).execute()
            else:
                logger.warning(f"⚠️ No active subscription found for user {user_id}. Token usage recorded in audit table but not in subscription.")
                
        except Exception as e:
            logger.error(f"Error recording token usage: {e}")
    
    def get_token_usage_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get token usage analytics for a user.
        
        Args:
            user_id: User ID
            days: Number of days to look back (default: 30)
            
        Returns:
            Dictionary with token usage statistics
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Cannot get token analytics.")
            return {
                "total_tokens": 0,
                "operations": {},
                "daily_breakdown": [],
                "recent_usage": []
            }
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get all token usage records for the user
            result = self.supabase.table("token_usage").select("*").eq(
                "user_id", user_id
            ).gte("created_at", cutoff_date).order("created_at", desc=True).execute()
            
            records = result.data if result.data else []
            
            # Calculate statistics
            total_tokens = sum(int(r.get("tokens_used", 0) or 0) for r in records)
            
            # Group by operation type
            operations = {}
            for record in records:
                op = record.get("operation", "unknown")
                tokens = int(record.get("tokens_used", 0) or 0)
                if op not in operations:
                    operations[op] = {"count": 0, "total_tokens": 0, "avg_tokens": 0}
                operations[op]["count"] += 1
                operations[op]["total_tokens"] += tokens
            
            # Calculate averages
            for op in operations:
                operations[op]["avg_tokens"] = operations[op]["total_tokens"] // operations[op]["count"] if operations[op]["count"] > 0 else 0
            
            # Daily breakdown
            daily_breakdown = {}
            for record in records:
                date_str = record.get("created_at", "")[:10]  # Get YYYY-MM-DD
                if date_str:
                    if date_str not in daily_breakdown:
                        daily_breakdown[date_str] = {"count": 0, "tokens": 0}
                    daily_breakdown[date_str]["count"] += 1
                    daily_breakdown[date_str]["tokens"] += int(record.get("tokens_used", 0) or 0)
            
            # Convert to list and sort by date
            daily_list = [
                {"date": date, "count": data["count"], "tokens": data["tokens"]}
                for date, data in sorted(daily_breakdown.items(), reverse=True)
            ]
            
            # Recent usage (last 10 records)
            recent_usage = [
                {
                    "operation": r.get("operation", "unknown"),
                    "tokens": int(r.get("tokens_used", 0) or 0),
                    "created_at": r.get("created_at", "")
                }
                for r in records[:10]
            ]
            
            # Get current subscription info
            subscription_result = self.supabase.table("subscriptions").select("tokens_used, tokens_limit").eq(
                "user_id", user_id
            ).eq("status", "active").order("created_at", desc=True).limit(1).execute()
            
            current_usage = 0
            token_limit = 0
            if subscription_result.data:
                sub = subscription_result.data[0]
                current_usage = sub.get("tokens_used", 0) or 0
                token_limit = sub.get("tokens_limit", 0) or 0
            
            return {
                "total_tokens_last_30_days": total_tokens,
                "current_usage": current_usage,
                "token_limit": token_limit,
                "tokens_remaining": max(0, token_limit - current_usage),
                "operations": operations,
                "daily_breakdown": daily_list,
                "recent_usage": recent_usage,
                "total_operations": len(records)
            }
            
        except Exception as e:
            logger.error(f"Error getting token usage analytics: {e}")
            return {
                "total_tokens": 0,
                "operations": {},
                "daily_breakdown": [],
                "recent_usage": [],
                "error": str(e)
            }
    
    def refresh_free_user_tokens(self) -> int:
        """
        Refresh tokens for free users whose subscription is 30+ days old.
        Resets tokens_used to 0 for free plan users.
        
        Returns:
            Number of users whose tokens were refreshed
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Token refresh skipped.")
            return 0
        
        try:
            # Get all active Free plan subscriptions that are 30+ days old
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            # Find free subscriptions created 30+ days ago
            result = self.supabase.table("subscriptions").select("*").eq(
                "plan_name", "Free"
            ).eq("status", "active").lte("created_at", thirty_days_ago).execute()
            
            refreshed_count = 0
            for subscription in result.data:
                subscription_id = subscription["id"]
                user_id = subscription["user_id"]
                
                # Reset tokens_used to 0 and update created_at to now (reset the 30-day cycle)
                self.supabase.table("subscriptions").update({
                    "tokens_used": 0,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }).eq("id", subscription_id).execute()
                
                refreshed_count += 1
                logger.info(f"Refreshed tokens for free user {user_id}")
            
            return refreshed_count
        except Exception as e:
            logger.error(f"Error refreshing free user tokens: {e}")
            return 0
    
    def downgrade_expired_paid_users(self) -> int:
        """
        Downgrade Pro/Starter users to Free if their subscription expired or payment failed.
        
        Returns:
            Number of users downgraded
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Downgrade skipped.")
            return 0
        
        try:
            downgraded_count = 0
            now = datetime.now()
            
            # Get all active paid subscriptions (Pro or Starter)
            result = self.supabase.table("subscriptions").select("*").in_(
                "plan_name", ["Pro", "Starter"]
            ).eq("status", "active").execute()
            
            for subscription in result.data:
                subscription_id = subscription["id"]
                user_id = subscription["user_id"]
                plan_name = subscription["plan_name"]
                expires_at = subscription.get("expires_at")
                
                # Check if subscription expired
                should_downgrade = False
                if expires_at:
                    expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00") if "Z" in expires_at else expires_at)
                    if now > expires:
                        should_downgrade = True
                        logger.info(f"Subscription expired for user {user_id} (plan: {plan_name})")
                
                # Also check if subscription is 30+ days old without renewal (for safety)
                created_at = subscription.get("created_at")
                if created_at and not expires_at:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00") if "Z" in created_at else created_at)
                    if (now - created).days >= 30:
                        should_downgrade = True
                        logger.info(f"Subscription expired (30+ days old) for user {user_id} (plan: {plan_name})")
                
                if should_downgrade:
                    # Update user plan to Free
                    self.supabase.table("users").update({
                        "plan": "Free",
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", user_id).execute()
                    
                    # Mark old subscription as expired
                    self.supabase.table("subscriptions").update({
                        "status": "expired",
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", subscription_id).execute()
                    
                    # Create new Free subscription with reset tokens
                    tokens_limit = self._get_tokens_limit("Free")
                    new_subscription_data = {
                        "id": f"sub_{secrets.token_urlsafe(16)}",
                        "user_id": user_id,
                        "plan_name": "Free",
                        "status": "active",
                        "tokens_used": 0,
                        "tokens_limit": tokens_limit,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    self.supabase.table("subscriptions").insert(new_subscription_data).execute()
                    
                    downgraded_count += 1
                    logger.info(f"Downgraded user {user_id} from {plan_name} to Free")
            
            return downgraded_count
        except Exception as e:
            logger.error(f"Error downgrading expired paid users: {e}")
            return 0
    
    def handle_payment_failure(self, user_id: str, subscription_id: Optional[str] = None):
        """
        Handle payment failure by downgrading user to Free plan.
        
        Args:
            user_id: User ID
            subscription_id: Optional subscription ID to mark as failed
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Payment failure handling skipped.")
            return
        
        try:
            # Get user's current plan
            user_result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if not user_result.data:
                logger.warning(f"User {user_id} not found for payment failure handling")
                return
            
            user = user_result.data[0]
            current_plan = user.get("plan", "Free")
            
            # Only downgrade if user is on a paid plan
            if current_plan in ["Pro", "Starter"]:
                # Update user plan to Free
                self.supabase.table("users").update({
                    "plan": "Free",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", user_id).execute()
                
                # Mark subscription as failed/cancelled
                if subscription_id:
                    self.supabase.table("subscriptions").update({
                        "status": "cancelled",
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", subscription_id).execute()
                else:
                    # Mark all active paid subscriptions for this user as cancelled
                    self.supabase.table("subscriptions").update({
                        "status": "cancelled",
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).in_("plan_name", ["Pro", "Starter"]).eq("status", "active").execute()
                
                # Create new Free subscription with reset tokens
                tokens_limit = self._get_tokens_limit("Free")
                new_subscription_data = {
                    "id": f"sub_{secrets.token_urlsafe(16)}",
                    "user_id": user_id,
                    "plan_name": "Free",
                    "status": "active",
                    "tokens_used": 0,
                    "tokens_limit": tokens_limit,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                self.supabase.table("subscriptions").insert(new_subscription_data).execute()
                
                logger.info(f"Downgraded user {user_id} from {current_plan} to Free due to payment failure")
        except Exception as e:
            logger.error(f"Error handling payment failure for user {user_id}: {e}")
    
    def run_subscription_maintenance(self) -> Dict[str, int]:
        """
        Run all subscription maintenance tasks.
        
        Returns:
            Dictionary with counts of actions taken
        """
        refreshed = self.refresh_free_user_tokens()
        downgraded = self.downgrade_expired_paid_users()
        
        return {
            "tokens_refreshed": refreshed,
            "users_downgraded": downgraded
        }
    
    def _get_tokens_limit(self, plan: str) -> int:
        """Get token limit for a plan."""
        limits = {
            "Free": 200000,
            "Starter": 2000000,
            "Pro": 7000000
        }
        return limits.get(plan, 200000)
