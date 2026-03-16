"""
Whiteout Survival Bot - Main Entry Point
Hybrid AI Bot with Template Matching + OCR + Vision
"""

import sys
import time
import random
import logging
from datetime import datetime
from pathlib import Path

from loguru import logger

from config import Config, GameConfig
from adb.controller import ADBController
from core.context import GameContext, ScreenType, ActionType
from core.vision_facade import VisionFacade
from tasks.gather import GatherTask


def setup_logging():
    """Configure logging"""
    Config.ensure_dirs()
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=Config.LOG_LEVEL,
        colorize=True
    )
    
    # File handler
    logger.add(
        Config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level=Config.LOG_LEVEL,
        rotation="1 day",
        retention="7 days"
    )
    
    return logger


class WhiteoutBot:
    """
    Main bot orchestrator
    
    Coordinates all tasks and manages the bot lifecycle
    """

    def __init__(self):
        self.logger = logging.getLogger("WhiteoutBot")
        
        # Initialize components
        self.adb = ADBController()
        self.context = GameContext()
        self.vision = VisionFacade()
        
        # State
        self.running = False
        self.start_time = None
        
        # Preload templates
        self._preload_templates()

    def _preload_templates(self):
        """Preload critical templates into cache"""
        templates = [
            # Navigation
            "furnace_icon",
            "world_map_ui",
            "world_map_button",
            "home_button",
            "search_button",
            
            # Resources
            "resource_meat_icon",
            "resource_wood_icon",
            "resource_coal_icon",
            "resource_iron_icon",
            
            # Actions
            "gather_deploy_button",
            "march_button",
        ]
        
        self.vision.preload_templates(templates)
        self.logger.info(f"Preloaded {len(templates)} templates")

    def start(self) -> bool:
        """
        Start the bot
        
        Returns:
            True if started successfully
        """
        self.logger.info("=" * 50)
        self.logger.info("Starting Whiteout Survival Bot v1.0")
        self.logger.info("=" * 50)
        
        # Connect to ADB
        self.logger.info(f"Connecting to {self.adb.device}...")
        
        if not self.adb.connect():
            self.logger.error("Failed to connect to emulator")
            return False
        
        # Check connection
        if not self.adb.check_connection():
            self.logger.error("Device not connected")
            return False
        
        self.logger.info("✓ Connected to emulator")
        
        # Check AI availability
        if self.vision.ai_analyzer.is_available():
            self.logger.info(f"✓ AI available (model: {Config.OLLAMA_MODEL})")
        else:
            self.logger.warning("⚠ AI not available (Ollama not running?)")
        
        self.running = True
        self.start_time = datetime.now()
        
        self.logger.info("Bot started successfully")
        return True

    def stop(self):
        """Stop the bot"""
        self.running = False
        self.logger.info("Stopping bot...")
        
        # Disconnect ADB
        self.adb.disconnect()
        
        # Log final stats
        self._log_final_stats()

    def run(self):
        """Main bot loop"""
        if not self.start():
            return
        
        try:
            self.logger.info("Starting main loop...")
            
            while self.running:
                # Check if break needed
                if self.context.should_take_break():
                    self._take_break()
                    continue
                
                # Main loop iteration
                self._loop_iteration()
                
                # Random delay between iterations
                delay = random.uniform(
                    Config.CHECK_INTERVAL_MIN,
                    Config.CHECK_INTERVAL_MAX
                )
                self.logger.debug(f"Waiting {delay:.1f}s before next iteration")
                time.sleep(delay)
                
        except KeyboardInterrupt:
            self.logger.info("\nInterrupted by user")
        finally:
            self.stop()

    def _loop_iteration(self):
        """Single iteration of the main loop"""
        self.logger.debug("--- New iteration ---")
        
        # Take screenshot
        screenshot = self.adb.screenshot()
        
        if not screenshot:
            self.logger.error("Failed to capture screenshot")
            time.sleep(5)
            return
        
        self.context.screenshots_count += 1
        
        # Detect screen type
        screen_type = self.vision.detect_screen_type(screenshot, self.context)
        self.logger.debug(f"Current screen: {screen_type.value}")
        
        # Check for anomalies
        anomalies = self.vision.ai_analyzer.detect_anomalies(screenshot)
        
        if anomalies:
            self.logger.warning(f"Anomalies detected: {anomalies}")
            self.context.record_error("anomaly", f"Detected: {anomalies}")
            
            # Handle specific anomalies
            if "popup" in anomalies:
                self._handle_popup()
            return
        
        # Decide action based on screen type
        if screen_type == ScreenType.HOME:
            self._handle_home_screen(screenshot)
        elif screen_type == ScreenType.WORLD:
            self._handle_world_screen(screenshot)
        else:
            self._handle_unknown_screen(screenshot, screen_type)

    def _handle_home_screen(self, screenshot):
        """Handle actions on home screen"""
        self.logger.debug("On home screen")
        
        # Check daily rewards, etc.
        # For now, just navigate to gather
        task = GatherTask(self.adb, self.vision, self.context)
        success = task.run()
        
        if not success:
            self.logger.warning("Gather task failed")

    def _handle_world_screen(self, screenshot):
        """Handle actions on world map"""
        self.logger.debug("On world map")
        
        # Look for resources to gather
        task = GatherTask(self.adb, self.vision, self.context)
        success = task.run()
        
        if not success:
            # Return home
            self._navigate_home()

    def _handle_unknown_screen(self, screenshot, screen_type):
        """Handle unknown screen type"""
        self.logger.warning(f"Unknown screen: {screen_type.value}")
        
        # Ask AI what to do
        decision = self.vision.analyze_and_decide(screenshot, self.context)
        
        if decision.get("action") == "navigate":
            # Try to navigate home
            self._navigate_home()
        else:
            # Wait and see
            time.sleep(2)

    def _navigate_home(self):
        """Navigate to home screen"""
        screenshot = self.adb.screenshot()
        
        if screenshot:
            nav_action = self.vision.navigate_to_screen(
                screenshot,
                ScreenType.HOME,
                self.context
            )
            
            if nav_action and nav_action.get("action") == "tap":
                self.adb.tap(nav_action["x"], nav_action["y"])
                time.sleep(2)

    def _handle_popup(self):
        """Handle popup/advertisement"""
        self.logger.info("Handling popup...")
        
        # Try to find close button
        close_templates = ["popup_close", "popup_x", "close_button"]
        
        screenshot = self.adb.screenshot()
        
        if screenshot:
            for template in close_templates:
                result = self.vision.find_element(screenshot, template)
                
                if result and result.found:
                    self.logger.info(f"Found popup close button at ({result.x}, {result.y})")
                    self.adb.tap(result.x, result.y)
                    time.sleep(1)
                    return
            
            # Fallback: tap approximate close position (top-right)
            self.logger.debug("Close button not found, tapping fallback position")
            self.adb.tap(680, 50)
            time.sleep(1)

    def _take_break(self):
        """Take a break (anti-ban measure)"""
        duration = random.uniform(
            Config.BREAK_DURATION_MIN,
            Config.BREAK_DURATION_MAX
        )
        
        self.logger.info(f"Taking break for {duration:.0f} seconds...")
        time.sleep(duration)
        
        # Reset action counter
        self.context.consecutive_errors = 0
        self.logger.info("Break finished, resuming...")

    def _log_final_stats(self):
        """Log final statistics"""
        stats = self.context.get_session_stats()
        vision_stats = self.vision.get_stats()
        
        self.logger.info("=" * 50)
        self.logger.info("Session Statistics")
        self.logger.info("=" * 50)
        self.logger.info(f"Uptime: {stats['uptime']}")
        self.logger.info(f"Actions: {stats['actions']}")
        self.logger.info(f"Screenshots: {stats['screenshots']}")
        self.logger.info(f"Active marches: {stats['active_marches']}")
        self.logger.info(f"Errors: {stats['errors']}")
        self.logger.info(f"Resources gathered: {stats['resources_gathered']}")
        self.logger.info(f"Vision stats: {vision_stats}")
        self.logger.info("=" * 50)


def main():
    """Entry point"""
    # Setup logging
    setup_logging()
    
    # Create and run bot
    bot = WhiteoutBot()
    bot.run()


if __name__ == "__main__":
    main()
