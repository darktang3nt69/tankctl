#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
API_URL="http://localhost:8000/api/v1"
AUTH_KEY="super_secret_tank_psk"             # your tank PSK
ADMIN_API_KEY="supersecretgrafanakey123"     # your admin key
TANK_NAME="DynTestTank_$(date +%s)"          # unique per run

# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE A DYNAMIC 5-MINUTE WINDOW (IST)
# ─────────────────────────────────────────────────────────────────────────────
# Note: `date -u` then convert to Asia/Kolkata works too, but here we rely on tzdata
ON_TIME=$(TZ="Asia/Kolkata" date +%H:%M)
OFF_TIME=$(TZ="Asia/Kolkata" date -d '+5 minutes' +%H:%M)

echo "🕑 Testing window: LIGHT_ON=${ON_TIME}, LIGHT_OFF=${OFF_TIME} (IST)"

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
function register_tank() {
  echo
  echo "🚀 Registering tank '${TANK_NAME}' with schedule ${ON_TIME}–${OFF_TIME}..."
  local resp
  resp=$(curl -s -X POST "${API_URL}/tank/register" \
    -H "Content-Type: application/json" \
    -d '{
      "auth_key": "'"${AUTH_KEY}"'",
      "tank_name": "'"${TANK_NAME}"'",
      "light_on": "'"${ON_TIME}"'",
      "light_off": "'"${OFF_TIME}"'"
    }')
  echo "$resp" | jq .
  TANK_ID=$(echo "$resp" | jq -r .tank_id)
  TOKEN=$(echo "$resp" | jq -r .access_token)
  echo "✅ Got TANK_ID=${TANK_ID}"
}

function get_settings() {
  echo
  echo "🔍 Fetching settings..."
  curl -s -X GET "${API_URL}/tank/settings?tank_id=${TANK_ID}" \
    -H "x-api-key: ${ADMIN_API_KEY}" \
    | jq .
}

function toggle_schedule() {
  local flag=$1
  echo
  echo "⏸️  Setting is_schedule_enabled=${flag}..."
  curl -s -X PUT "${API_URL}/tank/settings?tank_id=${TANK_ID}" \
    -H "Content-Type: application/json" \
    -H "x-api-key: ${ADMIN_API_KEY}" \
    -d '{
      "tank_id": "'"${TANK_ID}"'",
      "is_schedule_enabled": '"${flag}"'
    }' | jq .
}

function manual_override() {
  local state=$1
  echo
  echo "🔧 Manual override → ${state}"
  curl -s -X POST "${API_URL}/tank/${TANK_ID}/override" \
    -H "Content-Type: application/json" \
    -H "x-api-key: ${ADMIN_API_KEY}" \
    -d '{
      "override_state": '"${state}"'
    }' | jq .
}

function fetch_and_ack() {
  echo
  echo "📬 Checking for pending command..."
  local raw
  raw=$(curl -s -w "\n%{http_code}" -X GET "${API_URL}/tank/command" \
    -H "Authorization: Bearer ${TOKEN}")
  local code=$(echo "$raw" | tail -n1)
  local body=$(echo "$raw" | sed '$d')
  if [[ "$code" -ne 200 ]]; then
    echo "⚠️  Unexpected code $code"
    echo "$body" | jq .
    return
  fi
  local cmd_id=$(echo "$body" | jq -r .command_id)
  local cmd_pl=$(echo "$body" | jq -r .command_payload)
  if [[ "$cmd_id" != "null" ]]; then
    echo "📥 Got command [$cmd_id]: $cmd_pl"
    echo "   → ACK’ing it"
    curl -s -X POST "${API_URL}/tank/command/ack" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${TOKEN}" \
      -d '{
        "command_id": "'"${cmd_id}"'",
        "success": true
      }' | jq .
  else
    echo "📭 No pending commands."
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN FLOW
# ─────────────────────────────────────────────────────────────────────────────
echo "🎯 Starting dynamic‐schedule smoke-test…"

register_tank
get_settings

# 1) Pause schedule
toggle_schedule false
echo "⏳ Waiting 1m to verify no scheduled trigger…"
sleep 65
fetch_and_ack

# 2) Resume schedule
toggle_schedule true
echo "⏳ Waiting 1m inside window for scheduled ON…"
sleep 65
fetch_and_ack

# 3) Manual OFF override
manual_override false
echo "⏳ Immediately fetching override→OFF…"
sleep 5
fetch_and_ack

# 4) Manual ON override
manual_override true
echo "⏳ Immediately fetching override→ON…"
sleep 5
fetch_and_ack

# 5) Let scheduler auto-clear override (still within window)
echo
echo "⏳ Waiting 1m for scheduler to clear override…"
sleep 65
fetch_and_ack

echo
echo "✅ Dynamic‐schedule smoke-test COMPLETE."
