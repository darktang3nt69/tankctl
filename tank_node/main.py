# main.py — ESP32 MicroPython firmware with inverted relay logic

import os
import network
import urequests
import ujson
import time
import gc
import machine
from machine import WDT, Pin, PWM
from onewire import OneWire
from ds18x20 import DS18X20

# ───── CONFIGURATION ─────
SSID              = 'xxx.4G'
PASSWORD          = 'xxxx'
BASE_URL          = 'https://xxx.xxxx.xxxx'

# API endpoints
REGISTER_API      = '/api/v1/tank/register'
STATUS_API        = '/api/v1/tank/status'
COMMAND_API       = '/api/v1/tank/command'
ACK_API           = '/api/v1/tank/command/ack'

# Auth credentials
AUTH_KEY          = 'xxx'
TANK_NAME         = 'xxx'
LOCATION          = 'xxxx'

# Files for persistence
STATE_FILE        = 'state.json'   # Stores current state (light, etc.)
STATUS_QUEUE_FILE = 'status_queue.json'
ACK_QUEUE_FILE    = 'ack_queue.json'

# Timing parameters
WIFI_RETRIES      = 5
WIFI_TIMEOUT      = 10
WDT_TIMEOUT_MS    = 10000
STATUS_INTERVAL   = 60
COMMAND_POLL_MS   = 5000
FLUSH_INTERVAL_MS = 30000
MIN_HEAP_BYTES    = 50000
TOKEN_REFRESH_MS  = 1500000  # Refresh token every 25 minutes (more conservative than server's 30 min expiry)

# GPIO pins
RELAY_PIN         = 15      # D15: light relay (active-low)
SERVO_PIN         = 4       # D4: continuous SG90 servo
DS18B20_PIN       = 22      # D22: DS18B20 temperature sensor

# Relay logic inversion
RELAY_ON          = 0       # drive low to turn relay/light ON
RELAY_OFF         = 1       # drive high to turn relay/light OFF

# Servo PWM settings
SERV_FREQ         = 50
STOP_DUTY         = 77
FORWARD_DUTY      = 100
REVERSE_DUTY      = 50

# Default Tank Lighting schedule
LIGHT_ON_TIMING   = "10:00"
LIGHT_OFF_TIMING  = "18:00"

# Firmware Version
FIRMWARE          = "1.0.0"

# ───── HARDWARE SETUP ─────
# new: force the relay off state (active‑low) immediately
light_relay = Pin(RELAY_PIN, Pin.OUT, value=RELAY_OFF)
# initialize servo
servo = PWM(Pin(SERVO_PIN), freq=SERV_FREQ)
# initialize DS18B20
ds_pin = Pin(DS18B20_PIN)
ds_sensor = DS18X20(OneWire(ds_pin))
roms = ds_sensor.scan()
if not roms:
    print("⚠️ No DS18B20 sensor found!")
else:
    print("✔ DS18B20 sensor found:", roms[0])
    ds_sensor.convert_temp()  # Initial conversion

# ───── WATCHDOG & SELF‑HEALING ─────
wdt = WDT(timeout=WDT_TIMEOUT_MS)
def feed():
    wdt.feed()
    gc.collect()
    if gc.mem_free() < MIN_HEAP_BYTES:
        print("⚠️ Low memory—rebooting")
        time.sleep(1)
        machine.reset()

# ───── FILESYSTEM UTILITIES ─────
def safe_remove(fname):
    """Safely remove a file with error handling."""
    try:
        os.remove(fname)
        return True
    except:
        return False

def safe_rename(src, dst):
    """Safely rename a file with error handling."""
    try:
        os.rename(src, dst)
        return True
    except:
        return False

def load_json(fname, default=None):
    """Load JSON with simple fallback to default."""
    try:
        with open(fname) as f:
            return ujson.load(f)
    except:
        return default

