﻿#!/usr/bin/env python3
"""
Setup and manage the ESP Thread CLI device.
"""
import os
import subprocess
from esp_thread_setup.config.constants import ESP_IDF_PATH
from esp_thread_setup.utils.ports import find_device_port
from esp_thread_setup.utils.logs import show_build_logs

def build_and_flash_cli():
    """Flash the CLI using ESP32C6 example image from ESP-IDF"""
    print("\n=== Setting up CLI (ESP32C6) ===")
    print("IMPORTANT: For this step, you only need to connect the ESP32C6 CLI device.")
    print("The Border Router device will be needed again in later steps.")
    input("Connect your ESP32C6 (CLI) device and press Enter to continue...")

    # Get the port using improved detection
    cli_port = find_device_port("ESP32C6 CLI")
    if not cli_port:
        print("ERROR: ESP32C6 device not found")
        return False, None

    print(f"ESP32C6 device found at port: {cli_port}")

    # Check if the OT CLI example directory exists in ESP-IDF
    cli_example_dir = os.path.join(ESP_IDF_PATH, "examples/openthread/ot_cli")
    if not os.path.exists(cli_example_dir):
        print(f"ERROR: CLI example directory not found at {cli_example_dir}")
        print("Please make sure the ESP-IDF repository is complete with examples")
        return False, None

    # Change to the CLI example directory
    os.chdir(cli_example_dir)

    # Clean previous build
    print("Cleaning previous CLI build...")
    clean_cmd = ["idf.py", "fullclean"]
    subprocess.run(clean_cmd, check=False)

    # Build and flash the CLI example
    print("Building and flashing OpenThread CLI example for ESP32C6...")
    
    # FIXED COMMAND: The -p flag should come before set-target
    flash_cmd = [
        "idf.py",
        "-p", cli_port,  # Port specification comes first
        "set-target", "esp32c6",
        "flash"
    ]

    try:
        subprocess.run(flash_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to flash OpenThread CLI example: {e}")
        show_build_logs(cli_example_dir + "/build")
        return False, None

    print("✓ OpenThread CLI (ESP32C6) flashed successfully")
    return True, cli_port