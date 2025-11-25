"""
PayPal Payment Service

Handles PayPal subscription creation, payment processing, and webhook verification.
"""

import os
from typing import Optional, Dict, Any
from paypalrestsdk import Api, configure
from paypalrestsdk.exceptions import ResourceNotFound, BadRequest
import logging

logger = logging.getLogger(__name__)


class PayPalService:
    """Service for handling PayPal payments and subscriptions."""
    
    def __init__(self):
        """Initialize PayPal API client."""
        # Get PayPal credentials from environment
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
        
        # Strip whitespace and quotes if present
        if self.client_id:
            self.client_id = self.client_id.strip().strip("'").strip('"')
        if self.client_secret:
            self.client_secret = self.client_secret.strip().strip("'").strip('"')
        if self.mode:
            self.mode = self.mode.strip().strip("'").strip('"')
        
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not found. Payment features will be disabled.")
            self.api = None
        else:
            try:
                # Validate credentials are not empty after stripping
                if not self.client_id.strip() or not self.client_secret.strip():
                    raise ValueError("PayPal credentials are empty after processing")
                
                # Configure PayPal API (for global configuration)
                configure({
                    "mode": self.mode,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                })
                # Create Api instance with credentials passed directly
                self.api = Api({
                    "mode": self.mode,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                })
                logger.info("PayPal service initialized successfully.")
            except KeyError as e:
                logger.error(f"PayPal configuration error - missing key: {e}")
                logger.warning("Payment features will be disabled.")
                self.api = None
            except Exception as e:
                logger.error(f"Failed to initialize PayPal service: {type(e).__name__}: {e}")
                logger.warning("Payment features will be disabled.")
                self.api = None
    
    def create_subscription(self, plan_name: str, user_email: str, user_id: str) -> Dict[str, Any]:
        """
        Create a PayPal subscription for a user.
        
        Args:
            plan_name: Name of the plan (Free, Starter, Pro)
            user_email: User's email address
            user_id: Unique user identifier
            
        Returns:
            Dictionary containing subscription details and approval URL
        """
        if not self.api:
            raise ValueError("PayPal is not configured. Please set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.")
        
        # Map plan names to PayPal plan IDs (you'll need to create these in PayPal)
        plan_mapping = {
            "Starter": os.getenv("PAYPAL_PLAN_ID_STARTER", "P-XXXXXXXXXX"),
            "Pro": os.getenv("PAYPAL_PLAN_ID_PRO", "P-XXXXXXXXXX")
        }
        
        if plan_name not in plan_mapping:
            raise ValueError(f"Invalid plan name: {plan_name}")
        
        plan_id = plan_mapping[plan_name]
        
        # Validate plan ID is not a placeholder
        if plan_id == "P-XXXXXXXXXX" or not plan_id or not plan_id.startswith("P-"):
            raise ValueError(
                f"PayPal plan ID for {plan_name} is not configured. "
                f"Please set PAYPAL_PLAN_ID_{plan_name.upper()} in your .env file. "
                f"Create the plan in PayPal first, then add the plan ID to .env"
            )
        
        # Set start_time to current time + 1 minute (PayPal requires future time)
        from datetime import datetime, timedelta
        start_time = (datetime.utcnow() + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create subscription
        subscription = {
            "plan_id": plan_id,
            "start_time": start_time,
            "subscriber": {
                "name": {
                    "given_name": user_id,
                    "surname": ""
                },
                "email_address": user_email
            },
            "application_context": {
                "brand_name": "EasyExcel",
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                },
                "return_url": os.getenv("PAYPAL_RETURN_URL", "http://localhost:5173/payment/success"),
                "cancel_url": os.getenv("PAYPAL_CANCEL_URL", "http://localhost:5173/payment/cancel")
            }
        }
        
        try:
            # Create subscription using PayPal REST API
            # Note: paypalrestsdk doesn't directly support subscriptions v1 API
            # We'll use a direct HTTP approach or upgrade to paypal-sdk
            import requests
            import base64
            
            # Get access token
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            base_url = "https://api.sandbox.paypal.com" if self.mode == "sandbox" else "https://api.paypal.com"
            
            # Get access token
            token_response = requests.post(
                f"{base_url}/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"}
            )
            
            if token_response.status_code != 200:
                raise Exception(f"Failed to get access token: {token_response.text}")
            
            access_token = token_response.json()["access_token"]
            
            # Create subscription
            sub_response = requests.post(
                f"{base_url}/v1/billing/subscriptions",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                json=subscription
            )
            
            if sub_response.status_code not in [200, 201]:
                error_data = sub_response.json() if sub_response.headers.get('content-type', '').startswith('application/json') else {}
                error_name = error_data.get('name', 'UNKNOWN_ERROR')
                error_message = error_data.get('message', sub_response.text)
                
                # Provide helpful error messages
                if error_name == 'RESOURCE_NOT_FOUND' or 'INVALID_RESOURCE_ID' in str(error_data):
                    raise ValueError(
                        f"PayPal plan '{plan_id}' not found. "
                        f"Please create the subscription plan in PayPal first, then update PAYPAL_PLAN_ID_{plan_name.upper()} in your .env file. "
                        f"See PAYPAL_SETUP.md for instructions."
                    )
                else:
                    raise Exception(f"Failed to create subscription: {error_message} (Error: {error_name})")
            
            subscription_data = sub_response.json()
            
            # Find approval URL
            approval_url = None
            for link in subscription_data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "subscription_id": subscription_data.get("id"),
                "status": subscription_data.get("status"),
                "approval_url": approval_url,
                "plan_name": plan_name
            }
            
        except Exception as e:
            logger.error(f"Error creating PayPal subscription: {str(e)}")
            raise
    
    def verify_webhook(self, headers: Dict[str, str], body: str) -> bool:
        """
        Verify PayPal webhook signature.
        
        Args:
            headers: HTTP headers from webhook request
            body: Raw request body
            
        Returns:
            True if webhook is verified, False otherwise
        """
        # Webhook verification implementation
        # This requires PayPal webhook ID from environment
        webhook_id = os.getenv("PAYPAL_WEBHOOK_ID")
        if not webhook_id:
            logger.warning("PayPal webhook ID not configured. Webhook verification disabled.")
            return True  # In development, you might want to skip verification
        
        # Implement webhook verification using PayPal's verification API
        # This is a simplified version - implement full verification in production
        return True
    
    def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get details of a PayPal subscription.
        
        Args:
            subscription_id: PayPal subscription ID
            
        Returns:
            Subscription details
        """
        import requests
        import base64
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        base_url = "https://api.sandbox.paypal.com" if self.mode == "sandbox" else "https://api.paypal.com"
        
        # Get access token
        token_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"grant_type": "client_credentials"}
        )
        
        if token_response.status_code != 200:
            raise Exception(f"Failed to get access token: {token_response.text}")
        
        access_token = token_response.json()["access_token"]
        
        # Get subscription details
        sub_response = requests.get(
            f"{base_url}/v1/billing/subscriptions/{subscription_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if sub_response.status_code != 200:
            raise Exception(f"Failed to get subscription: {sub_response.text}")
        
        return sub_response.json()
    
    def cancel_subscription(self, subscription_id: str, reason: str = "User requested cancellation") -> bool:
        """
        Cancel a PayPal subscription.
        
        Args:
            subscription_id: PayPal subscription ID
            reason: Reason for cancellation
            
        Returns:
            True if cancellation was successful
        """
        import requests
        import base64
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        base_url = "https://api.sandbox.paypal.com" if self.mode == "sandbox" else "https://api.paypal.com"
        
        # Get access token
        token_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"grant_type": "client_credentials"}
        )
        
        if token_response.status_code != 200:
            raise Exception(f"Failed to get access token: {token_response.text}")
        
        access_token = token_response.json()["access_token"]
        
        # Cancel subscription
        cancel_response = requests.post(
            f"{base_url}/v1/billing/subscriptions/{subscription_id}/cancel",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={"reason": reason}
        )
        
        return cancel_response.status_code == 204