def save_json(fname, data):
    """Save JSON with atomic write and proper cleanup."""
    temp = fname + '.tmp'
    backup = fname + '.bak'
    
    # First, try to create backup of existing file
    try:
        if fname in os.listdir():
            safe_rename(fname, backup)
    except:
        pass
    
    # Write to temp file
    try:
        with open(temp, 'w') as f:
            ujson.dump(data, f)
            f.flush()
            os.sync()
        
        # Atomic rename
        if safe_rename(temp, fname):
            # Clean up backup if everything succeeded
            safe_remove(backup)
            return True
    except:
        # If anything fails, try to restore from backup
        try:
            if backup in os.listdir():
                safe_rename(backup, fname)
        except:
            pass
    
    # Clean up temp file if it exists
    safe_remove(temp)
    return False

def cleanup_files():
    """Clean up temporary and backup files."""
    files_to_clean = [
        '*.tmp',
        '*.bak',
        '*.old',
        '*.new'
    ]
    
    for pattern in files_to_clean:
        try:
            for f in os.listdir():
                if f.endswith(pattern[1:]):  # Remove the * from pattern
                    safe_remove(f)
        except:
            pass

# ───── OFFLINE QUEUES ─────
def enqueue_status(payload):
    """Add status to queue with proper file handling."""
    try:
        q = load_json(STATUS_QUEUE_FILE, [])
        q.append(payload)
        return save_json(STATUS_QUEUE_FILE, q)
    except:
        return False

def flush_status_queue(token):
    """Flush status queue with proper error handling."""
    try:
        q = load_json(STATUS_QUEUE_FILE, [])
        if not q:
            return True
            
        rem = []
        for item in q:
            try:
                resp = urequests.post(
                    BASE_URL+STATUS_API,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer '+token
                    },
                    data=ujson.dumps(item)
                )
                if resp.status_code == 200:
                    resp.close()
                    feed()
                    continue
                resp.close()
            except:
                pass
            rem.append(item)
        
        return save_json(STATUS_QUEUE_FILE, rem)
    except:
        return False

def enqueue_ack(cid, success):
    """Add acknowledgment to queue with proper file handling."""
    try:
        q = load_json(ACK_QUEUE_FILE, [])
        q.append({'command_id': cid, 'success': success})
        return save_json(ACK_QUEUE_FILE, q)
    except:
        return False

def flush_ack_queue(token):
    """Flush acknowledgment queue with proper error handling."""
    try:
        q = load_json(ACK_QUEUE_FILE, [])
        if not q:
            return True
            
        rem = []
        for item in q:
            try:
                resp = urequests.post(
                    BASE_URL+ACK_API,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer '+token
                    },
                    data=ujson.dumps(item)
                )
                if resp.status_code == 200:
                    resp.close()
                    feed()
                    continue
                resp.close()
            except:
                pass
            rem.append(item)
        
        return save_json(ACK_QUEUE_FILE, rem)
    except:
        return False

# ───── STATE PERSISTENCE ─────
def load_state():
    try:
        with open(STATE_FILE) as f:
            return ujson.load(f)
    except:
        return {'light_state': 0}

def save_state(state):
    try:
        feed()
        save_json(STATE_FILE, state)
        feed()
    except Exception as e:
        print("❌ save_state error:", e)

# Restore light relay on boot (logical state inverted)
state = load_state()
logical = state.get('light_state', 0)
light_relay.value(RELAY_ON if logical else RELAY_OFF)
print("Restored light_state (logical):", logical)

# ───── SENSOR FUNCTIONS ─────
def get_temperature():
    try:
        ds_sensor.convert_temp()
        time.sleep_ms(750)  # Wait for conversion (12-bit resolution)
        temp = ds_sensor.read_temp(roms[0])
        if temp is not None:
            print(f"📊 Temperature: {temp}°C")
            return temp
        print("⚠️ Temperature read returned None")
        return 0.0
    except Exception as e:  
        print("❌ Temperature reading error:", e)
        return 0.0

