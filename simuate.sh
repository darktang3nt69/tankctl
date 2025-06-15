#!/bin/bash

# ----------------------------------------------
# AquaPi Multi-Tank Simulator (FINAL VERSION - HEARTBEAT CHECK AWARE)
# ----------------------------------------------

# CONFIGURATION
API_URL="http://192.168.1.100:8000"
AUTH_KEY="super_secret_tank_psk"
TANK_NAME_PREFIX="StressTank"
NUM_TANKS=3
HEARTBEAT_INTERVAL=30         # heartbeat every 30s (must be < 1 min threshold)
OFFLINE_DURATION=120          # simulate offline for 90s (server marks tank offline after 60s)
JWT_REFRESH_INTERVAL=3300     # refresh token ~55 minutes
COMMAND_CREATE_INTERVAL=180   # issue command every 3 min

# INTERNAL
declare -a tank_ids
declare -a access_tokens
declare -a last_registration_times
declare -a last_command_creation_times

# FUNCTIONS

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

  COMMAND_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/api/v1/tank/command" \
    -H "Authorization: Bearer ${access_tokens[$index]}" \
    -H "accept: application/json")

  HTTP_CODE=$(echo "$COMMAND_RESPONSE" | tail -n1)
  COMMAND_BODY=$(echo "$COMMAND_RESPONSE" | sed '$d')

  if [[ "$HTTP_CODE" == "401" ]]; then
    echo "🔴 Tank_$index detected expired token during command fetch. Re-registering..."
    register_tank $index
    return 1
  fi

  command_id=$(echo "$COMMAND_BODY" | jq -r '.command_id')
  command_payload=$(echo "$COMMAND_BODY" | jq -r '.command_payload')

  if [[ "$command_id" != "null" && ! -z "$command_id" ]]; then
    echo "[$(date)] 📥 Tank_$index received command: $command_payload (id=$command_id)"
    sleep 2

    curl -s -o /dev/null -X POST "$API_URL/api/v1/tank/command/ack" \
      -H "Authorization: Bearer ${access_tokens[$index]}" \
      -H "accept: application/json" \
      -H "Content-Type: application/json" \
      -d "{
            \"command_id\": \"$command_id\",
            \"success\": true
          }"

    echo "[$(date)] 📤 Tank_$index acknowledged command."
  fi
}

simulate_command_creation() {
  local index=$1
  now=$(date +%s)
  elapsed=$((now - last_command_creation_times[$index]))

  if (( elapsed > COMMAND_CREATE_INTERVAL )); then
    RANDOM_COMMAND=$(shuf -n 1 -e "feed_now" "light_on" "light_off" "pump_on" "pump_off")
    curl -s -o /dev/null -X POST "$API_URL/api/v1/tank/${tank_ids[$index]}/command" \
      -H "accept: application/json" \
      -H "Content-Type: application/json" \
      -d "{\"command_payload\": \"$RANDOM_COMMAND\"}"

    echo "[$(date)] ⚡ Tank_$index issued random command: $RANDOM_COMMAND"
    last_command_creation_times[$index]=$now
  fi
}

simulate_offline_cycle() {
  local index=$1
  if (( RANDOM % 25 == 0 )); then
    echo "[$(date)] 🛑 Tank_$index simulating OFFLINE for $OFFLINE_DURATION seconds..."
    offline_start=$(date +%s)

    while true; do
      now=$(date +%s)
      elapsed=$((now - offline_start))
      if (( elapsed >= OFFLINE_DURATION )); then
        break
      fi
      echo "[$(date)] 🚫 Tank_$index is OFFLINE... ($elapsed/${OFFLINE_DURATION}s)"
      sleep $HEARTBEAT_INTERVAL
    done

    echo "[$(date)] 🟢 Tank_$index coming ONLINE again."
    send_heartbeat $index
  fi
}

refresh_jwt_if_needed() {
  local index=$1
  now=$(date +%s)
  elapsed=$((now - last_registration_times[$index]))

  if (( elapsed > JWT_REFRESH_INTERVAL )); then
    echo "[$(date)] ♻️ Tank_$index proactively refreshing registration..."
    register_tank $index
  fi
}

node_loop() {
  local index=$1
  while true; do
    send_heartbeat $index
    fetch_and_ack_command $index
    simulate_command_creation $index
    simulate_offline_cycle $index
    refresh_jwt_if_needed $index
    sleep $HEARTBEAT_INTERVAL
  done
}

# MAIN

echo "🎯 Starting Multi-Tank Simulation..."

for ((i=0; i<NUM_TANKS; i++)); do
  register_tank $i
  node_loop $i &
  sleep 1
done

wait
