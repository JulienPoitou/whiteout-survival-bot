"""
Setup Test Script
Tests all components of the bot
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config


def test_imports():
    """Test that all modules can be imported"""
    print("\n=== Testing Imports ===")
    
    try:
        from adb.controller import ADBController
        print("✓ ADB Controller")
    except ImportError as e:
        print(f"✗ ADB Controller: {e}")
        return False
    
    try:
        from vision.template_matcher import TemplateMatcher
        print("✓ Template Matcher")
    except ImportError as e:
        print(f"✗ Template Matcher: {e}")
        return False
    
    try:
        from vision.ocr_reader import OCRReader
        print("✓ OCR Reader")
    except ImportError as e:
        print(f"✗ OCR Reader: {e}")
        return False
    
    try:
        from vision.ai_analyzer import AIAnalyzer
        print("✓ AI Analyzer")
    except ImportError as e:
        print(f"✗ AI Analyzer: {e}")
        return False
    
    try:
        from core.context import GameContext
        print("✓ Game Context")
    except ImportError as e:
        print(f"✗ Game Context: {e}")
        return False
    
    try:
        from core.vision_facade import VisionFacade
        print("✓ Vision Facade")
    except ImportError as e:
        print(f"✗ Vision Facade: {e}")
        return False
    
    try:
        from tasks.gather import GatherTask
        print("✓ Gather Task")
    except ImportError as e:
        print(f"✗ Gather Task: {e}")
        return False
    
    print("\n✓ All imports successful!")
    return True


def test_adb():
    """Test ADB connection"""
    print("\n=== Testing ADB Connection ===")
    
    try:
        from adb.controller import ADBController
        
        adb = ADBController()
        
        print(f"Connecting to {adb.device}...")
        
        if adb.connect():
            print("✓ Connected to emulator")
            
            if adb.check_connection():
                print("✓ Device responsive")
                
                # Test screenshot
                print("Testing screenshot...")
                screenshot = adb.screenshot()
                
                if screenshot:
                    print(f"✓ Screenshot captured: {screenshot.size}")
                    
                    # Save test screenshot
                    test_dir = Path("test_output")
                    test_dir.mkdir(exist_ok=True)
                    screenshot.save(test_dir / "test_screenshot.png")
                    print(f"✓ Screenshot saved to {test_dir / 'test_screenshot.png'}")
                else:
                    print("✗ Screenshot failed")
                    return False
            else:
                print("✗ Device not responsive")
                return False
        else:
            print("✗ Connection failed")
            print("\nMake sure:")
            print("  1. LDPlayer is running")
            print("  2. ADB debugging is enabled")
            print("  3. The port (5555) is correct in .env")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ ADB test error: {e}")
        return False


def test_ollama():
    """Test Ollama connection"""
    print("\n=== Testing Ollama (AI) ===")
    
    try:
        from vision.ai_analyzer import AIAnalyzer
        
        ai = AIAnalyzer()
        
        print(f"Checking Ollama at {ai.base_url}...")
        
        if ai.is_available():
            print("✓ Ollama is available")
            print(f"  Model configured: {Config.OLLAMA_MODEL}")
            print("\nNote: Make sure you've pulled the model:")
            print(f"  ollama pull {Config.OLLAMA_MODEL}")
            return True
        else:
            print("✗ Ollama is not available")
            print("\nTo fix:")
            print("  1. Install Ollama: https://ollama.ai")
            print("  2. Run: ollama serve")
            print("  3. Pull model: ollama pull moondream:1.8b")
            return False
        
    except Exception as e:
        print(f"✗ Ollama test error: {e}")
        return False


def test_templates():
    """Test template directory"""
    print("\n=== Testing Templates ===")
    
    templates_dir = Config.TEMPLATES_DIR
    
    if not templates_dir.exists():
        print(f"✗ Templates directory not found: {templates_dir}")
        print("\nTo fix:")
        print("  Create the templates directory and add PNG files")
        return False
    
    # Count templates
    template_files = list(templates_dir.glob("*.png"))
    
    if len(template_files) == 0:
        print(f"⚠ No templates found in {templates_dir}")
        print("\nYou need to add template PNG images for:")
        print("  - Navigation (furnace_icon, world_map_button, etc.)")
        print("  - Resources (resource_meat_icon, etc.)")
        print("  - Actions (gather_deploy_button, march_button)")
        print("\nSee README.md for template list")
        return False
    
    print(f"✓ Found {len(template_files)} templates")
    
    for f in template_files[:10]:  # Show first 10
        print(f"  - {f.name}")
    
    if len(template_files) > 10:
        print(f"  ... and {len(template_files) - 10} more")
    
    return True


def test_opencv():
    """Test OpenCV installation"""
    print("\n=== Testing OpenCV ===")
    
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
        
        # Test basic operation
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = cv2.matchTemplate(img, img, cv2.TM_CCOEFF_NORMED)
        print("✓ Template matching works")
        
        return True
        
    except ImportError as e:
        print(f"✗ OpenCV not installed: {e}")
        print("\nTo fix: pip install opencv-python")
        return False
    except Exception as e:
        print(f"✗ OpenCV test error: {e}")
        return False


def test_tesseract():
    """Test Tesseract installation"""
    print("\n=== Testing Tesseract (OCR) ===")
    
    try:
        import pytesseract
        
        # Get version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract version: {version}")
        
        # Test basic OCR
        from PIL import Image
        img = Image.new('L', (100, 30), color=255)
        text = pytesseract.image_to_string(img)
        print("✓ OCR works")
        
        return True
        
    except ImportError as e:
        print(f"✗ pytesseract not installed: {e}")
        print("\nTo fix: pip install pytesseract")
        return False
    except Exception as e:
        print(f"✗ Tesseract test error: {e}")
        print("\nMake sure Tesseract OCR is installed:")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("Whiteout Survival Bot - Setup Test")
    print("=" * 50)
    
    results = {
        "Imports": test_imports(),
        "OpenCV": test_opencv(),
        "Tesseract": test_tesseract(),
        "Templates": test_templates(),
        "ADB": test_adb(),
        "Ollama": test_ollama(),
    }
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Bot is ready to run.")
        print("\nTo start the bot:")
        print("  python main.py")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
