#!/bin/bash

# Configuration
API_URL="http://192.168.1.100:8000"
NUM_TANKS=10
STATUS_UPDATES=5
SLEEP_BETWEEN_REQUESTS=2  # Add delay between API calls
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

log "Starting comprehensive system test..."

# Register tanks
log "Registering $NUM_TANKS tanks..."
declare -a TANK_IDS
declare -a TANK_TOKENS

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
    else
        log "Failed to register $tank_name"
        exit 1
    fi
done

# Schedule commands for each tank
log "Scheduling commands for each tank..."
for i in $(seq 1 $NUM_TANKS); do
    tank_id=${TANK_IDS[$i]}
    token=${TANK_TOKENS[$i]}
    
    # Schedule water change
    log "Scheduling water_change for tank $i..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"water_change\",\"parameters\":{\"volume\":10}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully scheduled water_change for tank $i"
    else
        log "Failed to schedule water_change for tank $i"
    fi
    
    # Schedule light control
    log "Scheduling light_control for tank $i..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"light_control\",\"parameters\":{\"state\":\"on\",\"duration\":3600}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully scheduled light_control for tank $i"
    else
        log "Failed to schedule light_control for tank $i"
    fi
    
    # Schedule feeding
    log "Scheduling feed_now for tank $i..."
    response=$(api_request "POST" "$API_URL/commands" "{\"command\":\"feed_now\",\"parameters\":{\"amount\":5}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Command scheduled successfully" ]; then
        log "Successfully scheduled feed_now for tank $i"
    else
        log "Failed to schedule feed_now for tank $i"
    fi
done

# Simulate nodes consuming commands and sending status updates
log "Simulating nodes consuming commands and sending status updates..."
for i in $(seq 1 $NUM_TANKS); do
    tank_id=${TANK_IDS[$i]}
    token=${TANK_TOKENS[$i]}
    
    # Send initial status
    log "Sending initial status for tank $i..."
    response=$(api_request "POST" "$API_URL/status" "{\"status\":{\"temperature\":25.0,\"ph\":7.0,\"turbidity\":0.5}}" "$token")
    if [ "$(echo "$response" | jq -r '.message')" = "Status updated successfully" ]; then
        log "Successfully sent initial status for tank $i"
    else
        log "Failed to send initial status for tank $i"
    fi
    
    # Get and acknowledge pending commands
    log "Getting pending commands for tank $i..."
    commands=$(api_request "GET" "$API_URL/commands/$tank_id" "" "$token")
    if [ -n "$commands" ]; then
        echo "$commands" | jq -c '.[]' | while read -r cmd; do
            cmd_id=$(echo "$cmd" | jq -r '.id')
            log "Acknowledging command $cmd_id for tank $i..."
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
        log "Sending status update $j for tank $i..."
        response=$(api_request "POST" "$API_URL/status" "{\"status\":{\"temperature\":$((25 + RANDOM % 5)).$((RANDOM % 10)),\"ph\":$((6 + RANDOM % 3)).$((RANDOM % 10)),\"turbidity\":$((RANDOM % 10)).$((RANDOM % 10))}}" "$token")
        if [ "$(echo "$response" | jq -r '.message')" = "Status updated successfully" ]; then
            log "Successfully sent status update $j for tank $i"
        else
            log "Failed to send status update $j for tank $i"
        fi
    done
done

log "Comprehensive system test completed!" 