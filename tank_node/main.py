# main.py — ESP32 MicroPython firmware for aquarium tank control
# Optimized for minimal memory usage and CPU load
# Features:
# - Temperature monitoring with DS18B20 sensor
# - Light control with relay
# - Automatic feeder control with servo
# - WiFi connectivity with automatic reconnection
# - Remote control via REST API
# - Self-healing with watchdog timer

import os
import network
import urequests
import ujson
import time
import gc
import machine
from machine import WDT, Pin, PWM, reset_cause
from onewire import OneWire
from ds18x20 import DS18X20

# ───── CONFIGURATION ─────
# Network settings - Update these with your WiFi credentials
SSID              = 'xxxx.4G'  # WiFi SSID
PASSWORD          = 'xxxx'     # WiFi password
BASE_URL          = 'https://xxxx.xxxxx.xxxx'  # API base URL

# API endpoints - Using constants to avoid string concatenation and reduce memory usage
REGISTER_API      = '/api/v1/tank/register'    # Tank registration endpoint
STATUS_API        = '/api/v1/tank/status'      # Status update endpoint
COMMAND_API       = '/api/v1/tank/command'     # Command polling endpoint
ACK_API           = '/api/v1/tank/command/ack' # Command acknowledgment endpoint

# Tank identification - Update these with your tank details
AUTH_KEY          = 'xxxxx'    # Authentication key for API
TANK_NAME         = 'xxxx'     # Name of your tank
LOCATION          = 'xxxx'     # Location of your tank

# File paths - Using constants to avoid string operations
CONFIG_FILE       = 'config.json'  # Stores tank_id and token
STATE_FILE        = 'state.json'   # Stores current state (light, etc.)

# Timing parameters (in seconds/ms) - Adjust based on your needs
WIFI_RETRIES      = 5          # Number of WiFi connection attempts before reboot
WIFI_TIMEOUT      = 10         # WiFi connection timeout in seconds
WDT_TIMEOUT_MS    = 10000      # Watchdog timeout in milliseconds
STATUS_INTERVAL   = 60         # Status update interval in seconds
COMMAND_POLL_MS   = 5000       # Command polling interval in milliseconds
MIN_HEAP_BYTES    = 50000      # Minimum heap before reboot
TEMP_CACHE_MS     = 5000       # Temperature cache duration in milliseconds

# GPIO pins - Hardware connections
RELAY_PIN         = 15         # D15: light relay (active-low)
SERVO_PIN         = 4          # D4: continuous SG90 servo
DS18B20_PIN       = 22         # D22: DS18B20 temperature sensor

# Hardware control constants
RELAY_ON          = 0          # Relay ON state (active-low)
RELAY_OFF         = 1          # Relay OFF state
SERV_FREQ         = 50         # Servo PWM frequency in Hz
STOP_DUTY         = 77         # Servo stop position (duty cycle)
FORWARD_DUTY      = 100        # Servo forward position (duty cycle)
REVERSE_DUTY      = 50         # Servo reverse position (duty cycle)

# Tank settings - Update these with your preferences
LIGHT_ON_TIMING   = "10:00"    # Light ON time (24-hour format)
LIGHT_OFF_TIMING  = "16:00"    # Light OFF time (24-hour format)
FIRMWARE          = "1.0.0"    # Firmware version

# ───── ERROR HANDLING ─────
def log_error(error_msg):
    try:
        with open('error.log', 'a') as f:
            timestamp = time.time()
            f.write(f"{timestamp}: {error_msg}\n")
    except:
        pass

class TankError(Exception):
    pass

