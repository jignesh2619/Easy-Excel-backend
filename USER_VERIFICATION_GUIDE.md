# User Verification and Subscription Management Guide

This guide explains how the user verification and subscription system works, and what you need to set up.

## What You Need

### 1. PayPal Business Account ✅
- **Yes, you need a PayPal Business account**
- Go to [paypal.com](https://www.paypal.com) and create a business account
- This is required to accept payments

### 2. PayPal Developer Account ✅
- **Yes, you need a PayPal Developer account**
- Go to [developer.paypal.com](https://developer.paypal.com)
- Log in with your PayPal Business account
- This gives you access to API credentials and sandbox testing

### 3. Database (Already Set Up) ✅
- SQLite database is automatically created at `backend/data/users.db`
- No additional setup needed - it's handled automatically

## How It Works

### User Registration Flow

1. **User Signs Up**
   - User enters email on pricing page
   - System creates user account with API key
   - User gets API key to use the service

2. **User Subscribes**
   - User clicks "Upgrade to Starter" or "Upgrade to Pro"
   - Redirected to PayPal for payment
   - After payment, PayPal sends webhook to your server
   - Server automatically upgrades user's subscription

3. **User Uses Service**
   - User includes API key in requests
   - System verifies:
     - API key is valid
     - Subscription is active
     - User has enough tokens
   - If all checks pass, request is processed
   - Tokens are deducted from user's account

### Subscription Verification

Every API request checks:
- ✅ **API Key Valid**: User exists and API key is correct
- ✅ **Subscription Active**: Subscription status is "active"
- ✅ **Not Expired**: Subscription hasn't expired (for paid plans)
- ✅ **Enough Tokens**: User has sufficient tokens for the operation

### Token Limits

- **Free Plan**: 200,000 tokens total
- **Starter Plan**: 2,000,000 tokens per month
- **Pro Plan**: 7,000,000 tokens per month

Tokens are estimated based on:
- File size (rows × columns)
- Prompt complexity
- Operations performed

## Setup Steps

### Step 1: Set Up PayPal (Follow PAYPAL_SETUP.md)

1. Create PayPal Business account
2. Create PayPal Developer account
3. Create subscription plans in PayPal
4. Get API credentials
5. Set up webhooks

### Step 2: Configure Environment Variables

Add to your `.env` file:

```env
# PayPal Configuration (from PAYPAL_SETUP.md)
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
PAYPAL_MODE=sandbox
PAYPAL_PLAN_ID_STARTER=P-XXXXXXXXXX
PAYPAL_PLAN_ID_PRO=P-XXXXXXXXXX
PAYPAL_RETURN_URL=http://localhost:5173/payment/success
PAYPAL_CANCEL_URL=http://localhost:5173/payment/cancel
```

### Step 3: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Start Server

```bash
python start_server.py
```

The database will be automatically created at `backend/data/users.db`

## API Usage

### Register a User

```bash
POST /api/users/register
Content-Type: application/json

{
  "email": "user@example.com",
  "plan": "Free"
}
```

Response:
```json
{
  "status": "success",
  "user": {
    "user_id": "user_...",
    "email": "user@example.com",
    "api_key": "ex_...",
    "plan": "Free"
  }
}
```

### Use API with Authentication

All API requests require an API key in the Authorization header:

```bash
POST /process-file
Authorization: Bearer ex_your_api_key_here
Content-Type: multipart/form-data

file: [file]
prompt: "clean this data"
```

### Get User Info

```bash
GET /api/users/me
Authorization: Bearer ex_your_api_key_here
```

## Frontend Integration

### Update Frontend to Use API Keys

You'll need to:

1. **Store API Key**: After user registration, store API key in localStorage or session
2. **Include in Requests**: Add API key to all API requests
3. **Handle Errors**: Show appropriate messages for:
   - Invalid API key
   - Insufficient tokens
   - Expired subscription

Example frontend code:

```typescript
// Register user
const response = await fetch('http://localhost:8000/api/users/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: userEmail, plan: 'Free' })
});
const { user } = await response.json();
localStorage.setItem('api_key', user.api_key);

// Use API key in requests
const apiKey = localStorage.getItem('api_key');
const formData = new FormData();
formData.append('file', file);
formData.append('prompt', prompt);

await fetch('http://localhost:8000/process-file', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apiKey}`
  },
  body: formData
});
```

## Webhook Handling

PayPal sends webhooks to `/api/payments/webhook` when:
- Subscription is created
- Subscription is activated
- Payment is completed
- Subscription is cancelled

The system automatically:
- Creates/updates user account
- Updates subscription status
- Changes user's plan
- Resets token limits

## Testing

### Test User Registration

1. Register a user via API
2. Get API key
3. Use API key in requests
4. Check token usage

### Test Subscription Flow

1. Use PayPal sandbox
2. Create subscription
3. Complete payment in sandbox
4. Check webhook received
5. Verify user subscription updated

### Test Token Limits

1. Create Free plan user
2. Make requests until tokens run out
3. Verify error message shown
4. Upgrade to paid plan
5. Verify tokens reset

## Database Structure

The system uses SQLite with three tables:

### `users` table
- `id`: Unique user ID
- `email`: User email (unique)
- `api_key`: API key for authentication
- `plan`: Current plan (Free, Starter, Pro)
- `created_at`, `updated_at`: Timestamps

### `subscriptions` table
- `id`: Subscription ID
- `user_id`: Foreign key to users
- `paypal_subscription_id`: PayPal subscription ID
- `plan_name`: Plan name
- `status`: active, cancelled, expired
- `tokens_used`: Tokens consumed
- `tokens_limit`: Token limit for plan
- `expires_at`: Expiration date
- `created_at`, `updated_at`: Timestamps

### `token_usage` table
- `id`: Auto-increment ID
- `user_id`: Foreign key to users
- `tokens_used`: Tokens used in this operation
- `operation`: Type of operation
- `created_at`: Timestamp

## Security Notes

- ✅ API keys are randomly generated and secure
- ✅ API keys are required for all operations
- ✅ Token limits prevent abuse
- ✅ Subscriptions are verified on every request
- ⚠️ In production, use HTTPS for all API calls
- ⚠️ Store API keys securely (not in localStorage for production)
- ⚠️ Implement rate limiting
- ⚠️ Add logging for security monitoring

## Troubleshooting

### "API key required" error
- User needs to register first
- API key must be in Authorization header
- Format: `Bearer ex_your_api_key_here`

### "Insufficient tokens" error
- User has used all their tokens
- Need to upgrade plan or wait for monthly reset

### "Subscription is not active" error
- Subscription was cancelled
- Payment failed
- Check PayPal dashboard

### Webhook not working
- Verify webhook URL is accessible
- Check PayPal webhook configuration
- Check server logs for errors

## Next Steps

1. ✅ Set up PayPal (follow PAYPAL_SETUP.md)
2. ✅ Test user registration
3. ✅ Test subscription flow
4. ✅ Update frontend to use API keys
5. ✅ Test token limits
6. ✅ Deploy to production
7. ✅ Monitor webhooks and subscriptions

## Support

For issues:
- Check server logs: `backend/data/users.db` for database
- Check PayPal Dashboard for subscription status
- Review webhook logs in PayPal Dashboard


