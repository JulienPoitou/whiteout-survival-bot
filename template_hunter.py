#!/usr/bin/env python
"""
Template Hunter v2 - FIXED
Recherche automatique de templates
"""

import sys
import time
import logging
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from PIL import Image

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "template_hunter.log", encoding='utf-8', mode='w')
    ]
)

logger = logging.getLogger("TemplateHunter")


class TemplateHunter:
    def __init__(self):
        from config import Config
        Config.ensure_dirs()
        
        from adb.controller import ADBController
        from vision.fast_matcher import FastTemplateMatcher
        
        self.adb = ADBController()
        self.matcher = FastTemplateMatcher(threshold=0.55)
        
        self.found_templates: Dict[str, dict] = {}
        self.tested_templates: List[str] = []
        self.start_time = datetime.now()
        self.last_report_time = self.start_time
        
        self.templates_dir = Path("C:/Users/julie/new-bot/templates")
        self.primebot_dir = Path("C:/Users/julie/primebot/images/whiteout")
        
        self.all_templates = self._scan_primebot_templates()
        
        logger.info("=" * 80)
        logger.info("TEMPLATE HUNTER V2 - FIXED")
        logger.info(f"Templates a tester: {len(self.all_templates)}")
        logger.info("=" * 80)
    
    def _scan_primebot_templates(self) -> List[str]:
        templates = []
        if self.primebot_dir.exists():
            for png in self.primebot_dir.rglob("*.png"):
                rel_path = png.relative_to(self.primebot_dir)
                name = str(rel_path.with_suffix('')).replace('/', '_')
                templates.append(name)
        logger.info(f"Primebot templates: {len(templates)}")
        return templates
    
    def _test_template(self, template_name: str, screenshot: Image.Image) -> Optional[dict]:
        try:
            result = self.matcher.find(screenshot, template_name, threshold=0.55)
            if result.found:
                return {
                    "name": template_name,
                    "confidence": result.confidence,
                    "x": result.x,
                    "y": result.y,
                    "timestamp": datetime.now().isoformat()
                }
            return None
        except Exception as e:
            logger.debug(f"Error testing {template_name}: {e}")
            return None
    
    def _log_report(self, force: bool = False):
        now = datetime.now()
        elapsed = now - self.start_time
        elapsed_minutes = int(elapsed.total_seconds() / 60)  # FIX: convert to int
        
        if not force and (now - self.last_report_time).total_seconds() < 600:
            return
        
        self.last_report_time = now
        
        total = len(self.all_templates)
        tested = len(self.tested_templates)
        found = len(self.found_templates)
        progress = (tested / total * 100) if total > 0 else 0
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"RAPPORT - {elapsed_minutes}min ecoulees")
        logger.info("=" * 80)
        logger.info(f"  Progress: {tested}/{total} ({progress:.1f}%)")
        logger.info(f"  Trouves:  {found} templates")
        logger.info(f"  Taux:     {found/max(1,tested)*100:.1f}%")
        
        if found > 0:
            logger.info("  TOP TEMPLATES:")
            sorted_found = sorted(self.found_templates.values(), key=lambda x: -x['confidence'])[:5]
            for t in sorted_found:
                logger.info(f"    {t['name']}: {t['confidence']:.1%} @ ({t['x']},{t['y']})")
        
        logger.info("=" * 80)
        self._save_results()
    
    def _save_results(self):
        results_file = LOG_DIR / "hunter_results.json"
        data = {
            "start_time": self.start_time.isoformat(),
            "last_update": datetime.now().isoformat(),
            "tested": self.tested_templates,
            "found": self.found_templates,
            "stats": {
                "total_tested": len(self.tested_templates),
                "total_found": len(self.found_templates),
                "success_rate": len(self.found_templates) / max(1, len(self.tested_templates))
            }
        }
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def run(self, max_hours: float = 5.0):
        logger.info(f"Demarrage pour {max_hours}h max")
        
        if not self.adb.connect():
            logger.error("ADB connection failed")
            return
        
        max_end = self.start_time + timedelta(hours=max_hours)
        iteration = 0
        screenshot = None
        
        while datetime.now() < max_end:
            iteration += 1
            
            # Rapport toutes les 10 min
            self._log_report(force=(iteration == 1))
            
            # Nouveau screenshot toutes les 30s
            if screenshot is None or iteration % 10 == 0:
                screenshot = self.adb.screenshot()
                if not screenshot:
                    time.sleep(2)
                    continue
            
            # Tester templates
            for template_name in self.all_templates:
                if template_name in self.tested_templates:
                    continue
                
                result = self._test_template(template_name, screenshot)
                self.tested_templates.append(template_name)
                
                if result:
                    self.found_templates[template_name] = result
                    logger.info(f"TROUVE: {template_name} @ ({result['x']},{result['y']}) - {result['confidence']:.1%}")
                
                time.sleep(0.05)
                
                if datetime.now() >= max_end:
                    break
        
        # Rapport final
        self._log_report(force=True)
        logger.info("TERMINE")


if __name__ == "__main__":
    hunter = TemplateHunter()
    hunter.run(max_hours=5.0)