# ───── HARDWARE MANAGEMENT ─────
class HardwareManager:
    """Manages all hardware components (relay, servo, temperature sensor)"""
    
    def __init__(self):
        """Initialize hardware components with minimal memory usage"""
        # Initialize relay in safe state (OFF)
        self.light_relay = Pin(RELAY_PIN, Pin.OUT, value=RELAY_OFF)
        
        # Initialize servo in stopped position
        self.servo = PWM(Pin(SERVO_PIN), freq=SERV_FREQ)
        self.servo.duty(STOP_DUTY)
        
        # Initialize temperature sensor
        self.ds_pin = Pin(DS18B20_PIN)
        self.ds_sensor = DS18X20(OneWire(self.ds_pin))
        self.roms = self.ds_sensor.scan()
        
        # Temperature reading optimization
        self._last_temp = None          # Last valid temperature reading
        self._last_temp_time = 0        # Timestamp of last reading
        self._temp_retries = 0          # Number of failed attempts

    def get_temperature(self):
        """Get temperature with caching and retry logic
        
        Returns:
            float: Temperature in Celsius, or None if reading failed
        """
        current_time = time.ticks_ms()
        
        # Return cached temperature if valid (within cache duration)
        if (self._last_temp is not None and 
            time.ticks_diff(current_time, self._last_temp_time) < TEMP_CACHE_MS):
            return self._last_temp

        try:
            # Start temperature conversion
            self.ds_sensor.convert_temp()
            time.sleep_ms(750)  # Wait for conversion (12-bit resolution)
            
            # Read temperature
            temp = self.ds_sensor.read_temp(self.roms[0])
            
            if temp is not None:
                # Update cache with new reading
                self._last_temp = temp
                self._last_temp_time = current_time
                self._temp_retries = 0
                return temp
                
            self._temp_retries += 1
            return None
            
        except:
            self._temp_retries += 1
            return None

    def set_light(self, state):
        """Set light state with minimal operations
        
        Args:
            state (bool): True for ON, False for OFF
        """
        self.light_relay.value(RELAY_ON if state else RELAY_OFF)

    def feed(self, params):
        """Control feeder with minimal memory usage
        
        Args:
            params (dict): Feeding parameters
                - duration: Feeding duration in seconds
                - direction: 'forward' or 'reverse'
        """
        # Extract parameters with defaults
        dur = params.get('duration', 2)
        dir = params.get('direction', 'forward').lower()
        duty = FORWARD_DUTY if dir == 'forward' else REVERSE_DUTY
        
        # Execute feed operation
        self.servo.duty(duty)
        time.sleep(dur)
        self.servo.duty(STOP_DUTY)

# ───── STATE MANAGEMENT ─────
class StateManager:
    """Manages tank state and persistence"""
    
    def __init__(self):
        """Initialize state with minimal memory usage"""
        self.state = self._load_state()
        self.hardware = HardwareManager()
        self.hardware.set_light(self.state.get('light_state', 0))

    def _load_state(self):
        """Load state with minimal error handling
        
        Returns:
            dict: Current tank state
        """
        try:
            with open(STATE_FILE) as f:
                return ujson.load(f)
        except:
            return {'light_state': 0}

    def _save_state(self):
        """Save state with minimal operations"""
        try:
            with open(STATE_FILE, 'w') as f:
                ujson.dump(self.state, f)
        except:
            pass

    def update_light_state(self, state):
        """Update light state with minimal operations
        
        Args:
            state (bool): True for ON, False for OFF
        """
        self.state['light_state'] = 1 if state else 0
        self.hardware.set_light(self.state['light_state'])
        self._save_state()

# ───── NETWORK MANAGEMENT ─────
class NetworkManager:
    """Manages WiFi connectivity with automatic reconnection"""
    
    def __init__(self):
        """Initialize network with minimal memory usage"""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.connected = False
        self.last_attempt = 0

    def connect(self):
        """Connect to WiFi with minimal operations
        
        Returns:
            bool: True if connected, False otherwise
        """
        current_time = time.ticks_ms()
        
        # Skip if recently attempted (prevent rapid reconnection attempts)
        if (self.connected or 
            time.ticks_diff(current_time, self.last_attempt) < 5000):
            return self.connected

        self.last_attempt = current_time
        
        try:
            if not self.wlan.isconnected():
                self.wlan.connect(SSID, PASSWORD)
                start = time.ticks_ms()
                
                # Wait for connection with timeout
                while not self.wlan.isconnected():
                    if time.ticks_diff(time.ticks_ms(), start) > WIFI_TIMEOUT * 1000:
                        break
                    time.sleep(0.1)
                
                self.connected = self.wlan.isconnected()
                
        except:
            self.connected = False
            
        return self.connected

