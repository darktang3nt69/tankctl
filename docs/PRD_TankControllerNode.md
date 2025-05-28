# Product Requirements Document: Tank Controller Node Firmware and API Server

## 1. Introduction

This document outlines the requirements for the ESP32-based tank controller node firmware and the associated central API server. The system's primary function is to manage aquarium hardware components (lights, feeder) via the node firmware and enable remote monitoring and control through the API server and its client applications.

## 2. Goals

-   Provide reliable control over aquarium lights (on/off) and an automatic feeder via the node firmware.
-   Enable nodes to periodically report tank status (temperature, pH, light state, firmware version) to the central API server.
-   Allow the API server to issue commands to specific tank nodes for execution.
-   Implement robustness features in the node firmware to handle network interruptions and potential device issues.
-   Persist configuration and state on the node across reboots.
-   Enable potential future Over-The-Air (OTA) firmware updates for nodes.
-   Provide a scalable and reliable API server to manage multiple tank nodes and serve client applications.
-   Implement monitoring capabilities using Prometheus metrics for both nodes and the server.

## 3. Target Audience

-   Aquarium owners needing remote monitoring and control.
-   Developers maintaining and extending the tank node firmware and the API server.
-   Operators of the central API server infrastructure.
-   Developers building client applications that interact with the API server.

## 4. Functionality / User Stories

    -   Connect my tank node to my local Wi-Fi network easily.
    -   Have the tank node automatically register with the central server.
    -   View the current status of my tank (temperature, pH, light state) via a remote application connected to the API server.
    -   Remotely turn the tank lights ON or OFF via the remote application and API server.
    -   Remotely trigger the fish feeder for a specified duration via the remote application and API server.
    -   Know that the device is running a specific firmware version.
    -   Have the device attempt to recover automatically from network issues or errors.
    -   Onboard and manage multiple tank devices via the API server.
    -   Receive status updates from all connected tank nodes via the API server.
    -   Issue commands to specific tank nodes via the API server.
    -   Receive acknowledgments from tank nodes regarding command execution status via the API server.
    -   Be able to identify devices by a unique ID and monitor their firmware versions via the API server.
    -   Monitor the health and performance of the API server and connected nodes using metrics.

## 5. Technical Overview

-   **Tank Node Hardware:** ESP32 microcontroller, Relay module (active-low), Continuous Rotation Servo (SG90), Placeholder sensors (Temperature, pH).
-   **Tank Node Software:** MicroPython firmware.
-   **API Server:** Central application (technology TBD) managing tank data, commands, and serving clients.
-   **Communication:** Wi-Fi (STA mode) for nodes, HTTP(S) requests between nodes and API server.
-   **Data Format:** JSON for API communication.
-   **Persistence (Node):** Configuration, state, and offline queues stored in JSON files on the ESP32 filesystem.
-   **Persistence (Server):** Database (TBD) for storing tank information, status history, command queues, etc.
-   **Self-Healing (Node):** Watchdog timer, Wi-Fi reconnection logic, memory check and reboot, offline queues for requests.
-   **Monitoring:** Prometheus metrics exposed by the API server and potentially pushed from nodes.

#### Tech Involved
*   MicroPython
*   Placeholder sensor functions (`get_temperature`, `get_ph`)
*   `urequests` library (HTTP/S)
*   JSON
*   ESP32 filesystem (for queue)

## 6. API Interactions

The system relies on communication between the Tank Node firmware and the central API server via four defined API endpoints:

-   **`/api/v1/tank/register` (POST)**
    *   **Purpose:** Device onboarding and token acquisition/refresh. Allows a new or reconnecting node to identify itself and get credentials for future communication.
    *   **Inferred Input Schema (JSON Body):**
        ```json
        {
          "auth_key": "string",          // A pre-shared key for initial authentication
          "tank_name": "string",         // Name of the tank (e.g., "Hyd_tank")
          "location": "string",          // Location of the tank (e.g., "Hyderabad")
          "firmware_version": "string",  // Current firmware version of the node
          "light_on": "string",          // Default light ON time (e.g., "10:00")
          "light_off": "string"          // Default light OFF time (e.g., "18:00")
        }
        ```
    *   **Expected Response Schema (JSON Body - Status 201 Created):**
        ```json
        {
          "tank_id": "string",           // Unique identifier assigned to the tank by the server
          "access_token": "string"       // Token to be used in the Authorization header for subsequent requests
        }
        ```
    *   **Error Response:** Any status code other than 201 leads to a device reboot. Server should handle invalid `auth_key`, duplicate registrations, etc.

-   **`/api/v1/tank/status` (POST)**
    *   **Purpose:** Used by the tank node to send current status and sensor readings to the server for storage and display in client applications.
    *   **Inferred Input Schema (JSON Body):**
        ```json
        {
          "temperature": "number",       // Current water temperature
          "ph": "number",                // Current water pH level
          "light_state": "integer",      // Current logical light state (0 for OFF, 1 for ON)
          "firmware_version": "string"   // Current firmware version
        }
        ```
    *   **Authentication:** Requires `Authorization: Bearer <access_token>` header, validated by the server.
    *   **Expected Response:** Status code 200 OK on successful receipt and processing. Server should store the status data associated with the authenticated `tank_id`. Other status codes lead to the payload being re-queued by the node.

