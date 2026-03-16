"""
Template Matching module using OpenCV
Fast and reliable UI element detection

Supports:
- Local templates in templates/ folder
- Legacy templates from primebot/wos-bot
- Auto-generated templates from AI
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging

from config import Config


@dataclass
class MatchResult:
    """Result of template matching"""
    found: bool
    x: int  # Center X coordinate
    y: int  # Center Y coordinate
    confidence: float  # Match confidence (0-1)
    template_name: str


class TemplateMatcher:
    """
    Template matching using OpenCV
    
    Features:
    - Template caching for performance
    - Grayscale matching for robustness
    - Region of interest (ROI) support
    - Multi-scale support
    """

    def __init__(self, templates_dir: str = None, threshold: float = None):
        self.templates_dir = Path(templates_dir) if templates_dir else Config.TEMPLATES_DIR
        self.threshold = threshold or Config.TEMPLATE_MATCH_THRESHOLD
        self.logger = logging.getLogger(__name__)
        
        # Template cache: {template_name: cv2_image}
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_gray: Dict[str, np.ndarray] = {}
        
        self.logger.info(f"TemplateMatcher initialized (threshold: {self.threshold})")

    def _load_template(self, name: str, grayscale: bool = False) -> Optional[np.ndarray]:
        """Load template from cache, local folder, or legacy projects"""
        cache = self._cache_gray if grayscale else self._cache
        cache_key = f"{name}_gray" if grayscale else name
        
        if cache_key in cache:
            return cache[cache_key]
        
        # Try to find template file - multiple strategies
        template_paths = [
            # 1. Local templates folder
            self.templates_dir / f"{name}.png",
            self.templates_dir / f"{name}.jpg",
            
            # 2. Auto-generated templates
            self.templates_dir / "auto_generated" / f"{name}.png",
            
            # 3. Legacy primebot templates (folder-based)
            Path("C:/Users/julie/primebot/images/whiteout") / f"{name.replace('_', '/')}.png",
            
            # 4. Legacy primebot - common folders
            Path("C:/Users/julie/primebot/images/whiteout/furnace") / f"{name.replace('furnace_', '')}.png",
            Path("C:/Users/julie/primebot/images/whiteout/menu") / f"{name.replace('menu_', '')}.png",
            Path("C:/Users/julie/primebot/images/whiteout/popups") / f"{name.replace('popup_', '')}.png",
            Path("C:/Users/julie/primebot/images/whiteout/gathering") / f"{name.replace('gather_', '')}.png",
            Path("C:/Users/julie/primebot/images/whiteout/buildings") / f"{name.replace('building_', '')}.png",
            
            # 5. Legacy wos-bot images
            Path("C:/Users/julie/wos-bot/wos-hmi/src/main/resources/images") / f"{name}.png",
        ]
        
        for path in template_paths:
            if path.exists():
                if grayscale:
                    template = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                else:
                    template = cv2.imread(str(path), cv2.IMREAD_COLOR)
                
                if template is not None:
                    cache[cache_key] = template
                    self.logger.debug(f"Loaded template: {name} from {path}")
                    return template
        
        self.logger.warning(f"Template not found: {name}")
        return None

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        cv2_image = np.array(pil_image)
        # Convert RGB to BGR for OpenCV
        if len(cv2_image.shape) == 3:
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR)
        return cv2_image

    def find(
        self,
        screenshot: Image.Image,
        template_name: str,
        threshold: float = None,
        roi: Optional[Tuple[int, int, int, int]] = None,
        use_grayscale: bool = True
    ) -> MatchResult:
        """
        Find template in screenshot
        
        Args:
            screenshot: PIL Image of the screen
            template_name: Name of template file (without extension)
            threshold: Match threshold (0-1), overrides default
            roi: Region of interest (x, y, width, height) or None for full screen
            use_grayscale: Use grayscale matching for robustness
            
        Returns:
            MatchResult with coordinates and confidence
        """
        threshold = threshold or self.threshold
        
        # Load template
        template = self._load_template(template_name, grayscale=use_grayscale)
        if template is None:
            return MatchResult(False, 0, 0, 0.0, template_name)
        
        # Convert screenshot to OpenCV format
        cv2_image = self._pil_to_cv2(screenshot)
        if use_grayscale:
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        
        # Apply ROI if specified
        if roi:
            x, y, w, h = roi
            cv2_image = cv2_image[y:y+h, x:x+w]
        
        # Check dimensions
        if cv2_image.shape[0] < template.shape[0] or cv2_image.shape[1] < template.shape[1]:
            self.logger.warning(f"Screenshot too small for template {template_name}")
            return MatchResult(False, 0, 0, 0.0, template_name)
        
        # Perform template matching
        method = cv2.TM_CCOEFF_NORMED
        result = cv2.matchTemplate(cv2_image, template, method)
        
        # Find best match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Calculate center coordinates
        template_h, template_w = template.shape[:2]
        center_x = max_loc[0] + template_w // 2
        center_y = max_loc[1] + template_h // 2
        
        # Adjust for ROI
        if roi:
            center_x += roi[0]
            center_y += roi[1]
        
        found = max_val >= threshold
        
        if found:
            self.logger.debug(f"✓ Found '{template_name}' at ({center_x}, {center_y}) - {max_val:.2%}")
        else:
            self.logger.debug(f"✗ '{template_name}' not found (best: {max_val:.2%})")
        
        return MatchResult(
            found=found,
            x=center_x,
            y=center_y,
            confidence=max_val,
            template_name=template_name
        )

    def find_all(
        self,
        screenshot: Image.Image,
        template_name: str,
        threshold: float = None,
        max_results: int = 10
    ) -> List[MatchResult]:
        """
        Find all occurrences of template in screenshot
        
        Args:
            screenshot: PIL Image
            template_name: Template name
            threshold: Match threshold
            max_results: Maximum number of results
            
        Returns:
            List of MatchResult
        """
        threshold = threshold or self.threshold
        
        # Load template
        template = self._load_template(template_name, grayscale=True)
        if template is None:
            return []
        
        # Convert screenshot
        cv2_image = self._pil_to_cv2(screenshot)
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        
        # Match
        method = cv2.TM_CCOEFF_NORMED
        result = cv2.matchTemplate(cv2_image, template, method)
        
        results = []
        template_h, template_w = template.shape[:2]
        
        while len(results) < max_results:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val < threshold:
                break
            
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2
            
            results.append(MatchResult(
                found=True,
                x=center_x,
                y=center_y,
                confidence=max_val,
                template_name=template_name
            ))
            
            # Mask out this match to find next
            top_left = max_loc
            bottom_right = (top_left[0] + template_w, top_left[1] + template_h)
            cv2.rectangle(result, top_left, bottom_right, 0, -1)
        
        return results

    def find_any(
        self,
        screenshot: Image.Image,
        template_names: List[str],
        threshold: float = None
    ) -> Optional[MatchResult]:
        """
        Find first matching template from a list
        
        Useful for multi-region templates (e.g., different language versions)
        
        Args:
            screenshot: PIL Image
            template_names: List of template names to try
            threshold: Match threshold
            
        Returns:
            First MatchResult found, or None
        """
        for name in template_names:
            result = self.find(screenshot, name, threshold)
            if result.found:
                return result
        return None

    def clear_cache(self):
        """Clear template cache"""
        self._cache.clear()
        self._cache_gray.clear()
        self.logger.info("Template cache cleared")

    def preload_templates(self, template_names: List[str]):
        """Preload templates into cache"""
        for name in template_names:
            self._load_template(name)
            self._load_template(name, grayscale=True)
        self.logger.info(f"Preloaded {len(template_names)} templates")
