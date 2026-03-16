"""
Configuration management for Whiteout Survival Bot
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration"""

    # ADB Settings
    # Support both formats: IP:PORT or device name (emulator-5554)
    ADB_DEVICE = os.getenv("ADB_DEVICE", "")  # e.g., "emulator-5554"
    ADB_HOST = os.getenv("ADB_HOST", "127.0.0.1")
    ADB_PORT = int(os.getenv("ADB_PORT", "5555"))
    
    # Full device string (computed)
    if ADB_DEVICE:
        ADB_DEVICE_STRING = ADB_DEVICE  # "emulator-5554"
    else:
        ADB_DEVICE_STRING = f"{ADB_HOST}:{ADB_PORT}"  # "127.0.0.1:5555"

    # Screen Resolution
    # Physical resolution (what LDPlayer reports to Android)
    SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", "720"))
    SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", "1280"))
    
    # Actual capture resolution (what screenshots return)
    # LDPlayer often overrides to 400x652 even when set to 720x1280
    CAPTURE_WIDTH = int(os.getenv("CAPTURE_WIDTH", "400"))
    CAPTURE_HEIGHT = int(os.getenv("CAPTURE_HEIGHT", "652"))
    
    # Scaling factors (computed at runtime)
    SCALE_X = SCREEN_WIDTH / CAPTURE_WIDTH
    SCALE_Y = SCREEN_HEIGHT / CAPTURE_HEIGHT

    # Ollama (AI Vision)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
    OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "moondream:1.8b")
    OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

    # Vision Settings
    TEMPLATE_MATCH_THRESHOLD = float(os.getenv("TEMPLATE_MATCH_THRESHOLD", "0.85"))
    OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng")
    ENABLE_AI_FALLBACK = os.getenv("ENABLE_AI_FALLBACK", "true").lower() == "true"

    # Bot Settings
    ACTION_DELAY_MIN = float(os.getenv("ACTION_DELAY_MIN", "1.0"))
    ACTION_DELAY_MAX = float(os.getenv("ACTION_DELAY_MAX", "3.0"))
    CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "5"))
    CHECK_INTERVAL_MAX = int(os.getenv("CHECK_INTERVAL_MAX", "15"))

    # Safety Settings
    ENABLE_RANDOM_DELAYS = os.getenv("ENABLE_RANDOM_DELAYS", "true").lower() == "true"
    ENABLE_HUMAN_BEHAVIOR = os.getenv("ENABLE_HUMAN_BEHAVIOR", "true").lower() == "true"
    MAX_CONSECUTIVE_ACTIONS = int(os.getenv("MAX_CONSECUTIVE_ACTIONS", "50"))
    BREAK_DURATION_MIN = int(os.getenv("BREAK_DURATION_MIN", "300"))
    BREAK_DURATION_MAX = int(os.getenv("BREAK_DURATION_MAX", "600"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")
    SAVE_SCREENSHOTS = os.getenv("SAVE_SCREENSHOTS", "false").lower() == "true"

    # Dead Zones (areas to avoid or adjust for better clicking)
    DEAD_ZONE_TOP_LEFT = {"x": 0, "y": 0, "width": 120, "height": 80}
    DEAD_ZONE_TOP_RIGHT = {"x": 600, "y": 0, "width": 120, "height": 80}
    
    # Back arrow click adjustment (offset to hit the clickable area)
    BACK_ARROW_OFFSET_X = int(os.getenv("BACK_ARROW_OFFSET_X", "15"))
    BACK_ARROW_OFFSET_Y = int(os.getenv("BACK_ARROW_OFFSET_Y", "15"))
    BACK_ARROW_RETRIES = int(os.getenv("BACK_ARROW_RETRIES", "3"))

    # Paths
    BASE_DIR = Path(__file__).parent
    TEMPLATES_DIR = BASE_DIR / "templates"
    LOGS_DIR = BASE_DIR / "logs"
    SCREENSHOTS_DIR = BASE_DIR / "screenshots"
    KNOWLEDGE_DIR = BASE_DIR / "knowledge"

    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        cls.KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


# Game constants
class GameConfig:
    """Whiteout Survival game configuration"""

    # Screen types
    SCREEN_HOME = "home"
    SCREEN_WORLD = "world"
    SCREEN_GATHER = "gather"
    SCREEN_INTEL = "intel"
    SCREEN_ARENA = "arena"
    SCREEN_ALLIANCE = "alliance"
    SCREEN_TRAINING = "training"
    SCREEN_UNKNOWN = "unknown"

    # Resource types
    RESOURCE_MEAT = "meat"
    RESOURCE_WOOD = "wood"
    RESOURCE_COAL = "coal"
    RESOURCE_IRON = "iron"

    # Navigation paths (templates to validate each screen)
    SCREEN_VALIDATION = {
        SCREEN_HOME: "furnace_icon",
        SCREEN_WORLD: "world_map_ui",
        SCREEN_GATHER: "search_button",
        SCREEN_INTEL: "intel_ui",
        SCREEN_ARENA: "arena_ui",
        SCREEN_ALLIANCE: "alliance_ui",
        SCREEN_TRAINING: "training_ui",
    }

    # Action coordinates (approximate, will be refined with template matching)
    HOME_TO_WORLD = {"x": 650, "y": 100}
    WORLD_TO_HOME = {"x": 50, "y": 50}
    HOME_TO_INTEL = {"x": 100, "y": 600}
    HOME_TO_ARENA = {"x": 600, "y": 600}
    HOME_TO_ALLIANCE = {"x": 350, "y": 100}
