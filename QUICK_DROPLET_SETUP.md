# Quick Droplet Setup Guide

## ⚠️ Important: Run These Commands on Your Droplet, Not Windows!

You need to **SSH into your droplet first** before running these commands.

## Step 1: SSH into Your Droplet

From your Windows PowerShell or Command Prompt:

```powershell
ssh root@your-droplet-ip
```

Replace `your-droplet-ip` with your actual droplet IP address.

If you're using an SSH key:
```powershell
ssh -i path\to\your\key.pem root@your-droplet-ip
```

## Step 2: Once Connected to Droplet, Run These Commands

After you're connected (you'll see a Linux prompt like `root@ubuntu-s-...`), then run:

```bash
# 1. Navigate to backend directory
cd /opt/easyexcel-backend

# 2. Pull latest changes
git pull origin main

# 3. Make deployment script executable
chmod +x deploy.sh

# 4. Update Nginx configuration
sudo nano /etc/nginx/sites-available/easyexcel
```

## Step 3: Update Nginx Configuration

In the nano editor, find the `location /` block and add these lines:

```nginx
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
send_timeout 300s;
```

Save and exit: Press `Ctrl+X`, then `Y`, then `Enter`

## Step 4: Test and Restart Services

```bash
# Test Nginx configuration
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx

# Restart backend service
sudo systemctl restart easyexcel-backend

# Check status
sudo systemctl status easyexcel-backend
```

## Alternative: Use the Deployment Script

After pulling changes, you can use the automated script:

```bash
cd /opt/easyexcel-backend
./deploy.sh
```

This will automatically:
- Pull latest changes
- Install dependencies
- Restart the service
- Show status

## Troubleshooting

### Can't SSH into droplet?
1. Check your droplet IP address in DigitalOcean dashboard
2. Make sure SSH is enabled (port 22)
3. Verify your SSH key is added to the droplet

### Permission denied?
- Make sure you're using `root` user or have sudo access
- Check that your SSH key has the correct permissions

### Git pull fails?
- Make sure the repository is cloned correctly
- Check that you have internet connection on the droplet

## Quick Reference

**Windows (Local):**
```powershell
ssh root@your-droplet-ip
```

**Droplet (After SSH):**
```bash
cd /opt/easyexcel-backend
git pull origin main
./deploy.sh
```






