#!/bin/bash

# Configuration
API_URL="http://localhost:8000"
PRE_SHARED_KEY="7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM="
TANK_NAME="Test-Tank-$(date +%Y%m%d_%H%M%S)"
TANK_ID=""

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to make API requests
api_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4
    
    local headers=()
    if [ -n "$token" ]; then
        headers+=("-H" "Authorization: Bearer $token")
    fi
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
             -H "Content-Type: application/json" \
             "${headers[@]}" \
             -d "$data" \
             "$API_URL$endpoint"
    else
        curl -s -X "$method" \
             -H "Content-Type: application/json" \
             "${headers[@]}" \
             "$API_URL$endpoint"
    fi
}

# Function to check metrics
check_metrics() {
    log "Checking Prometheus metrics..."
    curl -s "$API_URL/metrics" | grep -E "tankctl_|process_"
}

# Test 1: Register Tank
log "Starting node lifecycle test..."
log "Test 1: Registering tank $TANK_NAME"
response=$(api_request POST "/register" "{\"name\": \"$TANK_NAME\", \"key\": \"$PRE_SHARED_KEY\"}")
if [ $? -eq 0 ] && echo "$response" | grep -q "token"; then
    log "Success: Tank registered"
    TOKEN=$(echo "$response" | jq -r '.token')
    TANK_ID=$(echo "$response" | jq -r '.id')
else
    log "Error: Failed to register tank"
    log "Response: $response"
    exit 1
fi
log "Successfully registered tank with ID: $TANK_ID"

# Test 2: Send Status Update
log "Test 2: Sending initial status update"
status_data="{\"status\": {\"temperature\": 25.5, \"ph\": 7.2, \"water_level\": 80}}"
response=$(api_request POST "/status" "$status_data" "$TOKEN")
if [ $? -eq 0 ] && echo "$response" | grep -q "success"; then
    log "Success: Status updated"
else
    log "Error: Failed to update status"
    log "Response: $response"
    exit 1
fi

# Test 3: Queue Commands
log "Test 3: Queueing commands"
response=$(api_request POST "/commands" "{\"command\": \"water_change\", \"parameters\": {\"duration\": 30}}" "$TOKEN")
if [ $? -eq 0 ]; then
    log "Success: Water change command queued"
else
    log "Error: Failed to queue water change command"
    log "Response: $response"
    exit 1
fi

response=$(api_request POST "/commands" "{\"command\": \"feed_fish\", \"parameters\": {\"amount\": 2}}" "$TOKEN")
if [ $? -eq 0 ]; then
    log "Success: Feed fish command queued"
else
    log "Error: Failed to queue feed fish command"
    log "Response: $response"
    exit 1
fi

# Test 4: Get Pending Commands
log "Test 4: Getting pending commands"
commands=$(api_request GET "/commands?unacknowledged_only=true" "" "$TOKEN")
echo "Pending commands: $commands"

# Test 5: Acknowledge Commands
log "Test 5: Acknowledging commands"
for cmd_id in $(echo $commands | jq -r '.[].id'); do
    log "Acknowledging command $cmd_id"
    response=$(api_request POST "/commands/ack" "{\"command_id\": $cmd_id}" "$TOKEN")
    if [ $? -eq 0 ]; then
        log "Success: Command acknowledged"
    else
        log "Error: Failed to acknowledge command"
        log "Response: $response"
        exit 1
    fi
done

# Test 6: Send Status Update After Commands
log "Test 6: Sending status update after commands"
status_data="{\"status\": {\"temperature\": 25.6, \"ph\": 7.1, \"water_level\": 100}}"
response=$(api_request POST "/status" "$status_data" "$TOKEN")
if [ $? -eq 0 ] && echo "$response" | grep -q "success"; then
    log "Success: Status updated"
else
    log "Error: Failed to update status"
    log "Response: $response"
    exit 1
fi

# Test 7: Check Metrics
log "Test 7: Checking metrics"
check_metrics

# Test 8: Simulate Node Going Offline
log "Test 8: Simulating node going offline"
log "Waiting 60 seconds to simulate offline state..."
sleep 60

# Test 9: Check if Node is Marked as Offline
log "Test 9: Checking if node is marked as offline"
api_request GET "/tanks/$TANK_ID" "" "$TOKEN"

# Test 10: Send Status Update to Mark as Online
log "Test 10: Sending status update to mark as online"
status_data="{\"status\": {\"temperature\": 25.5, \"ph\": 7.2, \"water_level\": 95}}"
response=$(api_request POST "/status" "$status_data" "$TOKEN")
if [ $? -eq 0 ] && echo "$response" | grep -q "success"; then
    log "Success: Status updated"
else
    log "Error: Failed to update status"
    log "Response: $response"
    exit 1
fi

# Test 11: Final Metrics Check
log "Test 11: Final metrics check"
check_metrics

log "Node lifecycle test completed" 