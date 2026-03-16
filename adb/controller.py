"""
ADB Controller for LDPlayer communication
Handles screenshot capture, tap, swipe, and other device commands

Features:
- Smart tap with dead zone adjustment
- Retry logic for difficult clicks (back arrows)
- Screen change detection
- Fast screenshot via exec-out (no disk I/O)
"""

import subprocess
import logging
import time
import os
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import io

from config import Config

# Use Android SDK ADB (version 41) - HARDCODED PATH
ADB_PATH = r"C:\Users\julie\AppData\Local\Android\Sdk\platform-tools\adb.exe"


class ADBController:
    """Controls LDPlayer emulator via ADB commands"""

    def __init__(self, device: str = None):
        # Use provided device or default from config
        self.device = device or Config.ADB_DEVICE_STRING
        self.logger = logging.getLogger(__name__)
        self.connected = False

    def _run_command(self, command: str, timeout: int = 30, use_shell: bool = True) -> Tuple[bool, bytes, bytes]:
        """Execute ADB command using explicit ADB path (version 41)
        
        Args:
            command: ADB command (without 'adb' prefix)
            timeout: Timeout in seconds
            use_shell: If True, use shell=True (recommended for Windows)
        """
        try:
            # Use explicit ADB path to avoid version conflicts
            # Always use shell=True on Windows for compatibility
            full_command = f'"{ADB_PATH}" -s {self.device} {command}'
            
            result = subprocess.run(
                full_command,
                shell=True,  # Always True for Windows compatibility
                capture_output=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, result.stdout, result.stderr
            return False, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, b'', b'Timeout'
        except Exception as e:
            return False, b'', str(e).encode()

    def _run_adb_command(self, command: str, timeout: int = 30, use_shell: bool = True) -> tuple:
        """Alias for _run_command for compatibility"""
        return self._run_command(command, timeout, use_shell)

    def connect(self) -> bool:
        """Connect to LDPlayer emulator
        
        Note: connect command should NOT use -s device prefix
        """
        self.logger.info(f"Connecting to {self.device}...")
        try:
            # connect command doesn't use -s device prefix
            result = subprocess.run(
                f'"{ADB_PATH}" connect {self.device}',
                shell=True,
                capture_output=True,
                timeout=30
            )
            output_str = result.stdout.decode()
            
            if "connected" in output_str.lower() or "already" in output_str.lower():
                self.connected = True
                self.logger.info("✓ Connected to emulator")
                return True
            
            self.logger.error(f"✗ Connection failed: {output_str}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from emulator"""
        self._run_command(f"disconnect {self.device}")
        self.connected = False
        self.logger.info("Disconnected from emulator")

    def check_connection(self) -> bool:
        """Check if device is connected and responsive"""
        try:
            success, output, err = self._run_command("devices")
            if not success:
                return False
            
            output_str = output.decode() if isinstance(output, bytes) else output

            # Check if our device is in the list and marked as "device"
            for line in output_str.strip().split('\n')[1:]:  # Skip header
                if self.device in line and "device" in line.split():
                    return True

            return False
        except Exception:
            return False

    def screenshot(self, save_path: Optional[str] = None) -> Optional[Image.Image]:
        """
        Take screenshot via ADB using exec-out (FAST - direct to RAM)

        Uses adb exec-out screencap -p which streams PNG directly
        without writing to device storage.

        Args:
            save_path: Optional path to save the screenshot

        Returns:
            PIL Image object or None if failed
        """
        try:
            # exec-out streams PNG directly (no disk I/O)
            result = subprocess.run(
                f'"{ADB_PATH}" -s {self.device} exec-out screencap -p',
                shell=True,
                capture_output=True,
                timeout=60  # Increased timeout
            )

            if result.returncode == 0 and result.stdout:
                img = Image.open(io.BytesIO(result.stdout))

                if save_path:
                    img.save(save_path, format='PNG')
                    self.logger.debug(f"Screenshot saved to {save_path}")

                return img
            else:
                self.logger.error(f"Screenshot failed: {result.stderr.decode()[:200]}")
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("Screenshot timeout (60s)")
            return None
        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return None

    def tap(self, x: int, y: int, scale: bool = True) -> bool:
        """
        Tap at screen coordinates with automatic scaling
        
        Args:
            x: X coordinate in CAPTURE resolution (0-400)
            y: Y coordinate in CAPTURE resolution (0-652)
            scale: If True, scale to SCREEN resolution (720x1280)
        """
        # Scale coordinates if needed (400x652 → 720x1280)
        if scale:
            real_x = int(x * Config.SCALE_X)
            real_y = int(y * Config.SCALE_Y)
            self.logger.debug(f"Scaling coords: ({x},{y}) → ({real_x},{real_y})")
        else:
            real_x, real_y = x, y
        
        success, _, _ = self._run_command(f"shell input tap {real_x} {real_y}")
        if success:
            self.logger.debug(f"Tapped at ({real_x}, {real_y})")
        return success

    def is_in_dead_zone(self, x: int, y: int) -> Tuple[bool, str]:
        """
        Check if coordinates are in a dead zone
        
        Returns:
            (is_in_dead_zone, zone_name)
        """
        # Top-left dead zone
        dl = Config.DEAD_ZONE_TOP_LEFT
        if dl["x"] <= x <= dl["x"] + dl["width"] and dl["y"] <= y <= dl["y"] + dl["height"]:
            return True, "top_left"
        
        # Top-right dead zone
        tr = Config.DEAD_ZONE_TOP_RIGHT
        if tr["x"] <= x <= tr["x"] + tr["width"] and tr["y"] <= y <= tr["y"] + tr["height"]:
            return True, "top_right"
        
        return False, ""

    def adjust_for_dead_zone(self, x: int, y: int, element_name: str = "") -> Tuple[int, int]:
        """
        Adjust coordinates if they're in a dead zone
        
        Returns:
            Adjusted (x, y) coordinates
        """
        in_zone, zone_name = self.is_in_dead_zone(x, y)
        
        if in_zone:
            self.logger.info(f"⚠️  {element_name} in dead zone ({zone_name}), adjusting...")
            
            if zone_name == "top_left":
                # Adjust toward center
                new_x = x + Config.BACK_ARROW_OFFSET_X
                new_y = y + Config.BACK_ARROW_OFFSET_Y
                self.logger.info(f"   Adjusted: ({x},{y}) → ({new_x},{new_y})")
                return new_x, new_y
            
            elif zone_name == "top_right":
                # Adjust left and down
                new_x = x - Config.BACK_ARROW_OFFSET_X
                new_y = y + Config.BACK_ARROW_OFFSET_Y
                self.logger.info(f"   Adjusted: ({x},{y}) → ({new_x},{new_y})")
                return new_x, new_y
        
        return x, y

    def smart_tap(self, x: int, y: int, element_name: str = "", retries: int = None, scale: bool = True) -> bool:
        """
        Smart tap with dead zone adjustment, retry logic, and scaling
        
        Args:
            x, y: Target coordinates (in CAPTURE resolution)
            element_name: Name of element being clicked
            retries: Number of retry attempts
            scale: If True, scale coords to SCREEN resolution
        """
        retries = retries or Config.BACK_ARROW_RETRIES
        
        # Adjust for dead zones (BEFORE scaling)
        adj_x, adj_y = self.adjust_for_dead_zone(x, y, element_name)
        
        # Try multiple times
        for attempt in range(1, retries + 1):
            success = self.tap(adj_x, adj_y, scale=scale)
            
            if success:
                self.logger.debug(f"✓ Tap #{attempt} at ({adj_x}, {adj_y})")
                time.sleep(0.3)
                return True
        
        self.logger.warning(f"✗ Tap failed after {retries} attempts for {element_name}")
        return False

    def tap_back_arrow(self, retries: int = None) -> bool:
        """
        Special method to tap the back arrow (top-left corner)
        
        Uses coordinates in SCREEN resolution (720x1280) since it's
        a fixed position, not from template matching.
        
        Args:
            retries: Number of retry attempts
            
        Returns:
            True if back arrow was clicked successfully
        """
        # Coordinates in SCREEN resolution (already scaled)
        # Top-left corner of 720x1280 screen
        screen_x = 100  # Already in screen coords
        screen_y = 100  # Already in screen coords

        retries = retries or Config.BACK_ARROW_RETRIES

        self.logger.info(f"🔙 Attempting back arrow click (retries={retries})...")

        for attempt in range(1, retries + 1):
            self.logger.debug(f"  Attempt #{attempt}: tapping at ({screen_x}, {screen_y})")

            # scale=False because coords are already in screen resolution
            success = self.tap(screen_x, screen_y, scale=False)

            if success:
                time.sleep(0.5)  # Wait for screen transition
                self.logger.debug(f"✓ Back arrow tap succeeded")
                return True

        self.logger.warning(f"✗ Back arrow tap failed after {retries} attempts")
        return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """
        Swipe gesture

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration: Swipe duration in milliseconds
        """
        success, _, _ = self._run_command(
            f"shell input swipe {x1} {y1} {x2} {y2} {duration}"
        )
        if success:
            self.logger.debug(f"Swiped from ({x1}, {y1}) to ({x2}, {y2})")
        return success

    def key_event(self, keycode: int) -> bool:
        """
        Send Android key event

        Common keycodes:
        - 3: HOME
        - 4: BACK
        - 66: ENTER
        """
        success, _, _ = self._run_command(f"shell input keyevent {keycode}")
        return success

    def text(self, text: str) -> bool:
        """Input text (for search fields, etc.)"""
        # Escape special characters
        escaped = text.replace(" ", "%s").replace("'", "\\'")
        success, _, _ = self._run_command(f"shell input text '{escaped}'")
        return success

    def get_resolution(self) -> Optional[Tuple[int, int]]:
        """Get screen resolution"""
        success, output, _ = self._run_command("shell wm size")
        if success:
            try:
                # Output format: "Physical size: 720x1280"
                size_str = output.decode().strip().split(':')[-1].strip()
                width, height = map(int, size_str.split('x'))
                return width, height
            except Exception:
                pass
        return None

    def restart_app(self, package: str = "com.funplus.whiteoutsurvival"):
        """Restart the game app"""
        # Force stop
        self._run_command(f"shell am force-stop {package}")
        # Start
        self._run_command(f"shell monkey -p {package} -c android.intent.category.LAUNCHER 1")
        self.logger.info(f"Restarted app: {package}")

    def is_app_running(self, package: str = "com.funplus.whiteoutsurvival") -> bool:
        """Check if game app is running"""
        success, output, err = self._run_command("shell ps")
        output_str = output.decode() if isinstance(output, bytes) else output
        return package in output_str if success else False
