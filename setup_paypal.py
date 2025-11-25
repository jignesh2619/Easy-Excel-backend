"""
PayPal Automatic Setup Script

This script automates PayPal setup once you have Client ID and Secret.
Run: python setup_paypal.py
"""

import os
import sys
import requests
import base64
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load existing .env if it exists
env_path = Path(__file__).parent / ".env"


def get_access_token(client_id: str, client_secret: str, mode: str = "sandbox") -> str:
    """Get PayPal access token."""
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    response = requests.post(
        f"{base_url}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get access token: {response.text}")
    
    return response.json()["access_token"]


def create_product(access_token: str, product_name: str, mode: str = "sandbox") -> str:
    """Create a product in PayPal (required before creating plans)."""
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    product_data = {
        "name": product_name,
        "description": f"EasyExcel {product_name} subscription",
        "type": "SERVICE",
        "category": "SOFTWARE"
    }
    
    response = requests.post(
        f"{base_url}/v1/catalogs/products",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        json=product_data
    )
    
    if response.status_code not in [200, 201]:
        error_text = response.text
        # If product already exists, try to find it
        if "already exists" in error_text.lower() or response.status_code == 409:
            print(f"  ⚠️  Product '{product_name}' might already exist. Checking...")
            # Try to list products and find it
            list_response = requests.get(
                f"{base_url}/v1/catalogs/products",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                params={"page_size": 20, "page": 1}
            )
            if list_response.status_code == 200:
                products = list_response.json().get("products", [])
                for product in products:
                    if product.get("name") == product_name:
                        return product.get("id")
            return None
        raise Exception(f"Failed to create product: {error_text}")
    
    product = response.json()
    return product.get("id")


