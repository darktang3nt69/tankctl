#!/bin/bash
# Cleanup and start WhatsApp bot

# echo "🧹 Cleaning old Chrome processes..."
# pkill -9 chromium 2>/dev/null || true
# rm -rf /tmp/chrome-profile 2>/dev/null || true

echo "✅ Starting WhatsApp bot..."
exec node bot.js
