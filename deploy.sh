#!/bin/bash
set -e

echo "=========================================="
echo "EasyExcel Backend Deployment Script"
echo "=========================================="

cd /opt/easyexcel-backend

echo "📥 Pulling latest changes from GitHub..."
git pull origin main

echo "📦 Installing/updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "🔄 Restarting easyexcel-backend service..."
systemctl restart easyexcel-backend

echo "⏳ Waiting for service to start..."
sleep 5

echo "✅ Checking service status..."
systemctl status easyexcel-backend --no-pager

echo ""
echo "=========================================="
echo "✅ Deployment complete!"
echo "=========================================="

