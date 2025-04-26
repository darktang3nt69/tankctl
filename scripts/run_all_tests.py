"""
Main test runner script for TankCTL.

This script runs all test scenarios in sequence:
1. Node simulation
2. Command execution tests
3. Health monitoring tests
"""

import asyncio
import logging
from simulate_node import NodeSimulator
from test_commands import CommandTester
from test_health import HealthTester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_all_tests():
    """Run all test scenarios in sequence."""
    logger.info("Starting TankCTL test suite...")
    
    # Step 1: Start node simulation
    logger.info("Starting node simulation...")
    simulator = NodeSimulator()
    simulator_task = asyncio.create_task(simulator.run(duration=600))  # Run for 10 minutes
    
    # Wait for nodes to register
    await asyncio.sleep(5)
    
    # Step 2: Run command execution tests
    logger.info("Running command execution tests...")
    command_tester = CommandTester()
    await command_tester.run_tests()
    
    # Step 3: Run health monitoring tests
    logger.info("Running health monitoring tests...")
    health_tester = HealthTester()
    await health_tester.run_tests()
    
    # Stop the node simulation
    logger.info("Stopping node simulation...")
    await simulator.stop()
    simulator_task.cancel()
    
    logger.info("All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 