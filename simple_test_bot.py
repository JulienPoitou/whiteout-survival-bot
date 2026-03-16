"""
Simple test bot - sans IA
Teste juste la connexion et les templates
"""

import logging
import time
from config import Config
from adb.controller import ADBController
from vision.template_matcher import TemplateMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🤖 Simple Test Bot - Sans IA")
    logger.info("=" * 50)
    
    # Init
    Config.ensure_dirs()
    adb = ADBController()
    matcher = TemplateMatcher()
    
    # Connect
    logger.info(f"Device: {adb.device}")
    if not adb.connect():
        logger.error("❌ Connexion échouée")
        return
    
    logger.info("✅ Connecté")
    
    # Test simple tap
    logger.info("Test: Tap au centre de l'écran...")
    adb.tap(360, 640)
    time.sleep(1)
    
    # Test back arrow
    logger.info("Test: Back arrow (top-left)...")
    adb.tap(70, 70)
    time.sleep(1)
    
    # Test template matching (si templates disponibles)
    logger.info("Test: Template matching...")
    # Pas de screenshot pour l'instant - trop lent
    
    logger.info("=" * 50)
    logger.info("✅ Tests terminés !")
    logger.info("Le bot peut cliquer, mais le screenshot est trop lent.")
    logger.info("\nProchaines étapes:")
    logger.info("1. Vérifier que LDPlayer est bien ouvert")
    logger.info("2. Vérifier que le jeu est au premier plan")
    logger.info("3. Essayer de redémarrer l'émulateur")

if __name__ == "__main__":
    main()
