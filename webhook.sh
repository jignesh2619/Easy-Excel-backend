#!/bin/bash
# GitHub Webhook handler for auto-deployment
# This script should be called by a webhook server (like webhook or nginx)

cd /opt/easyexcel-backend
./deploy.sh

