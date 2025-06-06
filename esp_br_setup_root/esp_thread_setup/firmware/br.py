﻿#!/usr/bin/env python3
"""
Setup and manage the ESP Thread Border Router.
"""
import os
import subprocess
from esp_thread_setup.config.constants import ESP_THREAD_BR_PATH
from esp_thread_setup.utils.ports import find_device_port, check_port

def setup_border_router():
    """Flash the Thread Border Router firmware with RCP auto-update disabled and Web GUI enabled"""
    print("\n=== Setting up ESP Thread Border Router ===")
    print("IMPORTANT: For this step, you only need to connect the Border Router device.")
    print("The CLI device will be set up in a later step.")
    input("Connect your ESP Thread Border Router device and press Enter to continue...")

    border_router_port = find_device_port("ESP Thread Border Router")
    if not border_router_port:
        print("ERROR: ESP Thread Border Router device not found")
        return False, None
    print(f"ESP Thread Border Router found at port: {border_router_port}")

    # Change to the Border Router example directory
    br_example_dir = os.path.join(ESP_THREAD_BR_PATH, "examples/basic_thread_border_router")
    if not os.path.exists(br_example_dir):
        print(f"ERROR: Border Router example directory not found at {br_example_dir}")
        return False, None

    os.chdir(br_example_dir)

    # Disable RCP auto-update and Enable Web GUI by modifying the sdkconfig file
    print("Disabling RCP auto-update and Enabling Web GUI...")
    try:
        sdkconfig_path = os.path.join(br_example_dir, "sdkconfig")
        if not os.path.exists(sdkconfig_path):
            sdkconfig_path = os.path.join(br_example_dir, "sdkconfig.defaults")
            if not os.path.exists(sdkconfig_path):
                print("Warning: Neither sdkconfig nor sdkconfig.defaults found.")
                return True, border_router_port  # Cannot disable, but continue

        with open(sdkconfig_path, "r") as f:
            content = f.readlines()

        found_auto_update = False
        found_update_sequence = False
        found_web_gui = False  # Track if web GUI config is found
        new_content = []
        for line in content:
            if line.startswith("CONFIG_OPENTHREAD_BR_AUTO_UPDATE_RCP="):
                new_content.append("CONFIG_OPENTHREAD_BR_AUTO_UPDATE_RCP=n\n")
                found_auto_update = True
            elif line.startswith("CONFIG_OPENTHREAD_BR_UPDATE_SEQUENCE="):
                new_content.append("CONFIG_OPENTHREAD_BR_UPDATE_SEQUENCE=0\n")
                found_update_sequence = True
            elif line.startswith("CONFIG_OPENTHREAD_BR_WEB_GUI_ENABLE="):
                new_content.append("CONFIG_OPENTHREAD_BR_WEB_GUI_ENABLE=y\n")
                found_web_gui = True
            else:
                new_content.append(line)

        if not found_auto_update:
            new_content.append("\nCONFIG_OPENTHREAD_BR_AUTO_UPDATE_RCP=n\n")
        if not found_update_sequence:
            new_content.append("CONFIG_OPENTHREAD_BR_UPDATE_SEQUENCE=0\n")
        if not found_web_gui:
            new_content.append("CONFIG_OPENTHREAD_BR_WEB_GUI_ENABLE=y\n")

        with open(sdkconfig_path, "w") as f:
            f.writelines(new_content)

    except Exception as e:
        print(f"Error modifying sdkconfig: {e}")

    # Clean build directory and rebuild
    print("Cleaning previous build...")
    clean_cmd = ["idf.py", "fullclean"]
    subprocess.run(clean_cmd, check=False)

    print("Building Border Router firmware...")
    build_cmd = ["idf.py", "build"]
    try:
        subprocess.run(build_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Build failed: {e}")
        return False, None

    # Flash the Border Router
    print("Flashing Border Router firmware...")
    flash_cmd = ["idf.py", "-p", border_router_port, "flash"]
    try:
        subprocess.run(flash_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Flashing failed: {e}")
        return False, None

    print("✓ Border Router firmware flashed successfully")
    return True, border_router_port