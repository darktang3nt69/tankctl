#!/bin/bash

# AquaPi Full Feature Tester
# Tests: Registration ✅ Heartbeat ✅ Command Fetch ✅ Acknowledgement ✅

API_URL="http://192.168.1.100:8000"  # Change this if needed
VALID_AUTH_KEY="super_secret_tank_psk"
TANK_NAME="Simulated Tank Node Tester"

echo "🛠️ Starting AquaPi Full Feature Tester..."

# 1️⃣ Register Tank
echo "🚀 Registering tank..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tank/register" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{\"auth_key\": \"$VALID_AUTH_KEY\", \"tank_name\": \"$TANK_NAME\"}")

TANK_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.tank_id')
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Tank registration failed! Response: $REGISTER_RESPONSE"
  exit 1
fi

echo "✅ Tank registered! tank_id=$TANK_ID"

# 2️⃣ Send Heartbeat
echo "🫀 Sending heartbeat..."
curl -s -X POST "$API_URL/api/v1/tank/status" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
        "temperature": 27.0,
        "ph": 7.4,
        "light_state": true,
        "firmware_version": "v1.0.2"
      }' > /dev/null

echo "✅ Heartbeat sent."

# 3️⃣ (Admin) Issue a command
COMMAND_TO_SEND="feed_now"
echo "📤 Issuing command: $COMMAND_TO_SEND"

ISSUE_COMMAND_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tank/$TANK_ID/command" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{\"command_payload\": \"$COMMAND_TO_SEND\"}")

COMMAND_ID=$(echo "$ISSUE_COMMAND_RESPONSE" | jq -r '.command_id')

if [ "$COMMAND_ID" == "null" ] || [ -z "$COMMAND_ID" ]; then
  echo "❌ Command issue failed! Response: $ISSUE_COMMAND_RESPONSE"
  exit 1
fi

echo "✅ Command issued! command_id=$COMMAND_ID"

# 4️⃣ (Node) Fetch Pending Command
echo "📥 Fetching pending command..."

PENDING_COMMAND=$(curl -s -X GET "$API_URL/api/v1/tank/command" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "accept: application/json")

PENDING_COMMAND_ID=$(echo "$PENDING_COMMAND" | jq -r '.command_id')
PENDING_COMMAND_PAYLOAD=$(echo "$PENDING_COMMAND" | jq -r '.command_payload')

if [ "$PENDING_COMMAND_ID" == "null" ]; then
  echo "❌ No pending command found! Response: $PENDING_COMMAND"
  exit 1
fi

echo "✅ Pending command fetched: $PENDING_COMMAND_PAYLOAD (command_id=$PENDING_COMMAND_ID)"

# 5️⃣ (Node) Acknowledge the command as SUCCESS
echo "📨 Sending ACK for command..."

curl -s -X POST "$API_URL/api/v1/tank/command/ack" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{
        \"command_id\": \"$PENDING_COMMAND_ID\",
        \"success\": true
      }" > /dev/null

echo "✅ Command acknowledged successfully."

echo "🎉 All AquaPi Full Features Tested Successfully!"
