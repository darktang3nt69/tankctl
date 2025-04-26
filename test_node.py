import asyncio
import aiohttp
import json
from datetime import datetime

class TankNode:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.token = None
        self.tank_id = None
        self.name = f"Test-Tank-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    async def register(self):
        """Register the tank with the API server."""
        async with aiohttp.ClientSession() as session:
            data = {
                "name": self.name,
                "key": "7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM="
            }
            async with session.post(f"{self.api_url}/register", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.token = result["token"]
                    self.tank_id = result["tank_id"]
                    print(f"Successfully registered tank {self.name} (ID: {self.tank_id})")
                    return True
                else:
                    print(f"Failed to register tank: {await response.text()}")
                    return False

    async def send_status(self):
        """Send tank status to the API server."""
        if not self.token:
            print("Tank not registered")
            return False

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                "status": {
                    "temperature": 25.5,
                    "ph": 7.2,
                    "turbidity": 0.8
                }
            }
            async with session.post(f"{self.api_url}/status", headers=headers, json=data) as response:
                if response.status == 200:
                    print("Successfully sent status update")
                    return True
                else:
                    print(f"Failed to send status: {await response.text()}")
                    return False

    async def get_commands(self):
        """Get pending commands from the API server."""
        if not self.token:
            print("Tank not registered")
            return None

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.get(f"{self.api_url}/commands/{self.tank_id}", headers=headers) as response:
                if response.status == 200:
                    commands = await response.json()
                    return commands
                else:
                    print(f"Failed to get commands: {await response.text()}")
                    return None

    async def acknowledge_command(self, command_id):
        """Acknowledge a command completion."""
        if not self.token:
            print("Tank not registered")
            return False

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with session.post(f"{self.api_url}/commands/{command_id}/ack", headers=headers) as response:
                if response.status == 200:
                    print(f"Successfully acknowledged command {command_id}")
                    return True
                else:
                    print(f"Failed to acknowledge command: {await response.text()}")
                    return False

async def main():
    # Create and register a tank node
    node = TankNode()
    if not await node.register():
        return

    # Send initial status
    await node.send_status()

    # Main loop - simulate tank operation
    try:
        while True:
            # Send status update
            await node.send_status()

            # Check for commands
            commands = await node.get_commands()
            if commands:
                for command in commands:
                    print(f"Received command: {command}")
                    # Simulate command execution
                    await asyncio.sleep(2)
                    # Acknowledge command completion
                    await node.acknowledge_command(command["id"])

            # Wait before next update
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping tank node simulation...")

if __name__ == "__main__":
    asyncio.run(main()) 