# ───── API COMMUNICATION ─────
class APIManager:
    """Manages API communication with automatic token refresh"""
    
    def __init__(self):
        """Initialize API manager with minimal memory usage"""
        self.token = None
        self._load_config()

    def _load_config(self):
        """Load config with minimal operations"""
        try:
            with open(CONFIG_FILE) as f:
                self.token = ujson.load(f)['token']
        except:
            self.token = None

    def _save_config(self, token):
        """Save config with minimal operations
        
        Args:
            token (str): API access token
        """
        try:
            with open(CONFIG_FILE, 'w') as f:
                ujson.dump({'token': token}, f)
            self.token = token
        except:
            pass

    def register(self):
        """Register tank with minimal memory usage
        
        Returns:
            bool: True if registration successful
        """
        try:
            # Prepare registration data
            data = {
                'auth_key': AUTH_KEY,
                'tank_name': TANK_NAME,
                'location': LOCATION,
                'firmware_version': FIRMWARE,
                'light_on': LIGHT_ON_TIMING,
                'light_off': LIGHT_OFF_TIMING
            }
            
            # Send registration request
            resp = urequests.post(
                BASE_URL + REGISTER_API,
                headers={'Content-Type': 'application/json'},
                data=ujson.dumps(data)
            )
            
            if resp.status_code == 201:
                self._save_config(resp.json()['access_token'])
                resp.close()
                return True
                
            resp.close()
            return False
            
        except:
            return False

    def send_status(self, payload):
        """Send status with minimal operations
        
        Args:
            payload (dict): Status data to send
            
        Returns:
            bool: True if status sent successfully
        """
        try:
            resp = urequests.post(
                BASE_URL + STATUS_API,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                },
                data=ujson.dumps(payload)
            )
            
            status = resp.status_code
            resp.close()
            
            if status == 401:
                if self.register():
                    return self.send_status(payload)
                return False
                
            return status == 200
            
        except:
            return False

    def poll_command(self):
        """Poll for commands with minimal operations
        
        Returns:
            dict: Command data if available, empty dict otherwise
        """
        try:
            resp = urequests.get(
                BASE_URL + COMMAND_API,
                headers={'Authorization': f'Bearer {self.token}'}
            )
            
            if resp.status_code == 401:
                resp.close()
                if self.register():
                    return self.poll_command()
                return {}
                
            if resp.status_code != 200:
                resp.close()
                return {}
                
            data = resp.json()
            resp.close()
            return data
            
        except:
            return {}

    def send_ack(self, command_id, success):
        """Send command acknowledgment with minimal operations
        
        Args:
            command_id (str): ID of the command to acknowledge
            success (bool): Whether command was successful
            
        Returns:
            bool: True if acknowledgment sent successfully
        """
        try:
            resp = urequests.post(
                BASE_URL + ACK_API,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                },
                data=ujson.dumps({
                    'command_id': command_id,
                    'success': success
                })
            )
            
            status = resp.status_code
            resp.close()
            
            if status == 401:
                if self.register():
                    return self.send_ack(command_id, success)
                return False
                
            return status == 200
            
        except:
            return False

# ───── MAIN APPLICATION ─────
class TankController:
    """Main application controller"""
    
    def __init__(self):
        """Initialize controller with minimal memory usage"""
        # Initialize watchdog for self-healing
        self.wdt = WDT(timeout=WDT_TIMEOUT_MS)
        
        # Initialize managers
        self.state_manager = StateManager()
        self.network_manager = NetworkManager()
        self.api_manager = APIManager()
        
        # Initialize timing
        self.last_status_time = 0
        self.last_command_poll = 0
        
        # Initialize command map
        self.command_map = {
            'LIGHT_ON': lambda p: self.state_manager.update_light_state(True),
            'LIGHT_OFF': lambda p: self.state_manager.update_light_state(False),
            'FEED_NOW': lambda p: self.state_manager.hardware.feed(p)
        }

    def feed_watchdog(self):
        """Feed watchdog and check memory"""
        self.wdt.feed()
        gc.collect()
        if gc.mem_free() < MIN_HEAP_BYTES:
            machine.reset()

    def handle_command(self, command):
        """Handle command with minimal operations
        
        Args:
            command (dict): Command data from API
        """
        try:
            command_id = command.get('command_id')
            command_payload = command.get('command_payload', '').upper()
            params = command.get('params', {})
            
            if command_payload in self.command_map:
                self.command_map[command_payload](params)
                self.api_manager.send_ack(command_id, True)
            else:
                self.api_manager.send_ack(command_id, False)
                
        except:
            self.api_manager.send_ack(command.get('command_id'), False)

    def send_status_update(self):
        """Send status update with minimal operations"""
        try:
            temp = self.state_manager.hardware.get_temperature()
            payload = {
                'temperature': temp,
                'ph': 7.2,
                'light_state': self.state_manager.state['light_state'],
                'firmware_version': FIRMWARE
            }
            
            self.api_manager.send_status(payload)
                
        except:
            pass

    def run(self):
        """Main loop with minimal operations"""
        while True:
            try:
                # Feed watchdog
                self.feed_watchdog()
                current_time = time.ticks_ms()
                
                # Handle network
                if not self.network_manager.connect():
                    time.sleep(1)
                    continue
                
                # Send status
                if time.ticks_diff(current_time, self.last_status_time) >= STATUS_INTERVAL * 1000:
                    self.send_status_update()
                    self.last_status_time = current_time
                
                # Poll commands
                if time.ticks_diff(current_time, self.last_command_poll) >= COMMAND_POLL_MS:
                    command = self.api_manager.poll_command()
                    if command:
                        self.handle_command(command)
                    self.last_command_poll = current_time
                
                time.sleep(0.1)
                
            except:
                time.sleep(1)

if __name__ == '__main__':
    controller = TankController()
    controller.run()
