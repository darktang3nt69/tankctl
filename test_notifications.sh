#!/bin/bash

# Configuration
API_URL="http://192.168.1.100:8000"
PRE_SHARED_KEY="7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM="

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to make API requests
api_request() {
    local method=$1
    local url=$2
    local data=$3
    local token=$4
    
    local headers=()
    if [ -n "$token" ]; then
        headers+=("-H" "Authorization: Bearer $token")
    fi
    
    if [ -n "$data" ]; then
        headers+=("-H" "Content-Type: application/json")
        curl -s -X "$method" "$url" "${headers[@]}" -d "$data"
    else
        curl -s -X "$method" "$url" "${headers[@]}"
    fi
}

log "Starting notification tests..."

# Register a test tank
log "Registering test tank..."
response=$(api_request "POST" "$API_URL/register" "{\"name\":\"Test-Tank-$(date +%Y%m%d_%H%M%S)\", \"key\":\"$PRE_SHARED_KEY\"}")
tank_id=$(echo "$response" | jq -r '.tank_id')
token=$(echo "$response" | jq -r '.token')

if [ "$tank_id" = "null" ]; then
    log "Failed to register test tank"
    exit 1
fi

log "Successfully registered test tank (ID: $tank_id)"

# Test 1: Command Success Notification
log "Testing command success notification..."
response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"water_change\",\"parameters\":{\"volume\":10}}" "$token")
if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
    log "Successfully triggered command success notification"
else
    log "Failed to trigger command success notification"
fi

# Test 2: Tank Offline Notification
log "Testing tank offline notification..."
log "Waiting 60 seconds for tank to be marked as offline..."
sleep 60

# Test 3: Error Notification
log "Testing error notification..."
response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"invalid_command\",\"parameters\":{}}" "$token")
if [ "$(echo "$response" | jq -r '.message')" != "Command scheduled successfully" ]; then
    log "Successfully triggered error notification"
else
    log "Failed to trigger error notification"
fi

# Test 4: Status Update Notification
log "Testing status update notification..."
response=$(api_request "POST" "$API_URL/status" "{\"status\":{\"temperature\":25.0,\"ph\":7.0,\"turbidity\":0.5}}" "$token")
if [ "$(echo "$response" | jq -r '.message')" = "Status updated successfully" ]; then
    log "Successfully triggered status update notification"
else
    log "Failed to trigger status update notification"
fi

log "Notification tests completed!" 