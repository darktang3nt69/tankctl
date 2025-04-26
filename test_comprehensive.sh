#!/bin/bash

# Configuration
API_URL="http://192.168.1.100:8000"
NUM_TANKS=5  # Reduced from 10 to make testing faster
STATUS_UPDATES=3  # Reduced from 5 to make testing faster
SLEEP_BETWEEN_REQUESTS=1  # Reduced from 2 to make testing faster
PRE_SHARED_KEY="7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM="

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to make API requests with rate limiting
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
    
    sleep $SLEEP_BETWEEN_REQUESTS
}

# Function to test notifications for a specific tank
test_notifications() {
    local tank_id=$1
    local token=$2
    local tank_name=$3
    
    log "Testing notifications for tank $tank_name (ID: $tank_id)..."
    
    # Test 1: Command Success Notification
    log "Testing command success notification..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"water_change\",\"parameters\":{\"volume\":10}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully triggered command success notification"
    else
        log "Failed to trigger command success notification"
    fi
    
    # Test 2: Error Notification
    log "Testing error notification..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"invalid_command\",\"parameters\":{}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" != "Command scheduled successfully" ]; then
        log "Successfully triggered error notification"
    else
        log "Failed to trigger error notification"
    fi
    
    # Test 3: Status Update Notification
    log "Testing status update notification..."
    response=$(api_request "POST" "$API_URL/status" "{\"status\":{\"temperature\":25.0,\"ph\":7.0,\"turbidity\":0.5}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Status updated successfully" ]; then
        log "Successfully triggered status update notification"
    else
        log "Failed to trigger status update notification"
    fi
}

# Function to test tank offline notification
test_offline_notification() {
    local tank_id=$1
    local token=$2
    local tank_name=$3
    
    log "Testing offline notification for tank $tank_name (ID: $tank_id)..."
    log "Waiting 60 seconds for tank to be marked as offline..."
    sleep 60
    
    # Verify tank is marked as offline
    response=$(api_request "GET" "$API_URL/tanks/$tank_id" "" "")
    is_offline=$(echo "$response" | jq -r '.is_offline')
    if [ "$is_offline" = "true" ]; then
        log "Successfully detected tank as offline"
    else
        log "Failed to detect tank as offline"
    fi
}

log "Starting comprehensive system test..."

# Register tanks
log "Registering $NUM_TANKS tanks..."
declare -a TANK_IDS
declare -a TANK_TOKENS
declare -a TANK_NAMES

for i in $(seq 1 $NUM_TANKS); do
    tank_name="Test-Tank-$(date +%Y%m%d_%H%M%S)-$i"
    log "Registering $tank_name..."
    
    response=$(api_request "POST" "$API_URL/register" "{\"name\":\"$tank_name\", \"key\":\"$PRE_SHARED_KEY\"}")
    tank_id=$(echo "$response" | jq -r '.tank_id')
    token=$(echo "$response" | jq -r '.token')
    
    if [ "$tank_id" != "null" ]; then
        log "Successfully registered $tank_name (ID: $tank_id)"
        TANK_IDS[$i]=$tank_id
        TANK_TOKENS[$i]=$token
        TANK_NAMES[$i]=$tank_name
    else
        log "Failed to register $tank_name"
        exit 1
    fi
done

# Test notifications for each tank
for i in $(seq 1 $NUM_TANKS); do
    test_notifications "${TANK_IDS[$i]}" "${TANK_TOKENS[$i]}" "${TANK_NAMES[$i]}"
done

# Schedule commands for each tank
log "Scheduling commands for each tank..."
for i in $(seq 1 $NUM_TANKS); do
    tank_id=${TANK_IDS[$i]}
    token=${TANK_TOKENS[$i]}
    tank_name=${TANK_NAMES[$i]}
    
    # Schedule water change
    log "Scheduling water_change for $tank_name..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"water_change\",\"parameters\":{\"volume\":10}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully scheduled water_change for $tank_name"
    else
        log "Failed to schedule water_change for $tank_name"
    fi
    
    # Schedule light control
    log "Scheduling light_control for $tank_name..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"light_control\",\"parameters\":{\"state\":\"on\",\"duration\":3600}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully scheduled light_control for $tank_name"
    else
        log "Failed to schedule light_control for $tank_name"
    fi
    
    # Schedule feeding
    log "Scheduling feed_now for $tank_name..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"feed_now\",\"parameters\":{\"amount\":5}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully scheduled feed_now for $tank_name"
    else
        log "Failed to schedule feed_now for $tank_name"
    fi
done

# Simulate nodes consuming commands and sending status updates
log "Simulating nodes consuming commands and sending status updates..."
for i in $(seq 1 $NUM_TANKS); do
    tank_id=${TANK_IDS[$i]}
    token=${TANK_TOKENS[$i]}
    tank_name=${TANK_NAMES[$i]}
    
    # Send initial status
    log "Sending initial status for $tank_name..."
    response=$(api_request "POST" "$API_URL/status" "{\"status\":{\"temperature\":25.0,\"ph\":7.0,\"turbidity\":0.5}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Status updated successfully" ]; then
        log "Successfully sent initial status for $tank_name"
    else
        log "Failed to send initial status for $tank_name"
    fi
    
    # Get and acknowledge pending commands
    log "Getting pending commands for $tank_name..."
    commands=$(api_request "GET" "$API_URL/commands/$tank_id" "" "$token")
    if [ -n "$commands" ]; then
        echo "$commands" | jq -c '.[]' | while read -r cmd; do
            cmd_id=$(echo "$cmd" | jq -r '.id')
            log "Acknowledging command $cmd_id for $tank_name..."
            response=$(api_request "POST" "$API_URL/commands/$cmd_id/ack" "" "$token")
            if [ "$(echo "$response" | jq -r '.message')" = "Command acknowledged" ]; then
                log "Successfully acknowledged command $cmd_id"
            else
                log "Failed to acknowledge command $cmd_id"
            fi
        done
    fi
    
    # Send periodic status updates
    for j in $(seq 1 $STATUS_UPDATES); do
        log "Sending status update $j for $tank_name..."
        response=$(api_request "POST" "$API_URL/status" "{\"status\":{\"temperature\":$((25 + RANDOM % 5)).$((RANDOM % 10)),\"ph\":$((6 + RANDOM % 3)).$((RANDOM % 10)),\"turbidity\":$((RANDOM % 10)).$((RANDOM % 10))}}" "$token")
        if [ "$(echo "$response" | jq -r '.message')" = "Status updated successfully" ]; then
            log "Successfully sent status update $j for $tank_name"
        else
            log "Failed to send status update $j for $tank_name"
        fi
    done
done

# Test offline notifications for each tank
for i in $(seq 1 $NUM_TANKS); do
    test_offline_notification "${TANK_IDS[$i]}" "${TANK_TOKENS[$i]}" "${TANK_NAMES[$i]}"
done

log "Comprehensive system test completed!" 