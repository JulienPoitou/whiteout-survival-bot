"""
AI Vision Analyzer using Qwen2.5-VL / Moondream via Ollama
Handles complex decisions and context-aware analysis
"""

import base64
import io
import json
import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import requests

from config import Config


class AIAnalyzer:
    """
    AI vision analyzer for complex game decisions
    
    Uses Qwen2.5-VL or Moondream via Ollama API to:
    - Analyze game state
    - Make farming decisions
    - Detect anomalies
    - Validate OCR results
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        model: str = None
    ):
        self.host = host or Config.OLLAMA_HOST
        self.port = port or Config.OLLAMA_PORT
        self.model = model or Config.OLLAMA_MODEL
        self.base_url = f"http://{self.host}:{self.port}"
        self.logger = logging.getLogger(__name__)
        
        # System prompt for game analysis
        self.system_prompt = """Tu es un assistant expert pour le jeu Whiteout Survival.
Tu analyses des screenshots du jeu et tu prends des décisions pour optimiser le farm de ressources.

Réponds UNIQUEMENT en JSON avec ce format exact:
{
  "action": "tap" | "swipe" | "wait" | "navigate" | "error",
  "x": <number ou null>,
  "y": <number ou null>,
  "x2": <number ou null pour swipe>,
  "y2": <number ou null pour swipe>,
  "reason": "explication courte en anglais",
  "priority": "high" | "medium" | "low",
  "screen_type": "home" | "world" | "gather" | "intel" | "arena" | "unknown",
  "anomalies": ["popup", "maintenance", "error", "loading"] ou []
}

Règles:
- Si un popup/publicité est présent, retourne action="error" avec anomalies=["popup"]
- Si l'écran est en chargement, retourne action="wait"
- Privilégie les actions de farm de ressources (nourriture, bois, charbon, fer)
- Si rien à faire, retourne action="wait"
- Coordonnées doivent être dans l'écran 720x1280"""

        self.logger.info(f"AIAnalyzer initialized (model: {self.model})")

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def analyze(
        self,
        image: Image.Image,
        context: Optional[Dict[str, Any]] = None,
        custom_prompt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze screenshot and return action decision
        
        Args:
            image: Screenshot to analyze
            context: Optional game context (current screen, last action, etc.)
            custom_prompt: Optional custom prompt to override default
            
        Returns:
            Dict with action decision or None if error
        """
        try:
            # Convert image to base64
            img_base64 = self._image_to_base64(image)
            
            # Build context-aware prompt
            prompt = self._build_prompt(context, custom_prompt)
            
            # Prepare Ollama API request
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{img_base64}"
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "options": {
                    "temperature": 0.3,  # Low temperature for consistency
                    "max_tokens": 512
                }
            }
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                # Parse JSON response
                return self._parse_response(content)
            else:
                self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            self.logger.error("Could not connect to Ollama. Is it running?")
            return None
        except Exception as e:
            self.logger.error(f"AI analysis error: {e}")
            return None

    def _build_prompt(
        self,
        context: Optional[Dict[str, Any]],
        custom_prompt: Optional[str]
    ) -> str:
        """Build prompt with optional context"""
        if custom_prompt:
            return custom_prompt
        
        prompt = "Quelle action faire pour optimiser le farm de ressources ?\n"
        
        if context:
            prompt += "\nContexte actuel:\n"
            
            if "current_screen" in context:
                prompt += f"- Écran: {context['current_screen']}\n"
            
            if "last_action" in context:
                prompt += f"- Dernière action: {context['last_action']}\n"
            
            if "active_marches" in context:
                prompt += f"- Marches actives: {len(context['active_marches'])}\n"
            
            if "target_resources" in context:
                targets = context['target_resources']
                prompt += f"- Objectifs: bois={targets.get('wood', '?')}, nourriture={targets.get('meat', '?')}, charbon={targets.get('coal', '?')}, fer={targets.get('iron', '?')}\n"
        
        return prompt

    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response"""
        try:
            # Try to find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = content[start:end]
                parsed = json.loads(json_str)
                
                # Validate required fields
                if "action" not in parsed:
                    parsed["action"] = "none"
                if "reason" not in parsed:
                    parsed["reason"] = "No reason provided"
                
                return parsed
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parse error: {e}")
        
        # Fallback: return safe default
        return {
            "action": "wait",
            "reason": "Could not parse AI response",
            "priority": "low"
        }

    def analyze_screen_type(
        self,
        image: Image.Image,
        template_results: Dict[str, bool]
    ) -> str:
        """
        Determine current screen type using AI + template results
        
        Args:
            image: Screenshot
            template_results: Dict of {template_name: found}
            
        Returns:
            Screen type string
        """
        # First try template-based detection
        screen_templates = {
            "home": ["furnace_icon", "home_ui"],
            "world": ["world_map_ui", "map_coordinates"],
            "gather": ["search_button", "gather_ui"],
            "intel": ["intel_ui", "intel_tab"],
            "arena": ["arena_ui", "arena_button"],
            "alliance": ["alliance_ui", "alliance_tab"],
        }
        
        for screen_type, templates in screen_templates.items():
            for template in templates:
                if template_results.get(template, False):
                    self.logger.debug(f"Screen detected via template: {screen_type}")
                    return screen_type
        
        # Fallback to AI
        self.logger.debug("Using AI for screen detection")
        result = self.analyze(image, custom_prompt="Quel type d'écran est affiché ? Réponds juste: home, world, gather, intel, arena, alliance, ou unknown")
        
        if result:
            return result.get("screen_type", "unknown")
        
        return "unknown"

    def validate_ocr(
        self,
        image: Image.Image,
        ocr_text: str,
        expected_pattern: str,
        area_description: str
    ) -> Optional[str]:
        """
        Use AI to validate/correct OCR result
        
        Args:
            image: Screenshot
            ocr_text: Raw OCR output
            expected_pattern: Expected format (e.g., "HH:MM:SS", "number")
            area_description: What the area contains
            
        Returns:
            Corrected text or None
        """
        try:
            img_base64 = self._image_to_base64(image)
            
            prompt = f"""J'ai lu ce texte avec OCR: "{ocr_text}"
Zone: {area_description}
Format attendu: {expected_pattern}

Est-ce correct ? Si oui, retourne le texte corrigé au format attendu.
Si non, retourne null.

Réponds juste avec le texte corrigé ou null."""
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{img_base64}"
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 64
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("message", {}).get("content", "").strip()
                
                if text.lower() == "null" or text.lower() == "none":
                    return None
                
                return text
            
        except Exception as e:
            self.logger.error(f"OCR validation error: {e}")
        
        return ocr_text  # Return original on error

    def detect_anomalies(self, image: Image.Image) -> List[str]:
        """
        Detect unexpected elements (popups, errors, maintenance)
        
        Args:
            image: Screenshot
            
        Returns:
            List of anomaly types
        """
        result = self.analyze(image, custom_prompt="Y a-t-il des éléments anormaux ? (publicité, popup, erreur, maintenance, chargement). Réponds en JSON: {\"anomalies\": [\"popup\", ...]} ou {\"anomalies\": []}")
        
        if result:
            return result.get("anomalies", [])
        
        return []

    def is_available(self) -> bool:
        """Check if Ollama API is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