-   **`/api/v1/tank/command` (GET)**
    *   **Purpose:** Used by the tank node to poll the server for pending commands queued for its specific `tank_id`.
    *   **Inferred Input:** None (GET request). The server identifies the target tank based on the `access_token` in the Authorization header.
    *   **Authentication:** Requires `Authorization: Bearer <access_token>` header, validated by the server.
    *   **Expected Response Schema (JSON Body - Status 200 OK):**
        ```json
        // If a command is pending for the authenticated tank_id
        {
          "command_id": "string",        // Unique identifier for the command (generated by server)
          "command_payload": "string",   // The command name (e.g., "LIGHT_ON", "FEED_NOW")
          "params": "object"             // Optional parameters for the command (e.g., {"duration": 5})
        }
        // If no command is pending
        {} // Empty object
        ```
    *   **Error Response:** Any status code other than 200 results in an empty response object `{}` being processed by the node. Server should handle invalid tokens with 401.

-   **`/api/v1/tank/command/ack` (POST)**
    *   **Purpose:** Used by the tank node to acknowledge that a command has been received and processed, reporting the outcome (success or failure) to the server.
    *   **Inferred Input Schema (JSON Body):**
        ```json
        {
          "command_id": "string",        // The ID of the command being acknowledged
          "success": "boolean"           // True if the command was processed successfully, false otherwise
        }
        ```
    *   **Authentication:** Requires `Authorization: Bearer <access_token>` header, validated by the server.
    *   **Expected Response:** Status code 200 OK on successful receipt and processing (e.g., marking the command as completed). Other status codes lead to the acknowledgment being re-queued by the node. Server should handle invalid tokens or command IDs.

## 7. Device Workflow (Node)

1.  **Boot-up:**
    *   Initialize hardware (set relay to OFF state).
    *   Initialize watchdog timer.
    *   Load persistent state (`state.json`) to restore light state.
    *   Load persistent configuration (`config.json`) for `tank_id` and `access_token`.
2.  **Network Connection:**
    *   Connect to the configured Wi-Fi network (`SSID`, `PASSWORD`) with multiple retries. If connection fails after retries, reboot.
3.  **Registration/Authentication:**
    *   If no `tank_id` or `access_token` is loaded, or if an API request fails with a 401 (token expired), attempt to register with the server using the `AUTH_KEY`.
    *   On successful registration, save the received `tank_id` and `access_token` to `config.json`.
    *   If registration fails, reboot.
4.  **Main Loop:**
    *   Continuously feed the watchdog timer.
    *   Perform garbage collection and check free memory, rebooting if critically low.
    *   **Status Reporting:** Every `STATUS_INTERVAL` seconds, gather sensor data and light state, and send a status update to the server via `/api/v1/tank/status`. If the request fails (not 200), enqueue the payload in `status_queue.json`.
    *   **Command Polling:** Every `COMMAND_POLL_MS` milliseconds, poll the server for commands via `/api/v1/tank/command`.
        *   If a command is received (`command_id` present), parse the `command_payload` and `params`.
        *   Execute the corresponding hardware control function (e.g., `handle_light`, `handle_feed`).
        *   Acknowledge the command's success or failure to the server via `/api/v1/tank/command/ack`. If the acknowledgment request fails (not 200), enqueue the acknowledgment in `ack_queue.json`.
    *   **Queue Flushing:** Every `FLUSH_INTERVAL_MS` milliseconds, attempt to resend queued status updates and command acknowledgments to the server. Successful requests are removed from their respective queues.
    *   Short sleep interval (`time.sleep(0.1)`) to yield execution.

## 8. API Server Responsibilities

The central API server is responsible for:

-   **Tank Management:** Registering new tanks, issuing unique `tank_id`s, managing `access_token`s (generation, validation, expiry, refresh).
-   **Data Ingestion:** Receiving and storing status updates from tank nodes (`/api/v1/tank/status`).
-   **Command Queueing:** Receiving command requests (presumably from client applications) and queueing them for specific tanks.
-   **Command Delivery:** Serving pending commands to tank nodes when they poll (`/api/v1/tank/command`).
-   **Command Acknowledgment Processing:** Receiving and processing command acknowledgments from nodes (`/api/v1/tank/command/ack`), updating command status.
-   **Data Serving:** Providing APIs for client applications (web, mobile) to retrieve tank lists, current status, historical data, and issue new commands.
-   **Authentication and Authorization:** Validating the `auth_key` during registration and `access_token` for all subsequent authenticated requests. Ensuring commands are issued to the correct tanks.
-   **Metrics Exposure:** Providing an endpoint (typically `/metrics`) in Prometheus exposition format for monitoring.

## 9. Hardware Components & Control (Node)

