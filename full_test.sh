#!/bin/bash

# ⚙️ CONFIGURATION
API_URL="http://localhost:8000"
AUTH_KEY="super_secret_tank_psk"
TANK_NAME="DebugTank"
ADMIN_API_KEY="supersecretgrafanakey123"

# ⏱ DYNAMIC SCHEDULE: Turn ON in 1 minute, OFF in 6 minutes from now
NOW=$(date +%s)
LIGHT_ON=$(date -d "@$((NOW + 60))" +%T)     # +1 minute
LIGHT_OFF=$(date -d "@$((NOW + 360))" +%T)   # +6 minutes

# 📦 Register
register_tank() {
  echo "📡 Registering tank $TANK_NAME..."
  RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tank/register" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{\"auth_key\": \"$AUTH_KEY\", \"tank_name\": \"$TANK_NAME\"}")

  tank_id=$(echo "$RESPONSE" | jq -r '.tank_id')
  token=$(echo "$RESPONSE" | jq -r '.access_token')
  echo "✅ Registered tank_id=$tank_id"
}

# 🧠 Update schedule
update_schedule() {
  echo "⏰ Updating lighting schedule to $LIGHT_ON → $LIGHT_OFF..."
  curl -s -X PUT "$API_URL/api/v1/tanks/settings" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{\"light_on\": \"$LIGHT_ON\", \"light_off\": \"$LIGHT_OFF\"}" \
    && echo "✅ Schedule updated"
}

# 👁 Fetch settings
get_settings() {
  echo "📥 Fetching /tank/settings..."
  curl -s -X GET "$API_URL/api/v1/tank/settings" \
    -H "Authorization: Bearer $token" \
    | jq .
}

# 🧪 Trigger manual override
trigger_manual_override() {
  echo "⚠️ Triggering manual override: light_off"
  curl -s -X POST "$API_URL/api/v1/admin/send_command_to_tank" \
    -H "x-api-key: $ADMIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"tank_id\": \"$tank_id\", \"command_payload\": \"light_off\"}" \
    | jq .
}

# ❤️ Heartbeat
send_heartbeat() {
  echo "💓 Sending heartbeat"
  curl -s -X POST "$API_URL/api/v1/tank/status" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d '{
      "temperature": 26.4,
      "ph": 7.1,
      "light_state": true,
      "firmware_version": "v1.1.test"
    }'
}

# 📥 Fetch + ACK command
fetch_and_ack_command() {
  echo "📬 Fetching pending command..."
  COMMAND=$(curl -s -X GET "$API_URL/api/v1/tank/command" \
    -H "Authorization: Bearer $token")

  command_id=$(echo "$COMMAND" | jq -r '.command_id')
  command_payload=$(echo "$COMMAND" | jq -r '.command_payload')

  if [[ "$command_id" != "null" ]]; then
    echo "📥 Got command: $command_payload (id: $command_id)"
    sleep 2
    echo "✅ Acknowledging..."
    curl -s -X POST "$API_URL/api/v1/tank/command/ack" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "{\"command_id\": \"$command_id\", \"success\": true}"
  else
    echo "📭 No pending command."
  fi
}

# 📴 Simulate going offline
simulate_offline() {
  echo "🛑 Simulating offline..."
  sleep 120
  echo "🟢 Coming back online. Sending heartbeat..."
  send_heartbeat
}

# 🧪 TEST RUN
register_tank
update_schedule
get_settings
send_heartbeat
trigger_manual_override
fetch_and_ack_command
simulate_offline
get_settings
