---
title: Development Workflow & Commands
type: reference
permalink: tankctl/workflow/development-workflow-commands
tags:
- workflow
- commands
- setup
- development
---

## Development Commands

### Backend Setup
```bash
cd /mnt/samba/tankctl
pip install -r requirements.txt
python src/main.py          # Start backend server
```

### Flutter Development
```bash
cd tankctl_app
flutter pub get             # Install dependencies
flutter run -d chrome       # Run on Chrome
flutter run -d android      # Run on Android device
flutter build apk --debug   # Build APK
flutter clean              # Clean build artifacts
```

### Database Migrations
```sql
-- Migrations in /migrations/ folder
-- Applied via SQLAlchemy or manual SQL
```

### MQTT Testing
```bash
# Use tools/device_simulator.py for testing
python tools/device_simulator.py
```

### Docker Deployment
```bash
docker-compose up           # Start all services
docker-compose down         # Stop services
```

### Key Services
- **Backend:** `http://localhost:8000`
- **Mosquitto (MQTT):** `localhost:1883`
- **Grafana:** Usually on `localhost:3000`
- **Flutter app:** Connects to backend API

### Testing
- Backend tests in `/tests/` folder
- Flutter tests in `tankctl_app/test/`
- Integration tests for end-to-end scenarios

### Firmware Upload
```bash
# Arduino IDE or CLI
tools/upload_firmware.sh    # Upload sketch to device
```

### Debugging
- Use `ws_monitor.py` for WebSocket monitoring
- Check MQTT topics with mosquitto_sub
- Review logs in stdout/Docker containers