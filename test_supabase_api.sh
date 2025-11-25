#!/bin/bash
# Test if Supabase is working by testing the API

echo "Testing Supabase integration..."
echo ""

# Test user registration endpoint
echo "1. Testing user registration (creates user in Supabase)..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test_supabase@example.com", "plan": "Free"}')

echo "Response: $RESPONSE"
echo ""

# Check if we got a user with API key
if echo "$RESPONSE" | grep -q "api_key"; then
    echo "✅ SUCCESS: User created in Supabase!"
    echo "✅ Supabase is working correctly!"
else
    echo "❌ FAILED: Could not create user"
    echo "Check the error message above"
fi



