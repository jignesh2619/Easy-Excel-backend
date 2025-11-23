# Setting Up Backend on DigitalOcean Droplet

This guide will help you set up your FastAPI backend on a DigitalOcean Droplet for the first time.

## Prerequisites

- DigitalOcean Droplet created (Ubuntu 20.04 or 22.04 recommended)
- SSH access to your Droplet
- Your Droplet IP address

## Step 1: Initial Server Setup

### Connect to Your Droplet

```powershell
ssh root@YOUR_DROPLET_IP
# Example: ssh root@165.227.29.127
```

### Update System

```bash
apt update && apt upgrade -y
```

### Install Required Software

```bash
# Install Python 3.11 and pip
apt install -y python3.11 python3.11-venv python3-pip git nginx

# Install other dependencies
apt install -y build-essential libssl-dev libffi-dev python3-dev
```

## Step 2: Set Up Application Directory

```bash
# Create app directory
mkdir -p /opt/easyexcel-backend
cd /opt/easyexcel-backend

# Clone your repository (or upload files)
# Option A: Clone from GitHub
git clone https://github.com/YOUR_USERNAME/easyexcel.git .

# Option B: If repo is private, use SSH:
# git clone git@github.com:YOUR_USERNAME/easyexcel.git .
```

## Step 3: Set Up Python Environment

```bash
cd /opt/easyexcel-backend/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add your environment variables:

```env
GEMINI_API_KEY=your_actual_gemini_key
PORT=8000
HOST=0.0.0.0

PAYPAL_CLIENT_ID=ATEF1de5CXpZ5E7PXmkXqqmFXor69bPrpJOrr9ZpHXH55ZlPWNmiYfJGDUOOaXTgIGSBN70P5EP4hfDL
PAYPAL_CLIENT_SECRET=EIsw28kLVXE9u08OPsv8ZLQzzjVR9YgU_QBbvKmFNMA24xadoLrNNz3H0x47smXPJZ0AWRaHaIRjfKAr
PAYPAL_MODE=sandbox
PAYPAL_PLAN_ID_STARTER=your_starter_plan_id
PAYPAL_PLAN_ID_PRO=your_pro_plan_id
PAYPAL_RETURN_URL=https://your-frontend.vercel.app/payment/success
PAYPAL_CANCEL_URL=https://your-frontend.vercel.app/payment/cancel
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

## Step 5: Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/easyexcel-backend.service
```

Add this content:

```ini
[Unit]
Description=EasyExcel Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/easyexcel-backend/backend
Environment="PATH=/opt/easyexcel-backend/backend/venv/bin"
ExecStart=/opt/easyexcel-backend/backend/venv/bin/python start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit, then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable easyexcel-backend

# Start the service
sudo systemctl start easyexcel-backend

# Check status
sudo systemctl status easyexcel-backend
```

## Step 6: Configure Firewall

```bash
# Allow SSH (if not already allowed)
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow your backend port (8000)
ufw allow 8000/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

## Step 7: Test Your Backend

```bash
# Test locally on the server
curl http://localhost:8000/health

# Test from your local machine
curl http://YOUR_DROPLET_IP:8000/health
```

## Step 8: Set Up Nginx Reverse Proxy (Optional but Recommended)

This allows you to use port 80/443 and add SSL later.

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/easyexcel-backend
```

Add this content:

```nginx
server {
    listen 80;
    server_name YOUR_DROPLET_IP;  # Or your domain name

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/easyexcel-backend /etc/nginx/sites-enabled/

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

Now your backend is accessible at: `http://YOUR_DROPLET_IP`

## Step 9: Set Up Logs

```bash
# View service logs
sudo journalctl -u easyexcel-backend -f

# View application logs (if using nohup)
tail -f /var/log/easyexcel-backend.log
```

## Step 10: Set Up Automatic Updates (GitHub Actions)

Follow the `GITHUB_AUTO_DEPLOY.md` guide to set up GitHub Actions for automatic deployments.

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u easyexcel-backend -n 50

# Check if port is in use
sudo lsof -i :8000

# Test manually
cd /opt/easyexcel-backend/backend
source venv/bin/activate
python start_server.py
```

### Permission Errors
```bash
# Fix permissions
sudo chown -R root:root /opt/easyexcel-backend
```

### Port Already in Use
```bash
# Find process using port 8000
sudo lsof -i :8000
# Kill the process
sudo kill -9 PID
```

## Security Recommendations

1. **Set up SSH key authentication** (disable password auth)
2. **Configure fail2ban** to prevent brute force attacks
3. **Set up SSL/HTTPS** using Let's Encrypt
4. **Regular updates**: `apt update && apt upgrade`

## Next Steps

1. ✅ Backend is running on Droplet
2. ✅ Set up GitHub repository
3. ✅ Connect Vercel to GitHub
4. ✅ Set up GitHub Actions for auto-deploy
5. ✅ Configure custom domain (optional)

