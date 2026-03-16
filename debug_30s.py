#!/usr/bin/env python
"""
Whiteout Survival Bot - DEBUG MODE 30s
Logs EXTREMELY detailed for analysis
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup logging ULTRA detailed
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-20s | %(funcName)-20s | L%(lineno)-4d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "bot_debug_30s.log", encoding='utf-8', mode='w')
    ]
)

logger = logging.getLogger("BotDebug")

def main():
    logger.info("=" * 100)
    logger.info("🔬 BOT DEBUG MODE - 30 SECONDES À PLEIN RÉGIME")
    logger.info("=" * 100)
    
    start_total = time.time()
    
    # Init avec logs détaillés
    t0 = time.time()
    from config import Config
    Config.ensure_dirs()
    logger.info(f"✓ Config loaded in {(time.time()-t0)*1000:.1f}ms")
    logger.info(f"  - SCREEN: {Config.SCREEN_WIDTH}x{Config.SCREEN_HEIGHT}")
    logger.info(f"  - CAPTURE: {Config.CAPTURE_WIDTH}x{Config.CAPTURE_HEIGHT}")
    logger.info(f"  - SCALE_X: {Config.SCALE_X:.3f}, SCALE_Y: {Config.SCALE_Y:.3f}")
    
    t0 = time.time()
    from adb.controller import ADBController
    adb = ADBController()
    logger.info(f"✓ ADBController created in {(time.time()-t0)*1000:.1f}ms")
    
    t0 = time.time()
    from vision.fast_matcher import FastTemplateMatcher
    matcher = FastTemplateMatcher(threshold=0.60)
    logger.info(f"✓ FastTemplateMatcher created in {(time.time()-t0)*1000:.1f}ms")
    
    t0 = time.time()
    from core.context import GameContext
    context = GameContext()
    logger.info(f"✓ GameContext created in {(time.time()-t0)*1000:.1f}ms")
    
    # Connect
    logger.info("\n" + "=" * 100)
    logger.info("📡 CONNECTING TO EMULATOR")
    logger.info("=" * 100)
    
    t0 = time.time()
    if not adb.connect():
        logger.error("✗ Connection FAILED")
        return
    logger.info(f"✓ Connected in {time.time()-t0:.2f}s")
    
    # Test screenshot
    logger.info("\n" + "=" * 100)
    logger.info("📸 TESTING SCREENSHOT")
    logger.info("=" * 100)
    
    t0 = time.time()
    img = adb.screenshot()
    scr_time = time.time() - t0
    
    if img:
        logger.info(f"✓ Screenshot OK in {scr_time*1000:.1f}ms")
        logger.info(f"  - Size: {img.size}")
    else:
        logger.error("✗ Screenshot FAILED")
        return
    
    # Main loop - 30 secondes
    logger.info("\n" + "=" * 100)
    logger.info("🚀 STARTING MAIN LOOP - 30 SECONDS FULL SPEED")
    logger.info("=" * 100)
    
    iteration = 0
    start_time = time.time()
    total_clicks = 0
    successful_clicks = 0
    templates_found = 0
    
    NAV_TEMPLATES = [
        "furnace_icon",
        "furnace_inactive",
        "back_arrow",
        "home_button",
        "popup_close",
        "gather_button",
    ]
    
    while (time.time() - start_time) < 30:
        iteration += 1
        iter_start = time.time()
        
        logger.info("-" * 100)
        logger.info(f"📍 ITERATION {iteration} @ {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        logger.info("-" * 100)
        
        try:
            # 1. Screenshot
            t0 = time.time()
            screenshot = adb.screenshot()
            scr_time = time.time() - t0
            
            if not screenshot:
                logger.error(f"✗ Screenshot FAILED after {scr_time*1000:.1f}ms")
                continue
            
            logger.info(f"📸 Screenshot: {screenshot.size} in {scr_time*1000:.1f}ms")
            context.screenshots_count += 1
            
            # 2. Template matching
            t0 = time.time()
            all_results = matcher.find_all_templates(screenshot, NAV_TEMPLATES)
            match_time = time.time() - t0
            
            templates_found += len(all_results)
            
            if all_results:
                logger.info(f"🔍 Found {len(all_results)} template(s) in {match_time*1000:.2f}ms:")
                
                sorted_results = sorted(all_results, key=lambda r: -r.confidence)
                
                for i, r in enumerate(sorted_results):
                    best_marker = " ← BEST" if i == 0 else ""
                    logger.info(f"   [{i+1}] {r.template_name:25} @ ({r.x:3d}, {r.y:3d}) - {r.confidence:5.1%}{best_marker}")
                
                best = sorted_results[0]
                logger.info(f"👆 Clicking BEST: {best.template_name}")
                
                real_x = int(best.x * Config.SCALE_X)
                real_y = int(best.y * Config.SCALE_Y)
                logger.info(f"   - Capture coords: ({best.x}, {best.y})")
                logger.info(f"   - Scale factors:  ({Config.SCALE_X:.2f}, {Config.SCALE_Y:.2f})")
                logger.info(f"   - Screen coords:  ({real_x}, {real_y})")
                
                t0 = time.time()
                success = adb.smart_tap(best.x, best.y, best.template_name, scale=True, retries=3)
                tap_time = time.time() - t0
                
                total_clicks += 1
                if success:
                    successful_clicks += 1
                    logger.info(f"✓ Click OK in {tap_time*1000:.1f}ms")
                else:
                    logger.warning(f"✗ Click FAILED after {tap_time*1000:.1f}ms")
            
            else:
                logger.info(f"⚠️  No templates found in {match_time*1000:.2f}ms")
            
            iter_time = time.time() - iter_start
            logger.info(f"⏱ Iteration {iteration} completed in {iter_time*1000:.0f}ms ({iter_time:.2f}s)")
            
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"✗ Iteration error: {e}", exc_info=True)
            time.sleep(1)
    
    total_time = time.time() - start_total
    
    logger.info("\n" + "=" * 100)
    logger.info("📊 FINAL STATISTICS - 30 SECOND TEST")
    logger.info("=" * 100)
    logger.info(f"Total duration:     {total_time:.1f}s")
    logger.info(f"Iterations:         {iteration}")
    logger.info(f"Templates found:    {templates_found}")
    logger.info(f"Total clicks:       {total_clicks}")
    logger.info(f"Successful clicks:  {successful_clicks}")
    logger.info(f"Click success rate: {successful_clicks/max(1,total_clicks)*100:.1f}%")
    logger.info(f"Avg iteration time: {total_time/iteration:.2f}s")
    logger.info("=" * 100)

if __name__ == "__main__":
    main()