-   **Light Relay (Pin 15):** Controlled via `machine.Pin`. Uses inverted logic (active-low): Driving the pin `low` turns the light ON (`RELAY_ON = 0`), driving it `high` turns the light OFF (`RELAY_OFF = 1`). State is persisted.
-   **Continuous Rotation Servo (Pin 4):** Controlled via `machine.PWM`. Used for the feeder.
    *   `SERV_FREQ = 50` Hz PWM frequency.
    *   `STOP_DUTY = 77` (example duty cycle for stopping).
    *   `FORWARD_DUTY = 100` (example duty cycle for forward rotation).
    *   `REVERSE_DUTY = 50` (example duty cycle for reverse rotation).
    *   Commands specify duration and optionally direction/duty cycle.
-   **Temperature Sensor (Placeholder):** Currently returns a hardcoded value. Future requires integration of a real sensor (e.g., DS18B20).
-   **pH Sensor (Placeholder):** Currently returns a hardcoded value. Future requires integration of a real sensor.

## 10. Configuration & Persistence

-   **Node (`config.json`):** Stores `tank_id` and `access_token`. Loaded on boot, saved after successful registration.
-   **Node (`state.json`):** Stores the logical `light_state`. Loaded on boot to restore the relay state, saved after light state changes.
-   **Node (`status_queue.json`):** Stores status payloads that failed to send immediately.
-   **Node (`ack_queue.json`):** Stores command acknowledgments that failed to send immediately.
-   **Node (Hardcoded):** Configuration constants (SSID, PASSWORD, BASE_URL, etc.) are currently hardcoded in `main.py`.
-   **Server:** Configuration for database connections, API keys for external services, logging settings, etc. (Configuration method TBD).

## 11. Robustness and Self-Healing (Node)

-   **Watchdog Timer:** Resets the device if the `feed()` function is not called within `WDT_TIMEOUT_MS`. `feed()` is called frequently in the main loop and during blocking operations like network requests.
-   **Wi-Fi Retries:** Attempts to connect to Wi-Fi multiple times before giving up and resetting.
-   **Offline Queues:** Ensures status updates and command acknowledgments are not lost due to temporary server or network issues, resending them later.
-   **Memory Check:** Reboots if free memory drops below `MIN_HEAP_BYTES`.
-   **Token Refresh:** Attempts to re-register and obtain a new token if a 401 Unauthorized response is received.
-   **Error Handling:** Basic try-except blocks are used for JSON file operations and network requests to prevent crashes, often resulting in re-queueing or device reset on critical failures.

## 12. Commands Handled (Node)

The `COMMAND_MAP` dictionary defines the recognized commands and their handlers on the node:

-   `LIGHT_ON`: Calls `handle_light(True)` to turn the light ON.
-   `LIGHT_OFF`: Calls `handle_light(False)` to turn the light OFF.
-   `FEED_NOW`: Calls `handle_feed(params)` to activate the servo for feeding based on provided parameters (duration, direction, duty).

## 13. Monitoring with Prometheus Metrics

Prometheus metrics should be implemented to monitor the health and performance of the system.

-   **API Server Metrics:** The server should expose a `/metrics` endpoint in Prometheus exposition format. Key metrics should include:
    *   Request duration and count per API endpoint (e.g., `http_requests_total`, `http_request_duration_seconds`).
    *   Number of active tank connections/registered tanks.
    *   Queue sizes for pending commands.
    *   Errors/failure rates per API endpoint.
    *   Database connection pool utilization.
    *   Server resource usage (CPU, memory, network I/O).
-   **Tank Node Metrics (Future/Optional):** While directly exposing a `/metrics` endpoint from a MicroPython ESP32 is challenging due to resource constraints, a future enhancement could involve pushing key node-level metrics to a Prometheus Pushgateway or including them in the regular status updates for the server to aggregate. Potential node metrics:
    *   Wi-Fi signal strength.
    *   Free memory (`gc.mem_free()`).
    *   Watchdog resets count.
    *   API request success/failure counts.
    *   Queue sizes (status, ack).
    *   Command execution success/failure counts.

## 14. Future Considerations / Potential Enhancements

-   **OTA Updates:** Implement a mechanism for Over-The-Air firmware updates controlled via the server.
-   **Additional Sensors:** Integrate drivers and reporting for real temperature (e.g., DS18B20) and pH sensors. Add support for other relevant sensors (e.g., water level, flow).
-   **More Commands:** Add handlers for controlling other potential hardware (e.g., pumps, heaters, cooling fans) or configuring device settings remotely.
-   **Improved Error Handling:** More granular error reporting from the node to the server, differentiating between network issues, hardware failures, and command parsing errors.
-   **Remote Configuration:** Allow server to update node configuration parameters (e.g., API endpoint, timing intervals, default light schedule) without requiring a full firmware update.
-   **Security:** Implement mutual authentication (TLS client certificates) for API communication. Encrypt sensitive configurations (AUTH_KEY, PASSWORD) on the filesystem.for scheduled tasks directly on the device.
-   **Client Applications:** Develop web and mobile applications to interact with the API server, providing user interfaces for monitoring and control.
-   **Server Scalability:** Design the server architecture and database to handle a large number of concurrent tank nodes and client requests.

---

This PRD provides a detailed overview of the current Tank Controller Node firmware, its interaction with the API server, and potential areas for future development, including monitoring capabilities.

--- 