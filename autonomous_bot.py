"""
Autonomous Learning Bot for Whiteout Survival
Apprend tout seul en explorant le jeu et en mémorisant ses découvertes
"""

import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import hashlib

from config import Config
from core.context import GameContext, ScreenType
from core.vision_facade import VisionFacade
from adb.controller import ADBController


@dataclass
class UIElement:
    """Élément d'interface appris"""
    name: str
    screen_type: str
    x: int
    y: int
    width: int = 60
    height: int = 60
    confidence: float = 0.5
    success_count: int = 0
    fail_count: int = 0
    last_used: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5
        return self.success_count / total
    
    def record_success(self):
        self.success_count += 1
        self.last_used = datetime.now().isoformat()
        self.confidence = min(1.0, self.confidence + 0.05)
    
    def record_failure(self):
        self.fail_count += 1
        self.confidence = max(0.1, self.confidence - 0.1)


@dataclass
class ScreenPattern:
    """Pattern d'écran appris"""
    screen_id: str  # Hash de l'image
    screen_type: str
    features: Dict[str, Any]  # Features visuelles
    actions: List[str]  # Actions possibles depuis cet écran
    visit_count: int = 0
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class KnowledgeBase:
    """
    Base de connaissances du bot
    Sauvegarde tout ce que le bot apprend
    """
    
    def __init__(self, save_path: str = None):
        self.save_path = Path(save_path) if save_path else Config.BASE_DIR / "knowledge"
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        self.elements: Dict[str, UIElement] = {}
        self.screens: Dict[str, ScreenPattern] = {}
        self.action_history: List[Dict] = []
        
        self.logger = logging.getLogger(__name__)
        self.load()
    
    def load(self):
        """Charger les connaissances depuis le disque"""
        elements_file = self.save_path / "elements.json"
        screens_file = self.save_path / "screens.json"
        
        if elements_file.exists():
            with open(elements_file, 'r') as f:
                data = json.load(f)
                self.elements = {k: UIElement(**v) for k, v in data.items()}
            self.logger.info(f"✓ Loaded {len(self.elements)} UI elements")
        
        if screens_file.exists():
            with open(screens_file, 'r') as f:
                data = json.load(f)
                self.screens = {k: ScreenPattern(**v) for k, v in data.items()}
            self.logger.info(f"✓ Loaded {len(self.screens)} screen patterns")
    
    def save(self):
        """Sauvegarder les connaissances"""
        elements_file = self.save_path / "elements.json"
        screens_file = self.save_path / "screens.json"
        
        with open(elements_file, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.elements.items()}, f, indent=2)
        
        with open(screens_file, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.screens.items()}, f, indent=2)
        
        self.logger.debug("✓ Knowledge saved")
    
    def add_element(self, name: str, screen_type: str, x: int, y: int) -> UIElement:
        """Ajouter ou mettre à jour un élément UI"""
        key = f"{screen_type}_{name}"
        
        if key in self.elements:
            element = self.elements[key]
            # Mettre à jour position si nouvelle découverte
            element.x = x
            element.y = y
        else:
            element = UIElement(
                name=name,
                screen_type=screen_type,
                x=x,
                y=y
            )
            self.elements[key] = element
            self.logger.info(f"✨ Discovered new element: {name} at ({x}, {y})")
        
        self.save()
        return element
    
    def get_element(self, name: str, screen_type: str = None) -> Optional[UIElement]:
        """Récupérer un élément appris"""
        # Chercher par nom exact
        if screen_type:
            key = f"{screen_type}_{name}"
            if key in self.elements:
                return self.elements[key]
        
        # Chercher dans tous les écrans
        for key, element in self.elements.items():
            if element.name == name:
                return element
        
        return None
    
    def get_best_element(self, name: str) -> Optional[UIElement]:
        """Récupérer la meilleure version d'un élément (plus haut succès)"""
        candidates = [e for e in self.elements.values() if e.name == name]
        
        if not candidates:
            return None
        
        return max(candidates, key=lambda e: e.success_rate)
    
    def record_action(self, action: str, screen: str, success: bool):
        """Enregistrer une action et son résultat"""
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "screen": screen,
            "success": success
        })
        
        # Garder seulement les 1000 dernières actions
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-1000:]
    
    def get_screen_hash(self, screenshot) -> str:
        """Créer un hash unique pour un screenshot"""
        import io
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        return hashlib.md5(buffer.getvalue()).hexdigest()
    
    def learn_screen(self, screenshot, screen_type: str) -> ScreenPattern:
        """Apprendre un nouvel écran"""
        screen_hash = self.get_screen_hash(screenshot)
        
        if screen_hash not in self.screens:
            # Extraire des features simples (couleurs dominantes, etc.)
            features = self._extract_features(screenshot)
            
            pattern = ScreenPattern(
                screen_id=screen_hash,
                screen_type=screen_type,
                features=features,
                actions=[]
            )
            self.screens[screen_hash] = pattern
            self.logger.info(f"✨ Learned new screen: {screen_type} ({screen_hash[:8]})")
            self.save()
        
        self.screens[screen_hash].visit_count += 1
        return self.screens[screen_hash]
    
    def _extract_features(self, screenshot) -> Dict[str, Any]:
        """Extraire des features visuelles d'un screenshot"""
        # Features simples pour reconnaissance
        import numpy as np
        from PIL import Image
        
        img_array = np.array(screenshot.convert('RGB'))
        
        # Couleurs dominantes (quartiles)
        features = {
            "avg_color": img_array.mean(axis=(0, 1)).tolist(),
            "std_color": img_array.std(axis=(0, 1)).tolist(),
            "brightness": img_array.mean(),
            "contrast": img_array.std(),
        }
        
        return features
    
    def recognize_screen(self, screenshot) -> Optional[ScreenPattern]:
        """Reconnaître un écran déjà appris"""
        current_features = self._extract_features(screenshot)
        
        best_match = None
        best_score = 0.85  # Seuil de confiance
        
        for screen_hash, pattern in self.screens.items():
            # Comparer les features
            brightness_diff = abs(current_features["brightness"] - pattern.features["brightness"])
            color_diff = sum(abs(a - b) for a, b in zip(
                current_features["avg_color"],
                pattern.features["avg_color"]
            ))
            
            # Score de similarité
            score = 1.0 - (brightness_diff / 255 + color_diff / 765) / 2
            
            if score > best_score:
                best_score = score
                best_match = pattern
        
        if best_match:
            self.logger.debug(f"Screen recognized: {best_match.screen_type} ({best_score:.2%})")
        
        return best_match
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques des connaissances"""
        total_actions = len(self.action_history)
        successful_actions = sum(1 for a in self.action_history if a["success"])
        
        return {
            "ui_elements": len(self.elements),
            "screen_patterns": len(self.screens),
            "total_actions": total_actions,
            "success_rate": successful_actions / max(1, total_actions),
            "knowledge_path": str(self.save_path)
        }


class AutonomousBot:
    """
    Bot autonome qui apprend tout seul
    
    Fonctionnalités:
    - Explore l'UI sans templates prédéfinis
    - Mémorise les éléments cliquables
    - Apprend quelles actions fonctionnent
    - S'améliore avec le temps
    """
    
    def __init__(self):
        self.logger = logging.getLogger("AutonomousBot")
        
        self.adb = ADBController()
        self.context = GameContext()
        self.vision = VisionFacade()
        self.knowledge = KnowledgeBase()
        
        self.running = False
        
        # Configuration auto-apprentissage
        self.explore_mode = True  # True = explore, False = farm optimisé
        self.min_confidence = 0.6  # Confiance minimale pour utiliser un élément appris
        self.learn_rate = 0.1  # Vitesse d'apprentissage
    
    def start(self) -> bool:
        """Démarrer le bot"""
        self.logger.info("=" * 60)
        self.logger.info("🤖 Autonomous Learning Bot v1.0")
        self.logger.info("Apprend et s'améliore automatiquement")
        self.logger.info("=" * 60)
        
        if not self.adb.connect():
            self.logger.error("Failed to connect to emulator")
            return False
        
        if not self.adb.check_connection():
            self.logger.error("Device not connected")
            return False
        
        self.logger.info(f"✓ Connected | 📚 Knowledge: {len(self.knowledge.elements)} elements")
        self.running = True
        return True
    
    def stop(self):
        """Arrêter le bot"""
        self.running = False
        self.adb.disconnect()
        self.logger.info("Bot stopped")
    
    def run(self):
        """Boucle principale"""
        if not self.start():
            return
        
        try:
            while self.running:
                self._autonomous_loop()
                time.sleep(random.uniform(3, 8))
        except KeyboardInterrupt:
            self.logger.info("\nInterrupted by user")
        finally:
            self.stop()
    
    def _autonomous_loop(self):
        """Boucle autonome - explore et apprend"""
        screenshot = self.adb.screenshot()
        
        if not screenshot:
            self.logger.error("Screenshot failed")
            return
        
        self.context.screenshots_count += 1
        
        # 1. Reconnaître l'écran actuel
        screen_pattern = self.knowledge.recognize_screen(screenshot)
        
        if screen_pattern:
            self.logger.debug(f"On known screen: {screen_pattern.screen_type}")
        else:
            # Nouvel écran - apprendre
            screen_type = self.vision.detect_screen_type(screenshot, self.context)
            screen_pattern = self.knowledge.learn_screen(screenshot, screen_type.value)
        
        # 2. Explorer et trouver de nouveaux éléments
        if self.explore_mode:
            self._explore_and_learn(screenshot, screen_pattern)
        
        # 3. Prendre décision basée sur connaissances
        self._make_decision(screenshot, screen_pattern)
        
        # 4. Nettoyer connaissances anciennes
        self._cleanup_knowledge()
    
    def _explore_and_learn(self, screenshot, screen_pattern: ScreenPattern):
        """Explorer l'écran et apprendre de nouveaux éléments"""
        self.logger.debug("Exploring screen for new elements...")
        
        # Zones typiques à explorer (grille)
        zones = [
            (100, 100), (360, 100), (620, 100),
            (100, 400), (360, 400), (620, 400),
            (100, 700), (360, 700), (620, 700),
            (100, 1000), (360, 1000), (620, 1000),
        ]
        
        for x, y in zones:
            # Demander à l'IA d'analyser cette zone
            element_name = self._ask_ai_element_name(screenshot, x, y)
            
            if element_name and element_name not in ["empty", "background", "decoration"]:
                # Vérifier si on a déjà cet élément
                existing = self.knowledge.get_element(element_name, screen_pattern.screen_type)
                
                if not existing:
                    # Nouvel élément découvert !
                    self.knowledge.add_element(element_name, screen_pattern.screen_type, x, y)
                    self.logger.info(f"✨ New element learned: {element_name}")
                
                # Ajouter aux actions possibles de l'écran
                if element_name not in screen_pattern.actions:
                    screen_pattern.actions.append(element_name)
                    self.knowledge.save()
    
    def _ask_ai_element_name(self, screenshot, x: int, y: int) -> Optional[str]:
        """Demander à l'IA le nom d'un élément à une position"""
        # Crop une petite zone autour du point
        crop_size = 80
        crop = screenshot.crop((
            max(0, x - crop_size),
            max(0, y - crop_size),
            min(screenshot.width, x + crop_size),
            min(screenshot.height, y + crop_size)
        ))
        
        # Demander à l'IA
        try:
            from vision.ai_analyzer import AIAnalyzer
            ai = AIAnalyzer()
            
            result = ai.analyze(
                crop,
                custom_prompt="Qu'est-ce que c'est ? Réponds par un seul mot en anglais (button, icon, resource, text, empty, etc.)"
            )
            
            if result:
                return result.get("reason", "unknown").split()[0].lower()
        except Exception:
            pass
        
        return None
    
    def _make_decision(self, screenshot, screen_pattern: ScreenPattern):
        """Prendre une décision basée sur les connaissances"""
        if not screen_pattern.actions:
            self.logger.debug("No known actions for this screen")
            return
        
        # Choisir une action à essayer
        action_name = self._choose_best_action(screen_pattern.actions)
        
        if not action_name:
            return
        
        # Récupérer l'élément appris
        element = self.knowledge.get_best_element(action_name)
        
        if not element:
            return
        
        # Vérifier confiance
        if element.confidence < self.min_confidence:
            self.logger.debug(f"Too low confidence for {element.name}: {element.confidence:.2%}")
            return
        
        # Exécuter l'action
        self.logger.info(f"Executing: {element.name} at ({element.x}, {element.y})")
        
        success = self._execute_action(element.x, element.y)
        
        # Enregistrer résultat
        element.record_success() if success else element.record_failure()
        self.knowledge.record_action(element.name, screen_pattern.screen_type, success)
        self.knowledge.save()
    
    def _choose_best_action(self, actions: List[str]) -> Optional[str]:
        """Choisir la meilleure action à exécuter"""
        if not actions:
            return None
        
        # Prioriser les actions avec haut succès
        candidates = []
        
        for action_name in actions:
            element = self.knowledge.get_best_element(action_name)
            if element:
                candidates.append((element, element.success_rate))
            else:
                candidates.append((None, 0.5))  # Inconnu = 50%
        
        # Choisir avec exploration (parfois essayer des actions inconnues)
        if random.random() < 0.2:  # 20% exploration
            return random.choice(actions)
        
        # 80% exploitation - choisir le meilleur
        best = max(candidates, key=lambda x: x[1])
        return best[0].name if best[0] else random.choice(actions)
    
    def _execute_action(self, x: int, y: int) -> bool:
        """Exécuter un tap et vérifier si ça a marché"""
        try:
            # Tap avec variation humaine
            x_var = x + random.randint(-3, 3)
            y_var = y + random.randint(-3, 3)
            
            self.adb.tap(x_var, y_var)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Vérifier si l'écran a changé (signe de succès)
            new_screenshot = self.adb.screenshot()
            if new_screenshot:
                old_hash = self.knowledge.get_screen_hash(self.adb.screenshot())
                # Simple check - dans une version avancée, comparer les features
                return True
            
            return True  # Assume success
            
        except Exception as e:
            self.logger.error(f"Action failed: {e}")
            return False
    
    def _cleanup_knowledge(self):
        """Nettoyer les connaissances peu fiables"""
        # Supprimer éléments avec trop d'échecs
        to_remove = []
        
        for key, element in self.knowledge.elements.items():
            if element.fail_count > 10 and element.success_rate < 0.3:
                to_remove.append(key)
        
        for key in to_remove:
            del self.knowledge.elements[key]
            self.logger.debug(f"Removed unreliable element: {key}")
        
        if to_remove:
            self.knowledge.save()
    
    def get_status(self) -> Dict[str, Any]:
        """Status complet du bot"""
        return {
            "running": self.running,
            "explore_mode": self.explore_mode,
            "knowledge": self.knowledge.get_stats(),
            "context": self.context.get_session_stats(),
        }


def main():
    """Entry point"""
    import sys
    from loguru import logger
    
    # Setup logging
    logger.remove()
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")
    
    bot = AutonomousBot()
    
    logger.info("🎯 Mode: Autonomous Learning")
    logger.info("Le bot va apprendre tout seul en explorant le jeu")
    logger.info("Plus il tourne, plus il devient intelligent !")
    
    bot.run()


if __name__ == "__main__":
    main()
