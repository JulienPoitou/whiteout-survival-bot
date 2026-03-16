"""
Script pour importer les templates depuis primebot/wos-bot vers new-bot
"""

import shutil
from pathlib import Path


# Mapping des templates primebot → new-bot naming
TEMPLATE_MAPPING = {
    # Navigation
    "furnace/on.png": "furnace_icon.png",
    "furnace/off.png": "furnace_icon_inactive.png",
    "menu/close.png": "popup_close.png",
    "menu/back.png": "home_button.png",
    
    # Gathering
    "gathering/gather.png": "gather_deploy_button.png",
    
    # Popups
    "popups": "popup_",  # Copier tout le dossier
}


def copy_templates():
    """Copy templates from primebot to new-bot"""
    
    primebot_dir = Path("C:/Users/julie/primebot/images/whiteout")
    newbot_templates = Path("C:/Users/julie/new-bot/templates")
    
    # Create destination
    newbot_templates.mkdir(parents=True, exist_ok=True)
    
    copied = []
    skipped = []
    
    print("=== Importing Templates ===\n")
    
    # Copy specific files
    mappings = [
        # Navigation
        ("furnace/on.png", "furnace_icon.png"),
        ("furnace/label.png", "furnace_label.png"),
        ("menu/close.png", "popup_close.png"),
        ("menu/back.png", "home_button.png"),
        
        # Gathering  
        ("gathering/gather.png", "gather_button.png"),
    ]
    
    for src_name, dst_name in mappings:
        src = primebot_dir / src_name
        dst = newbot_templates / dst_name
        
        if src.exists():
            shutil.copy2(src, dst)
            copied.append(src_name)
            print(f"✓ Copied: {src_name} → {dst_name}")
        else:
            skipped.append(src_name)
            print(f"⚠ Skipped (not found): {src_name}")
    
    # Copy entire folders
    folders_to_copy = [
        "popups",
        "bonus",
        "message_box",
    ]
    
    for folder in folders_to_copy:
        src_folder = primebot_dir / folder
        dst_folder = newbot_templates / folder
        
        if src_folder.exists():
            if dst_folder.exists():
                shutil.rmtree(dst_folder)
            shutil.copytree(src_folder, dst_folder)
            copied.append(f"{folder}/")
            print(f"✓ Copied folder: {folder}/")
        else:
            skipped.append(f"{folder}/")
            print(f"⚠ Skipped folder (not found): {folder}/")
    
    print(f"\n=== Summary ===")
    print(f"✓ Copied: {len(copied)} items")
    print(f"⚠ Skipped: {len(skipped)} items")
    
    # List what's still needed
    print(f"\n=== Templates Still Needed ===")
    needed = [
        "world_map_button.png",
        "world_map_ui.png",
        "search_button.png",
        "march_button.png",
        "resource_meat_icon.png",
        "resource_wood_icon.png",
        "resource_coal_icon.png",
        "resource_iron_icon.png",
    ]
    
    for template in needed:
        dst = newbot_templates / template
        if not dst.exists():
            print(f"  ❌ {template}")
        else:
            print(f"  ✓ {template}")


if __name__ == "__main__":
    copy_templates()
