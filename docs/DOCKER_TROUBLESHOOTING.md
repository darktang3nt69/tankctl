# Docker Troubleshooting Guide

**Common Docker issues and solutions for TankCtl.**

---

## 🔴 Container Status Issues

### Container won't start

**Symptom:** Container appears but immediately exits

```bash
docker-compose up -d backend
docker-compose ps  # Shows "Exited"
```

**Diagnosis:**
```bash
# View detailed error
docker-compose logs backend

# Run with interactive shell to test
docker run -it tankctl-backend:latest /bin/bash

# Check if image built correctly
docker images tankctl-backend
```

**Solutions:**

1. **Rebuild image from scratch**
   ```bash
   docker-compose build --no-cache backend
   docker-compose up -d backend
   ```

2. **Verify Dockerfile syntax**
   ```bash
   docker build --progress=plain -t test .
   ```

3. **Check dependencies installed**
   ```bash
   docker run tankctl-backend:latest pip list
   ```

4. **Inspect image layers**
   ```bash
   docker history tankctl-backend:latest
   ```

---

### Health check failing

**Symptom:**
```
tankctl-backend  unhealthy
```

**Diagnosis:**
```bash
# Test health endpoint directly
docker-compose exec backend curl http://localhost:8000/health

# View health check logs
docker-compose exec backend curl -v http://localhost:8000/health

# Check service logs
docker-compose logs --tail=50 backend
```

**Solutions:**

1. **Verify API is running**
   ```bash
   # Check if uvicorn started
   docker-compose exec backend ps aux | grep uvicorn
   ```

2. **Check if port 8000 is listening**
   ```bash
   docker-compose exec backend netstat -tlnp | grep 8000
   ```

3. **Wait longer before health check**
   ```yaml
   healthcheck:
     start_period: 15s  # Increase from 5s
   ```

4. **Test endpoint manually**
   ```bash
   docker-compose exec backend curl http://localhost:8000/
   ```

---

### Services not connecting

**Symptom:** Backend can't reach other services

```
ERROR: Connection refused (postgres, mosquitto, etc.)
```

**Diagnosis:**
```bash
# Check network connectivity
docker-compose exec backend ping postgres
docker-compose exec backend ping mosquitto
docker-compose exec backend ping timescaledb

# Check DNS resolution
docker-compose exec backend nslookup postgres
```

**Solutions:**

1. **Ensure all services are running**
   ```bash
   docker-compose ps
   # All should show "Up" or "healthy"
   ```

2. **Check service names are correct**
   ```yaml
   # In docker-compose.yml
   services:
     postgres:  # Service name must match
       ...
     backend:
       environment:
         POSTGRES_HOST: postgres  # Must match service name
   ```

3. **Verify network exists**
   ```bash
   docker network ls
   docker network inspect tankctl-network
   ```

4. **Restart all services**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## 🟠 Build Issues

### Build fails with "permission denied"

**Symptom:**
```
ERROR: permission denied while trying to connect to Docker daemon
```

**Solutions:**

1. **Add user to docker group**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Use sudo (temporary)**
   ```bash
   sudo docker build -t tankctl-backend .
   ```

3. **Check Docker daemon running**
   ```bash
   systemctl status docker
   sudo systemctl start docker
   ```

---

### Build uses too much disk space

**Symptom:**
```
ERROR: error creating build cache: failed to write index for database
```

**Solutions:**

1. **Clear old images**
   ```bash
   docker image prune -a
   ```

2. **Clean up volumes**
   ```bash
   docker volume prune
   ```

3. **Remove all unused**
   ```bash
   docker system prune -a --volumes
   ```

4. **Check disk space**
   ```bash
   df -h  # Check free space
   du -sh ~/.docker  # Docker storage size
   ```

---

### Build is too slow

**Symptom:** Takes >5 minutes to build

**Solutions:**

1. **Check layer caching**
   ```bash
   # Should see "CACHED" in output
   docker build --progress=plain -t tankctl-backend . | grep CACHED
   
   # If not using cache, rebuild without changes to verify
   ```

2. **Reduce context size**
   ```bash
   # Check .dockerignore
   cat .dockerignore
   
   # Verify it includes tests/, docs/, etc.
   ```

3. **Use BuildKit**
   ```bash
   DOCKER_BUILDKIT=1 docker build -t tankctl-backend .
   ```

