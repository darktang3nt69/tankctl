"""
Command execution test script for TankCTL.

This script tests various command execution scenarios:
- Successful commands
- Failed commands
- Long-running commands
- Command timeouts
- Command retries and notifications
"""

import asyncio
import httpx
import random
import time
from datetime import datetime, timedelta
import logging
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.tank_id = None
        self.tank_name = None
        
    async def register(self) -> bool:
        """Register a test node."""
        try:
            self.tank_name = f"command-test-node-{random.randint(1000, 9999)}"
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
            logger.info("Test node registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register test node: {str(e)}")
            return False
        
    async def schedule_command(self, command: str, parameters: dict = None) -> int:
        """Schedule a command for execution."""
        try:
            response = await self.session.post(
                f"{self.base_url}/commands",
                json={
                    "command": command,
                    "parameters": parameters or {},
                    "timeout": 300  # 5 minutes default timeout
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            data = response.json()
            command_id = data["id"]  # Changed from command_id to id
            logger.info(f"Command scheduled with ID: {command_id}")
            return command_id
        except Exception as e:
            logger.error(f"Failed to schedule command: {str(e)}")
            raise
            
    async def acknowledge_command(self, command_id: int, success: bool = True) -> bool:
        """Acknowledge command completion."""
        if not self.token:
            raise Exception("Test node not registered")
            
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
            logger.info(f"Command {command_id} acknowledged")
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge command: {str(e)}")
            return False
            
    async def test_successful_command(self):
        """Test successful command execution."""
        logger.info("Testing successful command...")
        command_id = await self.schedule_command("echo", {"message": "Hello World"})
        
        # Wait for command to complete
        await asyncio.sleep(5)
        
        # Acknowledge command
        await self.acknowledge_command(command_id, success=True)
            
    async def test_failed_command(self):
        """Test command failure scenario."""
        logger.info("Testing failed command...")
        command_id = await self.schedule_command("invalid_command")
        
        # Wait for command to fail
        await asyncio.sleep(5)
        
        # Acknowledge command
        await self.acknowledge_command(command_id, success=False)
            
    async def test_long_running_command(self):
        """Test long-running command."""
        logger.info("Testing long-running command...")
        command_id = await self.schedule_command("sleep", {"seconds": 10})
        
        # Wait for command to start
        await asyncio.sleep(5)
        
        # Acknowledge command
        await self.acknowledge_command(command_id, success=True)
            
    async def test_command_timeout(self):
        """Test command timeout."""
        logger.info("Testing command timeout...")
        command_id = await self.schedule_command("sleep", {"seconds": 30})
        
        # Wait for command to timeout
        await asyncio.sleep(10)
        
        # Acknowledge command
        await self.acknowledge_command(command_id, success=False)
            
    async def test_command_retries(self):
        """Test command retries and notifications."""
        logger.info("Testing command retries and notifications...")
        
        # Schedule a command that will fail
        command_id = await self.schedule_command("sleep", {"seconds": 30})
        
        # Wait for command to fail and retry
        await asyncio.sleep(5)
        
        # Acknowledge command
        await self.acknowledge_command(command_id, success=False)
        
        # Wait for retries to complete
        await asyncio.sleep(300)  # 5 minutes for all retries
        
        # Check command status
        response = await self.session.get(
            f"{self.base_url}/commands/{command_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        command_status = response.json()
        logger.info(f"Final command status: {command_status}")
            
    async def run_tests(self):
        """Run all command execution tests."""
        logger.info("Starting command execution tests...")
        
        # Register test node first
        if not await self.register():
            return
            
        # Run all tests
        await self.test_successful_command()
        await self.test_failed_command()
        await self.test_long_running_command()
        await self.test_command_timeout()
        await self.test_command_retries()
        
        logger.info("All tests completed!")

async def main():
    tester = CommandTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main()) 