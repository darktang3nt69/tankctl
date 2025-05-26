# app/metrics/tank_metrics.py

from prometheus_client import Gauge

# 1 = online, 0 = offline
tank_online_status = Gauge(
    "tank_status",
    "Current online status of each tank (1 = online, 0 = offline)",
    ["tank_name"]
)

# Temperature gauge
tank_temperature = Gauge(
    "tank_temperature_celsius",
    "Current temperature of each tank in Celsius",
    ["tank_name", "location"]
)