4. **Parallel pip installs**
   ```bash
   # In Dockerfile, use --compile with pip
   pip install --compile -r requirements.txt
   ```

---

### Build succeeds but image is too large

**Current:** ~195MB  
**Too large:** >400MB

**Solutions:**

1. **Check image size vs expected**
   ```bash
   docker images tankctl-backend
   
   # Should show ~195MB
   # If larger, check what's included
   ```

2. **Verify multi-stage build working**
   ```bash
   docker history tankctl-backend:latest
   
   # Should show:
   # - Builder layer (~500MB) - NOT in final
   # - Runtime layer (~195MB) - final image
   ```

3. **Remove unnecessary files**
   ```bash
   # Update .dockerignore
   # Add files that don't need to be copied
   
   # Rebuild
   docker build --no-cache -t tankctl-backend .
   ```

---

## 🟡 Runtime Issues

### High memory usage

**Symptom:**
```bash
docker stats  # Shows backend using >500MB
```

**Solutions:**

1. **Set memory limits**
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           memory: 512M
   ```

2. **Check for memory leaks**
   ```bash
   # Monitor memory over time
   docker stats --no-stream tankctl-backend
   
   # If growing continuously, there's a leak
   ```

3. **Reduce worker count**
   ```bash
   # In Dockerfile CMD
   ENV WORKERS=2
   CMD ["uvicorn", "src.api.main:app", "--workers", "${WORKERS}", ...]
   ```

---

### High CPU usage

**Symptom:**
```bash
docker stats  # Shows backend using 80%+ CPU
```

**Solutions:**

1. **Check active tasks**
   ```bash
   docker-compose logs backend | grep "ERROR\|WARNING"
   ```

2. **Limit worker threads**
   ```bash
   ENV WORKERS=1
   ```

3. **Check for busy loops**
   ```bash
   # Review recent code changes
   # Look for infinite loops or rapid polling
   ```

4. **Set CPU limits**
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           cpus: '1'
   ```

---

### Container intermittently crashes

**Symptom:**
```bash
docker-compose ps  # Container status changes frequently
```

**Diagnosis:**
```bash
# Check all logs
docker-compose logs backend | tail -100

# Look for patterns in errors
docker-compose logs backend | grep ERROR

# Check system logs
dmesg | tail -20
```

**Solutions:**

1. **Increase memory**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
   ```

2. **Increase restart grace period**
   ```yaml
   restart: unless-stopped
   stop_grace_period: 30s
   ```

3. **Check for resource exhaustion**
   ```bash
   # Check open file descriptors
   docker-compose exec backend cat /proc/1/limits
   ```

---

## 🔵 Database Issues

### Can't connect to PostgreSQL

**Symptom:**
```
ERROR: could not translate host name "postgres" to address
```

**Diagnosis:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres  # Should show "up"

# Test connectivity
docker-compose exec backend ping postgres

# Check PostgreSQL logs
docker-compose logs postgres
```

**Solutions:**

1. **Verify service name**
   ```yaml
   services:
     postgres:  # Must be exact name
   environment:
     POSTGRES_HOST: postgres  # Must match
   ```

2. **Wait for PostgreSQL to be ready**
   ```bash
   docker-compose exec backend pg_isready -h postgres
   # Repeat until shows "accepting connections"
   ```

3. **Check credentials**
   ```bash
   # In docker-compose.yml
   POSTGRES_USER: tankctl
   POSTGRES_PASSWORD: password
   ```

4. **Restart PostgreSQL**
   ```bash
   docker-compose restart postgres
   ```

---

### Database volume lost

**Symptom:** Data disappeared after restart

**Prevention:**
```bash
# Use named volume
docker-compose down  # DON'T use -v flag!

# ✅ Correct: keeps volumes
docker-compose down

# ❌ Wrong: deletes volumes
docker-compose down -v
```

**Recovery:**
```bash
# Check if volume still exists
docker volume ls | grep postgres

# If exists, can recover by restarting
docker-compose up postgres

# If deleted, data is gone (use backups)
```

---

### TimescaleDB connection issues

**Symptom:**
```
ERROR: could not connect to timescaledb
```

**Solutions:**

1. **Check TimescaleDB is running**
   ```bash
   docker-compose ps timescaledb
   ```

2. **Verify credentials match**
   ```yaml
   TIMESCALE_HOST: timescaledb
   TIMESCALE_USER: tankctl
   TIMESCALE_PASSWORD: password
   ```

