#!/usr/bin/env python
"""
Test des fixes ADB + Screenshot + Vision
"""

import time
import sys

print("=" * 60)
print("🧪 TEST DES FIXES")
print("=" * 60)

# Test 1: ADB version
print("\n[1/5] Vérification ADB version...")
from adb.controller import ADB_PATH
print(f"  ADB Path: {ADB_PATH}")

import subprocess
result = subprocess.run(f'"{ADB_PATH}" version', shell=True, capture_output=True, text=True)
if "1.0.41" in result.stdout or "36.0.0" in result.stdout:
    print("  ✅ ADB version 41 OK")
else:
    print("  ⚠️  ADB version peut-être ancienne")
    print(result.stdout[:200])

# Test 2: Connexion
print("\n[2/5] Connexion ADB...")
from config import Config
Config.ensure_dirs()
from adb.controller import ADBController

start = time.time()
adb = ADBController()
conn_time = time.time() - start
print(f"  Device: {adb.device}")
print(f"  Temps création: {conn_time:.2f}s")

start = time.time()
adb.connect()
conn_time = time.time() - start
print(f"  Temps connexion: {conn_time:.2f}s")
if conn_time < 5:
    print("  ✅ Connexion RAPIDE")
elif conn_time < 10:
    print("  ⚠️  Connexion OK (un peu lente)")
else:
    print("  ❌ Connexion trop lente")

# Test 3: Screenshot
print("\n[3/5] Screenshot (exec-out)...")
start = time.time()
img = adb.screenshot()
scr_time = time.time() - start

if img:
    print(f"  ✅ Screenshot OK: {img.size}")
    print(f"  Temps: {scr_time:.2f}s")
    if scr_time < 5:
        print("  🚀 ULTRA RAPIDE !")
    elif scr_time < 10:
        print("  ✅ RAPIDE")
    else:
        print("  ⚠️  Encore lent")
else:
    print("  ❌ Screenshot FAILED")

# Test 4: Template Matching
print("\n[4/5] Template Matching (OpenCV)...")
from vision.fast_matcher import FastTemplateMatcher

matcher = FastTemplateMatcher(threshold=0.8)

# Test avec un template qui devrait exister
start = time.time()
result = matcher.find(img, "furnace_icon")
match_time = time.time() - start

print(f"  Template: furnace_icon")
print(f"  Trouvé: {result.found} (confiance: {result.confidence:.2%})")
print(f"  Temps: {match_time:.4f}s")
if match_time < 0.1:
    print("  🚀 ULTRA RAPIDE !")
else:
    print("  ⚠️  Template peut-être manquant")

# Test 5: Multiple templates
print("\n[5/5] Multi-Template Matching...")
templates_to_test = [
    "furnace_icon",
    "world_map_button",
    "home_button",
    "gather_button",
]

start = time.time()
results = matcher.find_all_templates(img, templates_to_test)
multi_time = time.time() - start

print(f"  Templates testés: {len(templates_to_test)}")
print(f"  Trouvés: {len(results)}")
print(f"  Temps total: {multi_time:.4f}s")
print(f"  Par template: {multi_time/len(templates_to_test)*1000:.2f}ms")

for r in results:
    print(f"    ✓ {r.template_name} at ({r.x}, {r.y}) - {r.confidence:.2%}")

# Résumé
print("\n" + "=" * 60)
print("📊 RÉSUMÉ")
print("=" * 60)
print(f"  Connexion ADB:     {conn_time:.2f}s (cible: <5s)")
print(f"  Screenshot:        {scr_time:.2f}s (cible: <5s)")
print(f"  Template (1):      {match_time:.4f}s (cible: <0.1s)")
print(f"  Template (multi):  {multi_time:.4f}s")
print("=" * 60)

if conn_time < 5 and scr_time < 5 and match_time < 0.1:
    print("\n🎉 TOUS LES FIXES MARCHENT !")
    print("Le bot devrait être ~20x plus rapide maintenant !")
    sys.exit(0)
else:
    print("\n⚠️  Certains fixes peuvent être améliorés")
    sys.exit(1)
