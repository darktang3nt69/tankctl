from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.core import CollectorRegistry
from prometheus_client.exposition import generate_latest

# Create a registry
registry = CollectorRegistry()

# Define metrics
tank_temperature = Gauge(
    'tank_temperature_celsius',
    'Current temperature of the tank in Celsius',
    ['tank_id'],
    registry=registry
)

tank_ph_level = Gauge(
    'tank_ph_level',
    'Current pH level of the tank',
    ['tank_id'],
    registry=registry
)

tank_water_level = Gauge(
    'tank_water_level_percent',
    'Current water level of the tank in percentage',
    ['tank_id'],
    registry=registry
)

command_execution_time = Histogram(
    'tank_command_execution_time_seconds',
    'Time taken to execute commands',
    ['tank_id', 'command'],
    registry=registry
)

command_counter = Counter(
    'tank_commands_total',
    'Total number of commands executed',
    ['tank_id', 'command', 'status'],
    registry=registry
)

node_health = Gauge(
    'tank_node_health',
    'Health status of the tank node (1 = healthy, 0 = unhealthy)',
    ['tank_id'],
    registry=registry
)

command_queue_size = Gauge(
    'tank_command_queue_size',
    'Number of commands in the queue',
    ['tank_id'],
    registry=registry
)

# System resource metrics
cpu_usage = Gauge(
    'process_cpu_seconds_total',
    'Total CPU time used by the process',
    ['instance'],
    registry=registry
)

memory_usage = Gauge(
    'process_resident_memory_bytes',
    'Resident memory size in bytes',
    ['instance'],
    registry=registry
)

def get_metrics():
    """Return the latest metrics in Prometheus format."""
    return generate_latest(registry) 