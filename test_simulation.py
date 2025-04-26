#!/usr/bin/env python3
import os
import sys
import time
import random
import requests
import json
import subprocess
from typing import Dict, List
import asyncio
import aiohttp
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "http://192.168.1.100:8000"
PRE_SHARED_KEY = "7NZ4nKirAYm4vGqWVY936MdnDDsSTrIe8Fy5z8iQ/hM" # From settings.py
NUM_NODES = 4
TEST_DURATION_MINUTES = 5

class NodeSimulator:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.name = f"Tank-{node_id}"
        self.token = None
        self.session = aiohttp.ClientSession()
        self.commands = [
            {"command": "feed_now", "parameters": {"amount": 1, "duration": 5}},
            {"command": "feed_now", "parameters": {"amount": 2, "duration": 10}},
            {"command": "feed_now", "parameters": {"amount": 3, "duration": 15}},
            {"command": "feed_now", "parameters": {"amount": 4, "duration": 20}},
            {"command": "water_change", "parameters": {"amount": 10}},
            {"command": "water_change", "parameters": {"amount": 20}},
            {"command": "light_on", "parameters": {"duration": 60}},
            {"command": "light_off", "parameters": {}},
        ]

    async def register(self) -> bool:
        """Register the node and get an access token."""
        try:
            response = await self.session.post(
                f"{API_BASE_URL}/register",
                json={"name": self.name, "key": PRE_SHARED_KEY}
            )
            if response.status == 200:
                data = await response.json()
                self.token = data["token"]
                print(f"Node {self.name} registered successfully")
                return True
            else:
                print(f"Failed to register node {self.name}: {await response.text()}")
                return False
        except Exception as e:
            print(f"Error registering node {self.name}: {str(e)}")
            return False

    async def send_status(self) -> bool:
        """Send a status update for the node."""
        if not self.token:
            return False

        status = {
            "temperature": round(random.uniform(20.0, 30.0), 1),
            "ph": round(random.uniform(6.5, 8.5), 1),
            "water_level": round(random.uniform(80.0, 100.0), 1),
            "is_healthy": random.random() > 0.1  # 90% chance of being healthy
        }

        try:
            response = await self.session.post(
                f"{API_BASE_URL}/status",
                json=status,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status == 200:
                print(f"Node {self.name} status updated successfully")
                return True
            else:
                print(f"Failed to update status for node {self.name}: {await response.text()}")
                return False
        except Exception as e:
            print(f"Error updating status for node {self.name}: {str(e)}")
            return False

    async def queue_command(self) -> bool:
        """Queue a random command for the node."""
        if not self.token:
            return False

        command = random.choice(self.commands)
        try:
            response = await self.session.post(
                f"{API_BASE_URL}/commands",
                json=command,
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status == 200:
                print(f"Node {self.name} queued command: {command['command']}")
                return True
            else:
                print(f"Failed to queue command for node {self.name}: {await response.text()}")
                return False
        except Exception as e:
            print(f"Error queuing command for node {self.name}: {str(e)}")
            return False

    async def close(self):
        """Close the session."""
        await self.session.close()

async def run_simulation():
    """Run the simulation with multiple nodes."""
    # Create nodes
    nodes = [NodeSimulator(i+1) for i in range(NUM_NODES)]
    
    # Register all nodes
    registration_tasks = [node.register() for node in nodes]
    await asyncio.gather(*registration_tasks)
    
    # Run simulation for specified duration
    end_time = datetime.now() + timedelta(minutes=TEST_DURATION_MINUTES)
    
    while datetime.now() < end_time:
        # Each node performs actions
        for node in nodes:
            # Randomly choose between sending status or queuing command
            if random.random() < 0.7:  # 70% chance of status update
                await node.send_status()
            else:
                await node.queue_command()
            
            # Add some delay between actions
            await asyncio.sleep(random.uniform(1, 3))
    
    # Clean up
    for node in nodes:
        await node.close()

def cleanup_and_restart():
    """Clean up existing volumes and restart the stack."""
    print("Cleaning up existing volumes and containers...")
    subprocess.run(["docker", "compose", "down", "-v"], check=True)
    
    print("Building fresh images...")
    subprocess.run(["docker", "compose", "build"], check=True)
    
    print("Starting the stack...")
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    
    print("Waiting for services to be ready...")
    time.sleep(10)  # Give services time to start

def main():
    """Main function to run the test simulation."""
    try:
        # Clean up and restart
        cleanup_and_restart()
        
        # Run the simulation
        print("Starting simulation...")
        asyncio.run(run_simulation())
        
        print("Simulation completed successfully!")
        
    except Exception as e:
        print(f"Error during simulation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 