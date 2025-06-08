# TankCtl - Aquarium Tank Management System

A comprehensive API system for managing and monitoring aquarium tanks. This system provides real-time monitoring, automated control, and notifications for multiple aquarium tanks.

## 🌟 Features

### Tank Management
- **Tank Registration**: Register new tank nodes with secure JWT authentication
- **Status Monitoring**: Real-time tracking of:
  - Temperature
  - pH levels
  - Light status
  - Heartbeat monitoring
- **Command System**:
  - Issue commands to tanks (feed, light control)
  - Command acknowledgment tracking
  - Command history and status

### Lighting Control
- **Schedule Management**: Configure and update lighting schedules
- **Manual Overrides**: Temporary manual control of lights
- **Schedule Execution**: Automated schedule management

### Monitoring & Alerts
- **Discord Integration**: Real-time notifications for:
  - Tank online/offline status
  - Command execution
  - Manual overrides
  - System alerts
- **Prometheus Metrics**: Comprehensive monitoring metrics
- **Grafana Dashboards**: Visual monitoring and analytics

### Security
- JWT-based authentication
- Secure API endpoints
- Role-based access control

## 🛠 Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Monitoring**: Prometheus & Grafana
- **Containerization**: Docker
- **Tunneling**: Cloudflare Tunnel

## 🚀 Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Git
- Cloudflare account (for tunneling)

### Environment Variables
Create a `.env` file in the root directory with the following variables:

```env
# Database
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=tankctl

# API Settings
API_SECRET_KEY=your_secret_key
API_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# Redis
REDIS_URL=redis://redis:6379/0

# Cloudflare
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token
```

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/tankctl.git
   cd tankctl
   ```

2. **Create Network**
   ```bash
   docker network create tankctl
   ```

3. **Build and Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Access Services**
   - API Documentation: http://localhost:8000/docs
   - Grafana Dashboard: http://localhost:3000
   - Prometheus: http://localhost:9090
   - Flower (Celery Monitoring): http://localhost:5555

## 📊 API Endpoints

### Tank Management
- `POST /api/v1/register` - Register new tank
- `POST /api/v1/status` - Update tank status
- `GET /api/v1/status/{tank_id}` - Get tank status

### Commands
- `POST /api/v1/commands` - Issue command to tank
- `GET /api/v1/commands/{tank_id}` - Get command history

### Settings
- `GET /api/v1/settings` - Get tank settings
- `PUT /api/v1/settings` - Update tank settings

### Overrides
- `POST /api/v1/overrides` - Create manual override
- `GET /api/v1/overrides/{tank_id}` - Get override history

## 🔧 Development

### Project Structure
```
tankctl/
├── app/
│   ├── api/        # API endpoints
│   ├── core/       # Core functionality
│   ├── models/     # Database models
│   ├── schemas/    # Pydantic schemas
│   ├── services/   # Business logic
│   ├── utils/      # Utility functions
│   └── worker/     # Celery tasks
├── config/         # Configuration files
├── docker/         # Docker configurations
├── tests/          # Test files
└── scripts/        # Utility scripts
```

### Running Tests
```bash
docker-compose run web pytest
```

## 📈 Monitoring

### Grafana Dashboards
- Tank Status Overview
- Command Execution Metrics
- System Health Metrics
- Historical Data Analysis

### Prometheus Metrics
- Tank Status Metrics
- Command Execution Metrics
- System Performance Metrics

### Celery Task Monitoring (Flower)
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task rate limiting and scheduling
- Worker management and control

## 🔐 Security Considerations

1. **API Security**
   - All endpoints are protected with JWT authentication
   - Rate limiting implemented
   - Input validation using Pydantic

2. **Data Security**
   - Database credentials stored in environment variables
   - Secure password hashing
   - Regular security audits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

[Add your license information here]

## 🆘 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Tank Node Capabilities

### Hardware Features
- **Temperature Monitoring**
  - DS18B20 digital temperature sensor
  - 12-bit resolution (±0.0625°C)
  - Automatic error detection and recovery
  - Temperature caching for reduced sensor load
  - Configurable reading intervals

- **Light Control**
  - Relay-based control (active-low logic)
  - Configurable ON/OFF schedules
  - State persistence across reboots
  - Safe default state (OFF)

- **Automatic Feeder**
  - SG90 servo motor control
  - Bidirectional feeding (forward/reverse)
  - Configurable feeding duration
  - Adjustable PWM settings
  - Safe stop position

### Software Features
- **Network Management**
  - Automatic WiFi connection
  - Connection retry with backoff
  - Automatic reconnection
  - Connection state persistence

- **API Integration**
  - RESTful API communication
  - Automatic token refresh
  - Command polling
  - Status updates
  - Command acknowledgment

- **Self-Healing**
  - Watchdog timer
  - Memory monitoring
  - Automatic reboot on low memory
  - Error recovery
  - State persistence

- **Resource Optimization**
  - Minimal memory usage
  - Efficient CPU utilization
  - Optimized network operations
  - Temperature sensor caching
  - Reduced file I/O

## Configuration Options

This section details all environment variables and configuration options used by the TankCtl application. These variables are primarily loaded from a `.env` file in the project root or directly from the environment.

### Database Settings
- `POSTGRES_SERVER`: **(Required)** The hostname or IP address of the PostgreSQL/TimescaleDB server.
- `POSTGRES_PORT`: **(Required)** The port number for the PostgreSQL/TimescaleDB server (default: `5432`).
- `POSTGRES_USER`: **(Required)** The username for connecting to the PostgreSQL/TimescaleDB database.
- `POSTGRES_PASSWORD`: **(Required)** The password for connecting to the PostgreSQL/TimescaleDB database.
- `POSTGRES_DB`: **(Required)** The name of the database to connect to.

### SQLAlchemy Connection Pool Settings
- `SQLALCHEMY_POOL_SIZE`: The number of connections to keep in the SQLAlchemy connection pool (default: `10`).
- `SQLALCHEMY_MAX_OVERFLOW`: The maximum overflow size of the SQLAlchemy connection pool (default: `20`).
- `SQLALCHEMY_POOL_RECYCLE`: The number of seconds after which a connection is automatically recycled (default: `1800` seconds / `30` minutes).
- `SQLALCHEMY_POOL_TIMEOUT`: The number of seconds to wait for a connection to become available (default: `30` seconds).

### JWT (JSON Web Token) Settings
- `JWT_SECRET_KEY`: **(Required)** A strong, secret key used for signing JWT tokens.
- `JWT_ALGORITHM`: **(Required)** The algorithm used for JWT signing (e.g., `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: The expiration time for JWT access tokens in minutes (default: `30`).

