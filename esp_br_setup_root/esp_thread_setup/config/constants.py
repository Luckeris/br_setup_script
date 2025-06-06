﻿#!/usr/bin/env python3
"""
Constants and configuration values for the ESP Thread Setup utility.
"""
import os
from pathlib import Path

# Directory paths
HOME_DIR = str(Path.home())
ESP_IDF_PATH = os.environ.get('IDF_PATH', f"{HOME_DIR}/esp/esp-idf")
ESP_THREAD_BR_PATH = f"{HOME_DIR}/esp/esp-thread-br"

# Default values
DEFAULT_RCP_TARGET = "esp32c6"