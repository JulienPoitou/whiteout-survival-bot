#!/usr/bin/env python
"""
Whiteout Survival Bot - Fast Version
Uses OpenCV template matching instead of slow AI

Performance: ~2s per iteration (vs 136s before)
"""

import sys
import time
import random
import logging
from pathlib import Path

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "bot.log", encoding='utf-8')
    ]
)

logger = logging.getLogger("FastBot")

def main():
    logger.info("=" * 60)
    logger.info("🤖 Whiteout Survival Bot - FAST VERSION")
    logger.info("=" * 60)
    
    # Init
    from config import Config
    Config.ensure_dirs()
    logger.info("✓ Config loaded")
    
    from adb.controller import ADBController
    adb = ADBController()
    logger.info(f"✓ ADB ready: {adb.device}")
    
    from vision.fast_matcher import FastTemplateMatcher
    matcher = FastTemplateMatcher(threshold=0.65)  # Seuil plus bas pour résolution 400x652
    logger.info("✓ Vision ready (OpenCV)")
    
    from core.context import GameContext, ScreenType
    context = GameContext()
    logger.info("✓ Context ready")
    
    # Connect
    logger.info("\n📡 Connecting to emulator...")
    start = time.time()
    if not adb.connect():
        logger.error("✗ Connection failed!")
        return
    logger.info(f"✓ Connected in {time.time()-start:.1f}s")
    
    # Main loop
    logger.info("\n🚀 Starting main loop...")
    logger.info("Press Ctrl+C to stop\n")
    
    iteration = 0
    start_time = time.time()
    
    # Templates to search for (navigation)
    NAV_TEMPLATES = [
        "furnace_icon",      # Home screen
        "world_map_button",  # Go to world
        "home_button",       # Back home
        "back_arrow",        # Back navigation
    ]
    
    try:
        while True:
            iteration += 1
            iter_start = time.time()
            logger.info(f"\n{'='*40}")
            logger.info(f"📍 Iteration {iteration}")
            
            try:
                # 1. Screenshot (FAST: ~0.4s)
                logger.debug("📸 Screenshot...")
                screenshot = adb.screenshot()
                
                if not screenshot:
                    logger.error("✗ Screenshot failed")
                    time.sleep(2)
                    continue
                
                logger.info(f"✓ Screenshot: {screenshot.size}")
                context.screenshots_count += 1
                
                # 2. Find UI elements (FAST: ~0.01s)
                logger.debug("🔍 Finding UI elements...")
                results = matcher.find_all_templates(screenshot, NAV_TEMPLATES)
                
                if results:
                    logger.info(f"✓ Found {len(results)} element(s):")
                    for r in results:
                        logger.info(f"  • {r.template_name} at ({r.x}, {r.y}) - {r.confidence:.0%}")
                    
                    # 3. Click on BEST element (highest confidence)
                    best = max(results, key=lambda r: r.confidence)
                    logger.info(f"👆 Clicking BEST: {best.template_name} at ({best.x}, {best.y}) - {best.confidence:.0%}")
                    
                    # Smart tap with scaling (400x652 → 720x1280)
                    success = adb.smart_tap(best.x, best.y, best.template_name, scale=True)
                    
                    if success:
                        logger.info(f"✓ Click OK")
                        context.record_action("tap", {"element": best.template_name, "confidence": best.confidence})
                    else:
                        logger.warning("✗ Click failed")
                        context.record_error("tap", f"Failed to click {best.template_name}")
                    
                    time.sleep(1)
                    
                else:
                    logger.info("⚠️  No known elements found")
                    
                    # Safe click in center-bottom area
                    logger.info("👆 Clicking safe zone...")
                    adb.smart_tap(360, 900, "safe_zone")
                    time.sleep(1)
                
                # 4. Random delay (anti-ban)
                delay = random.uniform(2, 4)
                logger.debug(f"⏱ Waiting {delay:.1f}s")
                time.sleep(delay)
                
                # Log iteration time
                iter_time = time.time() - iter_start
                logger.info(f"⏱ Iteration time: {iter_time:.1f}s")
                
                # Check elapsed time (auto-stop after 10 minutes)
                elapsed = time.time() - start_time
                if elapsed > 600:  # 10 minutes
                    logger.info("\n⏰ 10 minutes elapsed, auto-stopping")
                    break
                
            except Exception as e:
                logger.error(f"✗ Iteration error: {e}", exc_info=True)
                time.sleep(3)
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
    
    finally:
        # Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 60)
        logger.info("📊 SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Duration: {elapsed/60:.1f} minutes")
        logger.info(f"  Iterations: {iteration}")
        logger.info(f"  Screenshots: {context.screenshots_count}")
        logger.info(f"  Actions: {context.actions_count}")
        logger.info(f"  Avg iteration: {elapsed/max(1,iteration):.1f}s")
        logger.info("=" * 60)
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    main()
