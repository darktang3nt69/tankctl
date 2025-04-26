"""
Multiple node simulation test script for TankCTL.

This script tests:
- Multiple nodes running simultaneously
- Command isolation between tanks
- Concurrent command execution
"""

import asyncio
import httpx
import random
import time
from datetime import datetime, timedelta
import logging
import json
import os
from typing import List, Dict
import uuid

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
        
    async def register(self) -> bool:
        """Register a test node."""
        try:
            self.tank_name = f"node-{self.node_id}-{random.randint(1000, 9999)}"
            response = await self.session.post(
                f"{self.base_url}/register",
                json={
                    "name": self.tank_name,
                    "key": os.getenv("PRE_SHARED_KEY", "7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM=")
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
                    "timeout": 300
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
                    "success": success
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            logger.info(f"Node {self.node_id} acknowledged command {command_id}")
            return True
        except Exception as e:
            logger.error(f"Node {self.node_id} failed to acknowledge command: {str(e)}")
            return False

    async def run_test_sequence(self):
        """Run a sequence of tests for this node."""
        if not await self.register():
            return

        # Schedule some commands
        commands = [
            ("echo", {"message": f"Hello from {self.tank_name}"}),
            ("sleep", {"seconds": 5}),
            ("echo", {"message": f"Goodbye from {self.tank_name}"})
        ]

        for cmd, params in commands:
            try:
                command_id = await self.schedule_command(cmd, params)
                await asyncio.sleep(2)  # Wait between commands
                await self.acknowledge_command(command_id, success=True)
            except Exception as e:
                logger.error(f"Node {self.node_id} failed in test sequence: {str(e)}")

        # Verify command isolation
        all_commands = await self.get_commands()
        for cmd in all_commands:
            if cmd["tank_id"] != self.tank_id:
                logger.error(f"Node {self.node_id} found command for another tank: {cmd}")

async def run_multiple_nodes(num_nodes: int = 3):
    """Run multiple nodes simultaneously."""
    logger.info(f"Starting {num_nodes} nodes...")
    
    # Create and register nodes
    nodes = [TankNode() for _ in range(num_nodes)]
    await asyncio.gather(*[node.register() for node in nodes])
    
    # Run test sequences concurrently
    await asyncio.gather(*[node.run_test_sequence() for node in nodes])
    
    logger.info("All nodes completed their test sequences")

async def main():
    await run_multiple_nodes(3)

if __name__ == "__main__":
    asyncio.run(main()) 