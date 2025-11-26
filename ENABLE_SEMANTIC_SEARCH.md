# ✅ Enable Semantic Search After Resize

## Current Status
- ✅ **Resize Complete:** Droplet now has 1GB RAM
- ⏳ **Server Status:** Needs to be powered on

## Step 1: Power On Droplet

1. In DigitalOcean dashboard, find your droplet
2. Click the **"Power"** button (or toggle switch)
3. Select **"Power On"**
4. Wait **30-60 seconds** for server to boot

## Step 2: Verify Server is Running

Once powered on, wait a minute, then check:

```bash
# Test connection
ssh root@165.227.29.127

# Check memory (should show ~1GB now)
free -h
# Should see: ~1GB total, ~500MB+ free

# Check service
systemctl status easyexcel-backend
```

## Step 3: Enable Semantic Search

Once the server is online, run these commands:

```bash
ssh root@165.227.29.127

# Navigate to backend
cd /opt/easyexcel-backend

# Remove the disable flag
sed -i '/DISABLE_EMBEDDINGS/d' .env

# Verify it's removed
cat .env | grep DISABLE || echo "✅ Flag removed!"

# Restart service
systemctl restart easyexcel-backend

# Wait a moment for embeddings to load
sleep 15

# Check if embeddings loaded
journalctl -u easyexcel-backend -n 100 | grep -i embedding
# Should see: "Embedding model loaded: all-MiniLM-L6-v2"
```

## Step 4: Verify Everything Works

```bash
# Check service status
systemctl status easyexcel-backend
# Should show: Active (running), Memory: ~200-300MB

# Check memory usage
free -h
# Should show: ~500MB+ free (enough for embeddings!)

# Check logs for semantic search
journalctl -u easyexcel-backend | grep -E "semantic|embedding|training"
# Should see embedding-related messages
```

## Expected Results

### Before (512MB):
- Memory: 512MB (31MB free)
- Semantic search: ❌ Disabled
- Embeddings: Not loaded

### After (1GB):
- Memory: 1GB (~500MB+ free) ✅
- Semantic search: ✅ Enabled
- Embeddings: ✅ Loaded
- Better accuracy: 15-25% improvement!

## Troubleshooting

### If server won't connect:
- Wait 1-2 minutes after power on
- Check DigitalOcean dashboard - droplet should show "Active"
- Try: `ping 165.227.29.127` to test connectivity

### If embeddings don't load:
```bash
# Check memory
free -h
# Need at least 200MB free

# Check if flag is removed
cat /opt/easyexcel-backend/.env | grep DISABLE
# Should return nothing

# Check logs
journalctl -u easyexcel-backend -n 200
# Look for errors
```

### If service fails:
```bash
# Restart service
systemctl restart easyexcel-backend

# Check status
systemctl status easyexcel-backend

# View logs
journalctl -u easyexcel-backend -f
```

## Next Steps

1. ⏳ **Power on** the droplet in DigitalOcean
2. ⏳ **Wait 1 minute** for boot
3. ⏳ **SSH in** and run the commands above
4. ✅ **Verify** embeddings loaded
5. 🚀 **Test** by processing a file!

**Once the server is powered on, let me know and I'll help you enable semantic search!** 🎯

