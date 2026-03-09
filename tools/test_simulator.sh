#!/bin/bash
# TankCtl Device Simulator - Quick Test Guide
#
# This script provides practical examples for testing the simulator
# and verifying the complete TankCtl system.
#
# Prerequisites:
# - Docker running with compose file
# - Python 3.10+ with dependencies installed
# - Terminal with bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8000"
MQTT_HOST="localhost"
MQTT_PORT="1883"
MQTT_USER="tankctl"
MQTT_PASS="password"
TIMESCALE_HOST="localhost"
TIMESCALE_PORT="5433"
TIMESCALE_USER="tankctl"
TIMESCALE_PASS="password"
TIMESCALE_DB="tankctl_telemetry"

# Helper functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 not found. Please install it."
        exit 1
    fi
}

# Test functions

test_setup() {
    print_header "Checking Prerequisites"

    check_command "python3"
    check_command "docker"
    check_command "curl"
    check_command "mosquitto_pub"
    check_command "mosquitto_sub"
    check_command "psql"

    print_success "All prerequisites installed"
}

test_services_running() {
    print_header "Checking Services"

    # Check API
    if curl -s "$API_URL/health" > /dev/null; then
        print_success "API is running on $API_URL"
    else
        print_error "API not responding on $API_URL"
        return 1
    fi

    # Check MQTT
    if timeout 2 bash -c "echo > /dev/tcp/$MQTT_HOST/$MQTT_PORT" 2>/dev/null; then
        print_success "MQTT broker is running on $MQTT_HOST:$MQTT_PORT"
    else
        print_error "MQTT broker not responding on $MQTT_HOST:$MQTT_PORT"
        return 1
    fi

    # Check TimescaleDB
    if psql -h "$TIMESCALE_HOST" -p "$TIMESCALE_PORT" -U "$TIMESCALE_USER" -d "$TIMESCALE_DB" \
        -c "SELECT 1" > /dev/null 2>&1; then
        print_success "TimescaleDB is running on $TIMESCALE_HOST:$TIMESCALE_PORT"
    else
        print_error "TimescaleDB not accessible"
        return 1
    fi
}

test_mqtt_connectivity() {
    print_header "Testing MQTT Connectivity"

    # Test basic MQTT access
    test_message="test_$(date +%s)"
    print_info "Publishing test message: $test_message"

    mosquitto_pub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "test/connectivity" -m "$test_message"

    print_success "Published to MQTT broker"
}

test_api_endpoints() {
    print_header "Testing API Endpoints"

    # Health check
    print_info "GET /health"
    if curl -s "$API_URL/health" | jq . > /dev/null; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        return 1
    fi

    # List devices
    print_info "GET /devices"
    device_count=$(curl -s "$API_URL/devices" | jq '.devices | length')
    print_success "Found $device_count devices"

    # Create device
    device_id="test_api_$(date +%s)"
    print_info "POST /devices (register $device_id)"
    if curl -s -X POST "$API_URL/devices" \
        -H "Content-Type: application/json" \
        -d "{\"device_id\": \"$device_id\", \"device_secret\": \"secret\"}" \
        | jq . > /dev/null; then
        print_success "Device registration works"
    else
        print_error "Device registration failed"
        return 1
    fi

    # Get device
    print_info "GET /devices/$device_id"
    if curl -s "$API_URL/devices/$device_id" | jq . > /dev/null; then
        print_success "Get device endpoint works"
    else
        print_error "Get device failed"
        return 1
    fi
}

test_simulator_basic() {
    print_header "Testing Device Simulator (Basic)"

    print_info "Starting 3 devices for 15 seconds..."
    timeout 15 python tools/device_simulator.py --devices 3 || true

    print_info "Waiting for data to be processed..."
    sleep 2

    # Check telemetry data
    print_info "Checking telemetry for tank1..."
    count=$(curl -s "$API_URL/devices/tank1/telemetry?limit=100" | jq '.count')

    if [ "$count" -gt 0 ]; then
        print_success "Received $count telemetry points from tank1"
    else
        print_error "No telemetry points received"
        return 1
    fi
}

