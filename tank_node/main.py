# main.py — ESP32 MicroPython firmware with self‑healing, offline queues, state persistence,
#              and SG90‑360 feeder + relay light on D15, servo on D4

import os
import network
import urequests
import ujson
import time
import gc
import machine
from machine import WDT, Pin, PWM

# ───── CONFIGURATION ─────
SSID              = 'xxxxxxx'                # Wi‑Fi SSID
PASSWORD          = 'xxxxxxxx'                   # Wi‑Fi password
BASE_URL          = 'https://endpoint.example.domain'

# API endpoints
REGISTER_API      = '/api/v1/tank/register'
STATUS_API        = '/api/v1/tank/status'
COMMAND_API       = '/api/v1/tank/command'
ACK_API           = '/api/v1/tank/command/ack'

# Auth credentials
AUTH_KEY          = 'super_secret_tank_psk'
TANK_NAME         = 'Hyd_tank'
LOCATION          = 'Hyderabad'

# Files for persistence
CONFIG_FILE       = 'config.json'                # stores tank_id & token
STATE_FILE        = 'state.json'                 # stores last known relay state
STATUS_QUEUE_FILE = 'status_queue.json'          # queued status payloads
ACK_QUEUE_FILE    = 'ack_queue.json'             # queued ack payloads

# Timing parameters
WIFI_RETRIES      = 5
WIFI_TIMEOUT      = 10       # seconds per Wi‑Fi attempt
WDT_TIMEOUT_MS    = 10000    # watchdog timeout in ms
STATUS_INTERVAL   = 60       # seconds between status updates
COMMAND_POLL_MS   = 5000     # ms between polling for commands
FLUSH_INTERVAL_MS = 30000    # ms between queue flush attempts
MIN_HEAP_BYTES    = 50000    # if free heap < this, trigger self‑heal reboot

# GPIO pins
RELAY_PIN         = 15       # physical D15: light relay switch
SERVO_PIN         = 4        # physical D4: continuous SG90 servo

# Servo PWM settings for SG90‑360
SERV_FREQ         = 50       # 50Hz PWM for servo
STOP_DUTY         = 77       # ~1.5ms pulse → stop
FORWARD_DUTY      = 100      # ~2.0ms pulse → forward spin
REVERSE_DUTY      = 50       # ~1.0ms pulse → reverse spin

# ───── HARDWARE SETUP ─────
light_relay = Pin(RELAY_PIN, Pin.OUT)             # relay control
# initialize servo
servo = PWM(Pin(SERVO_PIN), freq=SERV_FREQ)

# ───── WATCHDOG & SELF‑HEALING ─────
wdt = WDT(timeout=WDT_TIMEOUT_MS)
def feed():
    """
    Feed watchdog, run GC, and reboot on low memory.
    """
    wdt.feed()
    gc.collect()
    if gc.mem_free() < MIN_HEAP_BYTES:
        print("⚠️ Low memory, rebooting for self‑healing")
        time.sleep(1)
        machine.reset()

# ───── FILESYSTEM UTILITIES ─────
def load_json(fname):
    try:
        with open(fname) as f:
            return ujson.load(f)
    except:
        return []

def save_json(fname, data):
    try:
        with open(fname, 'w') as f:
            ujson.dump(data, f)
    except:
        pass

# ───── OFFLINE QUEUES ─────
def enqueue_status(payload):
    q = load_json(STATUS_QUEUE_FILE)
    q.append(payload)
    save_json(STATUS_QUEUE_FILE, q)

def flush_status_queue(token):
    q = load_json(STATUS_QUEUE_FILE); remain = []
    for item in q:
        try:
            resp = urequests.post(BASE_URL+STATUS_API,
                                  headers={'Content-Type':'application/json',
                                           'Authorization':'Bearer '+token},
                                  data=ujson.dumps(item))
            if resp.status_code == 200:
                resp.close(); feed(); continue
            resp.close()
        except:
            pass
        remain.append(item)
    save_json(STATUS_QUEUE_FILE, remain)

def enqueue_ack(cid, success):
    q = load_json(ACK_QUEUE_FILE)
    q.append({'command_id': cid, 'success': success})
    save_json(ACK_QUEUE_FILE, q)

def flush_ack_queue(token):
    q = load_json(ACK_QUEUE_FILE); remain = []
    for item in q:
        try:
            resp = urequests.post(BASE_URL+ACK_API,
                                  headers={'Content-Type':'application/json',
                                           'Authorization':'Bearer '+token},
                                  data=ujson.dumps(item))
            if resp.status_code == 200:
                resp.close(); feed(); continue
            resp.close()
        except:
            pass
        remain.append(item)
    save_json(ACK_QUEUE_FILE, remain)

# ───── STATE PERSISTENCE ─────
def load_state():
    """
    Return {'light_state':0 or 1}
    """
    try:
        with open(STATE_FILE) as f:
            return ujson.load(f)
    except:
        return {'light_state': 0}

def save_state(state):
    """
    Persist state dict to STATE_FILE.
    """
    try:
        feed()
        with open(STATE_FILE, 'w') as f:
            ujson.dump(state, f)
        feed()
    except Exception as e:
        print("❌ save_state error:", e)

# Restore relay on boot
state = load_state()
light_relay.value(state.get('light_state', 0))
print("Restored light_state:", state.get('light_state'))

# ───── SENSOR PLACEHOLDERS ─────
def get_temperature():
    return 25.0

def get_ph():
    return 7.2

