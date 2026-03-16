"""
Legacy Template Loader
Utilise les templates existants de wos-bot/primebot sans copier
"""

from pathlib import Path
import cv2
import numpy as np
from typing import Optional, Dict


class LegacyTemplateLoader:
    """
    Charge les templates depuis les anciens projets
    sans avoir besoin de les copier
    """
    
    def __init__(self):
        self.primbot_dir = Path("C:/Users/julie/primebot/images/whiteout")
        self.wosbot_dir = Path("C:/Users/julie/wos-bot")
        
        # Cache des templates chargés
        self.templates: Dict[str, np.ndarray] = {}
    
    def get_template(self, name: str) -> Optional[np.ndarray]:
        """
        Get template by name (with automatic lookup)
        
        Args:
            name: Template name (e.g., "furnace_icon")
            
        Returns:
            OpenCV image or None
        """
        if name in self.templates:
            return self.templates[name]
        
        # Search strategies
        paths_to_try = [
            # Direct mapping
            self.primbot_dir / f"{name}.png",
            self.primbot_dir / f"{name}.jpg",
            
            # Folder-based (furnace/on.png → furnace_on.png)
            self.primbot_dir / f"{name.replace('_', '/')}.png",
            
            # Common folders
            self.primbot_dir / "furnace" / f"{name.replace('furnace_', '')}.png",
            self.primbot_dir / "menu" / f"{name.replace('menu_', '')}.png",
            self.primbot_dir / "popups" / f"{name.replace('popup_', '')}.png",
            self.primbot_dir / "gathering" / f"{name.replace('gather_', '')}.png",
        ]
        
        for path in paths_to_try:
            if path.exists():
                template = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self.templates[name] = template
                    print(f"✓ Loaded template: {name} from {path}")
                    return template
        
        print(f"✗ Template not found: {name}")
        return None
    
    def list_available_templates(self) -> list:
        """List all available templates in primebot"""
        templates = []
        
        if not self.primbot_dir.exists():
            return templates
        
        # Scan all PNG files
        for png in self.primbot_dir.rglob("*.png"):
            # Convert path to name
            rel_path = png.relative_to(self.primbot_dir)
            name = str(rel_path.with_suffix('')).replace('/', '_')
            templates.append(name)
        
        return templates
    
    def preload_common_templates(self):
        """Preload commonly used templates"""
        common = [
            "furnace_on",
            "furnace_off",
            "menu_close",
            "menu_back",
            "gathering_gather",
            "popups_close",
        ]
        
        for name in common:
            self.get_template(name)


# Usage example in template_matcher.py
"""
from scripts.legacy_loader import LegacyTemplateLoader

loader = LegacyTemplateLoader()

# In TemplateMatcher._load_template():
template = loader.get_template(template_name)
if template is not None:
    return template
"""


if __name__ == "__main__":
    loader = LegacyTemplateLoader()
    
    print("=== Available Templates ===\n")
    
    templates = loader.list_available_templates()
    
    print(f"Found {len(templates)} templates in primebot/\n")
    
    # Show first 20
    for t in templates[:20]:
        print(f"  - {t}")
    
    if len(templates) > 20:
        print(f"  ... and {len(templates) - 20} more")
    
    print("\n=== Testing Load ===")
    
    test_templates = [
        "furnace_on",
        "menu_close",
        "gathering_gather",
    ]
    
    for name in test_templates:
        template = loader.get_template(name)
        if template is not None:
            print(f"  ✓ {name}: {template.shape}")
