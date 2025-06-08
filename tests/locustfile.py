from locust import HttpUser, task, between
import random
import uuid

# Base URL for the FastAPI application (assuming it's running locally)
# You might need to change this if your Docker setup exposes it differently
# e.g., http://localhost:8000
API_URL = "http://localhost:8000"

# These should ideally come from environment variables or a config file
AUTH_KEY = "super_secret_tank_psk"
ADMIN_API_KEY = "supersecretgrafanakey123"

class TankUser(HttpUser):
    wait_time = between(1, 5) # Simulate users waiting 1-5 seconds between tasks
    host = API_URL
    tanks = {} # Store registered tank_ids and tokens

    def on_start(self):
        """
        On start, each user registers a unique tank.
        """
        self.register_new_tank()

    def register_new_tank(self):
        tank_name = f"LocustTank_{uuid.uuid4().hex[:8]}"
        register_payload = {
            "auth_key": AUTH_KEY,
            "tank_name": tank_name,
            "location": "Locust Lab",
            "firmware_version": "1.0.0"
        }
        with self.client.post("/api/v1/tank/register", json=register_payload, catch_response=True) as response:
            if response.status_code == 201:
                self.tank_id = response.json()["tank_id"]
                self.token = response.json()["access_token"]
                self.tanks[self.tank_id] = self.token
                response.success()
                print(f"Registered new tank: {tank_name} with ID {self.tank_id}")
            else:
                response.failure(f"Failed to register tank: {response.text}")

    @task(3) # This task will be picked 3 times as often as tasks with no weight
    def send_tank_status(self):
        if not hasattr(self, 'tank_id'):
            self.register_new_tank()
            return # Skip this run if registration failed

        status_payload = {
            "temperature": round(random.uniform(20.0, 30.0), 2),
            "ph": round(random.uniform(6.0, 8.0), 2),
            "light_state": random.choice([True, False]),
            "firmware_version": "1.0.1"
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.post(f"/api/v1/tank/{self.tank_id}/status", json=status_payload, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401: # Token expired or invalid
                print(f"Tank {self.tank_id} token expired, re-registering...")
                self.register_new_tank()
                response.failure("Token expired")
            else:
                response.failure(f"Status update failed: {response.text}")

    @task(2)
    def poll_for_command(self):
        if not hasattr(self, 'tank_id'):
            self.register_new_tank()
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.get(f"/api/v1/tank/{self.tank_id}/command", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                command = response.json()
                if command and command.get("command_id"):
                    # Acknowledge command if received
                    ack_payload = {"command_id": command["command_id"], "success": random.choice([True, False])}
                    self.client.post(f"/api/v1/tank/{self.tank_id}/command/acknowledge", json=ack_payload, headers=headers)
                response.success()
            elif response.status_code == 401:
                print(f"Tank {self.tank_id} token expired during command poll, re-registering...")
                self.register_new_tank()
                response.failure("Token expired")
            else:
                response.failure(f"Command poll failed: {response.text}")

    @task(1)
    def get_command_history(self):
        if not hasattr(self, 'tank_id'):
            self.register_new_tank()
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.get(f"/api/v1/tank/{self.tank_id}/commands/history", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                print(f"Tank {self.tank_id} token expired during history, re-registering...")
                self.register_new_tank()
                response.failure("Token expired")
            else:
                response.failure(f"Command history failed: {response.text}")

    @task(0.5) # Less frequent task for admin operations
    def send_admin_command(self):
        # Select a random tank from already registered tanks
        if not self.tanks:
            self.register_new_tank() # Ensure at least one tank is registered
            if not self.tanks: return # If still no tanks, something is wrong

        target_tank_id = random.choice(list(self.tanks.keys()))
        command_payload = random.choice(["light_on", "light_off", "feed_now"])
        admin_command_payload = {
            "tank_id": target_tank_id,
            "command_payload": command_payload
        }
        headers = {"x-api-key": ADMIN_API_KEY}
        with self.client.post("/api/v1/admin/send_command_to_tank", json=admin_command_payload, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin command failed: {response.text}") 