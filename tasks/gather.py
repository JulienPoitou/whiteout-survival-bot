"""
Gather Task - Farm resources from the world map
"""

import random
import time
from typing import Optional, Dict, List

from tasks.base import BaseTask, TaskError, NavigationError
from core.context import ScreenType, ActionType


class GatherTask(BaseTask):
    """
    Resource gathering task
    
    Flow:
    1. Navigate to world map
    2. Find resource node (meat, wood, coal, iron)
    3. Send march to gather
    4. Wait for confirmation
    5. Return to home
    """

    # Resource templates to search for
    RESOURCE_TEMPLATES = {
        "meat": ["resource_meat_icon", "meat_node"],
        "wood": ["resource_wood_icon", "wood_node"],
        "coal": ["resource_coal_icon", "coal_node"],
        "iron": ["resource_iron_icon", "iron_node"],
    }
    
    # Search button to find resources
    SEARCH_BUTTON = "search_button"
    GATHER_BUTTON = "gather_deploy_button"
    MARCH_BUTTON = "march_button"
    
    # Target resource levels (adjust based on account progress)
    TARGET_LEVELS = {
        "meat": 5,
        "wood": 5,
        "coal": 5,
        "iron": 5,
    }

    def __init__(self, adb, vision, context, resource_type: str = None):
        super().__init__("Gather", adb, vision, context)
        self.target_resource = resource_type
        self.max_marches = 5  # Maximum active gathering marches

    def execute(self) -> bool:
        """Execute gather task"""
        try:
            # Step 1: Check if we have available marches
            active_marches = len(self.context.active_marches)
            if active_marches >= self.max_marches:
                self.logger.info("Max marches reached, skipping gather")
                return True  # Not an error, just skip
            
            # Step 2: Navigate to world map
            if not self._navigate_to_world():
                raise NavigationError("Failed to navigate to world map")
            
            # Step 3: Find resource node
            resource = self.target_resource or self._choose_target_resource()
            self.logger.info(f"Searching for {resource} node...")
            
            resource_pos = self._find_resource_node(resource)
            if not resource_pos:
                self.logger.warning(f"No {resource} node found")
                return False
            
            # Step 4: Tap on resource node
            self.logger.info(f"Tapping on resource at ({resource_pos['x']}, {resource_pos['y']})")
            self.adb.smart_tap(resource_pos['x'], resource_pos['y'], f"resource_{resource}")
            time.sleep(1)
            
            # Step 5: Click gather button
            gather_result = self.vision.find_element(
                self._screenshot(),
                self.GATHER_BUTTON
            )
            
            if gather_result and gather_result.found:
                self.adb.smart_tap(gather_result.x, gather_result.y, "gather_button")
                time.sleep(1)
            else:
                self.logger.warning("Gather button not found")
                return False
            
            # Step 6: Send march
            march_result = self.vision.find_element(
                self._screenshot(),
                self.MARCH_BUTTON
            )
            
            if march_result and march_result.found:
                self.adb.smart_tap(march_result.x, march_result.y, "march_button")
                time.sleep(2)
                
                # Add to active marches (estimated duration)
                self.context.add_march(
                    target_type="gather",
                    duration_seconds=60,  # Adjust based on tech/research
                    troops={"tier_1": 100}
                )
                
                self.context.increment_resource(resource, 1)
                self.logger.info(f"Gather march sent for {resource}")
            else:
                self.logger.warning("March button not found")
                return False
            
            # Step 7: Return home
            self._navigate_home()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Gather task failed: {e}")
            self.context.record_error("gather", str(e))
            return False

    def _navigate_to_world(self) -> bool:
        """Navigate to world map"""
        screenshot = self._screenshot()
        
        # Detect current screen
        current_screen = self.vision.detect_screen_type(screenshot, self.context)
        
        if current_screen == ScreenType.WORLD:
            self.logger.debug("Already on world map")
            return True
        
        if current_screen != ScreenType.HOME:
            # Navigate home first
            self._navigate_home()
            screenshot = self._screenshot()
        
        # Find world map button
        world_button = self.vision.find_element(screenshot, "world_map_button")
        
        if world_button and world_button.found:
            self.adb.smart_tap(world_button.x, world_button.y, "world_map_button")
            time.sleep(2)  # Wait for transition
            self.context.update_screen(ScreenType.WORLD)
            return True
        
        # Try alternative: use coordinates from config
        self.logger.debug("World button not found, using fallback coordinates")
        self.adb.smart_tap(650, 100, "world_button_fallback")  # Approximate world button position
        time.sleep(2)
        self.context.update_screen(ScreenType.WORLD)
        return True

    def _navigate_home(self) -> bool:
        """Navigate back to home screen"""
        screenshot = self._screenshot()
        current_screen = self.vision.detect_screen_type(screenshot, self.context)
        
        if current_screen == ScreenType.HOME:
            return True
        
        # Try back arrow first (top-left corner with dead zone handling)
        self.logger.info("Navigating home via back arrow...")
        back_success = self.adb.tap_back_arrow()
        
        if back_success:
            time.sleep(1)
            self.context.update_screen(ScreenType.HOME)
            return True
        
        # Fallback: find home button
        home_button = self.vision.find_element(screenshot, "home_button")
        
        if home_button and home_button.found:
            self.adb.smart_tap(home_button.x, home_button.y, "home_button")
            time.sleep(1)
            self.context.update_screen(ScreenType.HOME)
            return True
        
        # Last resort: tap approximate home position
        self.logger.debug("Home button not found, using fallback")
        self.adb.smart_tap(50, 50, "home_fallback")
        time.sleep(1)
        self.context.update_screen(ScreenType.HOME)
        return True

    def _choose_target_resource(self) -> str:
        """Choose which resource to gather based on targets"""
        # Simple implementation: random choice
        # Could be improved to prioritize based on needs
        resources = list(self.TARGET_LEVELS.keys())
        return random.choice(resources)

    def _find_resource_node(self, resource_type: str) -> Optional[Dict[str, int]]:
        """
        Find resource node on world map
        
        Returns:
            Dict with x, y coordinates or None
        """
        templates = self.RESOURCE_TEMPLATES.get(resource_type, [])
        screenshot = self._screenshot()
        
        # Try each template for this resource
        for template in templates:
            result = self.vision.find_element(screenshot, template)
            
            if result and result.found:
                self.logger.debug(f"Found {resource_type} at ({result.x}, {result.y})")
                return {"x": result.x, "y": result.y}
        
        # If not found, try AI-assisted search
        self.logger.debug(f"{resource_type} not found via template, trying AI...")
        
        # Swipe to search more area
        self._swipe_map()
        time.sleep(1)
        
        # Try again after swipe
        screenshot = self._screenshot()
        for template in templates:
            result = self.vision.find_element(screenshot, template)
            if result and result.found:
                return {"x": result.x, "y": result.y}
        
        return None

    def _swipe_map(self):
        """Swipe the world map to reveal new areas"""
        # Random swipe direction
        directions = [
            (200, 600, 500, 600),  # Left to right
            (500, 600, 200, 600),  # Right to left
            (360, 400, 360, 800),  # Top to bottom
            (360, 800, 360, 400),  # Bottom to top
        ]
        
        x1, y1, x2, y2 = random.choice(directions)
        self.adb.swipe(x1, y1, x2, y2, duration=500)

    def _screenshot(self):
        """Take screenshot"""
        self.context.screenshots_count += 1
        return self.adb.screenshot()
