# 🐟 tankctl

> **A Kubernetes-Inspired Control Plane for Smart Aquariums**  
> Secure. Scalable. Server-driven. Powered by FastAPI, Celery, Grafana, and ESP32.

---

## 📸 Overview

**tankctl** is a full-stack smart aquarium automation system that allows secure and scalable control of multiple aquarium tanks via a central API server. It mimics Kubernetes-style architecture—nodes (ESP32s) register themselves, report state, and receive scheduled or user-triggered commands. All communication is authenticated, logged, and visible via Grafana dashboards.

---

## 🔧 Features

- 🔐 **Secure Node Registration** using pre-approved keys and JWTs
- 🌊 **Real-time Status Updates** from each ESP32 tank node
- 📦 **Command Queueing & Retry Logic** using Celery + Redis
- 💡 **Grafana UI with Canvas Panels** for live control and schedule setting
- 📣 **Discord Alerts** for successful actions and critical failures
- 🌐 **Internet-Accessible via Cloudflare Tunnel** with full TLS
- 🔁 **Per-Tank Isolation** using `tank_id` across all routes, logs, and configs

---

## 🧱 Architecture

```text
               +------------------+
               |   Grafana UI     |
               +------------------+
                        |
                        ▼
+-----------------------------+
|   FastAPI Control Server    |  <-- TLS via Cloudflare
+-----------------------------+
 |       |           |        |
 ▼       ▼           ▼        ▼
ESP32   ESP32       DB       Redis
(tankA) (tankB)     ↑         ↑
       polling     |       Celery
       commands    |       tasks
       + status    +---> Command Logic
```

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/tankctl.git
cd tankctl
```

### 2. Create Tunnel & Place `credentials.json`

```bash
cloudflared tunnel login
cloudflared tunnel create aquarium-tunnel
# Add tunnel ID to config.yml and DNS entries in Cloudflare
```

### 3. Start the Stack

```bash
docker-compose up --build
```

### 4. Register an ESP32 Node

- Flash your ESP32 with firmware that calls:
  - `POST /register`
  - `POST /status`
  - `GET /commands/<tank_id>`
  - `POST /ack`
- Store returned JWT in Preferences

---

## 🔐 API Endpoints

| Endpoint            | Method | Auth | Description                      |
|---------------------|--------|------|----------------------------------|
| `/register`         | POST   | No   | Register node, get token         |
| `/status`           | POST   | Yes  | Report temp, pH, light state     |
| `/commands/<tank>`  | GET    | Yes  | Get queued command               |
| `/commands/ack`     | POST   | Yes  | Acknowledge command success      |
| `/config/update`    | POST   | Yes  | Update schedules (via Grafana)   |

---

## 📊 Grafana Dashboard

- Select aquarium from `$aquarium` variable
- Trigger actions via Canvas button panel
- View real-time status, logs, and node health

---

## 📣 Discord Alerts

- Command executed successfully ✅  
- Command failed after retries ❌  
- Tank node offline ⚠️  

---

## 📁 Stack Components

| Component | Tech Stack                       |
|-----------|----------------------------------|
| API       | FastAPI + SQLAlchemy             |
| DB        | PostgreSQL                       |
| Queue     | Celery + Redis                   |
| Tunneling | Cloudflare Tunnel                |
| UI        | Grafana with Canvas plugin       |
| Alerts    | Discord Webhooks                 |
| Nodes     | ESP32 + ArduinoJson + WiFiClient |

---

## 📝 License

MIT License © 2024 [Your Name or Org]

---

## 🤝 Contribute

Pull requests and issues are welcome!  
Want to collaborate on the firmware or build a plug-n-play enclosure? Let's make it happen.

## Environment Variables

The following environment variables are required for the application to function:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/tankctl

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key-here
PRE_SHARED_KEY=your-pre-shared-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

Create a `.env` file in the project root with these variables set to appropriate values.
