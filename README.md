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
