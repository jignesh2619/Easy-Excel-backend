# Quick Start: What You Need for Subscriptions

## Your Questions Answered

### 1. Do you need a PayPal Developer account?
**YES** ✅
- You need a **PayPal Business Account** (to accept payments)
- You need a **PayPal Developer Account** (to get API credentials)
- Both are free to create
- See `PAYPAL_SETUP.md` for step-by-step instructions

### 2. How do we verify users who have paid?
**Automatic System** ✅
- When user pays via PayPal, PayPal sends a webhook to your server
- Server automatically:
  - Creates/updates user account
  - Activates subscription
  - Sets token limits
  - Tracks usage
- Every API request checks:
  - ✅ User has valid API key
  - ✅ Subscription is active
  - ✅ User has enough tokens
  - ✅ Subscription hasn't expired

### 3. What do you need from my side?

#### Step 1: PayPal Setup (15 minutes)
1. Create PayPal Business account at paypal.com
2. Create PayPal Developer account at developer.paypal.com
3. Create subscription plans (Starter $4.99, Pro $12)
4. Get API credentials (Client ID, Secret)
5. Set up webhooks

**Follow**: `PAYPAL_SETUP.md` for detailed steps

#### Step 2: Environment Variables (2 minutes)
Add to `backend/.env`:
```env
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
PAYPAL_MODE=sandbox
PAYPAL_PLAN_ID_STARTER=P-XXXXXXXXXX
PAYPAL_PLAN_ID_PRO=P-XXXXXXXXXX
```

#### Step 3: Install Dependencies (1 minute)
```bash
cd backend
pip install -r requirements.txt
```

#### Step 4: Start Server
```bash
python start_server.py
```

That's it! The system handles everything else automatically.

## How It Works

### User Journey

1. **User visits pricing page**
   - Sees Free, Starter ($4.99), Pro ($12) plans

2. **User clicks "Upgrade"**
   - Enters email address
   - Redirected to PayPal
   - Completes payment

3. **PayPal sends webhook**
   - Your server receives payment confirmation
   - Automatically creates user account
   - Activates subscription
   - Sets token limits

4. **User gets API key**
   - User can register via `/api/users/register`
   - Gets unique API key
   - Uses API key for all requests

5. **User makes requests**
   - Includes API key in Authorization header
   - System verifies subscription
   - Checks token limits
   - Processes request if all checks pass
   - Deducts tokens from account

### Automatic Verification

Every request automatically checks:
- ✅ **API Key**: Valid and exists
- ✅ **Subscription**: Active status
- ✅ **Tokens**: Sufficient for operation
- ✅ **Expiration**: Not expired (paid plans)

If any check fails, request is rejected with clear error message.

## Database

- **Automatic**: SQLite database created at `backend/data/users.db`
- **No setup needed**: System creates tables automatically
- **Stores**:
  - User accounts (email, API key, plan)
  - Subscriptions (PayPal ID, status, tokens)
  - Token usage history

## Testing

### Test in Sandbox Mode
1. Use PayPal sandbox (free testing)
2. Create test accounts in PayPal Dashboard
3. Test full payment flow
4. Verify webhooks received
5. Check database updated

### Go Live
1. Change `PAYPAL_MODE=live` in `.env`
2. Use real PayPal credentials
3. Test with small amount first
4. Monitor webhooks

## What's Already Done

✅ User registration system
✅ API key generation and validation
✅ Subscription management
✅ Token tracking and limits
✅ PayPal webhook handling
✅ Automatic subscription activation
✅ Token usage recording
✅ Subscription verification on every request

## What You Need to Do

1. ✅ Set up PayPal (follow `PAYPAL_SETUP.md`)
2. ✅ Add credentials to `.env`
3. ✅ Install dependencies
4. ✅ Start server
5. ✅ Test in sandbox

## Documentation

- **PAYPAL_SETUP.md**: Step-by-step PayPal configuration
- **USER_VERIFICATION_GUIDE.md**: Complete system documentation
- **This file**: Quick overview

## Support

If you get stuck:
1. Check `PAYPAL_SETUP.md` for PayPal setup
2. Check `USER_VERIFICATION_GUIDE.md` for system details
3. Check server logs for errors
4. Check PayPal Dashboard for webhook status


