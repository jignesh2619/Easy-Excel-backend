#!/bin/bash
# Setup daily metadata cleanup cron job
# This script sets up a cron job to delete metadata every day at 2 AM

# Get the backend directory
BACKEND_DIR="/opt/easyexcel-backend"
API_URL="http://localhost:8000/api/metadata/cleanup/daily"

# Create cron job entry (runs daily at 2 AM)
CRON_JOB="0 2 * * * curl -X POST $API_URL >> /var/log/metadata-cleanup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "metadata/cleanup/daily"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "metadata/cleanup/daily" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Daily metadata cleanup cron job installed successfully!"
echo "Metadata will be deleted every day at 2 AM"
echo "Logs will be written to /var/log/metadata-cleanup.log"


