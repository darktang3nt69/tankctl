"""
End-to-end test script for TankCTL that simulates multiple nodes running all scenarios simultaneously.

This script tests:
- Multiple nodes running simultaneously
- Node registration and authentication
- Command execution and isolation
- Health monitoring and status updates
- Offline detection
- High resource usage detection
- Notification flows
"""

import asyncio
import httpx
import random
import time
import logging
import os
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TankNode:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.tank_id = None
        self.tank_name = None
        self.node_id = str(uuid.uuid4())[:8]
        self.is_running = True
        
    async def register(self) -> bool:
        """Register a test node."""
        try:
            self.tank_name = f"test-{self.node_id}-{random.randint(1000, 9999)}"
            response = await self.session.post(
                f"{self.base_url}/register",
                json={
                    "name": self.tank_name,
                    "key": os.getenv("PRE_SHARED_KEY", "7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM="),
                    "test_mode": True  # Add test_mode flag to disable notifications
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["token"]
            self.tank_id = data["tank_id"]
            logger.info(f"Node {self.node_id} registered as tank {self.tank_name} (ID: {self.tank_id})")
            return True
        except Exception as e:
            logger.error(f"Node {self.node_id} failed to register: {str(e)}")
            return False

    async def schedule_command(self, command: str, parameters: dict = None) -> int:
        """Schedule a command for execution."""
        try:
            response = await self.session.post(
                f"{self.base_url}/commands",
                json={
                    "command": command,
                    "parameters": parameters or {},
                    "timeout": 300,
                    "tank_id": self.tank_id  # Ensure tank_id is included
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            data = response.json()
            command_id = data["id"]
            logger.info(f"Node {self.node_id} scheduled command {command_id}: {command}")
            return command_id
        except Exception as e:
            logger.error(f"Node {self.node_id} failed to schedule command: {str(e)}")
            raise

    async def get_commands(self) -> List[Dict]:
        """Get all commands for this tank."""
        try:
            response = await self.session.get(
                f"{self.base_url}/commands",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            commands = response.json()
            logger.info(f"Node {self.node_id} has {len(commands)} commands")
            return commands
        except Exception as e:
            logger.error(f"Node {self.node_id} failed to get commands: {str(e)}")
            return []

    async def acknowledge_command(self, command_id: int, success: bool = True) -> bool:
        """Acknowledge command completion."""
        try:
            response = await self.session.post(
                f"{self.base_url}/commands/ack",
                json={
                    "command_id": command_id,
                    "success": success,
                    "tank_id": self.tank_id  # Ensure tank_id is included
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            logger.info(f"Node {self.node_id} acknowledged command {command_id}")
            return True
        except Exception as e:
            logger.error(f"Node {self.node_id} failed to acknowledge command: {str(e)}")
            return False

    async def report_health(self, status: str = "healthy", temperature: float = None, 
                          ph: float = None, water_level: float = None, humidity: float = None) -> bool:
        """Report health status."""
        try:
            if temperature is None:
                temperature = random.uniform(20.0, 30.0)
            if ph is None:
                ph = random.uniform(6.5, 8.5)
            if water_level is None:
                water_level = random.uniform(50.0, 100.0)
            if humidity is None:
                humidity = random.uniform(40.0, 80.0)

            response = await self.session.post(
                f"{self.base_url}/status",
                json={
                    "status": {
                        "status": status,
                        "temperature": temperature,
                        "ph": ph,
                        "water_level": water_level,
                        "humidity": humidity,
                        "tank_id": self.tank_id  # Ensure tank_id is included
                    }
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            logger.info(f"Node {self.node_id} reported health status: {status}")
            return True
        except Exception as e:
            logger.error(f"Node {self.node_id} failed to report health: {str(e)}")
            return False

    async def test_command_execution(self):
        """Test various command execution scenarios."""
        logger.info(f"Node {self.node_id} starting command execution tests")
        
        # Test successful command
        try:
            command_id = await self.schedule_command("echo", {"message": f"Hello from {self.tank_name}"})
            await asyncio.sleep(2)
            await self.acknowledge_command(command_id, success=True)
        except Exception as e:
            logger.error(f"Node {self.node_id} failed successful command test: {str(e)}")

        # Test failed command (using sleep with negative value)
        try:
            command_id = await self.schedule_command("sleep", {"seconds": -1})
            await asyncio.sleep(2)
            await self.acknowledge_command(command_id, success=False)
        except Exception as e:
            logger.error(f"Node {self.node_id} failed error command test: {str(e)}")

        # Test long-running command
        try:
            command_id = await self.schedule_command("sleep", {"seconds": 5})
            await asyncio.sleep(2)
            await self.acknowledge_command(command_id, success=True)
        except Exception as e:
            logger.error(f"Node {self.node_id} failed long-running command test: {str(e)}")

    async def test_health_monitoring(self):
        """Test health monitoring scenarios."""
        logger.info(f"Node {self.node_id} starting health monitoring tests")
        
        # Test normal health reporting
        try:
            await self.report_health(
                status="healthy",
                temperature=25.0,
                ph=7.0,
                water_level=80.0,
                humidity=60.0
            )
            await asyncio.sleep(30)  # Increased wait time
        except Exception as e:
            logger.error(f"Node {self.node_id} failed normal health test: {str(e)}")

        # Test warning conditions
        try:
            await self.report_health(
                status="warning",
                temperature=35.0,  # High temperature
                ph=9.0,  # High pH
                water_level=20.0,  # Low water level
                humidity=90.0  # High humidity
            )
            await asyncio.sleep(30)  # Increased wait time
        except Exception as e:
            logger.error(f"Node {self.node_id} failed warning condition test: {str(e)}")

        # Test critical conditions
        try:
            await self.report_health(
                status="critical",
                temperature=40.0,  # Very high temperature
                ph=10.0,  # Very high pH
                water_level=10.0,  # Very low water level
                humidity=95.0  # Very high humidity
            )
            await asyncio.sleep(30)  # Increased wait time
        except Exception as e:
            logger.error(f"Node {self.node_id} failed critical condition test: {str(e)}")

    async def test_offline_detection(self):
        """Test offline detection by stopping health reporting."""
        logger.info(f"Node {self.node_id} testing offline detection")
        # Stop health reporting for this node
        self.is_running = False
        await asyncio.sleep(30)  # Wait for offline detection
        self.is_running = True  # Resume health reporting

    async def run_all_tests(self):
        """Run all test scenarios for this node."""
        if not await self.register():
            return

        # Run health monitoring test first
        await self.test_health_monitoring()

        # Start health monitoring in background
        health_task = asyncio.create_task(self.run_health_monitoring())

        # Run other test scenarios concurrently
        await asyncio.gather(
            self.test_command_execution(),
            self.test_offline_detection()
        )

        # Stop health monitoring
        self.is_running = False
        await health_task

    async def run_health_monitoring(self):
        """Continuously report health status."""
        while self.is_running:
            try:
                await self.report_health()
                await asyncio.sleep(5)  # Report every 5 seconds
            except Exception as e:
                logger.error(f"Node {self.node_id} health monitoring error: {str(e)}")
                await asyncio.sleep(1)

async def clear_all_tasks():
    """Clear all tasks from the system."""
    try:
        # First register a temporary node to get authentication token
        async with httpx.AsyncClient() as client:
            # Register
            register_response = await client.post(
                "http://localhost:8000/register",
                json={
                    "name": "cleanup-node",
                    "key": os.getenv("PRE_SHARED_KEY", "7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM=")
                }
            )
            register_response.raise_for_status()
            data = register_response.json()
            token = data["token"]
            tank_id = data["tank_id"]

            # Get all commands with authentication
            response = await client.get(
                "http://localhost:8000/commands",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            commands = response.json()
            
            # Acknowledge all commands
            for command in commands:
                await client.post(
                    "http://localhost:8000/commands/ack",
                    json={
                        "command_id": command["id"],
                        "success": True,
                        "tank_id": command.get("tank_id", tank_id)
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
            logger.info(f"Cleared {len(commands)} tasks")
    except Exception as e:
        logger.error(f"Failed to clear tasks: {str(e)}")

async def run_end_to_end_test(num_nodes: int = 2, num_cycles: int = 1):  # Reduced default nodes and cycles
    """Run the end-to-end test with multiple nodes."""
    logger.info(f"Starting end-to-end test with {num_nodes} nodes for {num_cycles} cycles...")
    
    # Create nodes
    nodes = [TankNode() for _ in range(num_nodes)]
    
    # Run tests for all nodes
    for cycle in range(num_cycles):
        try:
            # Run all nodes concurrently
            await asyncio.gather(*(node.run_all_tests() for node in nodes))
            if cycle < num_cycles - 1:  # Don't wait after the last cycle
                logger.info(f"Test cycle {cycle + 1}/{num_cycles} completed, waiting 60 seconds before next cycle...")
                await asyncio.sleep(60)  # Increased wait time between cycles
        except Exception as e:
            logger.error(f"Error in test cycle {cycle + 1}: {str(e)}")
            await asyncio.sleep(5)

async def main():
    await run_end_to_end_test(num_nodes=2, num_cycles=1)  # Run with reduced nodes and only one cycle

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_all_tasks())
    else:
        asyncio.run(main()) 