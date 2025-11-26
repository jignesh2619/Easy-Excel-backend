# 🔄 Droplet Resize Steps

## Current Status
- **Current Plan:** 512 MB / 1 vCPU
- **Selected Plan:** 1 GB / 1 vCPU ($6/month) ✅ **CORRECT CHOICE!**

## Step-by-Step Process

### Step 1: Turn Off Droplet
1. In DigitalOcean dashboard, go to your droplet
2. Click the **"Power"** button (top right)
3. Select **"Power Off"**
4. Wait for it to fully shut down (~30 seconds)

### Step 2: Resize
1. With droplet powered off, click **"Resize"** again
2. You should see the same page
3. **Confirm** the 1 GB plan is selected (highlighted in blue)
4. Click **"Resize Droplet"** button at bottom
5. Wait 1-2 minutes for resize to complete

### Step 3: Power On
1. After resize completes, click **"Power"** button
2. Select **"Power On"**
3. Wait ~30 seconds for server to boot

### Step 4: Verify & Enable Semantic Search

Once the server is back online:

```bash
# SSH into server
ssh root@165.227.29.127

# Check new memory
free -h
# Should show: ~1GB total, ~500MB+ free

# Enable semantic search
cd /opt/easyexcel-backend
sed -i '/DISABLE_EMBEDDINGS/d' .env

# Restart service
systemctl restart easyexcel-backend

# Check service status
systemctl status easyexcel-backend
# Should show: Active (running), Memory: ~200-300MB

# Verify embeddings loaded
journalctl -u easyexcel-backend -n 50 | grep -i embedding
# Should see: "Embedding model loaded: all-MiniLM-L6-v2"
```

## What to Expect

### Before Resize:
- Memory: 512MB (31MB free)
- Semantic search: ❌ Disabled
- Stability: ⚠️ Low

### After Resize:
- Memory: 1GB (~500MB+ free)
- Semantic search: ✅ Enabled
- Stability: ✅ Good
- Cost: +$2/month

## Troubleshooting

### If service doesn't start:
```bash
# Check logs
journalctl -u easyexcel-backend -n 100

# Restart manually
cd /opt/easyexcel-backend
systemctl restart easyexcel-backend
```

### If embeddings don't load:
```bash
# Check if disabled flag is gone
cat .env | grep DISABLE
# Should return nothing

# Check memory
free -h
# Should show 500MB+ free

# Check logs
journalctl -u easyexcel-backend | grep embedding
```

## Ready to Proceed?

1. ✅ You've selected the right plan (1GB for $6/mo)
2. ⏳ Turn off the droplet
3. ⏳ Click "Resize Droplet"
4. ⏳ Power it back on
5. ⏳ Run the commands above to enable semantic search

**Let me know when the resize is complete and I'll help you enable semantic search!** 🚀

