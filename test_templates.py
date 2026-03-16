from config import Config
Config.ensure_dirs()
from adb.controller import ADBController
from vision.fast_matcher import FastTemplateMatcher

adb = ADBController()
print("Connecting...")
adb.connect()

img = adb.screenshot()
print(f"Screenshot: {img.size}")

matcher = FastTemplateMatcher(threshold=0.75)

templates = ['furnace_icon', 'back_arrow', 'home_button', 'popup_close']
print("\nTesting templates:")
for t in templates:
    result = matcher.find(img, t)
    print(f"  {t}: found={result.found}, conf={result.confidence:.1%}, at ({result.x}, {result.y})")