def get_ph(): return 7.2

# ───── WIFI & REGISTRATION ─────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Check if already connected
    if wlan.isconnected():
        print("✔ Already connected to Wi-Fi")
        return
    
    for i in range(1, WIFI_RETRIES+1):
        print(f"Wi‑Fi attempt {i}/{WIFI_RETRIES}")
        try:
            wlan.connect(SSID, PASSWORD)
            start = time.time()
            while not wlan.isconnected() and time.time()-start < WIFI_TIMEOUT:
                feed()
                time.sleep(0.2)
            
            if wlan.isconnected():
                print("✔ Wi‑Fi IP:", wlan.ifconfig()[0])
                return
        except Exception as e:
            print(f"⚠️ Wi‑Fi error: {e}")
        
        print("⚠️ Wi‑Fi failed")
        time.sleep(2)  # Wait before retry
    
    print("❌ Rebooting after Wi-Fi failure")
    time.sleep(2)
    machine.reset()

def register_tank():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            body = {
                'auth_key': AUTH_KEY,
                'tank_name': TANK_NAME,
                'location': LOCATION,
                'firmware_version': FIRMWARE,
                'light_on': LIGHT_ON_TIMING,
                'light_off': LIGHT_OFF_TIMING
            }
            
            resp = urequests.post(
                BASE_URL+REGISTER_API,
                headers={'Content-Type': 'application/json'},
                data=ujson.dumps(body)
            )
            
            if resp.status_code == 201:
                d = resp.json()
                resp.close()
                tid, tkn = d['tank_id'], d['access_token']
                print("✔ Registration successful")
                return tid, tkn
            else:
                print(f"❌ Registration failed: {resp.status_code}")
                resp.close()
        except Exception as e:
            print(f"❌ Registration error: {e}")
        
        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying registration... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    print("❌ Max registration retries reached")
    time.sleep(2)
    machine.reset()

def load_config():
    """Always return None to force fresh registration on boot."""
    return None, None

# ───── TOKEN REFRESH ─────
def request_with_refresh(fn, *args):
    global token
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            code, res = fn(token, *args)
            if code == 401:
                print("⚠️ Token expired—attempting re-registration")
                try:
                    _, new_token = register_tank()
                    if new_token:
                        token = new_token
                        code, res = fn(token, *args)
                        if code == 200:
                            print("✔ Token refresh successful")
                            return code, res
                        else:
                            print(f"❌ Request failed after token refresh: {code}")
                    else:
                        print("❌ Registration failed")
                except Exception as e:
                    print(f"❌ Registration error: {e}")
            elif code == 200:
                return code, res
            else:
                print(f"❌ Request failed with code: {code}")
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying... ({retry_count}/{max_retries})")
            time.sleep(2)  # Wait before retry
    
    print("❌ Max retries reached, rebooting...")
    time.sleep(2)
    machine.reset()

# ───── HTTP HELPERS ─────
def _post_status(tkn, payload):
    try:
        r=urequests.post(BASE_URL+STATUS_API, headers={'Content-Type':'application/json','Authorization':'Bearer '+tkn}, data=ujson.dumps(payload))
        st=r.status_code; r.close(); feed(); return st, None
    except: return None, None

def _post_ack(tkn, cid, success):
    try:
        r=urequests.post(BASE_URL+ACK_API, headers={'Content-Type':'application/json','Authorization':'Bearer '+tkn}, data=ujson.dumps({'command_id':cid,'success':success}))
        st=r.status_code; r.close(); feed(); return st, None
    except: return None, None

def _get_command(tkn):
    try:
        r=urequests.get(BASE_URL+COMMAND_API, headers={'Authorization':'Bearer '+tkn})
        st=r.status_code; d=r.json() if st==200 else {}; r.close(); feed(); return st, d
    except: return None, {}

