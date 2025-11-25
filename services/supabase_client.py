"""
Supabase Client Service

Handles connection to Supabase database.
"""

import os
from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance.
        
        Returns:
            Supabase client instance
            
        Raises:
            ValueError: If Supabase credentials are not configured
        """
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY "
                    "in your .env file."
                )
            
            # Strip whitespace
            supabase_url = supabase_url.strip()
            supabase_key = supabase_key.strip()
            
            try:
                cls._instance = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
        
        return cls._instance



