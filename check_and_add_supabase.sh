#!/bin/bash
# Script to check and add Supabase variables to .env file

ENV_FILE="/opt/easyexcel-backend/.env"

echo "Checking .env file..."
echo ""

# Check if variables exist
if grep -q "SUPABASE_URL" "$ENV_FILE"; then
    echo "✅ SUPABASE_URL found"
    grep "SUPABASE_URL" "$ENV_FILE"
else
    echo "❌ SUPABASE_URL NOT FOUND"
fi

echo ""

if grep -q "SUPABASE_KEY" "$ENV_FILE"; then
    echo "✅ SUPABASE_KEY found"
    grep "SUPABASE_KEY" "$ENV_FILE" | sed 's/\(.\{20\}\).*\(.\{10\}\)$/\1...\2/'  # Mask the key
else
    echo "❌ SUPABASE_KEY NOT FOUND"
fi

echo ""
echo "If variables are missing, add them with:"
echo "nano $ENV_FILE"
echo ""
echo "Add these lines:"
echo "SUPABASE_URL=https://pkkfenvnpddfccoiiqef.supabase.co"
echo "SUPABASE_KEY=sb_secret_N7Nelp809WFt5xk-QPHTOA_vkTcryTA"