test_telemetry_specific() {
    print_header "Testing Telemetry by Metric"

    print_info "Starting 2 devices for 10 seconds..."
    timeout 10 python tools/device_simulator.py --devices 2 || true

    sleep 2

    # Get temperature data
    print_info "GET /devices/tank1/telemetry/temperature"
    temp_count=$(curl -s "$API_URL/devices/tank1/telemetry/temperature?limit=50" | jq '.count')
    print_success "Got $temp_count temperature points"

    # Get humidity data
    print_info "GET /devices/tank1/telemetry/humidity"
    humid_count=$(curl -s "$API_URL/devices/tank1/telemetry/humidity?limit=50" | jq '.count')
    print_success "Got $humid_count humidity points"
}

test_telemetry_aggregation() {
    print_header "Testing Telemetry Aggregation"

    print_info "Starting 2 devices for 10 seconds..."
    timeout 10 python tools/device_simulator.py --devices 2 || true

    sleep 2

    # Get hourly summary
    print_info "GET /devices/tank1/telemetry/hourly/summary"
    summary=$(curl -s "$API_URL/devices/tank1/telemetry/hourly/summary?hours=1")
    
    if echo "$summary" | jq . > /dev/null; then
        print_success "Hourly aggregation is working"
        echo "$summary" | jq '.'
    else
        print_error "Hourly aggregation failed"
        return 1
    fi
}

test_command_delivery() {
    print_header "Testing Command Delivery"

    device_id="tank_command_test"
    
    print_info "Registering device: $device_id"
    curl -s -X POST "$API_URL/devices" \
        -H "Content-Type: application/json" \
        -d "{\"device_id\": \"$device_id\", \"device_secret\": \"secret\"}" > /dev/null

    print_info "Starting simulator with 1 device..."
    timeout 30 python tools/device_simulator.py --devices 1 &
    SIMULATOR_PID=$!

    sleep 3

    print_info "Sending set_light command..."
    curl -s -X POST "$API_URL/devices/tank1/light" \
        -H "Content-Type: application/json" \
        -d '{"value": "on"}' | jq .

    sleep 2

    print_info "Checking reported state..."
    reported=$(curl -s "$API_URL/devices/tank1/shadow" | jq '.reported')
    
    if echo "$reported" | grep -q "on"; then
        print_success "Command was processed by device"
    else
        print_error "Command not executed"
    fi

    # Cleanup
    kill $SIMULATOR_PID 2>/dev/null || true
}

test_load_testing() {
    print_header "Load Testing (50 Devices)"

    print_info "Starting 50 devices for 30 seconds..."
    print_info "This will generate ~1,400 MQTT messages"
    
    start_time=$(date +%s)
    timeout 30 python tools/device_simulator.py --devices 50 || true
    end_time=$(date +%s)
    duration=$((end_time - start_time))

    print_success "Simulation ran for $duration seconds"

    sleep 2

    # Check database size
    print_info "Checking telemetry data..."
    telemetry_count=$(psql -h "$TIMESCALE_HOST" -p "$TIMESCALE_PORT" -U "$TIMESCALE_USER" \
        -d "$TIMESCALE_DB" -t -c "SELECT COUNT(*) FROM telemetry;" 2>/dev/null || echo "0")

    print_success "Total telemetry points in database: $telemetry_count"

    # Check message rate
    if [ "$duration" -gt 0 ]; then
        msg_rate=$((telemetry_count / duration))
        print_success "Average ingestion rate: ~$msg_rate points/second"
    fi
}

test_mqtt_monitoring() {
    print_header "Monitoring MQTT Messages"

    print_info "Subscribing to all device topics (10 seconds)..."
    print_info "Press Ctrl+C to stop"

    timeout 10 mosquitto_sub -h "$MQTT_HOST" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -v -t "tankctl/+/telemetry" || true

    print_info "Done monitoring"
}

