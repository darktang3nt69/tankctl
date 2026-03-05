"""
Light schedule domain model.

Represents a daily light schedule for a device.
"""

from dataclasses import dataclass
from datetime import time, datetime
from typing import Optional


@dataclass
class LightSchedule:
    """
    Light schedule domain model.
    
    Defines when a device's light should turn on and off daily.
    """
    
    device_id: str
    """Device identifier"""
    
    on_time: time
    """Daily time to turn light on (e.g., 18:00)"""
    
    off_time: time
    """Daily time to turn light off (e.g., 06:00)"""
    
    enabled: bool = True
    """Whether schedule is active"""
    
    created_at: Optional[datetime] = None
    """When schedule was created"""
    
    updated_at: Optional[datetime] = None
    """When schedule was last modified"""
    
    def is_light_on_at(self, check_time: time) -> bool:
        """
        Determine if light should be on at a given time.
        
        Handles schedules that cross midnight (e.g., 18:00 - 06:00).
        
        Args:
            check_time: Time to check
            
        Returns:
            True if light should be on, False otherwise
        """
        if not self.enabled:
            return False
        
        # Schedule crosses midnight (e.g., 18:00 - 06:00)
        if self.on_time > self.off_time:
            return check_time >= self.on_time or check_time < self.off_time
        
        # Normal schedule (e.g., 06:00 - 18:00)
        return self.on_time <= check_time < self.off_time
    
    def get_current_desired_state(self) -> str:
        """
        Get the desired light state based on current time.
        
        Returns:
            "on" or "off"
        """
        now = datetime.now().time()
        return "on" if self.is_light_on_at(now) else "off"
