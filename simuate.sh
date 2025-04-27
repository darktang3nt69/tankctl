#!/bin/bash

# AquaPi Tank Node Simulator and Tester

API_URL="http://192.168.1.100:8000"  # change if different
VALID_AUTH_KEY="super_secret_tank_psk"
INVALID_AUTH_KEY="wrong_key"
TANK_NAME="Simulated Tank Node"

echo "🛠️ AquaPi Tank Node Full Simulator Starting..."

# 1. Test Invalid Auth Key
echo "🔑 Testing invalid auth_key..."
INVALID_REGISTER_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/v1/tank/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{\"auth_key\": \"$INVALID_AUTH_KEY\", \"tank_name\": \"$TANK_NAME\"}")

if [ "$INVALID_REGISTER_RESPONSE" == "401" ]; then
  echo "✅ Invalid auth_key correctly rejected with 401 Unauthorized"
else
  echo "❌ Invalid auth_key test failed!"
  exit 1
fi

# 2. Register Tank (valid key)
echo "🚀 Registering tank with correct auth_key..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tank/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{\"auth_key\": \"$VALID_AUTH_KEY\", \"tank_name\": \"$TANK_NAME\"}")

TANK_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.tank_id')
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Failed to register tank! Response: $REGISTER_RESPONSE"
  exit 1
fi

echo "✅ Registered tank successfully!"
echo "   • tank_id:     $TANK_ID"
echo "   • access_token: $ACCESS_TOKEN"

# 3. Re-register the same tank (should return same token)
echo "♻️ Re-registering same tank to check token reuse..."
REREGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tank/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{\"auth_key\": \"$VALID_AUTH_KEY\", \"tank_name\": \"$TANK_NAME\"}")

NEW_ACCESS_TOKEN=$(echo "$REREGISTER_RESPONSE" | jq -r '.access_token')

if [ "$NEW_ACCESS_TOKEN" == "$ACCESS_TOKEN" ]; then
  echo "✅ Re-registration returned the same token as expected."
else
  echo "❌ Re-registration returned a DIFFERENT token!"
  exit 1
fi

# 4. Start Heartbeat Loop
echo "🫀 Starting heartbeat simulation loop (online/offline)..."

COUNTER=0
ONLINE_HEARTBEATS=5
SLEEP_SECONDS=30

while true; do
  if (( COUNTER < ONLINE_HEARTBEATS )); then
    echo "🟢 Heartbeat $COUNTER: Sending status update..."
    curl -s -X POST "$API_URL/api/v1/tank/status" \
      -H "accept: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "temperature": 26,
        "ph": 7.5,
        "light_state": true,
        "firmware_version": "v1.0.1"
      }' > /dev/null
  else
    if (( COUNTER == ONLINE_HEARTBEATS )); then
      echo "🔴 Simulating tank going OFFLINE... (no heartbeats now)"
    fi
    # No heartbeat sent (simulate disconnection)
  fi

  if (( COUNTER == (ONLINE_HEARTBEATS + 5) )); then
    echo "🟢 Simulating tank COMING BACK ONLINE! Resetting heartbeat loop."
    COUNTER=0
  else
    COUNTER=$((COUNTER + 1))
  fi

  sleep $SLEEP_SECONDS
done
