# PayPal Integration Setup Guide

This guide will help you set up PayPal payments for EasyExcel.

## Prerequisites

1. A PayPal Business Account
2. Access to PayPal Developer Dashboard

## Step 1: Get Client ID and Client Secret

Follow the official PayPal guide: [Get Started with PayPal REST APIs](https://developer.paypal.com/api/rest/)

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com/)
2. **Log in to Dashboard** (or sign up if you don't have an account)
3. Select **Apps & Credentials**
4. **New accounts** come with a **Default Application** in the REST API apps section
5. **To create a new app**: Select **Create App**
   - **App Name**: EasyExcel
   - **Merchant**: Your business account
   - **Features**: **Subscriptions** (IMPORTANT: Check this box)
6. **Copy your credentials**:
   - **Client ID** - Identifies your app
   - **Client Secret** - Authenticates your app (keep this secret!)

> **Note**: You'll need a **PayPal Business account** to go live with integrations and test outside the US.

### Which API Do You Need?

**Answer: REST APIs - Billing/Subscriptions API**

- ✅ **Use**: **REST APIs** (see [PayPal REST APIs](https://developer.paypal.com/api/rest/))
- ✅ **Specifically**: **Subscriptions** API under REST APIs
- ❌ **Don't need**: JavaScript SDK, Mobile SDKs, NVP/SOAP APIs

Our code uses direct HTTP requests to PayPal's REST API endpoints:
- `/v1/oauth2/token` - Get access tokens (authentication)
- `/v1/billing/subscriptions` - Create and manage subscriptions
- `/v1/billing/plans` - Manage subscription plans

## Step 2: Get Access Token (Understanding How It Works)

According to [PayPal's REST API documentation](https://developer.paypal.com/api/rest/), you exchange your Client ID and Client Secret for an access token.

**Our code does this automatically**, but here's how it works:

```bash
curl -v -X POST "https://api-m.sandbox.paypal.com/v1/oauth2/token" \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials"
```

**You don't need to do this manually** - our `paypal_service.py` handles this automatically when creating subscriptions.

## Step 3: Create Subscription Plans

1. In PayPal Developer Dashboard, go to **Products** > **Subscriptions**
2. Click **Create Plan**
3. Create two plans:

### Starter Plan ($4.99/month)
- **Plan Name**: Starter Plan
- **Billing Cycle**: Monthly
- **Price**: $4.99 USD
- **Plan ID**: Copy this ID (starts with `P-`)

### Pro Plan ($12/month)
- **Plan Name**: Pro Plan
- **Billing Cycle**: Monthly
- **Price**: $12.00 USD
- **Plan ID**: Copy this ID (starts with `P-`)

## Step 4: Get Sandbox Account Credentials (For Testing)

According to [PayPal's documentation](https://developer.paypal.com/api/rest/), the sandbox is a test environment that mirrors real-world transactions.

1. Log into the Developer Dashboard
2. Select **Testing Tools** > **Sandbox Accounts**
3. You'll see 2 default accounts:
   - **Personal account** (for buying/testing)
   - **Business account** (for selling/receiving payments)
4. Click **⋮** on an account and select **View/Edit Account** to see credentials
5. Test at **sandbox.paypal.com/signin** with these credentials

> **Note**: Use sandbox accounts to test without real money. Switch to live mode when ready for production.

## Step 5: Configure Environment Variables

Add the following to your `.env` file in the `backend` directory:

```env
# PayPal Configuration
PAYPAL_CLIENT_ID=your_client_id_here
PAYPAL_CLIENT_SECRET=your_client_secret_here
PAYPAL_MODE=sandbox  # Use 'sandbox' for testing, 'live' for production
PAYPAL_PLAN_ID_STARTER=P-XXXXXXXXXX  # Replace with your Starter plan ID
PAYPAL_PLAN_ID_PRO=P-XXXXXXXXXX      # Replace with your Pro plan ID
PAYPAL_RETURN_URL=http://localhost:5173/payment/success
PAYPAL_CANCEL_URL=http://localhost:5173/payment/cancel
PAYPAL_WEBHOOK_ID=your_webhook_id_here  # Optional for webhook verification
```

## Step 4: Set Up Webhooks (Optional but Recommended)

1. In PayPal Developer Dashboard, go to **Webhooks**
2. Click **Add Webhook**
3. Enter your webhook URL: `https://yourdomain.com/api/payments/webhook`
4. Select events to listen for:
   - `BILLING.SUBSCRIPTION.CREATED`
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `PAYMENT.SALE.COMPLETED`
5. Copy the **Webhook ID** and add it to your `.env` file

## Step 5: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 7: Test the Integration

1. Start your backend server:
   ```bash
   python start_server.py
   ```

2. Test subscription creation:
   - Go to the pricing page
   - Click on "Upgrade to Starter" or "Upgrade to Pro"
   - Enter your email
   - You'll be redirected to PayPal sandbox
   - Use PayPal sandbox test accounts to complete the payment

### Using Sandbox Accounts

According to [PayPal's REST API guide](https://developer.paypal.com/api/rest/):
- Default accounts are provided in **Testing Tools** > **Sandbox Accounts**
- Personal account: For testing as a buyer
- Business account: For testing as a seller
- Sign in at **sandbox.paypal.com/signin** to test the payment flow
- Watch sandbox money move between accounts to verify API calls work

## Production Deployment

Before going live:

1. Change `PAYPAL_MODE` from `sandbox` to `live` in your `.env`
2. Update `PAYPAL_RETURN_URL` and `PAYPAL_CANCEL_URL` to your production URLs
3. Update webhook URL to your production domain
4. Test thoroughly with small amounts first
5. Monitor webhook events in PayPal Dashboard

## Troubleshooting

### Common Issues

1. **"PayPal is not configured" error**
   - Check that `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` are set correctly
   - Verify they're in your `.env` file

2. **"Invalid plan name" error**
   - Ensure `PAYPAL_PLAN_ID_STARTER` and `PAYPAL_PLAN_ID_PRO` are set
   - Verify the plan IDs start with `P-`

3. **Webhook verification fails**
   - Check that `PAYPAL_WEBHOOK_ID` is set
   - Verify webhook URL is accessible from the internet
   - Ensure webhook events are properly configured

4. **Subscription creation fails**
   - Verify you're using the correct mode (sandbox vs live)
   - Check that plans exist in your PayPal account
   - Ensure plan IDs match your PayPal dashboard

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables in production
- Enable webhook signature verification in production
- Regularly rotate your PayPal API credentials
- Monitor for suspicious activity in PayPal Dashboard

## Official PayPal Documentation

For more information, refer to PayPal's official documentation:

- **[Get Started with PayPal REST APIs](https://developer.paypal.com/api/rest/)** - Main REST API guide
- **[PayPal Subscriptions API](https://developer.paypal.com/docs/subscriptions/)** - Subscriptions documentation
- **[PayPal Webhooks](https://developer.paypal.com/docs/api-basics/notifications/webhooks/)** - Webhook setup
- **[PayPal Developer Dashboard](https://developer.paypal.com/)** - Your dashboard

## Support

- PayPal API Documentation: https://developer.paypal.com/api/rest/
- PayPal Support: https://developer.paypal.com/support/

