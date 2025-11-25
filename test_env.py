#!/usr/bin/env python3
"""
Quick script to test if Supabase environment variables are loaded correctly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("Environment Variables Check")
print("=" * 60)

# Check Supabase variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

print(f"\n✅ SUPABASE_URL: {supabase_url}")
if supabase_key:
    # Show first and last 10 chars for security
    masked_key = f"{supabase_key[:10]}...{supabase_key[-10:]}" if len(supabase_key) > 20 else "***"
    print(f"✅ SUPABASE_KEY: {masked_key} (length: {len(supabase_key)})")
else:
    print("❌ SUPABASE_KEY: NOT FOUND")

# Check if variables are set
if supabase_url and supabase_key:
    print("\n✅ Both Supabase variables are loaded!")
    
    # Try to import and test Supabase connection
    try:
        from supabase import create_client, Client
        
        print("\n🔄 Testing Supabase connection...")
        client = create_client(supabase_url.strip(), supabase_key.strip())
        
        # Test a simple query
        result = client.table("users").select("id").limit(1).execute()
        print("✅ Supabase connection successful!")
        print("✅ Database tables are accessible!")
        
    except ImportError:
        print("\n⚠️  Supabase library not installed. Run: pip install supabase postgrest")
    except Exception as e:
        print(f"\n❌ Supabase connection failed: {e}")
        print("   Check your credentials and network connection.")
else:
    print("\n❌ Missing Supabase variables!")
    print("   Make sure SUPABASE_URL and SUPABASE_KEY are in your .env file")

print("\n" + "=" * 60)



