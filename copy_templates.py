#!/usr/bin/env python
"""
Copie les templates critiques depuis primebot vers new-bot/templates
"""

import shutil
from pathlib import Path

# Source et destination
primebot = Path("C:/Users/julie/primebot/images/whiteout")
newbot_templates = Path("C:/Users/julie/new-bot/templates")

newbot_templates.mkdir(parents=True, exist_ok=True)

# Templates critiques à copier
critical_templates = [
    # Navigation
    ("furnace/on.png", "furnace_icon.png"),
    ("furnace/off.png", "furnace_inactive.png"),
    ("menu/close.png", "popup_close.png"),
    ("menu/back.png", "back_arrow.png"),
    ("menu/back.png", "home_button.png"),
    
    # Actions
    ("gathering/gather.png", "gather_button.png"),
    
    # UI
    ("bonus/*.png", "bonus_*.png"),  # Wildcard
]

copied = 0
skipped = 0

print("=== Copie des templates critiques ===\n")

# Copies spécifiques
copies = [
    ("furnace/on.png", "furnace_icon.png"),
    ("furnace/off.png", "furnace_inactive.png"),
    ("menu/close.png", "popup_close.png"),
    ("menu/back.png", "back_arrow.png"),
    ("menu/back.png", "home_button.png"),
    ("gathering/gather.png", "gather_button.png"),
]

for src_name, dst_name in copies:
    src = primebot / src_name
    dst = newbot_templates / dst_name
    
    if src.exists():
        shutil.copy2(src, dst)
        print(f"✓ {src_name} → {dst_name}")
        copied += 1
    else:
        print(f"⚠ {src_name} (not found)")
        skipped += 1

# Copier des dossiers entiers
folders = ["popups", "bonus", "message_box"]

for folder in folders:
    src_folder = primebot / folder
    dst_folder = newbot_templates / folder
    
    if src_folder.exists():
        if dst_folder.exists():
            shutil.rmtree(dst_folder)
        shutil.copytree(src_folder, dst_folder)
        count = len(list(src_folder.glob("*.png")))
        print(f"✓ {folder}/ ({count} templates)")
        copied += count
    else:
        print(f"⚠ {folder}/ (not found)")
        skipped += 1

print(f"\n=== Résumé ===")
print(f"✓ Copiés: {copied}")
print(f"⚠ Manquants: {skipped}")
print(f"\nTemplates prêts dans: {newbot_templates}")
