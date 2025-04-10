#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import shutil
from pathlib import Path
import re
import json
import urllib.request
import zipfile
import tempfile
import serial.tools.list_ports
import glob

class ESPThreadSetup:
    # [Previous methods remain the same until setup_border_router]

    def _show_build_logs(self, build_dir):
        """Display relevant build logs when failures occur"""
        log_dir = os.path.join(build_dir, "log")
        if not os.path.exists(log_dir):
            print("No log directory found")
            return
        
        print("\n=== Last 20 lines of build logs ===")
        try:
            # Show stderr log
            stderr_log = os.path.join(log_dir, "idf_py_stderr_output_*")
            stderr_files = glob.glob(stderr_log)
            if stderr_files:
                with open(stderr_files[0], "r") as f:
                    print("STDERR:", f.read())
            
            # Show stdout log
            stdout_log = os.path.join(log_dir, "idf_py_stdout_output_*")
            stdout_files = glob.glob(stdout_log)
            if stdout_files:
                with open(stdout_files[0], "r") as f:
                    print("STDOUT:", f.read())
        except Exception as e:
            print(f"Couldn't read log files: {e}")

    def setup_border_router(self):
        """Flash the Thread Border Router firmware which will automatically handle RCP flashing"""
        print("\n=== Setting up ESP Thread Border Router/Zigbee Gateway V1.2 ===")
        input("Connect your ESP Thread Border Router/Zigbee Gateway V1.2 device and press Enter to continue...")
        
        self.border_router_port = self._find_device_port("ESP Thread Border Router")
        if not self.border_router_port:
            print("ERROR: ESP Thread Border Router device not found")
            return False
            
        print(f"ESP Thread Border Router found at port: {self.border_router_port}")
        
        # Change to the Border Router example directory
        br_example_dir = os.path.join(self.esp_thread_br_path, "examples/basic_thread_border_router")
        if not os.path.exists(br_example_dir):
            print(f"ERROR: Border Router example directory not found at {br_example_dir}")
            return False
        
        os.chdir(br_example_dir)
        
        # Add clean step first
        print("Cleaning previous build...")
        clean_cmd = ["idf.py", "fullclean"]
        try:
            subprocess.run(clean_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Clean failed: {e}")
        
        # Then build and flash
        print("Building and flashing Border Router firmware (this may take several minutes)...")
        flash_br_cmd = [
            "idf.py", 
            "-p", self.border_router_port, 
            "flash"
        ]
        
        try:
            subprocess.run(flash_br_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to flash Border Router firmware: {e}")
            self._show_build_logs(br_example_dir + "/build")
            
            # Additional troubleshooting suggestions
            print("\nTroubleshooting suggestions:")
            print("1. Try running 'idf.py fullclean' then 'idf.py build' manually")
            print("2. Check if ESP-IDF is up to date")
            print("3. Verify all requirements are installed (run 'install.sh' in ESP-IDF)")
            return False
            
        print("✓ Border Router firmware flashed successfully")
        return True

    # [Rest of the class remains the same]

if __name__ == "__main__":
    setup = ESPThreadSetup()
    setup.run()
