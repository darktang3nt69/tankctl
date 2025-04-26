"""
Node simulation script for testing TankCTL workflows.

This script simulates a node's behavior including:
- Registration
- Command execution
- Health reporting
- Offline scenarios
"""

import asyncio
import httpx
import random
import time
import json
import os
from datetime import datetime, timedelta
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeSimulator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.node_id: Optional[str] = None
        self.token: Optional[str] = None
        self.session = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        self.last_seen = datetime.utcnow()
        
    async def register(self) -> bool:
        """Register the node with the controller."""
        try:
            response = await self.session.post(
                f"{self.base_url}/register",
                json={
                    "name": f"simulated-node-{random.randint(1000, 9999)}",
                    "key": os.getenv("PRE_SHARED_KEY", "7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM=")
                }
            )
            response.raise_for_status()
            data = response.json()
            self.node_id = data["tank_id"]
            self.token = data["token"]
            logger.info(f"Node registered successfully with ID: {self.node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register node: {str(e)}")
            return False
            
    async def send_health_report(self) -> bool:
        """Send a health report to the controller."""
        if not self.token:
            logger.error("Node not registered")
            return False
            
        try:
            self.last_seen = datetime.utcnow()
            response = await self.session.post(
                f"{self.base_url}/status",
                json={
                    "temperature": round(random.uniform(20.0, 30.0), 1),
                    "ph": round(random.uniform(6.5, 8.5), 1),
                    "water_level": round(random.uniform(80.0, 100.0), 1),
                    "is_healthy": random.random() > 0.1  # 90% chance of being healthy
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            logger.info("Health report sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send health report: {str(e)}")
            return False
            
    async def execute_command(self, command: str) -> bool:
        """Execute a command and report the result."""
        if not self.token:
            logger.error("Node not registered")
            return False
            
        try:
            # Simulate command execution
            logger.info(f"Executing command: {command}")
            await asyncio.sleep(random.uniform(1, 5))  # Simulate command execution time
            
            # Randomly fail 20% of commands
            if random.random() < 0.2:
                logger.warning("Command execution failed")
                return False
                
            logger.info("Command executed successfully")
            return True
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return False
            
    async def run(self, duration: int = 300):
        """Run the node simulation for the specified duration."""
        if not await self.register():
            return
            
        self.is_running = True
        start_time = time.time()
        
        while self.is_running and (time.time() - start_time) < duration:
            try:
                # Send health report every 30 seconds
                if (datetime.utcnow() - self.last_seen).total_seconds() >= 30:
                    await self.send_health_report()
                    
                # Randomly go offline for 1-2 minutes (10% chance)
                if random.random() < 0.1:
                    logger.warning("Simulating node going offline")
                    await asyncio.sleep(random.uniform(60, 120))
                    logger.info("Node back online")
                    
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in node simulation: {str(e)}")
                await asyncio.sleep(5)
                
    async def stop(self):
        """Stop the node simulation."""
        self.is_running = False
        await self.session.aclose()

async def main():
    # Create and run multiple simulated nodes
    nodes = [NodeSimulator() for _ in range(3)]
    tasks = [node.run() for node in nodes]
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Stopping node simulations...")
        for node in nodes:
            await node.stop()

if __name__ == "__main__":
    asyncio.run(main()) 