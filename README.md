```markdown
# Aquapi

Aquapi is a scalable, secure, cloud-controlled smart aquarium management system.  
It manages multiple tanks using lightweight ESP32 nodes, a FastAPI backend, Grafana dashboards, and real-time monitoring — all timestamped in IST.

---

## 🚀 Features

- 🌐 **Cloud-Controlled** — Manage and monitor aquariums from anywhere
- 🔒 **Secure** — Per-tank JWT authentication, Cloudflare Tunnel HTTPS
- 📈 **Grafana Dashboard** — Full admin control and visualization
- 🔄 **Over-the-Air (OTA) Firmware Updates** — Remotely update ESP32 devices
- 📬 **Real-time Discord Alerts** — Registration, Offline/Online status, Command success/failure
- 🐳 **Dockerized Deployment** — Easy launch with Docker Compose
- ⏰ **Indian Standard Time (IST)** — All system timestamps standardized to DD-MM-YYYY HH:MM IST

---

## 🛠 Stack Overview

| Component | Purpose |
|:----------|:--------|
| FastAPI | API server and orchestration |
| PostgreSQL | Primary database |
| Redis | Task queue (command retries) |
| Grafana | Dashboard for control and monitoring |
| Cloudflared | Secure HTTPS exposure |
| ESP32 Nodes | Lightweight agents (polling + action execution) |

---

## 📦 Project Structure

```plaintext
Aquapi/
├── app/                  # FastAPI backend
├── firmware/             # OTA firmware binaries for ESP32
├── docker-compose.yml    # Service orchestration
├── README.md             # Project documentation
└── .env.template         # Environment variable template
```

---

## ⚡ Quickstart

### 1. Clone the repository

```bash
git clone https://your-repo-url-here.git
cd Aquapi
```

### 2. Create your `.env` file

```bash
cp .env.template .env
# Fill in your database password, JWT secret, Cloudflare Tunnel token, etc.
```

### 3. Start the system

```bash
docker-compose up -d
```

---

## 🌐 Service Access

| Service | URL |
|:--------|:----|
| FastAPI | `https://api.yourdomain.com` |
| Grafana | `https://grafana.yourdomain.com` |

---

## 🔥 Core Flows

- ESP32 devices register with a pre-shared key → get Tank JWT
- ESP32 POSTs temperature, pH, and light status to server every 10s
- ESP32 polls server every 5s for pending commands (Feed Now, Light ON/OFF)
- Commands retry up to 3 times if ACK not received
- OTA firmware served via secured `/firmware/` endpoints
- Discord alerts triggered for key events (registration, failures, offline, etc.)

---

## 🔒 Security Model

- Per-tank JWT authentication (device scope)
- Admin JWT authentication (Grafana control scope)
- Full Cloudflare HTTPS protection
- Timestamps and logs in DD-MM-YYYY HH:MM IST

---

## 🧯 Recovery Plan

- Daily PostgreSQL backups using `pg_dump`
- ESP32 devices re-register automatically if token lost
- Simple Docker Compose re-deploy for server recovery
- Manual OTA rollback supported via firmware archives

---

## 📄 License

MIT License

---
```

✅ "**Give docker-compose.yml next**"  
✅ "**Bundle everything into Aquapi-Starter.zip**"  
✅ "**Pause here**"

What do you want next? 🎯🚀
