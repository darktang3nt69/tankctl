
#!/bin/bash

# ----------------------------------------------
# AquaPi Multi-Tank Simulator (EXTENDED VERSION)
# Features: Heartbeat, Offline Simulation, Manual Override, Schedule Testing
# ----------------------------------------------

API_URL="http://192.168.1.100:8000"
AUTH_KEY="super_secret_tank_psk"
TANK_NAME_PREFIX="StressTank"
NUM_TANKS=3
HEARTBEAT_INTERVAL=30
OFFLINE_DURATION=120
JWT_REFRESH_INTERVAL=3300
COMMAND_CREATE_INTERVAL=180

declare -a tank_ids
declare -a access_tokens
declare -a last_registration_times
declare -a last_command_creation_times

register_tank() {
  local index=$1
  local tank_name="${TANK_NAME_PREFIX}_${index}"

  echo "🚀 Registering Tank $tank_name..."

  REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tank/register" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{\"auth_key\": \"$AUTH_KEY\", \"tank_name\": \"$tank_name\"}")

  tank_ids[$index]=$(echo "$REGISTER_RESPONSE" | jq -r '.tank_id')
  access_tokens[$index]=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')

  if [[ "${access_tokens[$index]}" == "null" || -z "${access_tokens[$index]}" ]]; then
    echo "❌ Registration failed for Tank $tank_name! Response: $REGISTER_RESPONSE"
    exit 1
  fi

  last_registration_times[$index]=$(date +%s)
  last_command_creation_times[$index]=$(date +%s)
  echo "✅ Tank $tank_name registered successfully with ID=${tank_ids[$index]}"
}

send_heartbeat() {
  local index=$1
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/v1/tank/status" \
    -H "Authorization: Bearer ${access_tokens[$index]}" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{
          \"temperature\": 26.5,
          \"ph\": 7.2,
          \"light_state\": true,
          \"firmware_version\": \"v1.0.${index}\"
        }")

  if [[ "$RESPONSE" == "401" ]]; then
    echo "🔴 Tank_$index detected expired token during heartbeat. Re-registering..."
    register_tank $index
    return 1
  fi
  echo "[$(date)] ❤️ Tank_$index heartbeat sent."
}

fetch_and_ack_command() {
  local index=$1
  RESPONSE=$(curl -s -w "
%{http_code}" -X GET "$API_URL/api/v1/tank/command"     -H "Authorization: Bearer ${access_tokens[$index]}" -H "accept: application/json")
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  [[ "$HTTP_CODE" == "401" ]] && echo "🔴 Token expired. Re-registering Tank_$index..." && register_tank $index && return 1

  command_id=$(echo "$BODY" | jq -r '.command_id')
  command_payload=$(echo "$BODY" | jq -r '.command_payload')
  if [[ "$command_id" != "null" && ! -z "$command_id" ]]; then
    echo "[$(date)] 📥 Tank_$index received command: $command_payload"
    sleep 2
    curl -s -o /dev/null -X POST "$API_URL/api/v1/tank/command/ack"       -H "Authorization: Bearer ${access_tokens[$index]}" -H "accept: application/json"       -H "Content-Type: application/json" -d "{"command_id": "$command_id", "success": true}"
    echo "[$(date)] 📤 Tank_$index acknowledged command."
  fi
}

simulate_command_creation() {
  local index=$1
  now=$(date +%s)
  elapsed=$((now - last_command_creation_times[$index]))

  if (( elapsed > COMMAND_CREATE_INTERVAL )); then
    RANDOM_COMMAND=$(shuf -n 1 -e "feed_now" "light_on" "light_off" "pump_on" "pump_off")
    curl -s -o /dev/null -X POST "$API_URL/api/v1/admin/send_command_to_tank" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "x-api-key: supersecretgrafanakey123" \
  -d "{
        \"tank_id\": \"${tank_ids[$index]}\",
        \"command_payload\": \"$RANDOM_COMMAND\"
      }"

    echo "[$(date)] ⚡ Tank_$index issued command: $RANDOM_COMMAND"
    last_command_creation_times[$index]=$now
  fi
}

simulate_manual_override() {
  local index=$1
  if [[ $((RANDOM % 40)) == 0 ]]; then
    curl -s -o /dev/null -X POST "$API_URL/api/v1/tank/${tank_ids[$index]}/override" \
      -H "accept: application/json" \
      -H "Content-Type: application/json" \
      -d "{\"override_state\": true}" && \
    echo "[$(date)] 🔧 Manual override ENABLED for Tank_$index"
  fi
}

simulate_schedule_toggle() {
  local index=$1
  if [[ $((RANDOM % 50)) == 0 ]]; then
    curl -s -o /dev/null -X POST "$API_URL/api/v1/tank/${tank_ids[$index]}/schedule/toggle" \
      -H "accept: application/json" && \
    echo "[$(date)] 🔁 Toggled schedule for Tank_$index"
  fi
}


simulate_offline_cycle() {
  local index=$1
  [[ $((RANDOM % 25)) == 0 ]] && echo "[$(date)] 🛑 Tank_$index simulating OFFLINE..." && sleep $OFFLINE_DURATION
}

refresh_jwt_if_needed() {
  local index=$1
  now=$(date +%s)
  (( now - last_registration_times[$index] > JWT_REFRESH_INTERVAL )) && echo "♻️ Refreshing JWT for Tank_$index" && register_tank $index
}

node_loop() {
  local index=$1
  while true; do
    send_heartbeat $index
    fetch_and_ack_command $index
    simulate_command_creation $index
    simulate_manual_override $index
    simulate_schedule_toggle $index
    simulate_offline_cycle $index
    refresh_jwt_if_needed $index
    sleep $HEARTBEAT_INTERVAL
  done
}

echo "🎯 Starting Multi-Tank Simulation..."
for ((i=0; i<NUM_TANKS; i++)); do
  register_tank $i
  node_loop $i &
  sleep 1
done

wait
