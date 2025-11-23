# Quick PayPal Setup with Your Credentials

I've received your PayPal credentials. Here's how to complete the setup:

## Your Credentials (Already Configured)

- **Client ID**: `ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL`
- **Client Secret**: `EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr`
- **Mode**: sandbox (for testing)

## Option 1: Automatic Setup (Recommended)

Run these commands in your terminal:

```bash
cd backend
python update_paypal_credentials.py
python setup_paypal.py
```

The scripts will:
1. ✅ Save your credentials to `.env`
2. ✅ Test the connection
3. ✅ Create subscription plans automatically
4. ✅ Save plan IDs to `.env`

## Option 2: Manual .env Update

If Python isn't working, manually update `backend/.env`:

```env
PAYPAL_CLIENT_ID=ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL
PAYPAL_CLIENT_SECRET=EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr
PAYPAL_MODE=sandbox
PAYPAL_RETURN_URL=http://localhost:5173/payment/success
PAYPAL_CANCEL_URL=http://localhost:5173/payment/cancel
```

Then create plans in PayPal Dashboard and add:
```env
PAYPAL_PLAN_ID_STARTER=P-XXXXXXXXXX
PAYPAL_PLAN_ID_PRO=P-XXXXXXXXXX
```

## Next Steps

1. ✅ Credentials are ready
2. ⏳ Create subscription plans (automatic or manual)
3. ⏳ Test subscription flow
4. ⏳ Set up webhooks (optional)

## Security Note

⚠️ **Keep these credentials secret!** Never commit `.env` to version control.


