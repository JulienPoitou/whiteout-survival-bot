"""
OCR module using Tesseract
Reads timers, quantities, and text from game screens
"""

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
from typing import Optional, Tuple, List
from dataclasses import dataclass
import re
import logging
from datetime import datetime, timedelta

from config import Config


@dataclass
class OCRResult:
    """Result of OCR reading"""
    text: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None


class OCRReader:
    """
    OCR reader for game text
    
    Features:
    - Image preprocessing for better accuracy
    - Pattern-based parsing (timers, numbers)
    - Retry logic with different settings
    """

    def __init__(self, language: str = None):
        self.language = language or Config.OCR_LANGUAGE
        self.logger = logging.getLogger(__name__)
        
        # Tesseract configuration
        self.base_config = f"--oem 3 --psm 6 -l {self.language}"
        
        self.logger.info(f"OCRReader initialized (language: {self.language})")

    def _preprocess_image(self, image: Image.Image, mode: str = "default") -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        
        Modes:
        - default: Standard enhancement
        - binary: High contrast black/white
        - inverse: Inverted colors
        - blur: Slight blur for noise reduction
        """
        # Convert to grayscale
        gray = image.convert('L')
        
        if mode == "binary":
            # High contrast threshold
            threshold = 128
            binary = gray.point(lambda x: 255 if x > threshold else 0, '1')
            return binary.convert('L')
        
        elif mode == "inverse":
            return Image.eval(gray, lambda x: 255 - x)
        
        elif mode == "blur":
            return gray.filter(ImageFilter.GaussianBlur(radius=1))
        
        else:  # default
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.5)
            
            # Sharpen
            enhanced = enhanced.filter(ImageFilter.SHARPEN)
            
            return enhanced

    def read(
        self,
        image: Image.Image,
        area: Optional[Tuple[int, int, int, int]] = None,
        mode: str = "default",
        pattern: Optional[str] = None
    ) -> Optional[str]:
        """
        Read text from image
        
        Args:
            image: Full screenshot
            area: Crop area (left, top, right, bottom) or None for full image
            mode: Preprocessing mode
            pattern: Regex pattern to validate/extract
            
        Returns:
            Extracted text or None
        """
        # Crop if area specified
        if area:
            crop = image.crop(area)
        else:
            crop = image
        
        # Preprocess
        processed = self._preprocess_image(crop, mode)
        
        # Try multiple configurations
        configs = [
            self.base_config,
            f"--oem 3 --psm 7 -l {self.language}",  # Single line
            f"--oem 3 --psm 8 -l {self.language}",  # Single word
        ]
        
        for config in configs:
            try:
                text = pytesseract.image_to_string(processed, config=config).strip()
                
                # Validate with pattern if provided
                if pattern and text:
                    match = re.search(pattern, text)
                    if match:
                        self.logger.debug(f"OCR matched: {match.group()}")
                        return match.group()
                    continue  # Try next config
                
                if text:
                    self.logger.debug(f"OCR result: {text}")
                    return text
                    
            except Exception as e:
                self.logger.warning(f"OCR error: {e}")
                continue
        
        return None

    def read_time(self, image: Image.Image, area: Tuple[int, int, int, int]) -> Optional[datetime]:
        """
        Read timer from image
        
        Expected formats:
        - HH:MM:SS
        - MM:SS
        - Xh Ym Zs
        
        Args:
            image: Screenshot
            area: Timer location
            
        Returns:
            datetime with timer value, or None
        """
        text = self.read(image, area, mode="default", pattern=r'\d+:\d+(:\d+)?|\d+h\s*\d*m\s*\d*s?')
        
        if not text:
            # Try with binary mode
            text = self.read(image, area, mode="binary", pattern=r'\d+:\d+(:\d+)?')
        
        if not text:
            return None
        
        return self._parse_time(text)

    def _parse_time(self, text: str) -> Optional[datetime]:
        """Parse time string to datetime"""
        text = text.strip().lower()
        
        # Format: HH:MM:SS or MM:SS
        if ':' in text:
            parts = text.split(':')
            now = datetime.now()
            
            try:
                if len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    return now + timedelta(minutes=minutes, seconds=seconds)
                elif len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    return now + timedelta(hours=hours, minutes=minutes, seconds=seconds)
            except ValueError:
                pass
        
        # Format: Xh Ym Zs
        hours = minutes = seconds = 0
        
        hour_match = re.search(r'(\d+)\s*h', text)
        min_match = re.search(r'(\d+)\s*m', text)
        sec_match = re.search(r'(\d+)\s*s', text)
        
        if hour_match:
            hours = int(hour_match.group(1))
        if min_match:
            minutes = int(min_match.group(1))
        if sec_match:
            seconds = int(sec_match.group(1))
        
        if hours or minutes or seconds:
            now = datetime.now()
            return now + timedelta(hours=hours, minutes=minutes, seconds=seconds)
        
        return None

    def read_number(self, image: Image.Image, area: Tuple[int, int, int, int]) -> Optional[int]:
        """
        Read number from image (resource quantity, level, etc.)
        
        Args:
            image: Screenshot
            area: Number location
            
        Returns:
            Integer value or None
        """
        text = self.read(image, area, mode="binary", pattern=r'\d+')
        
        if text:
            try:
                return int(text.replace(',', '').replace('.', ''))
            except ValueError:
                pass
        
        return None

    def read_text_block(
        self,
        image: Image.Image,
        area: Tuple[int, int, int, int]
    ) -> List[OCRResult]:
        """
        Read text block with bounding boxes
        
        Returns list of lines with their positions
        
        Args:
            image: Screenshot
            area: Text block location
            
        Returns:
            List of OCRResult with bbox
        """
        crop = image.crop(area)
        processed = self._preprocess_image(crop)
        
        try:
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
            
            results = []
            n_boxes = len(data['level'])
            
            for i in range(n_boxes):
                if data['text'][i].strip():
                    # Convert local coordinates to global
                    bbox = (
                        area[0] + data['left'][i],
                        area[1] + data['top'][i],
                        area[0] + data['left'][i] + data['width'][i],
                        area[1] + data['top'][i] + data['height'][i]
                    )
                    
                    results.append(OCRResult(
                        text=data['text'][i].strip(),
                        confidence=data['conf'][i],
                        bbox=bbox
                    ))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Text block OCR error: {e}")
            return []
