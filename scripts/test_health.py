"""
Health monitoring test script for TankCTL.

This script tests various health monitoring scenarios:
- Node health reporting
- Offline detection
- Notification triggers
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

class HealthTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.tank_id = None
        self.tank_name = None
        
    async def register(self) -> bool:
        """Register a test node."""
        try:
            self.tank_name = f"health-test-node-{random.randint(1000, 9999)}"
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
            
    async def get_node_status(self) -> dict:
        """Get the current status of the node."""
        if not self.token:
            raise Exception("Test node not registered")
            
        try:
            response = await self.session.get(
                f"{self.base_url}/status/{self.tank_name}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get node status: {str(e)}")
            raise
            
    async def test_health_reporting(self):
        """Test normal health reporting."""
        logger.info("Testing normal health reporting...")
        
        # Send a series of health reports
        for i in range(5):
            try:
                response = await self.session.post(
                    f"{self.base_url}/status",
                    json={
                        "status": {
                            "temperature": round(random.uniform(20.0, 30.0), 1),
                            "humidity": round(random.uniform(40.0, 60.0), 1),
                            "ph": round(random.uniform(6.5, 8.5), 1),
                            "water_level": round(random.uniform(80.0, 100.0), 1),
                            "is_healthy": True
                        }
                    },
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                response.raise_for_status()
                logger.info(f"Health report {i+1}/5 sent successfully")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Failed to send health report: {str(e)}")
                
    async def test_offline_detection(self):
        """Test offline detection by stopping health reports."""
        logger.info("Testing offline detection...")
        
        # Get initial status
        initial_status = await self.get_node_status()
        logger.info(f"Initial node status: {initial_status}")
        
        # Wait for offline detection (should trigger after 60 seconds)
        logger.info("Waiting for offline detection...")
        await asyncio.sleep(70)
        
        # Check final status
        final_status = await self.get_node_status()
        logger.info(f"Final node status: {final_status}")
        
    async def test_high_resource_usage(self):
        """Test high resource usage detection."""
        logger.info("Testing high resource usage detection...")
        
        # Send reports with high resource usage
        for i in range(3):
            try:
                response = await self.session.post(
                    f"{self.base_url}/status",
                    json={
                        "status": {
                            "temperature": round(random.uniform(35.0, 40.0), 1),  # High temperature
                            "humidity": round(random.uniform(80.0, 90.0), 1),  # High humidity
                            "ph": round(random.uniform(4.0, 5.0), 1),  # Low pH
                            "water_level": round(random.uniform(20.0, 30.0), 1),  # Low water level
                            "is_healthy": False
                        }
                    },
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                response.raise_for_status()
                logger.info(f"High resource report {i+1}/3 sent successfully")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Failed to send high resource report: {str(e)}")
                
    async def run_tests(self):
        """Run all health monitoring tests."""
        logger.info("Starting health monitoring tests...")
        
        # Register test node first
        if not await self.register():
            return
            
        # Test normal health reporting
        await self.test_health_reporting()
        
        # Test offline detection
        await self.test_offline_detection()
        
        # Test high resource usage
        await self.test_high_resource_usage()
        
        logger.info("All health monitoring tests completed!")

async def main():
    tester = HealthTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main()) 