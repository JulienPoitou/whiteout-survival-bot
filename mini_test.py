#!/usr/bin/env python
print("START")

from config import Config
Config.ensure_dirs()
print("Config OK")

from adb.controller import ADBController
adb = ADBController()
print(f"ADB: {adb.device}")

adb.connect()
print("Connected")

img = adb.screenshot()
print(f"Screenshot: {img.size if img else 'FAILED'}")

from core.vision_facade import VisionFacade
vision = VisionFacade()
print("Vision OK")

screen = vision.detect_screen_type(img, None)
print(f"Screen: {screen}")

print("DONE")
