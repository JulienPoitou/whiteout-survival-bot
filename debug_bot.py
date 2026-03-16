#!/usr/bin/env python
"""
Autonomous Learning Bot for Whiteout Survival
Version debug avec logs complets
"""

import sys
import time
import random
import logging
from datetime import datetime
from pathlib import Path

# Setup logging FIRST
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "bot_debug.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("BotDebug")
logger.info("=" * 60)
logger.info("🤖 Autonomous Bot - DEBUG MODE")
logger.info("=" * 60)

try:
    from config import Config
    logger.info("✓ Config loaded")
    Config.ensure_dirs()
    logger.info("✓ Dirs created")
    
    from adb.controller import ADBController
    logger.info("✓ ADB module loaded")
    
    adb = ADBController()
    logger.info(f"✓ ADB created: {adb.device}")
    
    if not adb.connect():
        logger.error("✗ ADB connection failed")
        sys.exit(1)
    logger.info("✓ ADB connected")
    
    from core.context import GameContext, ScreenType
    logger.info("✓ GameContext loaded")
    context = GameContext()
    logger.info("✓ GameContext created")
    
    from core.vision_facade import VisionFacade
    logger.info("✓ VisionFacade loaded")
    vision = VisionFacade()
    logger.info("✓ VisionFacade created")
    
    from knowledge.base import KnowledgeBase
    logger.info("✓ KnowledgeBase loaded")
    knowledge = KnowledgeBase()
    logger.info(f"✓ KnowledgeBase created ({len(knowledge.elements)} elements)")
    
    logger.info("=" * 60)
    logger.info("🚀 Starting main loop...")
    logger.info("=" * 60)
    
    iteration = 0
    start_time = time.time()
    
    while True:
        iteration += 1
        logger.info(f"\n--- Iteration {iteration} ---")
        
        try:
            # Screenshot
            logger.debug("Taking screenshot...")
            screenshot = adb.screenshot()
            
            if not screenshot:
                logger.error("Screenshot failed!")
                time.sleep(5)
                continue
            
            logger.info(f"✓ Screenshot: {screenshot.size}")
            context.screenshots_count += 1
            
            # Detect screen
            logger.debug("Detecting screen type...")
            screen_type = vision.detect_screen_type(screenshot, context)
            logger.info(f"Screen type: {screen_type.value}")
            context.update_screen(screen_type)
            
            # Simple action: tap random safe zone
            if screen_type == ScreenType.UNKNOWN:
                logger.info("Unknown screen - tapping safe zone")
                # Tap center-bottom (safe area)
                adb.smart_tap(360, 900, "safe_zone")
                time.sleep(2)
            
            # Check elapsed time
            elapsed = time.time() - start_time
            if elapsed > 300:  # Stop after 5 minutes
                logger.info("5 minutes elapsed, stopping")
                break
            
            # Delay between iterations
            delay = random.uniform(3, 6)
            logger.debug(f"Waiting {delay:.1f}s")
            time.sleep(delay)
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Iteration error: {e}", exc_info=True)
            time.sleep(5)
    
    logger.info("=" * 60)
    logger.info("🛑 Bot stopped")
    logger.info(f"Total iterations: {iteration}")
    logger.info(f"Knowledge: {len(knowledge.elements)} elements, {len(knowledge.screens)} screens")
    logger.info("=" * 60)
    
except Exception as e:
    logger.error(f"Fatal error: {e}", exc_info=True)
    sys.exit(1)
