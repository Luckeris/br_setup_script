﻿#!/usr/bin/env python3
"""
Download and manage repositories for ESP Thread setup.
"""
import os
import shutil
import tempfile
import urllib.request
import zipfile
from esp_thread_setup.config.constants import HOME_DIR, ESP_THREAD_BR_PATH

def download_repositories(skip_repositories=False):
    """Download all necessary repositories as ZIP files instead of git clone"""
    if skip_repositories:
        print("\n=== Skipping Repository Download (Using Existing Repositories) ===")
        return True

    print("\n=== Downloading Repositories ===")

    # Create esp directory if it doesn't exist
    os.makedirs(f"{HOME_DIR}/esp", exist_ok=True)

    repositories = [
        ("esp-thread-br", "https://github.com/espressif/esp-thread-br/archive/refs/heads/main.zip", ESP_THREAD_BR_PATH)
    ]

    for name, url, path in repositories:
        if os.path.exists(path):
            print(f"Repository {name} already exists at {path}")
            response = input(f"Do you want to re-download and update {name}? (y/n): ")
            if response.lower() != 'y':
                continue
            # Remove existing directory to prepare for fresh download
            shutil.rmtree(path)

        print(f"Downloading {name} from {url}...")

        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, f"{name}.zip")

            # Download the ZIP file
            try:
                urllib.request.urlretrieve(url, zip_path)
            except Exception as e:
                print(f"ERROR: Failed to download {name}: {e}")
                return False

            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the extracted directory (typically repo-main)
            extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d)) and d != "__MACOSX"]
            if not extracted_dirs:
                print(f"ERROR: No directories found in the ZIP file for {name}")
                return False

            # Move the extracted directory to the target path
            extracted_path = os.path.join(temp_dir, extracted_dirs[0])
            shutil.move(extracted_path, path)

            print(f"Successfully downloaded and extracted {name}")

    print("✓ All repositories downloaded successfully")
    return True