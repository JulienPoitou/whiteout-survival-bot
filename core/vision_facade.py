"""
Hybrid Vision Facade
Intelligent router that chooses the best vision method for each task
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image

from config import Config, GameConfig
from core.context import GameContext, ScreenType
from vision.template_matcher import TemplateMatcher, MatchResult
from vision.ocr_reader import OCRReader
from vision.ai_analyzer import AIAnalyzer


class VisionFacade:
    """
    Unified interface for all vision operations
    
    Automatically chooses the best method:
    - Template Matching: Fast, reliable for UI elements
    - OCR: Reading text, numbers, timers
    - AI Vision: Complex decisions, context awareness
    
    Features:
    - Automatic method selection
    - Fallback mechanisms
    - Result caching
    - Performance tracking
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize vision modules
        self.template_matcher = TemplateMatcher()
        self.ocr_reader = OCRReader()
        self.ai_analyzer = AIAnalyzer()
        
        # Statistics
        self.stats = {
            "template_matches": 0,
            "ocr_reads": 0,
            "ai_analyses": 0,
            "fallbacks": 0
        }
        
        self.logger.info("VisionFacade initialized (Hybrid mode)")

    def find_element(
        self,
        screenshot: Image.Image,
        element_name: str,
        use_ai_fallback: bool = True
    ) -> Optional[MatchResult]:
        """
        Find UI element using best available method
        
        Args:
            screenshot: Current screen
            element_name: Template name to find
            use_ai_fallback: Try AI if template not found
            
        Returns:
            MatchResult or None
        """
        self.stats["template_matches"] += 1
        
        # Try template matching first (fastest)
        result = self.template_matcher.find(screenshot, element_name)
        
        if result.found:
            return result
        
        # Fallback to AI if enabled
        if use_ai_fallback and Config.ENABLE_AI_FALLBACK:
            self.stats["fallbacks"] += 1
            self.logger.debug(f"Template '{element_name}' not found, trying AI...")
            
            ai_result = self.ai_analyzer.analyze(
                screenshot,
                custom_prompt=f"Où se trouve l'élément '{element_name}' ? Retourne les coordonnées x, y ou null si absent."
            )
            
            if ai_result and ai_result.get("action") == "tap":
                return MatchResult(
                    found=True,
                    x=ai_result.get("x", 0),
                    y=ai_result.get("y", 0),
                    confidence=0.7,  # Lower confidence for AI
                    template_name=element_name
                )
        
        return None

    def find_any_element(
        self,
        screenshot: Image.Image,
        element_names: List[str]
    ) -> Optional[MatchResult]:
        """
        Find first matching element from list
        
        Args:
            screenshot: Current screen
            element_names: List of template names
            
        Returns:
            First MatchResult found
        """
        for name in element_names:
            result = self.find_element(screenshot, name, use_ai_fallback=False)
            if result and result.found:
                return result
        return None

    def detect_screen_type(
        self,
        screenshot: Image.Image,
        context: Optional[GameContext] = None
    ) -> ScreenType:
        """
        Detect current screen type
        
        Uses hybrid approach:
        1. Template matching for known validation templates
        2. AI analysis as fallback
        
        Args:
            screenshot: Current screen
            context: Optional game context
            
        Returns:
            ScreenType enum
        """
        # Try template-based detection first
        template_results = {}
        
        for screen_type, template_name in GameConfig.SCREEN_VALIDATION.items():
            result = self.template_matcher.find(screenshot, template_name, use_grayscale=True)
            template_results[template_name] = result.found
            
            if result.found:
                self.logger.debug(f"Screen detected via template: {screen_type}")
                return ScreenType(screen_type)
        
        # Fallback to AI
        self.stats["fallbacks"] += 1
        self.logger.debug("Using AI for screen detection")
        
        ai_screen_type = self.ai_analyzer.analyze_screen_type(screenshot, template_results)
        
        try:
            return ScreenType(ai_screen_type)
        except ValueError:
            return ScreenType.UNKNOWN

    def read_timer(
        self,
        screenshot: Image.Image,
        area: Tuple[int, int, int, int],
        use_ai_validation: bool = True
    ) -> Optional[Any]:
        """
        Read timer from screen
        
        Args:
            screenshot: Current screen
            area: Timer location (left, top, right, bottom)
            use_ai_validation: Validate OCR with AI
            
        Returns:
            datetime or None
        """
        self.stats["ocr_reads"] += 1
        
        # Read with OCR
        timer = self.ocr_reader.read_time(screenshot, area)
        
        # Validate with AI if enabled
        if use_ai_validation and Config.ENABLE_AI_FALLBACK and timer:
            # Crop timer area for AI validation
            timer_crop = screenshot.crop(area)
            
            ocr_text = self.ocr_reader.read(screenshot, area)
            if ocr_text:
                corrected = self.ai_analyzer.validate_ocr(
                    timer_crop,
                    ocr_text,
                    "HH:MM:SS or MM:SS",
                    "timer"
                )
                
                if corrected and corrected != ocr_text:
                    self.logger.debug(f"AI corrected OCR: '{ocr_text}' → '{corrected}'")
                    return self.ocr_reader._parse_time(corrected)
        
        return timer

    def read_number(
        self,
        screenshot: Image.Image,
        area: Tuple[int, int, int, int]
    ) -> Optional[int]:
        """
        Read number from screen (resource quantity, level, etc.)
        
        Args:
            screenshot: Current screen
            area: Number location
            
        Returns:
            Integer or None
        """
        self.stats["ocr_reads"] += 1
        return self.ocr_reader.read_number(screenshot, area)

    def analyze_and_decide(
        self,
        screenshot: Image.Image,
        context: GameContext
    ) -> Dict[str, Any]:
        """
        Analyze screen and return action decision
        
        This is the main entry point for bot decisions.
        Combines all vision methods for optimal decision.
        
        Args:
            screenshot: Current screen
            context: Current game context
            
        Returns:
            Dict with action decision
        """
        self.stats["ai_analyses"] += 1
        
        # Step 1: Detect screen type
        screen_type = self.detect_screen_type(screenshot, context)
        context.update_screen(screen_type)
        
        # Step 2: Check for anomalies (popups, errors)
        anomalies = self.ai_analyzer.detect_anomalies(screenshot)
        
        if anomalies:
            self.logger.warning(f"Anomalies detected: {anomalies}")
            return {
                "action": "error",
                "reason": f"Anomalies: {', '.join(anomalies)}",
                "anomalies": anomalies,
                "priority": "high"
            }
        
        # Step 3: Get AI decision with full context
        ai_decision = self.ai_analyzer.analyze(screenshot, context.to_dict())
        
        if ai_decision:
            ai_decision["screen_type"] = screen_type.value
            return ai_decision
        
        # Fallback: safe default
        return {
            "action": "wait",
            "reason": "No decision from AI",
            "priority": "low"
        }

    def navigate_to_screen(
        self,
        screenshot: Image.Image,
        target_screen: ScreenType,
        context: GameContext
    ) -> Optional[Dict[str, Any]]:
        """
        Get navigation action to reach target screen
        
        Args:
            screenshot: Current screen
            target_screen: Desired screen type
            context: Current game context
            
        Returns:
            Action dict (tap coordinates) or None
        """
        current_screen = self.detect_screen_type(screenshot, context)
        
        if current_screen == target_screen:
            self.logger.debug(f"Already on {target_screen.value} screen")
            return None
        
        # Navigation map (simplified)
        navigation_actions = {
            (ScreenType.HOME, ScreenType.WORLD): GameConfig.HOME_TO_WORLD,
            (ScreenType.HOME, ScreenType.INTEL): GameConfig.HOME_TO_INTEL,
            (ScreenType.HOME, ScreenType.ARENA): GameConfig.HOME_TO_ARENA,
            (ScreenType.HOME, ScreenType.ALLIANCE): GameConfig.HOME_TO_ALLIANCE,
            (ScreenType.WORLD, ScreenType.HOME): GameConfig.WORLD_TO_HOME,
        }
        
        key = (current_screen, target_screen)
        
        if key in navigation_actions:
            action = navigation_actions[key]
            return {
                "action": "tap",
                "x": action["x"],
                "y": action["y"],
                "reason": f"Navigate from {current_screen.value} to {target_screen.value}",
                "priority": "high"
            }
        
        # Unknown path - ask AI
        self.logger.warning(f"Unknown navigation path: {current_screen.value} → {target_screen.value}")
        return self.ai_analyzer.analyze(
            screenshot,
            custom_prompt=f"Comment aller à l'écran {target_screen.value} depuis l'écran actuel ?"
        )

    def get_stats(self) -> Dict[str, int]:
        """Get vision usage statistics"""
        return self.stats.copy()

    def preload_templates(self, template_names: List[str]):
        """Preload templates into cache"""
        self.template_matcher.preload_templates(template_names)

    def is_ready(self) -> bool:
        """Check if all vision modules are ready"""
        # Check ADB connection would be done elsewhere
        # Check AI availability
        ai_available = self.ai_analyzer.is_available()
        
        if not ai_available:
            self.logger.warning("AI analyzer not available (Ollama not running?)")
        
        # Template matching and OCR should always work if dependencies installed
        return True  # Assume ready, AI is optional fallback
