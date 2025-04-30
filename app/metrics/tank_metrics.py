# app/metrics/tank_metrics.py

from prometheus_client import Gauge

# 1 = online, 0 = offline
tank_online_status = Gauge(
    "tank_online_status",
    "Current online status of each tank (1 = online, 0 = offline)",
    ["tank_id", "tank_name"]
)