3. **Check if extension initialized**
   ```bash
   docker-compose exec timescaledb psql -U tankctl -d tankctl_telemetry -c '\dx'
   ```

---

## 🟢 MQTT Issues

### Can't connect to Mosquitto

**Symptom:**
```
ERROR: Connection refused on port 1883
```

**Diagnosis:**
```bash
# Check Mosquitto is running
docker-compose exec backend mosquitto_sub -h mosquitto -t test

# Check port is open
docker-compose exec mosquitto netstat -tlnp | grep 1883
```

**Solutions:**

1. **Verify service is healthy**
   ```bash
   docker-compose ps mosquitto
   ```

2. **Check Mosquitto logs**
   ```bash
   docker-compose logs mosquitto | tail -20
   ```

3. **Verify credentials**
   ```yaml
   MQTT_BROKER_HOST: mosquitto
   MQTT_BROKER_PORT: 1883
   MQTT_USERNAME: tankctl
   MQTT_PASSWORD: password
   ```

4. **Restart MQTT broker**
   ```bash
   docker-compose restart mosquitto
   ```

---

## 🟣 Network Issues

### Container can't reach external services

**Symptom:** Can't reach external APIs, GitHub, etc.

**Solutions:**

1. **Check host network connectivity**
   ```bash
   docker-compose exec backend ping 8.8.8.8
   docker-compose exec backend curl https://api.github.com
   ```

2. **Check DNS resolution**
   ```bash
   docker-compose exec backend nslookup google.com
   ```

3. **Check firewall rules**
   ```bash
   # Host firewall blocking docker
   sudo iptables -L -n | grep FORWARD
   ```

4. **Use host network (dev only)**
   ```yaml
   backend:
     network_mode: host
   ```

---

### Containers can't communicate

**Symptom:** Services isolated from each other

**Solution:**

1. **Check custom network**
   ```yaml
   networks:
     tankctl-network:
       driver: bridge
   
   services:
     backend:
       networks:
         - tankctl-network
     postgres:
       networks:
         - tankctl-network
   ```

---

## 📋 Diagnostic Commands

### Get complete system status

```bash
# All containers
docker-compose ps

# Detailed container info
docker-compose exec backend env

# Network connectivity
docker-compose exec backend ping mosquitto
docker-compose exec backend ping postgres
docker-compose exec backend pg_isready -h postgres

# Port bindings
docker-compose port backend 8000

# Resource usage
docker stats --no-stream

# All logs combined
docker-compose logs --timestamp
```

### Debug shell access

```bash
# Interactive shell
docker-compose exec backend /bin/bash

# One-off command
docker-compose exec backend env

# Run as root (if needed)
docker-compose exec -u root backend apt-get update

# Test API manually
docker-compose exec backend python -m http.client localhost 8000
```

---

## 🆘 Still Stuck?

### Gather diagnostic info

```bash
# Save all diagnostics to file
{
  echo "=== Docker Version ==="
  docker --version
  
  echo "=== Services Status ==="
  docker-compose ps
  
  echo "=== Backend Health ==="
  curl -s http://localhost:8000/health || echo "ERROR"
  
  echo "=== Recent Logs (last 100 lines) ==="
  docker-compose logs --tail=100 backend
  
  echo "=== All Logs ==="
  docker-compose logs backend
  
  echo "=== Network ==="
  docker network ls
  docker network inspect tankctl-network
  
  echo "=== Resources ==="
  docker stats --no-stream
} > diagnostics.txt

cat diagnostics.txt
```

### Recovery steps

1. **Restart everything**
   ```bash
   docker-compose down
   docker-compose build --no-cache backend
   docker-compose up -d
   ```

2. **Full reset**
   ```bash
   docker-compose down -v  # WARNING: deletes data!
   docker system prune -a --volumes
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Check resources**
   ```bash
   df -h              # Disk space
   free -h            # Memory
   ps aux | grep docker  # Docker process
   ```

---

## 📞 Getting Help

When reporting issues, include:

1. **docker-compose.yml** snippet
2. **Dockerfile** (if modified)
3. **docker-compose ps** output
4. **docker-compose logs** (last 50 lines)
5. **docker stats** output
6. **Error messages** (exact text)
7. **Environment info**: OS, Docker version, host specs

---

**Most issues resolved by:**
```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
docker-compose logs -f backend
```

Good luck! 🍀
