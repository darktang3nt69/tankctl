# TankCtl Tank API

An API to manage and monitor aquarium tanks. This project allows registration of tank nodes, receiving status updates (heartbeats, temperature, pH, light), issuing commands (feed, light on/off), managing lighting schedules and manual overrides, and sending notifications via Discord.

## Key Features

- **Tank Registration:** Register new tank nodes and receive a JWT token for authentication.
- **Status Updates:** Tanks send heartbeat and status updates (temperature, pH, light).
- **Command Issuance:** Admins can issue commands to specific tanks.
- **Command Acknowledgment:** Tanks acknowledge command execution success or failure.
- **Lighting Schedule Management:** Configure and update tank lighting schedules.
- **Manual Overrides:** Manually turn lights on/off, overriding the schedule temporarily.
- **Discord Notifications:** Send notifications for various events (tank online/offline, commands, overrides) to Discord via a webhook.
- **Prometheus Metrics:** Exposes metrics for monitoring tank status.

## Technology Stack

- **FastAPI:** Web framework for building the API.
- **SQLAlchemy:** ORM for database interactions (PostgreSQL).
- **Celery:** Task queue for background jobs (e.g., heartbeat monitoring, schedule execution, retries).
- **Pydantic:** Data validation and settings management.
- **python-jose:** JWT handling.
- **python-dotenv:** Loading environment variables.
- **requests:** Making HTTP requests (for Discord webhooks).
- **prometheus_fastapi_instrumentator, prometheus_client:** Prometheus metrics.

## Project Structure

- `app/api/v1/`: API routers for different functionalities (registration, status, commands, admin commands, settings).
- `app/core/`: Core components like database connection, configuration settings, audit logging, and Celery configuration.
- `app/metrics/`: Prometheus metrics related code.
- `app/models/`: SQLAlchemy models for database tables (tanks, status logs, event logs, commands, settings, etc.).
- `app/schemas/`: Pydantic schemas for request and response data validation.
- `app/services/`: Business logic and service functions for handling API requests and interacting with the database.
- `app/utils/`: Utility functions (Discord notifications, JWT handling, logging, timezone).
- `app/worker/`: Celery worker tasks (command dispatcher, heartbeat monitor, schedule executor, etc.).

## Setup and Installation

To set up and run the TankCtl Tank API, follow these steps:

1.  **Clone the Repository:**



## API Documentation

The API is built with FastAPI, which automatically generates interactive API documentation (Swagger UI) at the `/docs` endpoint when the application is running.

## Contributing

*(Information on how to contribute to this project is not available in the provided code analysis.)*

## License

*(License information for this project is not available in the provided code analysis.)*
