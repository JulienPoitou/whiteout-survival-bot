#!/usr/bin/env python
"""
Test du scaling de coordonnées
"""

from config import Config

print("=" * 60)
print("📊 TEST DU SCALING DE COORDONNÉES")
print("=" * 60)
print()
print(f"SCREEN resolution:   {Config.SCREEN_WIDTH}x{Config.SCREEN_HEIGHT}")
print(f"CAPTURE resolution:  {Config.CAPTURE_WIDTH}x{Config.CAPTURE_HEIGHT}")
print()
print(f"SCALE_X: {Config.SCALE_X:.2f}")
print(f"SCALE_Y: {Config.SCALE_Y:.2f}")
print()
print("Exemples de conversion (CAPTURE → SCREEN) :")
print("-" * 60)

test_coords = [
    (37, 266),   # furnace_icon
    (68, 198),   # home_button
    (166, 467),  # furnace_icon (autre pos)
    (200, 326),  # centre écran
]

for x, y in test_coords:
    real_x = int(x * Config.SCALE_X)
    real_y = int(y * Config.SCALE_Y)
    print(f"  ({x:3d}, {y:3d}) → ({real_x:4d}, {real_y:4d})")

print()
print("Ces coordonnées seront utilisées pour les clicks ADB.")
print("=" * 60)
