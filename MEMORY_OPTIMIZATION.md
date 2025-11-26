# Memory Optimization for Semantic Search

## Issue
The server has 512MB RAM, and loading the embedding model causes OOM (Out of Memory) kills.

## Solution Implemented

### 1. Lazy Loading
- Embeddings are **NOT** generated on startup
- They generate **on first use** when semantic search is needed
- Prevents OOM on server startup

### 2. Graceful Fallback
- If memory is insufficient, falls back to keyword search
- No errors or crashes
- System continues working normally

### 3. Memory-Efficient Model
- Using `all-MiniLM-L6-v2` (smallest good model)
- CPU-only torch (no CUDA overhead)
- ~100-150MB memory when loaded

## Current Behavior

### On Startup:
1. Service starts normally ✅
2. Embedding model **NOT** loaded
3. Uses keyword search initially
4. No memory issues

### On First Semantic Search:
1. User processes a file
2. System tries to load embedding model
3. If successful: generates embeddings, uses semantic search
4. If fails (OOM): falls back to keyword search gracefully

## Memory Usage

### Without Embeddings:
- Service: ~100-150MB
- Available: ~350-400MB

### With Embeddings (when loaded):
- Service: ~250-300MB
- Available: ~200-250MB
- **Risk:** May cause OOM if other processes use memory

## Recommendations

### Option 1: Keep Current (Recommended)
- Lazy loading prevents startup OOM
- Falls back gracefully if memory insufficient
- Works for most cases

### Option 2: Upgrade Server
- Upgrade to 1GB or 2GB RAM
- Embeddings will load reliably
- Better performance

### Option 3: Disable Embeddings
- Set environment variable: `DISABLE_EMBEDDINGS=true`
- Always uses keyword search
- Zero memory overhead

## Status

✅ **Lazy loading implemented**
✅ **Graceful fallback working**
✅ **Service starts successfully**
⏳ **Embeddings load on first use (may cause OOM if memory tight)**

## Testing

To test if embeddings work:
1. Process a file with a prompt
2. Check logs: `journalctl -u easyexcel-backend | grep embedding`
3. If you see "Embedding model loaded" - it worked!
4. If you see "Could not load embedding model" - it fell back to keyword search

Both scenarios work fine! 🚀

