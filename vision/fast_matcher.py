"""
Fast OpenCV Template Matching
Remplaces slow AI vision for UI element detection

Performance: 0.01s vs 15-30s for AI inference
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


class FastTemplateMatcher:
    """
    Ultra-fast template matching using OpenCV
    
    Performance:
    - Single template: ~0.001s
    - 10 templates: ~0.01s
    - 100 templates: ~0.1s
    
    Vs AI inference: 15-30s
    """

    def __init__(self, templates_dir: str = None, threshold: float = 0.85):
        self.templates_dir = Path(templates_dir) if templates_dir else Config.TEMPLATES_DIR
        self.threshold = threshold
        self.logger = logging.getLogger(__name__)

        # Cache: {template_name: cv2_image} - thread-safe with lock
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_lock = threading.Lock()

        # Also search in primebot legacy templates
        self.legacy_dirs = [
            Path("C:/Users/julie/primebot/images/whiteout"),
            Path("C:/Users/julie/wos-bot/wos-hmi/src/main/resources/images"),
        ]
        
        self.logger.info(f"FastTemplateMatcher initialized (threshold: {self.threshold})")

    def _load_template(self, name: str) -> Optional[np.ndarray]:
        """Load template from cache or disk (including legacy dirs)"""
        # Thread-safe cache check
        with self._cache_lock:
            if name in self._cache:
                return self._cache[name]

        # Search locations (outside lock - disk I/O)
        search_paths = [
            self.templates_dir / f"{name}.png",
            self.templates_dir / f"{name}.jpg",
        ]

        # Add legacy paths
        for legacy_dir in self.legacy_dirs:
            if legacy_dir.exists():
                # Try direct
                search_paths.append(legacy_dir / f"{name}.png")
                search_paths.append(legacy_dir / f"{name}.jpg")

                # Try folder-based (e.g., furnace/on.png)
                if '_' in name:
                    parts = name.split('_')
                    search_paths.append(legacy_dir / parts[0] / f"{'_'.join(parts[1:])}.png")

        # Search and load
        for path in search_paths:
            if path.exists():
                template = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    # Thread-safe cache write
                    with self._cache_lock:
                        self._cache[name] = template
                    self.logger.debug(f"Loaded template: {name} from {path}")
                    return template

        self.logger.debug(f"Template not found: {name}")
        return None

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        cv2_image = np.array(pil_image)
        if len(cv2_image.shape) == 3:
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR)
        return cv2_image

    def find(
        self,
        screenshot: Image.Image,
        template_name: str,
        threshold: float = None,
        roi: Optional[Tuple[int, int, int, int]] = None
    ) -> MatchResult:
        """
        Find template in screenshot (FAST)
        
        Args:
            screenshot: PIL Image
            template_name: Template to find
            threshold: Match threshold (0-1)
            roi: Region of interest (x, y, width, height)
            
        Returns:
            MatchResult with coordinates
        """
        threshold = threshold or self.threshold
        
        # Load template
        template = self._load_template(template_name)
        if template is None:
            return MatchResult(False, 0, 0, 0.0, template_name)
        
        # Convert screenshot
        cv2_image = self._pil_to_cv2(screenshot)
        cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        
        # Apply ROI if specified
        if roi:
            x, y, w, h = roi
            cv2_image = cv2_image[y:y+h, x:x+w]
        
        # Check dimensions
        if cv2_image.shape[0] < template.shape[0] or cv2_image.shape[1] < template.shape[1]:
            return MatchResult(False, 0, 0, 0.0, template_name)
        
        # Template matching (FAST)
        result = cv2.matchTemplate(cv2_image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Calculate center
        template_h, template_w = template.shape
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

    def find_any(
        self,
        screenshot: Image.Image,
        template_names: List[str],
        threshold: float = None
    ) -> Optional[MatchResult]:
        """Find first matching template from list"""
        threshold = threshold or self.threshold
        
        for name in template_names:
            result = self.find(screenshot, name, threshold)
            if result.found:
                return result
        
        return None

    def find_all_templates(
        self,
        screenshot: Image.Image,
        template_names: List[str],
        threshold: float = None
    ) -> List[MatchResult]:
        """Find all matching templates from list"""
        results = []
        
        for name in template_names:
            result = self.find(screenshot, name, threshold)
            if result.found:
                results.append(result)
        
        return results

    def clear_cache(self):
        """Clear template cache"""
        self._cache.clear()
        self.logger.info("Template cache cleared")

    def preload(self, template_names: List[str]):
        """Preload templates into cache"""
        for name in template_names:
            self._load_template(name)
        self.logger.info(f"Preloaded {len(template_names)} templates")
