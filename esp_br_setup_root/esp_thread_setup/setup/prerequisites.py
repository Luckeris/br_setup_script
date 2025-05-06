#!/usr/bin/env python3
"""
Check prerequisites for ESP Thread setup.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", "esp_br_setup_root")))

import os
import subprocess
from esp_thread_setup.config.constants import ESP_THREAD_BR_PATH

ESP_IDF_PATH = "/home/jakub/esp-idf"

def detect_esp_idf_path():
    """Attempt to detect the ESP-IDF installation path."""
    import shutil

    # Check if IDF_PATH is already set
    if 'IDF_PATH' in os.environ:
        return os.environ['IDF_PATH']

    # Common installation paths to check
    common_paths = [
        os.path.expanduser("~/esp-idf"),  # Direct esp-idf directory
        os.path.expanduser("~/esp/esp-idf"),
        "/opt/esp/esp-idf",
        "/usr/local/esp/esp-idf"
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    # Attempt to locate idf.py in PATH
    idf_py_path = shutil.which("idf.py")
    if idf_py_path:
        return os.path.dirname(os.path.dirname(idf_py_path))

    return None

# Update the check_prerequisites function to use detect_esp_idf_path
ESP_IDF_PATH = detect_esp_idf_path()

if not ESP_IDF_PATH:
    print("ERROR: Unable to detect ESP-IDF installation.")
    print("Please install ESP-IDF and set the IDF_PATH environment variable.")
    exit(1)

def check_prerequisites():
    """Check if ESP-IDF environment is properly set up"""
    print("Checking prerequisites...")
    skip_repositories = False

    # Check if ESP-IDF is installed and sourced
    if not os.path.exists(ESP_IDF_PATH):
        print("ERROR: ESP-IDF not found at:", ESP_IDF_PATH)
        print("Please install ESP-IDF and set IDF_PATH environment variable")
        return False, skip_repositories

    # Check if required ESP-IDF tools are available
    try:
        subprocess.run(["idf.py", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: ESP-IDF tools not found. Have you sourced export.sh?")
        print("Run: . $IDF_PATH/export.sh")
        return False, skip_repositories

    print("✓ ESP-IDF environment is properly set up")

    # Check if repositories are already installed
    br_exists = os.path.exists(ESP_THREAD_BR_PATH)

    if br_exists:
        print("\nDetected existing repositories:")
        print(f"- ESP Thread Border Router found at: {ESP_THREAD_BR_PATH}")

        response = input("\nDo you want to skip repository setup and use existing ones? (y/n): ")
        if response.lower() == 'y':
            skip_repositories = True
            print("✓ Will use existing repositories")
        else:
            print("Will download/update repositories...")

    return True, skip_repositories

def verify_esp_idf_version():
    """Verify that the detected ESP-IDF version is compatible."""
    try:
        result = subprocess.run(["idf.py", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"Detected ESP-IDF version: {version}")

        # Ensure the version matches the expected format and is compatible
        if not version.startswith("v5.2.4"):
            print("WARNING: Detected ESP-IDF version may not be compatible. Expected v5.2.4.")
    except Exception as e:
        print(f"ERROR: Unable to verify ESP-IDF version: {e}")
        exit(1)

# Call the version verification function
verify_esp_idf_version()