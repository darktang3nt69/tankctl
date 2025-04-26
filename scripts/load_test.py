"""
Load test script for TankCTL.

This script simulates multiple tanks executing commands concurrently to test:
- Celery task handling per tank
- Command execution throughput
- System stability under load
- Task queue performance
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
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TankSimulator:
    def __init__(self, base_url: str = "http://localhost:8000", tank_id: int = None):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)
        self.token = None
        self.tank_id = tank_id
        self.tank_name = None
        self.command_latencies: List[float] = []
        self.commands_executed = 0
        self.commands_failed = 0
        
    async def register(self) -> bool:
        """Register a test tank."""
        try:
            self.tank_name = f"load-test-tank-{self.tank_id}"
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
            logger.info(f"Tank {self.tank_name} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register tank {self.tank_name}: {str(e)}")
            return False
            
    async def execute_command(self, command: str, timeout: int = 60) -> bool:
        """Schedule and execute a command, measuring latency."""
        if not self.token:
            if not await self.register():
                return False
                
        try:
            start_time = time.time()
            
            # Schedule command
            response = await self.session.post(
                f"{self.base_url}/commands",
                json={
                    "command": command,
                    "timeout": timeout
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            data = response.json()
            command_id = data["id"]
            
            # Simulate command execution
            execution_time = random.uniform(0.5, 2.0)
            await asyncio.sleep(execution_time)
            
            # Randomly fail some commands (10% failure rate)
            success = random.random() > 0.1
            
            # Acknowledge command completion
            response = await self.session.post(
                f"{self.base_url}/commands/ack",
                json={
                    "command_id": command_id,
                    "success": success
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            
            end_time = time.time()
            latency = end_time - start_time
            self.command_latencies.append(latency)
            
            if success:
                self.commands_executed += 1
                logger.debug(f"Tank {self.tank_name} executed command {command_id} in {latency:.2f}s")
            else:
                self.commands_failed += 1
                logger.debug(f"Tank {self.tank_name} failed command {command_id} in {latency:.2f}s")
            
            return success
            
        except Exception as e:
            logger.error(f"Tank {self.tank_name} command execution error: {str(e)}")
            self.commands_failed += 1
            return False
            
    def get_stats(self) -> Dict:
        """Get execution statistics for this tank."""
        if not self.command_latencies:
            return {
                "tank_id": self.tank_id,
                "tank_name": self.tank_name,
                "commands_executed": 0,
                "commands_failed": 0,
                "avg_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
                "p95_latency": 0
            }
            
        return {
            "tank_id": self.tank_id,
            "tank_name": self.tank_name,
            "commands_executed": self.commands_executed,
            "commands_failed": self.commands_failed,
            "avg_latency": statistics.mean(self.command_latencies),
            "min_latency": min(self.command_latencies),
            "max_latency": max(self.command_latencies),
            "p95_latency": statistics.quantiles(self.command_latencies, n=20)[-1]
        }

class LoadTester:
    def __init__(
        self,
        num_tanks: int = 10,
        commands_per_tank: int = 20,
        base_url: str = "http://localhost:8000"
    ):
        self.num_tanks = num_tanks
        self.commands_per_tank = commands_per_tank
        self.base_url = base_url
        self.tanks: List[TankSimulator] = []
        
    async def setup_tanks(self):
        """Create and register all tanks."""
        self.tanks = [
            TankSimulator(self.base_url, tank_id=i)
            for i in range(self.num_tanks)
        ]
        
        # Register all tanks concurrently
        await asyncio.gather(
            *(tank.register() for tank in self.tanks)
        )
        
    async def run_tank_commands(self, tank: TankSimulator):
        """Run all commands for a single tank."""
        commands = [
            f"echo 'Test command {i} from {tank.tank_name}'"
            for i in range(self.commands_per_tank)
        ]
        
        for command in commands:
            await tank.execute_command(command)
            # Random delay between commands (100ms to 1s)
            await asyncio.sleep(random.uniform(0.1, 1.0))
            
    async def run_load_test(self):
        """Run the complete load test."""
        logger.info(f"Starting load test with {self.num_tanks} tanks, "
                   f"{self.commands_per_tank} commands per tank")
        
        # Setup tanks
        await self.setup_tanks()
        
        # Record start time
        start_time = time.time()
        
        # Run all tank commands concurrently
        await asyncio.gather(
            *(self.run_tank_commands(tank) for tank in self.tanks)
        )
        
        # Calculate total execution time
        total_time = time.time() - start_time
        
        # Collect and display statistics
        total_commands = 0
        total_failures = 0
        all_latencies = []
        
        print("\nLoad Test Results:")
        print("=" * 80)
        print(f"Total execution time: {total_time:.2f}s")
        print(f"Number of tanks: {self.num_tanks}")
        print(f"Commands per tank: {self.commands_per_tank}")
        print("\nPer-Tank Statistics:")
        print("-" * 80)
        print(f"{'Tank Name':<20} {'Commands':<10} {'Failed':<10} "
              f"{'Avg (s)':<10} {'Min (s)':<10} {'Max (s)':<10} {'P95 (s)':<10}")
        print("-" * 80)
        
        for tank in self.tanks:
            stats = tank.get_stats()
            total_commands += stats["commands_executed"]
            total_failures += stats["commands_failed"]
            all_latencies.extend(tank.command_latencies)
            
            print(
                f"{stats['tank_name']:<20} "
                f"{stats['commands_executed']:<10} "
                f"{stats['commands_failed']:<10} "
                f"{stats['avg_latency']:.2f}{'s':<8} "
                f"{stats['min_latency']:.2f}{'s':<8} "
                f"{stats['max_latency']:.2f}{'s':<8} "
                f"{stats['p95_latency']:.2f}{'s':<8}"
            )
            
        print("\nOverall Statistics:")
        print("-" * 80)
        print(f"Total commands executed: {total_commands}")
        print(f"Total commands failed: {total_failures}")
        print(f"Overall success rate: {(total_commands/(total_commands+total_failures))*100:.1f}%")
        print(f"Average latency: {statistics.mean(all_latencies):.2f}s")
        print(f"95th percentile latency: {statistics.quantiles(all_latencies, n=20)[-1]:.2f}s")
        print(f"Commands per second: {(total_commands+total_failures)/total_time:.1f}")

async def main():
    # Run load test with 10 tanks, 20 commands each
    tester = LoadTester(num_tanks=10, commands_per_tank=20)
    await tester.run_load_test()

if __name__ == "__main__":
    asyncio.run(main()) 