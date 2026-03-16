"""
Base Task class for bot actions
All tasks should inherit from this class
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from core.context import GameContext, ScreenType
from core.vision_facade import VisionFacade
from adb.controller import ADBController


class TaskState:
    """Task execution states"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class BaseTask(ABC):
    """
    Abstract base class for all bot tasks
    
    Provides:
    - State management
    - Error handling
    - Logging
    - Context access
    """

    def __init__(
        self,
        name: str,
        adb: ADBController,
        vision: VisionFacade,
        context: GameContext
    ):
        self.name = name
        self.adb = adb
        self.vision = vision
        self.context = context
        self.logger = logging.getLogger(f"Task.{name}")
        
        self.state = TaskState.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        
        # Statistics
        self.executions_count = 0
        self.success_count = 0
        self.fail_count = 0

    @abstractmethod
    def execute(self) -> bool:
        """
        Execute the task
        
        Returns:
            True if successful, False if failed
        """
        pass

    def run(self) -> bool:
        """
        Wrapper for execute with state management
        
        Returns:
            Success status
        """
        self.start_time = datetime.now()
        self.state = TaskState.RUNNING
        self.executions_count += 1
        
        self.logger.info(f"Starting task: {self.name}")
        
        try:
            success = self.execute()
            
            if success:
                self.state = TaskState.COMPLETED
                self.success_count += 1
                self.logger.info(f"Task completed: {self.name}")
            else:
                self.state = TaskState.FAILED
                self.fail_count += 1
                self.logger.warning(f"Task failed: {self.name}")
            
            return success
            
        except Exception as e:
            self.state = TaskState.FAILED
            self.fail_count += 1
            self.error_message = str(e)
            self.logger.error(f"Task error: {self.name} - {e}")
            return False
            
        finally:
            self.end_time = datetime.now()

    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        return {
            "name": self.name,
            "state": self.state,
            "executions": self.executions_count,
            "successes": self.success_count,
            "fails": self.fail_count,
            "success_rate": self.success_count / max(1, self.executions_count),
            "last_error": self.error_message
        }


class TaskError(Exception):
    """Task execution error"""
    pass


class NavigationError(TaskError):
    """Navigation failed"""
    pass


class ValidationError(TaskError):
    """Validation failed"""
    pass
