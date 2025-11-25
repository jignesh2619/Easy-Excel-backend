# PayPal API Reference for EasyExcel

## Which API Do We Need?

**Answer: REST APIs - Billing/Subscriptions API**

## In PayPal Developer Dashboard

When you're in the dashboard (like in the image you showed), you need:

### ✅ Use This:
- **REST APIs** (under "APIs & SDKs" in sidebar)
- Specifically: **Billing/Subscriptions API**

### ❌ Don't Need:
- JavaScript SDK
- Mobile SDKs  
- NVP/SOAP APIs
- Donate SDK
- Braintree GraphQL API

## API Endpoints We Use

Our code makes direct HTTP requests to these PayPal REST API endpoints:

### 1. OAuth Token Endpoint
```
POST https://api.sandbox.paypal.com/v1/oauth2/token
```
- **Purpose**: Get access token for API calls
- **Used in**: Every API request (authentication)

### 2. Create Subscription
```
POST https://api.sandbox.paypal.com/v1/billing/subscriptions
```
- **Purpose**: Create a new subscription for a user
- **Used when**: User clicks "Upgrade to Starter" or "Upgrade to Pro"

### 3. Get Subscription Details
```
GET https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}
```
- **Purpose**: Check subscription status
- **Used when**: Verifying user subscription

### 4. Cancel Subscription
```
POST https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/cancel
```
- **Purpose**: Cancel a subscription
- **Used when**: User cancels their subscription

### 5. Webhooks
```
POST https://your-domain.com/api/payments/webhook
```
- **Purpose**: PayPal sends events to your server
- **Events we handle**:
  - `BILLING.SUBSCRIPTION.CREATED`
  - `BILLING.SUBSCRIPTION.ACTIVATED`
  - `BILLING.SUBSCRIPTION.CANCELLED`
  - `PAYMENT.SALE.COMPLETED`

## API Documentation Links

### Official PayPal Documentation:
1. **Billing/Subscriptions API**: 
   - https://developer.paypal.com/docs/api/subscriptions/v1/

2. **Create Subscription**:
   - https://developer.paypal.com/docs/api/subscriptions/v1/#subscriptions_create

3. **Webhooks**:
   - https://developer.paypal.com/docs/api-basics/notifications/webhooks/

4. **Authentication**:
   - https://developer.paypal.com/docs/api/overview/#get-an-access-token

## How Our Code Uses It

### In `backend/services/paypal_service.py`:

1. **Get Access Token**:
   ```python
   POST /v1/oauth2/token
   # Returns: access_token
   ```

2. **Create Subscription**:
   ```python
   POST /v1/billing/subscriptions
   # Body: subscription details
   # Returns: subscription_id, approval_url
   ```

3. **Get Subscription**:
   ```python
   GET /v1/billing/subscriptions/{id}
   # Returns: subscription details
   ```

## Sandbox vs Live

- **Sandbox**: `https://api.sandbox.paypal.com` (for testing)
- **Live**: `https://api.paypal.com` (for production)

Set `PAYPAL_MODE=sandbox` or `PAYPAL_MODE=live` in your `.env` file.

## What You Need to Enable

In PayPal Developer Dashboard:

1. ✅ **Create App** with "Subscriptions" feature enabled
2. ✅ **Create Subscription Plans** (Starter $4.99, Pro $12)
3. ✅ **Set up Webhooks** (optional but recommended)
4. ✅ **Get API Credentials** (Client ID, Secret)

## Quick Checklist

- [ ] PayPal Business Account
- [ ] PayPal Developer Account  
- [ ] App created with "Subscriptions" feature
- [ ] REST API access (automatic with app creation)
- [ ] Subscription plans created
- [ ] Client ID and Secret copied
- [ ] Webhooks configured (optional)

## Testing

Use PayPal Sandbox:
- Test accounts provided by PayPal
- No real money involved
- Full API functionality
- Switch to Live when ready

## Need Help?

- PayPal API Docs: https://developer.paypal.com/docs/api/
- PayPal Support: https://developer.paypal.com/support/
- Our Setup Guide: `PAYPAL_SETUP.md`






