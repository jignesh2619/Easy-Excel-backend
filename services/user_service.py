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
            tokens_used: Number of tokens used
            operation: Type of operation
        """
        if not self.supabase:
            logger.warning("Supabase not configured. Token usage not recorded.")
            return
        
        try:
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
                
                # Update the specific subscription
                self.supabase.table("subscriptions").update({
                    "tokens_used": new_tokens,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", subscription_id).execute()
                
        except Exception as e:
            logger.error(f"Error recording token usage: {e}")
    
    def _get_tokens_limit(self, plan: str) -> int:
        """Get token limit for a plan."""
        limits = {
            "Free": 200000,
            "Starter": 2000000,
            "Pro": 7000000
        }
        return limits.get(plan, 200000)