# ───── HIGH‑LEVEL WRAPPERS ─────
def send_status():
    temp = get_temperature()
    payload = {
        'temperature': temp,
        'ph': get_ph(),
        'light_state': state['light_state'],   # logical state
        'firmware_version': FIRMWARE
    }
    print("📤 Sending status:", payload)
    code,_=request_with_refresh(_post_status,payload)
    print("📥 Status→", code)
    if code==200: flush_status_queue(token)
    else: enqueue_status(payload)

def ack_command(cid, success):
    code,_=request_with_refresh(_post_ack,cid,success)
    if code==200: flush_ack_queue(token)
    else: enqueue_ack(cid, success)

def poll_command():
    c,d = request_with_refresh(_get_command)
    return d if c==200 else {}

# ───── COMMAND HANDLERS ─────
def handle_light(on):
    # invert logic: 1=on->low, 0=off->high
    state['light_state'] = 1 if on else 0
    light_relay.value(RELAY_ON if state['light_state'] else RELAY_OFF)
    save_state(state)

def handle_feed(params):
    dur = params.get('duration', 2)
    dir = params.get('direction','forward').lower()
    duty = params.get('duty', FORWARD_DUTY if dir=='forward' else REVERSE_DUTY)
    print(f"▶ Feed: dir={dir}, dur={dur}s")
    servo.duty(duty); time.sleep(dur); servo.duty(STOP_DUTY)
    print("✔ Feed done")

COMMAND_MAP = {
    'LIGHT_ON':  lambda p: handle_light(True),
    'LIGHT_OFF': lambda p: handle_light(False),
    'FEED_NOW':  handle_feed,
}

def main():
    global tank_id, token, state
    connect_wifi()
    tank_id, token = register_tank()  # Always register on boot
    print("▶ Running, tank_id:", tank_id)

    last_s = time.time()-STATUS_INTERVAL
    last_p = time.ticks_ms()-COMMAND_POLL_MS
    last_f = time.ticks_ms()-FLUSH_INTERVAL_MS
    last_c = time.ticks_ms()  # For cleanup
    last_t = time.ticks_ms()  # For token refresh

    while True:
        feed()
        if time.time()-last_s >= STATUS_INTERVAL:
            send_status(); last_s = time.time()

        if time.ticks_diff(time.ticks_ms(), last_p) >= COMMAND_POLL_MS:
            print("Polling for command...")
            cmd = poll_command(); last_p = time.ticks_ms()
            if 'command_id' in cmd:
                cid = cmd['command_id']; raw = cmd.get('command_payload','')
                params = cmd.get('params',{}); key = raw.upper()
                print("Cmd:",raw,"->",key)
                ok=True
                try: COMMAND_MAP.get(key,lambda p:print("Unknown",key))(params)
                except Exception as e: ok=False; print("Err:",e)
                ack_command(cid, ok)

        if time.ticks_diff(time.ticks_ms(), last_f) >= FLUSH_INTERVAL_MS:
            flush_status_queue(token); flush_ack_queue(token); last_f = time.ticks_ms()

        # Proactively refresh token before expiry (every 25 minutes)
        if time.ticks_diff(time.ticks_ms(), last_t) >= TOKEN_REFRESH_MS:
            print("🔄 Proactively refreshing token...")
            try:
                _, new_token = register_tank()
                if new_token:
                    token = new_token
                    last_t = time.ticks_ms()
                    print("✔ Token refresh successful")
                else:
                    print("❌ Token refresh failed")
                    # If refresh fails, force a reboot to get a fresh token
                    time.sleep(2)
                    machine.reset()
            except Exception as e:
                print(f"❌ Token refresh error: {e}")
                # If refresh errors, force a reboot to get a fresh token
                time.sleep(2)
                machine.reset()

        # Clean up temporary files every hour
        if time.ticks_diff(time.ticks_ms(), last_c) >= 3600000:  # 1 hour in milliseconds
            cleanup_files()
            last_c = time.ticks_ms()

        time.sleep(0.1)

if __name__=='__main__':
    main()