### Tank Settings
- `TANK_PRESHARED_KEY`: **(Required)** A pre-shared key used for new tank registrations to ensure authorized devices.

### Celery Settings (Background Tasks)
- `CELERY_BROKER_URL`: **(Required)** The URL for the Celery message broker (e.g., `redis://redis:6379/0`).
- `CELERY_BACKEND_URL`: **(Required)** The URL for storing Celery task results (e.g., `redis://redis:6379/0`).
- `celery_result_backend`: **(Required)** Alias for `CELERY_BACKEND_URL` (ensure consistency).

### Heartbeat Monitor Settings
- `HEARTBEAT_CHECK_INTERVAL_MINUTES`: Frequency (in minutes) at which the system checks tank heartbeats (default: `1`).
- `TANK_OFFLINE_THRESHOLD_MINUTES`: The duration (in minutes) after which a tank is considered offline if no heartbeat is received (default: `2`).

### Discord Integration
- `DISCORD_WEBHOOK_URL`: **(Required)** The webhook URL for sending notifications to Discord.

### Admin API Key
- `ADMIN_API_KEY`: **(Required)** A secret key used to authenticate administrative API requests.

### Application Timezone
- `APP_TIMEZONE`: The timezone used by the application for all time-related operations (default: `Asia/Kolkata`). This is set via environment variable directly, not through `app/core/config.py` and is leveraged in `app/utils/timezone.py`.

## API Endpoints

### Registration
- **Endpoint**: `/api/v1/tank/register`
- **Method**: POST
- **Purpose**: Register tank with server
- **Payload**:
  ```json
  {
    "auth_key": "your_auth_key",
    "tank_name": "tank_name",
    "location": "location",
    "firmware_version": "1.0.0",
    "light_on": "10:00",
    "light_off": "16:00"
  }
  ```

### Status Updates
- **Endpoint**: `/api/v1/tank/status`
- **Method**: POST
- **Purpose**: Send tank status
- **Payload**:
  ```json
  {
    "temperature": 25.5,
    "ph": 7.2,
    "light_state": 1,
    "firmware_version": "1.0.0"
  }
  ```

### Command Polling
- **Endpoint**: `/api/v1/tank/command`
- **Method**: GET
- **Purpose**: Check for pending commands
- **Response**:
  ```json
  {
    "command_id": "cmd_123",
    "command_payload": "LIGHT_ON",
    "params": {}
  }
  ```

### Command Acknowledgment
- **Endpoint**: `/api/v1/tank/command/ack`
- **Method**: POST
- **Purpose**: Acknowledge command execution
- **Payload**:
  ```json
  {
    "command_id": "cmd_123",
    "success": true
  }
  ```

## Available Commands

### Light Control
- `LIGHT_ON`: Turn light ON
- `LIGHT_OFF`: Turn light OFF

### Feeder Control
- `FEED_NOW`: Activate feeder
  - Parameters:
    - `duration`: Feeding duration in seconds (default: 2)
    - `direction`: 'forward' or 'reverse' (default: 'forward')
    - `duty`: Custom duty cycle (optional)

## Error Handling

### Temperature Sensor
- Automatic retry on read failure
- Temperature caching to reduce sensor load
- Error state tracking
- Graceful degradation

### Network
- Automatic reconnection
- Connection state persistence
- Retry with backoff
- Token refresh on expiration

### Memory Management
- Regular garbage collection
- Memory monitoring
- Automatic reboot on low memory
- State persistence across reboots

## File System

### Configuration Files
- `config.json`: Stores tank_id and token
- `state.json`: Stores current state (light, etc.)

### State Management
- Automatic state persistence
- Safe state recovery
- Default state handling
- Error state recovery

## Performance Considerations

### Memory Usage
- Minimal object creation
- Efficient string handling
- Optimized data structures
- Regular garbage collection

### CPU Load
- Efficient timing calculations
- Optimized sensor readings
- Reduced network operations
- Minimal file I/O

### Network Usage
- Efficient polling intervals
- Optimized payload sizes
- Connection state caching
- Minimal retry attempts

## Security Features

### API Security
- Token-based authentication
- Automatic token refresh
- Secure communication
- Command validation

### Hardware Security
- Safe default states
- Error state recovery
- Watchdog protection
- State persistence

## Development Notes

### Adding New Features
1. Add hardware initialization in `HardwareManager`
2. Implement feature logic in appropriate manager
3. Add command handling in `TankController`
4. Update API endpoints if needed
5. Add configuration options
6. Update documentation

### Testing
1. Test hardware initialization
2. Verify feature functionality
3. Check error handling
4. Validate state persistence
5. Test API integration
6. Verify performance impact

### Debugging
1. Check hardware connections
2. Verify configuration
3. Monitor memory usage
4. Check network connectivity
5. Validate API responses
6. Review error logs