# ───── WIFI & REGISTRATION ─────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    for i in range(1, WIFI_RETRIES+1):
        print(f"Wi‑Fi attempt {i}/{WIFI_RETRIES}")
        wlan.connect(SSID, PASSWORD)
        start = time.time()
        while not wlan.isconnected() and time.time()-start < WIFI_TIMEOUT:
            feed(); time.sleep(0.2)
        if wlan.isconnected():
            print("✔ Wi‑Fi IP:", wlan.ifconfig()[0]); return
        print("⚠️ Wi‑Fi failed")
    print("❌ Rebooting..."); time.sleep(2); machine.reset()

def register_tank():
    body = {'auth_key':AUTH_KEY,'tank_name':TANK_NAME,
            'location':LOCATION,'firmware_version':'1.0.0',
            'light_on':'22:20','light_off':'22:25'}
    resp = urequests.post(BASE_URL+REGISTER_API,
                         headers={'Content-Type':'application/json'},
                         data=ujson.dumps(body))
    if resp.status_code != 201:
        print("❌ Register failed", resp.status_code)
        resp.close(); time.sleep(5); machine.reset()
    data = resp.json(); resp.close()
    tid, tkn = data['tank_id'], data['access_token']
    with open(CONFIG_FILE,'w') as f:
        ujson.dump({'tank_id':tid,'token':tkn},f)
    return tid, tkn

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            c = ujson.load(f); return c['tank_id'], c['token']
    except:
        return None, None

# ───── TOKEN REFRESH ─────
def request_with_refresh(fn, *args):
    global token
    code, res = fn(token, *args)
    if code == 401:
        print("⚠️ Token expired, re-register")
        _, token = register_tank()
        code, res = fn(token, *args)
    return code, res

# ───── HTTP HELPERS ─────
def _post_status(tkn, payload):
    try:
        resp = urequests.post(BASE_URL+STATUS_API,
                              headers={'Content-Type':'application/json',
                                       'Authorization':'Bearer '+tkn},
                              data=ujson.dumps(payload))
        st = resp.status_code; resp.close(); feed()
        return st, None
    except:
        return None, None

def _post_ack(tkn, cid, success):
    try:
        resp = urequests.post(BASE_URL+ACK_API,
                              headers={'Content-Type':'application/json',
                                       'Authorization':'Bearer '+tkn},
                              data=ujson.dumps({'command_id':cid,'success':success}))
        st = resp.status_code; resp.close(); feed()
        return st, None
    except:
        return None, None

def _get_command(tkn):
    try:
        resp = urequests.get(BASE_URL+COMMAND_API,
                             headers={'Authorization':'Bearer '+tkn})
        st = resp.status_code
        data = resp.json() if st==200 else {}
        resp.close(); feed()
        return st, data
    except:
        return None, {}

# ───── HIGH‑LEVEL WRAPPERS ─────
def send_status():
    payload = {
        'temperature': get_temperature(),
        'ph': get_ph(),
        'light_state': bool(light_relay.value()),
        'firmware_version': '1.0.0'
    }
    print("📤 Sending:", payload)
    code, _ = request_with_refresh(_post_status, payload)
    print(f"📥 Status→{code}")
    if code==200: flush_status_queue(token)
    else: enqueue_status(payload)

def ack_command(cid, success):
    code, _ = request_with_refresh(_post_ack, cid, success)
    if code==200: flush_ack_queue(token)
    else: enqueue_ack(cid, success)

def poll_command():
    code, data = request_with_refresh(_get_command)
    return data if code==200 else {}

# ───── COMMAND HANDLERS ─────
def handle_light(on):
    light_relay.value(1 if on else 0)
    state['light_state'] = light_relay.value()
    save_state(state)

def handle_feed(params):
    # spin servo based on params
    dur = params.get('duration', 2)
    dir = params.get('direction','forward').lower()
    duty = params.get('duty',
             FORWARD_DUTY if dir=='forward' else REVERSE_DUTY)
    print(f"▶ Feed: dir={dir}, dur={dur}s")
    servo.duty(duty); time.sleep(dur)
    servo.duty(STOP_DUTY)
    print("✔ Feed done")

COMMAND_MAP = {
    'LIGHT_ON':  lambda p: handle_light(True),
    'LIGHT_OFF': lambda p: handle_light(False),
    'FEED_NOW':  handle_feed,
}

# ───── MAIN LOOP ─────
def main():
    global tank_id, token, state
    connect_wifi()
    tank_id, token = load_config()
    if not token: tank_id, token = register_tank()
    print("▶ Running, tank_id:", tank_id)

    last_s = time.time() - STATUS_INTERVAL
    last_p = time.ticks_ms() - COMMAND_POLL_MS
    last_f = time.ticks_ms() - FLUSH_INTERVAL_MS

    while True:
        feed()
        # status
        if time.time()-last_s>=STATUS_INTERVAL:
            send_status(); last_s = time.time()
        # commands
        if time.ticks_diff(time.ticks_ms(), last_p)>=COMMAND_POLL_MS:
            cmd = poll_command(); last_p = time.ticks_ms()
            if 'command_id' in cmd:
                cid = cmd['command_id']; raw = cmd.get('command_payload','')
                params = cmd.get('params',{}); key = raw.upper()
                print("Cmd:", raw,"->",key)
                ok = True
                try: COMMAND_MAP.get(key, lambda p: print("Unknown",key))(params)
                except Exception as e: ok=False; print("Err:",e)
                ack_command(cid, ok)
        # flush queues
        if time.ticks_diff(time.ticks_ms(), last_f)>=FLUSH_INTERVAL_MS:
            flush_status_queue(token); flush_ack_queue(token)
            last_f = time.ticks_ms()
        time.sleep(0.1)

if __name__=='__main__':
    main()

