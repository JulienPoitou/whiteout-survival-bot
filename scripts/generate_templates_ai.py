"""
Template Generator using AI Vision
Analyse un screenshot et génère automatiquement les templates
"""

import base64
import io
import json
import requests
from pathlib import Path
from PIL import Image


def image_to_base64(image_path: str) -> str:
    """Convert image to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def analyze_screenshot_for_templates(image_path: str) -> dict:
    """
    Use AI to identify UI elements in screenshot
    
    Returns dict with element names and bounding boxes
    """
    img_base64 = image_to_base64(image_path)
    
    prompt = """
Analyse ce screenshot de Whiteout Survival (720x1280).

Identifie TOUS les éléments d'UI cliquables et retourne un JSON avec :
- name: nom de l'élément (en anglais, snake_case)
- type: "button", "icon", "resource", "popup", "text"
- bbox: [x1, y1, x2, y2] coordonnées du rectangle
- priority: "high", "medium", "low"

Éléments à chercher :
- Boutons de navigation (home, world, map, back)
- Icônes de ressources (meat, wood, coal, iron)
- Boutons d'action (gather, train, upgrade, deploy)
- Popups et leurs boutons de fermeture
- Éléments de menu

Format de réponse :
{
  "elements": [
    {"name": "furnace_icon", "type": "icon", "bbox": [300, 450, 380, 530], "priority": "high"},
    ...
  ]
}

Sois précis sur les coordonnées.
"""
    
    payload = {
        "model": "qwen2.5vl:7b",  # Utiliser un modèle plus précis
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": f"data:image/png;base64,{img_base64}"},
                {"type": "text", "text": prompt}
            ]
        }],
        "options": {
            "temperature": 0.1,
            "max_tokens": 2048
        }
    }
    
    response = requests.post(
        "http://localhost:11434/api/chat",
        json=payload,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result["message"]["content"]
        
        # Extract JSON
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start != -1 and end > start:
            return json.loads(content[start:end])
    
    return {"elements": []}


def extract_templates(screenshot_path: str, output_dir: str, elements: list):
    """
    Extract template images from screenshot based on bounding boxes
    
    Args:
        screenshot_path: Path to full screenshot
        output_dir: Directory to save templates
        elements: List of elements with bbox
    """
    screenshot = Image.open(screenshot_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    extracted = []
    
    for element in elements:
        name = element.get("name", "unknown")
        bbox = element.get("bbox", [])
        
        if len(bbox) != 4:
            print(f"⚠ Invalid bbox for {name}: {bbox}")
            continue
        
        x1, y1, x2, y2 = bbox
        
        # Validate coordinates
        if x2 <= x1 or y2 <= y1:
            print(f"⚠ Invalid coordinates for {name}")
            continue
        
        # Add small padding
        padding = 2
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(screenshot.width, x2 + padding)
        y2 = min(screenshot.height, y2 + padding)
        
        # Extract template
        template = screenshot.crop((x1, y1, x2, y2))
        
        # Save
        filename = f"{name}.png"
        template.save(output_path / filename)
        extracted.append(filename)
        
        print(f"✓ Extracted: {filename} ({x2-x1}x{y2-y1})")
    
    return extracted


def main():
    """Main script"""
    import sys
    
    print("=== AI Template Generator ===\n")
    
    # Get screenshot path
    if len(sys.argv) > 1:
        screenshot_path = sys.argv[1]
    else:
        screenshot_path = input("Screenshot path (or drag & drop): ").strip().strip('"')
    
    if not Path(screenshot_path).exists():
        print(f"✗ File not found: {screenshot_path}")
        return
    
    print(f"\nAnalyzing screenshot: {screenshot_path}")
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("✗ Ollama not running. Start it with: ollama serve")
            return
    except Exception:
        print("✗ Ollama not running. Start it with: ollama serve")
        return
    
    # Analyze with AI
    print("Analyzing with AI (this may take 10-30 seconds)...")
    
    try:
        result = analyze_screenshot_for_templates(screenshot_path)
        elements = result.get("elements", [])
        
        if not elements:
            print("✗ No elements detected by AI")
            return
        
        print(f"\n✓ Detected {len(elements)} elements:\n")
        
        for elem in elements:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[elem.get("priority", "low")]
            print(f"  {priority_icon} {elem['name']} ({elem['type']}) - bbox: {elem['bbox']}")
        
        # Extract templates
        output_dir = Path("C:/Users/julie/new-bot/templates/auto_generated")
        
        print(f"\nExtracting templates to: {output_dir}")
        extracted = extract_templates(screenshot_path, str(output_dir), elements)
        
        print(f"\n=== Summary ===")
        print(f"✓ Generated {len(extracted)} templates")
        print(f"📁 Saved to: {output_dir}")
        
        print("\n=== Next Steps ===")
        print("1. Review generated templates")
        print("2. Copy needed templates to main templates/ folder")
        print("3. Rename if necessary")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("  - Ollama is running: ollama serve")
        print("  - Model is installed: ollama pull qwen2.5vl:7b")


if __name__ == "__main__":
    main()
