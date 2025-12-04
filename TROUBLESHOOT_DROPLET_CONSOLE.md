# Troubleshoot Droplet Console Connection Issues

## Error: "Timed out while waiting for handshake"

This error occurs when the Droplet Console cannot establish a connection to your droplet. Here's how to fix it:

## Solution 1: Check if Droplet Agent is Running

The Droplet agent must be installed and running for the console to work.

### Check Agent Status
```bash
# Check if agent is installed
ls -la /opt/digitalocean/bin/droplet-agent

# Check agent service status (systemd)
systemctl status droplet-agent

# Or for older systems (initctl)
initctl status droplet-agent
```

### Install/Start the Agent

If the agent is not installed or not running:

```bash
# For Ubuntu/Debian
apt-get update
apt-get install -y droplet-agent

# Start the agent
systemctl enable droplet-agent
systemctl start droplet-agent

# Check status
systemctl status droplet-agent
```

## Solution 2: Check SSH Daemon Status

The Droplet Console requires SSH daemon to be running:

```bash
# Check SSH daemon status
systemctl status sshd
# or
systemctl status ssh

# If not running, start it
systemctl start sshd
systemctl enable sshd
```

## Solution 3: Check Firewall Rules

Ensure SSH traffic is allowed:

```bash
# Check UFW (Ubuntu Firewall)
ufw status
ufw allow ssh
ufw allow 22/tcp

# Check iptables
iptables -L -n | grep 22

# If using DigitalOcean Cloud Firewall, check in the control panel
```

## Solution 4: Restart Droplet Agent

If the agent is installed but not working:

```bash
# Restart the agent
systemctl daemon-reload
systemctl restart droplet-agent

# Check logs
journalctl -u droplet-agent -n 50
```

## Solution 5: Verify Network Connectivity

Check if the droplet can be reached:

```bash
# From your local machine, test SSH connection
ssh -v root@165.227.29.127

# Check if port 22 is open
nc -zv 165.227.29.127 22
```

## Solution 6: Use Recovery Console (Temporary)

If you need immediate access and the Droplet Console isn't working:

1. Go to DigitalOcean Control Panel
2. Click on your droplet
3. Click "Access" tab
4. Use "Recovery Console" instead (this uses VNC, not SSH)

## Solution 7: Reinstall Droplet Agent

If nothing else works:

```bash
# Remove old agent
systemctl stop droplet-agent
rm -rf /opt/digitalocean

# Reinstall
apt-get update
apt-get install -y droplet-agent

# Start and enable
systemctl enable droplet-agent
systemctl start droplet-agent

# Verify
systemctl status droplet-agent
```

## Quick Fix Command (Try This First)

```bash
# One-liner to check and fix common issues
systemctl restart droplet-agent && systemctl restart sshd && systemctl status droplet-agent
```

## After Fixing

1. Wait 1-2 minutes for the agent to fully initialize
2. Try the Droplet Console again
3. If still not working, check the agent logs: `journalctl -u droplet-agent -n 100`

## Reference

- [DigitalOcean Droplet Console Documentation](https://docs.digitalocean.com/products/droplets/how-to/connect-with-console)







