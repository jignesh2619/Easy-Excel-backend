#!/bin/bash
# Script to update Supabase credentials in .env file
# Run this on your DigitalOcean Droplet

ENV_FILE="/opt/easyexcel-backend/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Backup the .env file
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backed up .env file"

# Add or update Supabase URL
if grep -q "SUPABASE_URL=" "$ENV_FILE"; then
    # Update existing
    sed -i 's|^SUPABASE_URL=.*|SUPABASE_URL=https://pkkfenvnpddfccoiiqef.supabase.co|' "$ENV_FILE"
    echo "✅ Updated SUPABASE_URL"
else
    # Add new
    echo "" >> "$ENV_FILE"
    echo "# Supabase Configuration" >> "$ENV_FILE"
    echo "SUPABASE_URL=https://pkkfenvnpddfccoiiqef.supabase.co" >> "$ENV_FILE"
    echo "✅ Added SUPABASE_URL"
fi

# Add or update Supabase Key
if grep -q "SUPABASE_KEY=" "$ENV_FILE"; then
    # Update existing
    sed -i 's|^SUPABASE_KEY=.*|SUPABASE_KEY=sb_secret_N7Nelp809WFt5xk-QPHTOA_vkTcryTA|' "$ENV_FILE"
    echo "✅ Updated SUPABASE_KEY"
else
    # Add new
    echo "SUPABASE_KEY=sb_secret_N7Nelp809WFt5xk-QPHTOA_vkTcryTA" >> "$ENV_FILE"
    echo "✅ Added SUPABASE_KEY"
fi

echo ""
echo "✅ Supabase credentials updated successfully!"
echo "📝 Review the changes: nano $ENV_FILE"
echo "🔄 Restart the service: sudo systemctl restart easyexcel-backend"



