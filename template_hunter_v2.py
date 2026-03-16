#!/usr/bin/env python
"""
Template Hunter v2 - Fixed Version
"""

import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "template_hunter.log", encoding='utf-8', mode='w')
    ]
)

logger = logging.getLogger("TemplateHunter")

# ... (reste du code identique mais avec elapsed_minutes fixe)
