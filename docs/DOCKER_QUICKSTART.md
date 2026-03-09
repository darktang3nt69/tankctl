# TankCtl Docker Quick Start

**Get TankCtl running in 5 minutes.**

---

## 1️⃣ Build

```bash
# Build the Docker image
docker build -t tankctl-backend:latest .

# Verify build completed
docker images | grep tankctl-backend
```

Expected output:
```
REPOSITORY        TAG      SIZE
tankctl-backend   latest   195MB
```

---

## 2️⃣ Start Services

```bash
# Start all services (PostgreSQL, TimescaleDB, MQTT, Grafana, Backend)
docker-compose up -d

# Watch the startup
docker-compose logs -f backend
```

**Expected sequence:**
1. PostgreSQL starts
2. TimescaleDB starts  
3. MQTT starts
4. Backend starts
5. Grafana starts

---

## 3️⃣ Verify Health

```bash
# Check all services are running
docker-compose ps

# Should show all services with "healthy" or "up"
# CONTAINER ID  STATUS         NAMES
# ...           healthy        tankctl-backend
# ...           healthy        mosquitto
# ...           healthy        postgres
```

Test API:
```bash
# Health endpoint
curl http://localhost:8000/health

# Should return: {"status": "healthy"}

# API root
curl http://localhost:8000/

# Base API response
curl http://localhost:8000/devices
```

---

## 4️⃣ View Dashboards

| Service | URL | User | Password |
|---------|-----|------|----------|
| API | http://localhost:8000 | - | - |
| Grafana | http://localhost:3000 | admin | admin |
| PgAdmin | http://localhost:5050 | - | - |

---

## 5️⃣ Test with Simulator

```bash
# Terminal 1: Watch backend logs
docker-compose logs -f backend

# Terminal 2: Run device simulator
python tools/device_simulator.py --devices 3 --hours 1

# Verify simulator connects and publishes telemetry
# Check backend logs for incoming messages
```

---

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DELETE DATA!)
docker-compose down -v
```

---

## 📊 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Real-time resource usage
docker stats
```

---

## 🔧 Configuration

Environment variables in `docker-compose.yml`:

```yaml
environment:
  API_HOST: 0.0.0.0
  API_PORT: 8000
  MQTT_BROKER_HOST: mosquitto
  POSTGRES_HOST: postgres
  TIMESCALE_HOST: timescaledb
```

To customize, create `.env`:
```bash
# .env
API_DEBUG=true
POSTGRES_PASSWORD=my_password

# Start with custom env
docker-compose --env-file .env up -d
```

---

## ✅ Verification Checklist

- [ ] Docker image built (check size ~195MB)
- [ ] All containers running (`docker-compose ps`)
- [ ] Health endpoint responds (`curl http://localhost:8000/health`)
- [ ] API endpoints work (`curl http://localhost:8000/devices`)
- [ ] Could simulate devices with simulator
- [ ] No error logs (`docker-compose logs backend`)

---

## 🐛 Troubleshooting

### Container won't start
```bash
docker-compose logs backend
```

### Health check failing
```bash
docker-compose exec backend curl http://localhost:8000/health
```

### MQTT not connecting
```bash
docker-compose logs mosquitto
```

### Database not ready
```bash
docker-compose logs postgres
```

---

## 📚 Full Documentation

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for:
- Complete Dockerfile explanation
- Production configuration
- Performance optimization
- Security best practices
- Troubleshooting guide
- Maintenance procedures

---

**Ready to go!** 🚀

```bash
docker-compose up -d
```
