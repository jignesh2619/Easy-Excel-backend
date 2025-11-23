"""
User and Subscription Management Service

Handles user accounts, API keys, and subscription verification.
"""

import sqlite3
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import json

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "users.db"


class UserService:
    """Service for managing users and subscriptions."""
    
    def __init__(self):
        """Initialize database connection."""
        # Create data directory if it doesn't exist
        DB_PATH.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                plan TEXT NOT NULL DEFAULT 'Free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                paypal_subscription_id TEXT UNIQUE,
                plan_name TEXT NOT NULL,
                status TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                tokens_limit INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Token usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tokens_used INTEGER NOT NULL,
                operation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_user(self, email: str, plan: str = "Free") -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            email: User's email address
            plan: Subscription plan (Free, Starter, Pro)
            
        Returns:
            User data with API key
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Generate unique user ID and API key
        user_id = f"user_{secrets.token_urlsafe(16)}"
        api_key = f"ex_{secrets.token_urlsafe(32)}"
        
        try:
            cursor.execute("""
                INSERT INTO users (id, email, api_key, plan)
                VALUES (?, ?, ?, ?)
            """, (user_id, email, api_key, plan))
            
            # Create subscription record
            tokens_limit = self._get_tokens_limit(plan)
            cursor.execute("""
                INSERT INTO subscriptions (id, user_id, plan_name, status, tokens_limit)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"sub_{secrets.token_urlsafe(16)}",
                user_id,
                plan,
                "active",
                tokens_limit
            ))
            
            conn.commit()
            
            return {
                "user_id": user_id,
                "email": email,
                "api_key": api_key,
                "plan": plan
            }
        except sqlite3.IntegrityError:
            # User already exists, get existing user
            cursor.execute("SELECT id, email, api_key, plan FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "email": row[1],
                    "api_key": row[2],
                    "plan": row[3]
                }
            raise
        finally:
            conn.close()
    
    def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Get user by API key.
        
        Args:
            api_key: User's API key
            
        Returns:
            User data or None if not found
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.email, u.plan, s.status, s.tokens_used, s.tokens_limit, s.expires_at
            FROM users u
            LEFT JOIN subscriptions s ON u.id = s.user_id
            WHERE u.api_key = ?
            ORDER BY s.created_at DESC
            LIMIT 1
        """, (api_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row[0],
                "email": row[1],
                "plan": row[2],
                "subscription_status": row[3] or "active",
                "tokens_used": row[4] or 0,
                "tokens_limit": row[5] or self._get_tokens_limit(row[2]),
                "expires_at": row[6]
            }
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update user plan
        cursor.execute("UPDATE users SET plan = ?, updated_at = ? WHERE id = ?", 
                      (plan_name, datetime.now(), user_id))
        
        # Update or create subscription
        cursor.execute("""
            SELECT id FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        
        sub_row = cursor.fetchone()
        
        tokens_limit = self._get_tokens_limit(plan_name)
        expires_at = None
        if plan_name != "Free":
            # Set expiration to 30 days from now for paid plans
            expires_at = datetime.now() + timedelta(days=30)
        
        if sub_row:
            # Update existing subscription
            cursor.execute("""
                UPDATE subscriptions 
                SET paypal_subscription_id = ?, plan_name = ?, status = ?, 
                    tokens_limit = ?, expires_at = ?, updated_at = ?
                WHERE id = ?
            """, (paypal_subscription_id, plan_name, status, tokens_limit, expires_at, datetime.now(), sub_row[0]))
        else:
            # Create new subscription
            cursor.execute("""
                INSERT INTO subscriptions (id, user_id, paypal_subscription_id, plan_name, status, tokens_limit, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"sub_{secrets.token_urlsafe(16)}", user_id, paypal_subscription_id, plan_name, status, tokens_limit, expires_at))
        
        conn.commit()
        conn.close()
    
    def check_token_limit(self, user_id: str, tokens_needed: int = 0) -> Dict[str, Any]:
        """
        Check if user has enough tokens.
        
        Args:
            user_id: User ID
            tokens_needed: Number of tokens needed for operation
            
        Returns:
            Dictionary with can_proceed, tokens_used, tokens_limit, tokens_remaining
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tokens_used, tokens_limit, status, expires_at
            FROM subscriptions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                "can_proceed": False,
                "error": "No subscription found"
            }
        
        tokens_used, tokens_limit, status, expires_at = row
        
        # Check if subscription is active
        if status != "active":
            return {
                "can_proceed": False,
                "error": "Subscription is not active"
            }
        
        # Check expiration
        if expires_at:
            expires = datetime.fromisoformat(expires_at) if isinstance(expires_at, str) else expires_at
            if datetime.now() > expires:
                return {
                    "can_proceed": False,
                    "error": "Subscription has expired"
                }
        
        tokens_remaining = tokens_limit - (tokens_used or 0)
        
        return {
            "can_proceed": tokens_remaining >= tokens_needed,
            "tokens_used": tokens_used or 0,
            "tokens_limit": tokens_limit,
            "tokens_remaining": tokens_remaining,
            "status": status
        }
    
    def record_token_usage(self, user_id: str, tokens_used: int, operation: str = "file_processing"):
        """
        Record token usage for a user.
        
        Args:
            user_id: User ID
            tokens_used: Number of tokens used
            operation: Type of operation
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Record usage
        cursor.execute("""
            INSERT INTO token_usage (user_id, tokens_used, operation)
            VALUES (?, ?, ?)
        """, (user_id, tokens_used, operation))
        
        # Update subscription tokens_used
        cursor.execute("""
            UPDATE subscriptions
            SET tokens_used = tokens_used + ?, updated_at = ?
            WHERE user_id = ? AND status = 'active'
        """, (tokens_used, datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    
    def _get_tokens_limit(self, plan: str) -> int:
        """Get token limit for a plan."""
        limits = {
            "Free": 200000,
            "Starter": 2000000,
            "Pro": 7000000
        }
        return limits.get(plan, 200000)