def create_plan(access_token: str, plan_name: str, price: str, product_id: str, mode: str = "sandbox") -> str:
    """Create a subscription plan in PayPal."""
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    plan_data = {
        "product_id": product_id,
        "name": f"{plan_name} Plan",
        "description": f"EasyExcel {plan_name} subscription plan",
        "status": "ACTIVE",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,  # 0 = infinite
                "pricing_scheme": {
                    "fixed_price": {
                        "value": price,
                        "currency_code": "USD"
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {
                "value": "0",
                "currency_code": "USD"
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }
    
    response = requests.post(
        f"{base_url}/v1/billing/plans",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        json=plan_data
    )
    
    if response.status_code not in [200, 201]:
        error_text = response.text
        # If plan already exists, try to get it
        if "already exists" in error_text.lower() or response.status_code == 409:
            print(f"  ⚠️  Plan '{plan_name}' might already exist. Checking existing plans...")
            return None  # Will need to get plan ID manually
        raise Exception(f"Failed to create plan: {error_text}")
    
    plan = response.json()
    return plan.get("id")


def list_plans(access_token: str, mode: str = "sandbox") -> list:
    """List all existing plans."""
    base_url = "https://api.sandbox.paypal.com" if mode == "sandbox" else "https://api.paypal.com"
    
    response = requests.get(
        f"{base_url}/v1/billing/plans",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    return data.get("plans", [])


def update_env_file(client_id: str, client_secret: str, mode: str = "sandbox", 
                    starter_plan_id: str = None, pro_plan_id: str = None):
    """Update .env file with PayPal credentials."""
    env_path = Path(__file__).parent / ".env"
    
    # Create .env if it doesn't exist
    if not env_path.exists():
        env_path.touch()
    
    # Update or add PayPal credentials
    set_key(env_path, "PAYPAL_CLIENT_ID", client_id)
    set_key(env_path, "PAYPAL_CLIENT_SECRET", client_secret)
    set_key(env_path, "PAYPAL_MODE", mode)
    
    if starter_plan_id:
        set_key(env_path, "PAYPAL_PLAN_ID_STARTER", starter_plan_id)
    
    if pro_plan_id:
        set_key(env_path, "PAYPAL_PLAN_ID_PRO", pro_plan_id)
    
    # Set default return URLs if not set
    if not os.getenv("PAYPAL_RETURN_URL"):
        set_key(env_path, "PAYPAL_RETURN_URL", "http://localhost:5173/payment/success")
    
    if not os.getenv("PAYPAL_CANCEL_URL"):
        set_key(env_path, "PAYPAL_CANCEL_URL", "http://localhost:5173/payment/cancel")
    
    print(f"✅ Updated {env_path}")


def main():
    """Main setup function."""
    print("=" * 60)
    print("PayPal Automatic Setup for EasyExcel")
    print("=" * 60)
    print()
    
    # Try to load from .env first
    load_dotenv(env_path)
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    mode = os.getenv("PAYPAL_MODE", "sandbox")
    
    # Get credentials
    print("Step 1: PayPal Credentials")
    print("-" * 60)
    
    if client_id and client_secret:
        print(f"✅ Found credentials in .env file")
        print(f"   Client ID: {client_id[:20]}...")
        use_existing = input("Use these credentials? (y/n) [y]: ").strip().lower() or "y"
        if use_existing != "y":
            client_id = None
            client_secret = None
    
    if not client_id or not client_secret:
        client_id = input("Enter PayPal Client ID: ").strip()
        if not client_id:
            print("❌ Client ID is required!")
            sys.exit(1)
        
        client_secret = input("Enter PayPal Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret is required!")
            sys.exit(1)
        
        mode = input("Mode (sandbox/live) [sandbox]: ").strip().lower() or "sandbox"
        if mode not in ["sandbox", "live"]:
            mode = "sandbox"
    
    print()
    print("Step 2: Testing Connection")
    print("-" * 60)
    
    try:
        print("  🔄 Getting access token...")
        access_token = get_access_token(client_id, client_secret, mode)
        print("  ✅ Successfully authenticated with PayPal!")
    except Exception as e:
        print(f"  ❌ Failed to authenticate: {str(e)}")
        print("\nPlease check your Client ID and Client Secret.")
        sys.exit(1)
    
    print()
    print("Step 3: Creating Subscription Plans")
    print("-" * 60)
    
    # Check existing plans first
    print("  🔄 Checking existing plans...")
    existing_plans = list_plans(access_token, mode)
    
    starter_plan_id = None
    pro_plan_id = None
    
    # Create Starter Product first
    print("\n  📦 Creating Starter Product...")
    starter_product_id = None
    try:
        starter_product_id = create_product(access_token, "EasyExcel Starter", mode)
        if starter_product_id:
            print(f"  ✅ Created Starter Product: {starter_product_id}")
        else:
            print("  ⚠️  Product might already exist or couldn't be created")
            starter_product_id = input("  Enter Starter Product ID (or press Enter to skip): ").strip() or None
    except Exception as e:
        print(f"  ⚠️  Could not create Starter Product: {str(e)}")
        starter_product_id = input("  Enter Starter Product ID (or press Enter to skip): ").strip() or None
    
    # Create Starter Plan
    starter_plan_id = None
    if starter_product_id:
        print("\n  📦 Creating Starter Plan ($4.99/month)...")
        try:
            plan_id = create_plan(access_token, "Starter", "4.99", starter_product_id, mode)
            if plan_id:
                starter_plan_id = plan_id
                print(f"  ✅ Created Starter Plan: {plan_id}")
            else:
                print("  ⚠️  Plan might already exist. Please enter Plan ID manually:")
                starter_plan_id = input("  Enter Starter Plan ID (starts with P-): ").strip()
        except Exception as e:
            print(f"  ⚠️  Could not create Starter Plan: {str(e)}")
            print("  Please create it manually in PayPal Dashboard and enter the Plan ID:")
            starter_plan_id = input("  Enter Starter Plan ID (starts with P-): ").strip()
    
    # Create Pro Product first
    print("\n  📦 Creating Pro Product...")
    pro_product_id = None
    try:
        pro_product_id = create_product(access_token, "EasyExcel Pro", mode)
        if pro_product_id:
            print(f"  ✅ Created Pro Product: {pro_product_id}")
        else:
            print("  ⚠️  Product might already exist or couldn't be created")
            pro_product_id = input("  Enter Pro Product ID (or press Enter to skip): ").strip() or None
    except Exception as e:
        print(f"  ⚠️  Could not create Pro Product: {str(e)}")
        pro_product_id = input("  Enter Pro Product ID (or press Enter to skip): ").strip() or None
    
    # Create Pro Plan
    pro_plan_id = None
    if pro_product_id:
        print("\n  📦 Creating Pro Plan ($12.00/month)...")
        try:
            plan_id = create_plan(access_token, "Pro", "12.00", pro_product_id, mode)
            if plan_id:
                pro_plan_id = plan_id
                print(f"  ✅ Created Pro Plan: {plan_id}")
            else:
                print("  ⚠️  Plan might already exist. Please enter Plan ID manually:")
                pro_plan_id = input("  Enter Pro Plan ID (starts with P-): ").strip()
        except Exception as e:
            print(f"  ⚠️  Could not create Pro Plan: {str(e)}")
            print("  Please create it manually in PayPal Dashboard and enter the Plan ID:")
            pro_plan_id = input("  Enter Pro Plan ID (starts with P-): ").strip()
    
    print()
    print("Step 4: Saving Configuration")
    print("-" * 60)
    
    update_env_file(client_id, client_secret, mode, starter_plan_id, pro_plan_id)
    
    print()
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Your .env file has been updated with PayPal credentials")
    print("2. Start your server: python start_server.py")
    print("3. Test subscription creation from the frontend")
    print()
    
    if mode == "sandbox":
        print("💡 You're in SANDBOX mode - use test accounts for testing")
        print("   Switch to 'live' mode when ready for production")
    else:
        print("⚠️  You're in LIVE mode - real payments will be processed!")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        sys.exit(1)

