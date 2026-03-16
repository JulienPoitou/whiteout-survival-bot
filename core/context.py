"""
Game Context Manager
Maintains state and memory for intelligent decision making
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from config import GameConfig


class ScreenType(str, Enum):
    """Known screen types"""
    HOME = "home"
    WORLD = "world"
    GATHER = "gather"
    INTEL = "intel"
    ARENA = "arena"
    ALLIANCE = "alliance"
    TRAINING = "training"
    UNKNOWN = "unknown"


class ActionType(str, Enum):
    """Action types"""
    TAP = "tap"
    SWIPE = "swipe"
    WAIT = "wait"
    NAVIGATE = "navigate"
    ERROR = "error"


@dataclass
class MarchInfo:
    """Information about an active march"""
    id: int
    target_type: str  # "gather", "attack", "reinforce"
    departure_time: datetime
    return_time: datetime
    troops: Dict[str, int] = field(default_factory=dict)
    
    @property
    def is_returned(self) -> bool:
        return datetime.now() >= self.return_time
    
    @property
    def time_remaining(self) -> timedelta:
        return max(timedelta(0), self.return_time - datetime.now())


@dataclass
class ResourceTargets:
    """Resource gathering targets"""
    meat: int = 5
    wood: int = 5
    coal: int = 5
    iron: int = 5
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "meat": self.meat,
            "wood": self.wood,
            "coal": self.coal,
            "iron": self.iron
        }


@dataclass
class ActionRecord:
    """Record of an action for history tracking"""
    timestamp: datetime
    action_type: ActionType
    screen: ScreenType
    details: Dict[str, Any] = field(default_factory=dict)


class GameContext:
    """
    Maintains game state and memory
    
    Features:
    - Current screen tracking
    - Action history
    - Active marches monitoring
    - Resource targets
    - Error tracking
    - Session statistics
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self.current_screen: ScreenType = ScreenType.UNKNOWN
        self.last_action: Optional[ActionRecord] = None
        self.last_screenshot_time: Optional[datetime] = None
        
        # Marches
        self.active_marches: List[MarchInfo] = []
        
        # Resources
        self.resource_targets = ResourceTargets()
        self.resources_gathered = {"meat": 0, "wood": 0, "coal": 0, "iron": 0}
        
        # Error tracking
        self.consecutive_errors = 0
        self.last_error_time: Optional[datetime] = None
        self.error_history: List[Dict[str, Any]] = []
        
        # Action history
        self.action_history: List[ActionRecord] = []
        self.max_history = 100
        
        # Session stats
        self.session_start = datetime.now()
        self.actions_count = 0
        self.screenshots_count = 0
        
        # Navigation
        self.navigation_stack: List[ScreenType] = []
        
        self.logger.info("GameContext initialized")

    def update_screen(self, screen_type: ScreenType):
        """Update current screen type"""
        if self.current_screen != screen_type:
            self.logger.info(f"Screen changed: {self.current_screen.value} → {screen_type.value}")
            self.current_screen = screen_type
            self.last_screenshot_time = datetime.now()

    def record_action(
        self,
        action_type: str,  # Changed from ActionType to str for simplicity
        details: Optional[Dict[str, Any]] = None
    ):
        """Record an action for history and statistics"""
        record = ActionRecord(
            timestamp=datetime.now(),
            action_type=action_type,
            screen=self.current_screen,
            details=details or {}
        )

        self.last_action = record
        self.action_history.append(record)
        self.actions_count += 1

        # Trim history if needed
        if len(self.action_history) > self.max_history:
            self.action_history = self.action_history[-self.max_history:]

        # Reset error counter on successful action
        self.consecutive_errors = 0

        self.logger.debug(f"Action recorded: {action_type} ({self.actions_count} total)")

    def record_error(self, error_type: str, message: str):
        """Record an error for tracking"""
        now = datetime.now()
        
        self.error_history.append({
            "timestamp": now,
            "type": error_type,
            "message": message,
            "screen": self.current_screen.value
        })
        
        self.consecutive_errors += 1
        self.last_error_time = now
        
        self.logger.warning(f"Error recorded: {error_type} - {message} (consecutive: {self.consecutive_errors})")

    def add_march(
        self,
        target_type: str,
        duration_seconds: int,
        troops: Optional[Dict[str, int]] = None
    ) -> MarchInfo:
        """Add a new active march"""
        now = datetime.now()
        march = MarchInfo(
            id=len(self.active_marches) + 1,
            target_type=target_type,
            departure_time=now,
            return_time=now + timedelta(seconds=duration_seconds),
            troops=troops or {}
        )
        
        self.active_marches.append(march)
        self.logger.info(f"March added: {target_type}, returns in {duration_seconds}s")
        
        return march

    def remove_returned_marches(self) -> List[MarchInfo]:
        """Remove and return marches that have returned"""
        returned = [m for m in self.active_marches if m.is_returned]
        self.active_marches = [m for m in self.active_marches if not m.is_returned]
        
        if returned:
            self.logger.info(f"{len(returned)} march(es) returned")
        
        return returned

    def increment_resource(self, resource_type: str, amount: int = 1):
        """Track gathered resource"""
        if resource_type in self.resources_gathered:
            self.resources_gathered[resource_type] += amount
            self.logger.debug(f"Resource gathered: {resource_type} +{amount}")

    def should_take_break(
        self,
        max_actions: int = 50,
        break_interval_minutes: int = 30
    ) -> bool:
        """Check if bot should take a break"""
        # Check action count since last break
        recent_actions = [
            a for a in self.action_history
            if a.timestamp > datetime.now() - timedelta(minutes=break_interval_minutes)
        ]
        
        if len(recent_actions) >= max_actions:
            self.logger.info(f"Action limit reached ({max_actions}), break recommended")
            return True
        
        # Check consecutive errors
        if self.consecutive_errors >= 5:
            self.logger.warning(f"Too many consecutive errors ({self.consecutive_errors}), break recommended")
            return True
        
        return False

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        uptime = datetime.now() - self.session_start
        
        return {
            "uptime": str(uptime).split('.')[0],
            "actions": self.actions_count,
            "screenshots": self.screenshots_count,
            "active_marches": len(self.active_marches),
            "errors": len(self.error_history),
            "consecutive_errors": self.consecutive_errors,
            "resources_gathered": self.resources_gathered.copy(),
            "current_screen": self.current_screen.value
        }

    def push_navigation_state(self):
        """Push current screen to navigation stack"""
        self.navigation_stack.append(self.current_screen)
        self.logger.debug(f"Navigation push: {self.current_screen.value}")

    def pop_navigation_state(self) -> Optional[ScreenType]:
        """Pop and return previous screen state"""
        if self.navigation_stack:
            previous = self.navigation_stack.pop()
            self.logger.debug(f"Navigation pop: {previous.value}")
            return previous
        return None

    def clear_navigation_stack(self):
        """Clear navigation stack"""
        self.navigation_stack.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export context as dictionary for AI analysis"""
        return {
            "current_screen": self.current_screen.value,
            "last_action": self.last_action.action_type.value if self.last_action else None,
            "active_marches": len(self.active_marches),
            "resources_gathered": self.resources_gathered,
            "target_resources": self.resource_targets.to_dict(),
            "consecutive_errors": self.consecutive_errors,
            "session_stats": self.get_session_stats()
        }
