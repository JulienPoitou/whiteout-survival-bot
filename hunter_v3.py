#!/usr/bin/env python
"""
Template Hunter v3 - EXPLORATION MODE
- Clique sur les templates trouvés
- Navigue dans le jeu
- Détecte les écrans déjà vus (hash)
- Auto-back si bloqué
"""

import sys
import time
import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
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
        logging.FileHandler(LOG_DIR / "hunter_v3.log", encoding='utf-8', mode='w')
    ]
)

logger = logging.getLogger("HunterV3")


class TemplateHunterV3:
    """
    Hunter v3 avec exploration intelligente
    
    Features:
    - Screen hashing pour éviter les doublons
    - Auto-back si bloqué
    - Navigation automatique
    - Mémoire des états visités
    """
    
    def __init__(self):
        from config import Config
        Config.ensure_dirs()
        
        from adb.controller import ADBController
        from vision.fast_matcher import FastTemplateMatcher
        
        self.adb = ADBController()
        self.matcher = FastTemplateMatcher(threshold=0.60)
        
        # États visités (hash d'écran)
        self.visited_states: Set[str] = set()
        
        # Templates trouvés
        self.found_templates: Dict[str, dict] = {}
        self.tested_templates: List[str] = []
        self.clicked_templates: Dict[str, int] = {}  # Compteur de clics par template
        self.blacklisted_templates: Set[str] = set()  # Templates à ignorer
        
        # Timing
        self.start_time = datetime.now()
        self.last_report_time = self.start_time
        self.last_new_template_time = self.start_time
        self.last_back_time = self.start_time
        
        # Config
        self.primebot_dir = Path("C:/Users/julie/primebot/images/whiteout")
        self.templates_dir = Path("C:/Users/julie/new-bot/templates")
        
        # Templates à tester
        self.all_templates = self._scan_primebot_templates()
        
        # Templates de navigation (pour explorer)
        self.nav_templates = [
            "search_left", "search_right",
            "viewport_city", "viewport_world",
            "back_arrow", "home_button",
            "furnace_icon", "furnace_off"
        ]
        
        logger.info("=" * 80)
        logger.info("TEMPLATE HUNTER V3 - EXPLORATION MODE")
        logger.info("=" * 80)
        logger.info(f"Templates totaux: {len(self.all_templates)}")
        logger.info(f"Navigation templates: {len(self.nav_templates)}")
        logger.info("Features:")
        logger.info("  - Screen hashing (anti-boucle)")
        logger.info("  - Auto-back (10s sans nouveau)")
        logger.info("  - Exploration automatique")
        logger.info("=" * 80)
    
    def _scan_primebot_templates(self) -> List[str]:
        templates = []
        if self.primebot_dir.exists():
            for png in self.primebot_dir.rglob("*.png"):
                rel_path = png.relative_to(self.primebot_dir)
                name = str(rel_path.with_suffix('')).replace('/', '_')
                templates.append(name)
        logger.info(f"Primebot: {len(templates)} templates")
        return templates
    
    def _get_screen_hash(self, screenshot: Image.Image) -> str:
        """
        Hash de l'écran - ignore les bords (animations)
        Sample seulement la zone centrale stable
        """
        # Crop zone centrale (ignore 20% sur les bords)
        w, h = screenshot.size
        left = int(w * 0.2)
        top = int(h * 0.2)
        right = int(w * 0.8)
        bottom = int(h * 0.8)
        
        center = screenshot.crop((left, top, right, bottom))
        
        # Sample 1 byte sur 200 pour être rapide
        sampled = center.tobytes()[::200]
        return hashlib.md5(sampled).hexdigest()
    
    def _is_screen_visited(self, screenshot: Image.Image) -> bool:
        """Check si cet écran a déjà été visité"""
        screen_hash = self._get_screen_hash(screenshot)
        return screen_hash in self.visited_states
    
    def _mark_screen_visited(self, screenshot: Image.Image):
        """Marquer cet écran comme visité"""
        screen_hash = self._get_screen_hash(screenshot)
        self.visited_states.add(screen_hash)
        logger.debug(f"Screen marked visited: {screen_hash[:8]}")
    
    def _test_template(self, template_name: str, screenshot: Image.Image) -> Optional[dict]:
        try:
            result = self.matcher.find(screenshot, template_name, threshold=0.60)
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
    
    def _click_template(self, result: dict) -> bool:
        """Clique sur un template trouvé"""
        try:
            logger.info(f"  👆 Clicking {result['name']} @ ({result['x']}, {result['y']})")

            # Scaling : capture 400x652 → screen 720x1280
            real_x = int(result['x'] * Config.SCALE_X)
            real_y = int(result['y'] * Config.SCALE_Y)

            logger.info(f"     Scaled to: ({real_x}, {real_y})")

            # Utiliser adb.tap() avec scale=False (déjà scalé ici)
            success = self.adb.tap(real_x, real_y, scale=False)

            if success:
                logger.info(f"     ✓ Click sent successfully!")
            else:
                logger.error(f"     ✗ Click failed")

            time.sleep(1.5)  # Attendre que l'UI réagisse

            return success
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False

    def _press_back(self):
        """Appuie sur retour (back arrow)"""
        logger.info("  🔙 Pressing BACK...")

        # Essayer back arrow template d'abord
        screenshot = self.adb.screenshot()
        if screenshot:
            back_result = self._test_template("back_arrow", screenshot)
            if back_result:
                self._click_template(back_result)
                time.sleep(1)
                return

        # Fallback: tap top-left corner (already in screen coords)
        self.adb.tap(70, 70, scale=False)
        time.sleep(1)
    
    def _log_report(self, force: bool = False):
        now = datetime.now()
        elapsed_minutes = int((now - self.start_time).total_seconds() / 60)
        
        if not force and (now - self.last_report_time).total_seconds() < 600:
            return
        
        self.last_report_time = now
        
        total = len(self.all_templates)
        tested = len(self.tested_templates)
        found = len(self.found_templates)
        visited = len(self.visited_states)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"RAPPORT V3 - {elapsed_minutes}min")
        logger.info("=" * 80)
        logger.info(f"  Templates testés: {tested}/{total}")
        logger.info(f"  Templates trouvés: {found}")
        logger.info(f"  Écrans visités: {visited}")
        logger.info(f"  Taux: {found/max(1,tested)*100:.1f}%")
        
        if found > 0:
            logger.info("  NOUVEAUX TEMPLATES:")
            recent = list(self.found_templates.values())[-5:]
            for t in recent:
                logger.info(f"    + {t['name']}: {t['confidence']:.1%}")
        
        logger.info("=" * 80)
        self._save_results()
    
    def _save_results(self):
        results_file = LOG_DIR / "hunter_v3_results.json"
        data = {
            "start_time": self.start_time.isoformat(),
            "last_update": datetime.now().isoformat(),
            "tested": self.tested_templates,
            "found": self.found_templates,
            "visited_states": len(self.visited_states),
            "stats": {
                "total_tested": len(self.tested_templates),
                "total_found": len(self.found_templates),
                "unique_screens": len(self.visited_states),
                "success_rate": len(self.found_templates) / max(1, len(self.tested_templates))
            }
        }
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def run(self, max_hours: float = 5.0):
        logger.info(f"Démarrage pour {max_hours}h max")
        
        if not self.adb.connect():
            logger.error("ADB connection failed")
            return
        
        max_end = self.start_time + timedelta(hours=max_hours)
        iteration = 0
        consecutive_no_new = 0  # Compteur sans nouveau template
        
        while datetime.now() < max_end:
            iteration += 1
            logger.debug(f"\n--- Iteration {iteration} ---")
            
            # Rapport toutes les 10 min
            self._log_report(force=(iteration == 1))
            
            # 1. Prendre screenshot
            screenshot = self.adb.screenshot()
            if not screenshot:
                logger.error("Screenshot failed")
                time.sleep(2)
                continue
            
            # 2. Check si écran déjà visité
            if self._is_screen_visited(screenshot):
                logger.info("🔁 Screen already visited → Pressing BACK")
                self._press_back()
                consecutive_no_new += 1
                time.sleep(1)
                continue
            
            # 3. Marquer écran comme visité
            self._mark_screen_visited(screenshot)
            logger.info(f"🆕 New screen! (total visited: {len(self.visited_states)})")
            
            # 4. Tester TOUS les templates sur cet écran
            found_on_this_screen = False
            templates_to_click = []  # Stocker les templates à cliquer

            for template_name in self.all_templates:
                # Skip si déjà testé ET déjà cliqué
                if template_name in self.tested_templates:
                    continue
                
                # Skip si blacklisté (cliqué 3+ fois sans succès)
                if template_name in self.blacklisted_templates:
                    continue
                
                result = self._test_template(template_name, screenshot)
                self.tested_templates.append(template_name)
                
                if result:
                    self.found_templates[template_name] = result
                    logger.info(f"✅ TROUVÉ: {result['name']} @ ({result['x']},{result['y']}) - {result['confidence']:.1%}")
                    found_on_this_screen = True
                    self.last_new_template_time = datetime.now()
                    consecutive_no_new = 0
                    
                    # Ajouter à la liste des clics
                    templates_to_click.append(result)
                
                # Limite de temps par écran
                if (datetime.now() - self.start_time).total_seconds() > 5:
                    break
            
            # 5. CLIQUER sur TOUS les templates trouvés (pas juste le meilleur)
            if templates_to_click:
                logger.info(f"  👆 Clicking {len(templates_to_click)} template(s)...")
                for template_result in templates_to_click[:3]:  # Max 3 clics par écran
                    # Tracker les clics
                    template_name = template_result['name']
                    self.clicked_templates[template_name] = self.clicked_templates.get(template_name, 0) + 1
                    
                    # Blacklister si cliqué 3+ fois
                    if self.clicked_templates[template_name] >= 3:
                        self.blacklisted_templates.add(template_name)
                        logger.warning(f"  ⚠️  Blacklisting {template_name} (cliqué 3+ fois)")
                    
                    self._click_template(template_result)
                    time.sleep(1)
                consecutive_no_new = 0
            
            # 6. Auto-back si bloqué 10s sans nouveau
            if consecutive_no_new >= 10:
                logger.info("⚠️  Stuck for 10s → Pressing BACK")
                self._press_back()
                consecutive_no_new = 0
                self.last_back_time = datetime.now()
            
            # 7. Petit délai
            time.sleep(0.5)
        
        # Rapport final
        self._log_report(force=True)
        logger.info("✅ EXPLORATION TERMINÉE")


if __name__ == "__main__":
    hunter = TemplateHunterV3()
    hunter.run(max_hours=5.0)