test_database_queries() {
    print_header "Testing Database Queries"

    print_info "Starting simulator for 10 seconds..."
    timeout 10 python tools/device_simulator.py --devices 3 || true

    sleep 2

    print_info "Raw data query:"
    psql -h "$TIMESCALE_HOST" -p "$TIMESCALE_PORT" -U "$TIMESCALE_USER" \
        -d "$TIMESCALE_DB" -c \
        "SELECT device_id, temperature, humidity, time FROM telemetry ORDER BY time DESC LIMIT 5;"

    print_info "Device count by ID:"
    psql -h "$TIMESCALE_HOST" -p "$TIMESCALE_PORT" -U "$TIMESCALE_USER" \
        -d "$TIMESCALE_DB" -c \
        "SELECT device_id, COUNT(*) as count FROM telemetry GROUP BY device_id ORDER BY count DESC;"

    print_info "Temperature statistics:"
    psql -h "$TIMESCALE_HOST" -p "$TIMESCALE_PORT" -U "$TIMESCALE_USER" \
        -d "$TIMESCALE_DB" -c \
        "SELECT device_id, MIN(temperature), MAX(temperature), AVG(temperature) FROM telemetry GROUP BY device_id;"
}

test_integration() {
    print_header "Full Integration Test"

    print_info "This test will:"
    print_info "1. Register devices"
    print_info "2. Run simulator"
    print_info "3. Send commands"
    print_info "4. Verify telemetry & state"

    # Run Python integration test
    if command -v python tools/integration_test.py &> /dev/null; then
        python tools/integration_test.py --verbose
    else
        print_error "Integration test script not found"
        print_info "Run: python tools/integration_test.py"
    fi
}

# Main menu
show_menu() {
    print_header "TankCtl Device Simulator - Test Menu"

    echo "1) Setup - Check prerequisites"
    echo "2) Services - Check all services running"
    echo "3) MQTT - Test MQTT connectivity"
    echo "4) API - Test all API endpoints"
    echo "5) Simulator Basic - Run 3 devices for 15s"
    echo "6) Telemetry Specific - Test metric-specific queries"
    echo "7) Aggregation - Test hourly aggregation"
    echo "8) Commands - Test command delivery"
    echo "9) Load Test - Run 50 devices for 30s"
    echo "10) MQTT Monitor - Watch MQTT messages (10s)"
    echo "11) Database - Query database directly"
    echo "12) Integration - Run full integration test"
    echo "13) Quick Demo - Run all quick tests (1-4)"
    echo "14) Full Demo - Run all tests"
    echo "0) Exit"
    echo ""
}

# Script start

if [ "$#" -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Select test (0-14): " choice

        case $choice in
            1) test_setup ;;
            2) test_services_running ;;
            3) test_mqtt_connectivity ;;
            4) test_api_endpoints ;;
            5) test_simulator_basic ;;
            6) test_telemetry_specific ;;
            7) test_telemetry_aggregation ;;
            8) test_command_delivery ;;
            9) test_load_testing ;;
            10) test_mqtt_monitoring ;;
            11) test_database_queries ;;
            12) test_integration ;;
            13) 
                test_setup
                test_services_running
                test_mqtt_connectivity
                test_api_endpoints
                ;;
            14)
                test_setup
                test_services_running
                test_mqtt_connectivity
                test_api_endpoints
                test_simulator_basic
                test_telemetry_specific
                # Skipping long tests in full demo
                ;;
            0) 
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                ;;
        esac

        read -p "Press Enter to continue..."
    done
else
    # Command line mode
    case "$1" in
        setup) test_setup ;;
        services) test_services_running ;;
        mqtt) test_mqtt_connectivity ;;
        api) test_api_endpoints ;;
        basic) test_simulator_basic ;;
        telemetry) test_telemetry_specific ;;
        aggregation) test_telemetry_aggregation ;;
        commands) test_command_delivery ;;
        load) test_load_testing ;;
        monitor) test_mqtt_monitoring ;;
        db) test_database_queries ;;
        integration) test_integration ;;
        *)
            echo "Usage: $0 {setup|services|mqtt|api|basic|telemetry|aggregation|commands|load|monitor|db|integration}"
            exit 1
            ;;
    esac
fi
