# main.py — ESP32 MicroPython firmware with inverted relay logic

import os
import network
import urequests
import ujson
import time
import gc
import machine
from machine import WDT, Pin, PWM

# ───── CONFIGURATION ─────
SSID              = 'xxxx.4G'
PASSWORD          = 'xxxx'
BASE_URL          = 'https://xxxx.xxxxx.xxxx'

# API endpoints
REGISTER_API      = '/api/v1/tank/register'
STATUS_API        = '/api/v1/tank/status'
COMMAND_API       = '/api/v1/tank/command'
ACK_API           = '/api/v1/tank/command/ack'

# Auth credentials
AUTH_KEY          = 'xxxxx'
TANK_NAME         = 'xxxx'
LOCATION          = 'xxxx'

# Files for persistence
CONFIG_FILE       = 'config.json'
STATE_FILE        = 'state.json'
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

# GPIO pins
RELAY_PIN         = 15      # D15: light relay (active-low)
SERVO_PIN         = 4       # D4: continuous SG90 servo

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
LIGHT_OFF_TIMING  = "16:00"

# Firmware Version
FIRMWARE          = "1.0.0"

# ───── HARDWARE SETUP ─────
# new: force the relay off state (active‑low) immediately
light_relay = Pin(RELAY_PIN, Pin.OUT, value=RELAY_OFF)
# initialize servo
servo = PWM(Pin(SERVO_PIN), freq=SERV_FREQ)

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
    q = load_json(STATUS_QUEUE_FILE); q.append(payload); save_json(STATUS_QUEUE_FILE, q)

def flush_status_queue(token):
    q = load_json(STATUS_QUEUE_FILE); rem=[]
    for item in q:
        try:
            resp = urequests.post(BASE_URL+STATUS_API, headers={
                'Content-Type':'application/json','Authorization':'Bearer '+token
            }, data=ujson.dumps(item))
            if resp.status_code==200: resp.close(); feed(); continue
            resp.close()
        except: pass
        rem.append(item)
    save_json(STATUS_QUEUE_FILE, rem)

def enqueue_ack(cid, success):
    q = load_json(ACK_QUEUE_FILE); q.append({'command_id':cid,'success':success}); save_json(ACK_QUEUE_FILE, q)

def flush_ack_queue(token):
    q = load_json(ACK_QUEUE_FILE); rem=[]
    for item in q:
        try:
            resp = urequests.post(BASE_URL+ACK_API, headers={
                'Content-Type':'application/json','Authorization':'Bearer '+token
            }, data=ujson.dumps(item))
            if resp.status_code==200: resp.close(); feed(); continue
            resp.close()
        except: pass
        rem.append(item)
    save_json(ACK_QUEUE_FILE, rem)

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
        with open(STATE_FILE, 'w') as f:
            ujson.dump(state, f)
        feed()
    except Exception as e:
        print("❌ save_state error:", e)

# Restore light relay on boot (logical state inverted)
state = load_state()
logical = state.get('light_state', 0)
light_relay.value(RELAY_ON if logical else RELAY_OFF)
print("Restored light_state (logical):", logical)

# ───── SENSOR PLACEHOLDERS ─────
def get_temperature(): return 25.0
def get_ph(): return 7.2

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
    print("❌ Rebooting"); time.sleep(2); machine.reset()

def register_tank():
    body = {
        'auth_key':AUTH_KEY,'tank_name':TANK_NAME,
        'location':LOCATION,'firmware_version': FIRMWARE,
        'light_on': LIGHT_ON_TIMING,'light_off': LIGHT_OFF_TIMING
    }
    resp = urequests.post(BASE_URL+REGISTER_API, headers={'Content-Type':'application/json'}, data=ujson.dumps(body))
    if resp.status_code!=201: resp.close(); time.sleep(5); machine.reset()
    d=resp.json(); resp.close()
    tid, tkn = d['tank_id'], d['access_token']
    with open(CONFIG_FILE,'w') as f: ujson.dump({'tank_id':tid,'token':tkn},f)
    return tid, tkn

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            c=ujson.load(f); return c['tank_id'], c['token']
    except:
        return None, None

# ───── TOKEN REFRESH ─────
def request_with_refresh(fn, *args):
    global token
    code, res = fn(token, *args)
    if code==401:
        print("⚠️ Token expired—re-register")
        _, token = register_tank()
        code, res = fn(token, *args)
    return code, res

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
    payload = {
        'temperature':get_temperature(),
        'ph':get_ph(),
        'light_state':state['light_state'],   # logical state
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

# ───── MAIN LOOP ─────
def main():
    global tank_id, token, state
    connect_wifi()
    tank_id, token = load_config()
    if not token: tank_id, token = register_tank()
    print("▶ Running, tank_id:", tank_id)

    last_s = time.time()-STATUS_INTERVAL
    last_p = time.ticks_ms()-COMMAND_POLL_MS
    last_f = time.ticks_ms()-FLUSH_INTERVAL_MS

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

        time.sleep(0.1)

if __name__=='__main__':
    main()
