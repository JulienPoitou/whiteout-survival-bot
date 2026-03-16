#!/usr/bin/env python
print("START")
import sys
print("Python:", sys.version)

print("Loading config...")
from config import Config
print("Config loaded!")

Config.ensure_dirs()
print("Dirs created!")

print("Device:", Config.ADB_DEVICE_STRING)

print("Loading ADB...")
from adb.controller import ADBController
print("ADB loaded!")

adb = ADBController()
print("ADB created:", adb.device)

print("Connecting...")
adb.connect()
print("Connected:", adb.connected)

print("Screenshot...")
img = adb.screenshot()
print("Screenshot:", img.size if img else "FAILED")

print("DONE")
