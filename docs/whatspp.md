# WHATSAPP_INTEGRATION.md

## Overview

This document describes how **TankCtl sends event notifications to WhatsApp** using **WhatsApp Web automation**.

Instead of using the official WhatsApp Business API, TankCtl runs a **local WhatsApp bot service** that automates WhatsApp Web.
The backend sends messages to this bot through a simple HTTP API.

This approach is ideal for **personal IoT systems** because:

* no API approval is required
* no usage fees
* easy to deploy
* works with a normal WhatsApp account

---

# Architecture

The notification flow is:

```text
Arduino Device
      ↓
MQTT Telemetry / Events
      ↓
TankCtl Backend
      ↓
Alert Service
      ↓
Notification Service
      ↓
WhatsApp Bot (WhatsApp Web automation)
      ↓
WhatsApp Message
```

Responsibilities:

| Component            | Responsibility                |
| -------------------- | ----------------------------- |
| Arduino              | sends telemetry and heartbeat |
| Backend              | processes events              |
| Alert Service        | evaluates alert conditions    |
| Notification Service | sends notifications           |
| WhatsApp Bot         | delivers messages to WhatsApp |

---

# WhatsApp Bot Service

TankCtl uses a small **Node.js service** that automates WhatsApp Web.

Recommended library:

```text
whatsapp-web.js
```

This library controls WhatsApp Web using a headless browser.

Advantages:

* stable
* widely used
* QR login once
* session persistence

---

# Bot Service Structure

Example directory:

```text
whatsapp-bot/
 ├── bot.js
 ├── package.json
 └── session/
```

The `session` directory stores login data so the bot remains authenticated.

---

# Installation

Initialize the project:

```bash
npm init -y
```

Install dependencies:

```bash
npm install whatsapp-web.js express qrcode-terminal
```

---

# Bot Implementation

Example `bot.js`:

```javascript
const { Client, LocalAuth } = require("whatsapp-web.js");
const express = require("express");
const qrcode = require("qrcode-terminal");

const app = express();
app.use(express.json());

const client = new Client({
  authStrategy: new LocalAuth()
});

client.on("qr", (qr) => {
  console.log("Scan this QR code with WhatsApp:");
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  console.log("WhatsApp bot ready");
});

client.initialize();

app.post("/send", async (req, res) => {

  const { number, message } = req.body;

  const chatId = number + "@c.us";

  await client.sendMessage(chatId, message);

  res.json({ status: "sent" });

});

app.listen(3001, () => {
  console.log("WhatsApp API running on port 3001");
});
```

---

# First Login

When the bot starts for the first time:

```bash
node bot.js
```

A QR code will appear in the terminal.

Steps:

1. Open WhatsApp on your phone
2. Go to **Linked Devices**
3. Click **Link Device**
4. Scan the QR code

After scanning, the session is stored locally and the bot remains logged in.

---

# Sending Messages From Backend

The TankCtl backend sends messages to the bot using HTTP.

Endpoint:

```text
POST http://whatsapp-bot:3001/send
```

Example request:

```json
{
  "number": "919999999999",
  "message": "⚠️ Tank1 temperature HIGH: 30.5°C"
}
```

---

# Backend Notification Service

Add a service in the backend:

```text
src/services/notification_service.py
```

Example implementation:

```python
import requests

class NotificationService:

    BOT_URL = "http://whatsapp-bot:3001/send"
    PHONE_NUMBER = "919999999999"

    def send_whatsapp(self, message: str):

        requests.post(
            self.BOT_URL,
            json={
                "number": self.PHONE_NUMBER,
                "message": message
            }
        )
```

This service can be used by the alert system.

---

# Example Alert Messages

Temperature alert:

```
⚠️ Tank1 temperature HIGH: 30.8°C
```

Device offline:

```
⚠️ Tank1 device OFFLINE
```

Device reconnected:

```
✅ Tank1 device reconnected
```

Manual override:

```
💡 Tank1 lights manually turned OFF
```

---

# Alert Triggers

The alert layer decides when to send notifications.

Typical triggers:

### Temperature Alerts

```
temperature > 30°C
temperature < 20°C
```

### Device Offline

```
no heartbeat for 60 seconds
```

### Device Recovery

```
device reconnect detected
```

---

# Rate Limiting

To avoid spam, alerts should be rate-limited.

Example:

```text
maximum 1 alert every 10 minutes
```

Implementation idea:

```
store last_alert_timestamp
```

Alerts are suppressed if sent too recently.

---

# Docker Deployment

The WhatsApp bot can run as part of the TankCtl stack.

Example `docker-compose` service:

```yaml
whatsapp-bot:
  image: node:20
  working_dir: /app
  volumes:
    - ./whatsapp-bot:/app
  command: node bot.js
  ports:
    - "3001:3001"
```

This allows the backend to communicate with the bot inside the Docker network.

---

# Security Considerations

Recommendations:

* run the bot inside the internal Docker network
* do not expose the API publicly
* restrict allowed phone numbers
* keep session storage persistent

---

# Future Improvements

Possible enhancements:

* WhatsApp command interface (control TankCtl via chat)
* multi-user notifications
* group chat alerts
* alert severity levels
* message templates

Example interactive command:

```
lights off tank1
```

The bot could parse this command and send an MQTT command to the backend.

---

# Design Goals

The WhatsApp notification system aims to be:

* simple
* reliable
* easy to deploy
* independent from commercial APIs
* suitable for personal IoT deployments
