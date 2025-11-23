# PayPal Subscription Operations We Need

Based on the PayPal Subscriptions API documentation you're viewing, here are the **specific operations** we use:

## ✅ Required Operations

### 1. **Create Plan** (POST)
- **Endpoint**: `POST /v1/billing/plans`
- **When**: One-time setup (create Starter and Pro plans)
- **How**: Done manually in PayPal Dashboard OR via API
- **Status**: ✅ We need this (but can do via Dashboard)

### 2. **Create Subscription** (POST) ⭐ MOST IMPORTANT
- **Endpoint**: `POST /v1/billing/subscriptions`
- **When**: User clicks "Upgrade to Starter" or "Upgrade to Pro"
- **Used in**: `paypal_service.py` → `create_subscription()`
- **Status**: ✅ **We use this**

### 3. **Show Subscription Details** (GET)
- **Endpoint**: `GET /v1/billing/subscriptions/{subscription_id}`
- **When**: Verifying subscription status
- **Used in**: `paypal_service.py` → `get_subscription_details()`
- **Status**: ✅ **We use this**

### 4. **Cancel Subscription** (POST)
- **Endpoint**: `POST /v1/billing/subscriptions/{subscription_id}/cancel`
- **When**: User cancels their subscription
- **Used in**: `paypal_service.py` → `cancel_subscription()`
- **Status**: ✅ **We use this**

### 5. **Webhooks** (POST to our server)
- **Endpoint**: PayPal sends to `/api/payments/webhook`
- **Events we handle**:
  - `BILLING.SUBSCRIPTION.CREATED`
  - `BILLING.SUBSCRIPTION.ACTIVATED`
  - `BILLING.SUBSCRIPTION.CANCELLED`
  - `PAYMENT.SALE.COMPLETED`
- **Status**: ✅ **We use this**

## ❌ NOT Needed

You can ignore these operations:
- ❌ Activate plan
- ❌ Deactivate plan
- ❌ Update pricing
- ❌ Revise plan or quantity
- ❌ Suspend subscription
- ❌ Activate subscription (handled via webhooks)
- ❌ List plans
- ❌ List subscriptions
- ❌ Update plan
- ❌ Update subscription

## Summary

**You need to focus on:**
1. ✅ **Create Plan** (one-time, via Dashboard is easiest)
2. ✅ **Create Subscription** (when user subscribes)
3. ✅ **Show Subscription Details** (to verify status)
4. ✅ **Cancel Subscription** (when user cancels)
5. ✅ **Webhooks** (automatic notifications from PayPal)

## Quick Reference

| Operation | Method | Endpoint | We Use? |
|-----------|--------|----------|---------|
| Create Plan | POST | `/v1/billing/plans` | ✅ (one-time setup) |
| Create Subscription | POST | `/v1/billing/subscriptions` | ✅ **YES** |
| Show Subscription | GET | `/v1/billing/subscriptions/{id}` | ✅ **YES** |
| Cancel Subscription | POST | `/v1/billing/subscriptions/{id}/cancel` | ✅ **YES** |
| Webhooks | POST | (to our server) | ✅ **YES** |

## In PayPal Dashboard

When you're looking at the Subscriptions API docs:
- ✅ **Focus on**: "Create subscription" section
- ✅ **Also useful**: "Show subscription details" and "Cancel subscription"
- ✅ **Set up**: Webhooks in Dashboard → Webhooks section
- ❌ **Skip**: All other operations (we don't need them)

## Code Locations

Our implementation uses these in:
- `backend/services/paypal_service.py`:
  - `create_subscription()` → POST /v1/billing/subscriptions
  - `get_subscription_details()` → GET /v1/billing/subscriptions/{id}
  - `cancel_subscription()` → POST /v1/billing/subscriptions/{id}/cancel

- `backend/app.py`:
  - `/api/payments/webhook` → Receives webhook events

## Next Steps

1. ✅ Create plans in PayPal Dashboard (Starter $4.99, Pro $12)
2. ✅ Get plan IDs (they start with `P-`)
3. ✅ Add plan IDs to `.env` file
4. ✅ Test "Create subscription" endpoint
5. ✅ Set up webhooks

That's it! You only need these 4-5 operations.


