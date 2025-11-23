"""
Quick script to update PayPal credentials in .env file
"""

from pathlib import Path
from dotenv import set_key, load_dotenv

# Your PayPal credentials
CLIENT_ID = "ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL"
CLIENT_SECRET = "EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr"

env_path = Path(__file__).parent / ".env"

# Load existing .env if exists
if env_path.exists():
    load_dotenv(env_path)
else:
    # Create .env file
    env_path.touch()

# Update PayPal credentials
set_key(env_path, "PAYPAL_CLIENT_ID", CLIENT_ID)
set_key(env_path, "PAYPAL_CLIENT_SECRET", CLIENT_SECRET)
set_key(env_path, "PAYPAL_MODE", "sandbox")

# Set default URLs if not already set
from dotenv import dotenv_values
existing = dotenv_values(env_path)
if not existing.get("PAYPAL_RETURN_URL"):
    set_key(env_path, "PAYPAL_RETURN_URL", "http://localhost:5173/payment/success")
if not existing.get("PAYPAL_CANCEL_URL"):
    set_key(env_path, "PAYPAL_CANCEL_URL", "http://localhost:5173/payment/cancel")

print("✅ PayPal credentials updated in .env file!")
print(f"   Client ID: {CLIENT_ID[:20]}...")
print(f"   Mode: sandbox")
print()
print("Next: Run 'python setup_paypal.py' to create subscription plans")


