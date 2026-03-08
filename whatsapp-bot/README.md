# WhatsApp Bot - TankCtl Integration

This is a containerized WhatsApp bot service that enables TankCtl to send alert notifications via WhatsApp.

## Architecture

```
TankCtl Backend
    ↓ (event-driven alerts)
NotificationService
    ↓ (HTTP POST)
WhatsApp Bot API (:3001)
    ↓ (WhatsApp Web automation)
WhatsApp Desktop Client (via Puppeteer/Chromium)
    ↓
WhatsApp Message
```

## Getting Started

### 1. Build the Container

```bash
docker compose build whatsapp-bot
```

The Dockerfile includes:
- Node.js 20 + system Chromium
- All WhatsApp dependencies
- LocalAuth for session persistence
- Healthcheck endpoint

### 2. Start the Bot

```bash
docker compose up -d whatsapp-bot
```

### 3. Authenticate (First-Time Only)

The bot will initialize Chromium and generate a QR code:

```bash
# Monitor logs for QR code output
docker compose logs whatsapp-bot -f
```

Once you see the QR code in the logs:

1. Open the QR code terminal link/image
2. Open WhatsApp on your phone
3. Go to **Settings → Linked Devices → Link a Device**
4. Scan the QR code

Your session will be saved in `whatsapp-bot/session/` and persisted across restarts.

### 4. Configure Backend

In `docker-compose.yml`, set the backend environment variables:

```yaml
backend:
  environment:
    WHATSAPP_ENABLED: "true"
    WHATSAPP_PHONE_NUMBER: "919999999999"  # Your phone number
    ALERTS_ENABLED: "true"
```

Target phone number format: **country code + number** (e.g., `919876543210` for India)

## API Endpoints

### Health Check

```bash
curl http://localhost:3001/health
```

Response:
```json
{"status": "ready"}   # or "starting"
```

### Send Message

```bash
curl -X POST http://localhost:3001/send \
  -H "Content-Type: application/json" \
  -d '{
    "number": "919999999999",
    "message": "Alert: Tank temperature HIGH"
  }'
```

Response:
```json
{"status": "sent"}
```

## Troubleshooting

### Bot shows "starting" status

- The bot is initializing Chromium and the WhatsApp Web client
- Wait 20-30 seconds, then try again
- Check logs: `docker compose logs whatsapp-bot`

### "Chrome executable not found" error

- The bot will automatically use system Chromium at `/usr/bin/chromium`
- If you get a different error, check the Dockerfile for system dep installation

### Session won't persist

- Ensure `whatsapp-bot/session/` directory is writable
- Check volume mount in `docker-compose.yml`
- Restart: `docker compose restart whatsapp-bot`

### Messages not sending

1. Check backend notification service logs:
   ```bash
   docker compose logs backend | grep -i whatsapp
   ```

2. Verify bot is healthy:
   ```bash
   docker compose exec whatsapp-bot curl http://localhost:3001/health
   ```

3. Check allowed phone numbers in environment:
   ```bash
   docker compose exec whatsapp-bot env | grep WHATSAPP
   ```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHATSAPP_BOT_PORT` | `3001` | Bot API port |
| `WHATSAPP_SESSION_PATH` | `/app/session` | Path to persist WhatsApp session |
| `WHATSAPP_ALLOWED_NUMBERS` | `` | Comma-separated allowed numbers (empty = all) |
| `CHROME_EXECUTABLE_PATH` | `/usr/bin/chromium` | Path to Chrome/Chromium binary |
| `NODE_ENV` | `production` | Node environment |

## Security Notes

- The bot API has no authentication. Run it only on private networks
- Restrict with `WHATSAPP_ALLOWED_NUMBERS` to prevent abuse
- Session tokens are stored unencrypted in `whatsapp-bot/session/`
- Never commit session files to git (already in `.gitignore`)

## Performance

- Bot container uses ~500MB RAM at idle
- Chrome may use additional RAM when active
- Chromium launch with `--disable-dev-shm-usage` reduces memory overhead

## Advanced: Pre-authenticated Session

To skip the QR code scan:

1. Authenticate the bot once (scan QR)
2. Copy `whatsapp-bot/session/` directory
3. Restore it into new deployments
4. Sessions expire after inactivity; re-authenticate if needed

## Limitations

- Only personal WhatsApp accounts (no Business API)
- Rate limit depends on WhatsApp's rate limiting
- Requires internet connectivity
- Session may disconnect if bot restarts or network issues occur
