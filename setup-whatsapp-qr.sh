#!/bin/bash

# WhatsApp Bot Setup Script
# Helps with initial QR code scanning for WhatsApp Web authentication

set -e

echo "========================================="
echo "TankCtl WhatsApp Bot - QR Code Scanner"
echo "========================================="
echo ""

# Check if docker compose is available
if ! command -v docker compose &> /dev/null; then
    echo "ERROR: docker compose not found. Please install Docker."
    exit 1
fi

# Check if bot container is running
if ! docker compose ps whatsapp-bot | grep -q "Up"; then
    echo "ERROR: whatsapp-bot container is not running."
    echo "Start it with: docker compose up -d whatsapp-bot"
    exit 1
fi

echo "Waiting for bot to generate QR code..."
echo "This may take 20-30 seconds on first run."
echo ""

MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS=$(docker compose exec whatsapp-bot curl -s http://localhost:3001/health 2>/dev/null | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    
    if [ "$STATUS" = "ready" ]; then
        echo "✓ WhatsApp bot is authenticated and ready!"
        exit 0
    elif [ "$STATUS" = "starting" ]; then
        echo -ne "\rWaiting for QR code... ($((ATTEMPT))s)"
        ATTEMPT=$((ATTEMPT + 1))
        sleep 1
    fi
done

echo ""
echo "QR code generation timed out."
echo ""
echo "To manually authenticate:"
echo "1. Check the bot logs: docker compose logs whatsapp-bot -f"
echo "2. Scan the QR code with WhatsApp on your phone"
echo "3. Session will be saved to whatsapp-bot/session/"
echo ""
exit 1
