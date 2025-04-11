#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path
import serial.tools.list_ports
import glob

class ESPThreadCommon:
    def __init__(self):
        self.home_dir = str(Path.home())
        self.esp_idf_path = os.environ.get('IDF_PATH', f"{self.home_dir}/esp/esp-idf")
        self.esp_thread_br_path = f"{self.home_dir}/esp/esp-thread-br"
        self.border_router_port = None
        self.cli_port = None
        self.dataset = None
        
    def check_prerequisites(self):
        """Check if ESP-IDF environment is properly set up"""
        print("Checking prerequisites...")

        # Check if ESP-IDF is installed and sourced
        if not os.path.exists(self.esp_idf_path):
            print("ERROR: ESP-IDF not found at:", self.esp_idf_path)
            print("Please install ESP-IDF and set IDF_PATH environment variable")
            return False

        # Check if required ESP-IDF tools are available
        try:
            subprocess.run(["idf.py", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: ESP-IDF tools not found. Have you sourced export.sh?")
            print("Run: . $IDF_PATH/export.sh")
            return False

        print("✓ ESP-IDF environment is properly set up")
        return True
        
    def find_device_port(self, device_type):
        """Improved device port detection using pySerial"""
        try:
            # Get all serial ports
            ports = serial.tools.list_ports.comports()

            if not ports:
                return input(f"No serial ports found. Please manually enter port for {device_type} (e.g., /dev/ttyUSB0): ")

            # Filter for likely ESP32 ports (CP210x, CH340, FTDI)
            esp_ports = [
                p for p in ports
                if 'CP210' in p.description or
                   'CH340' in p.description or
                   'FTDI' in p.description
            ]

            if not esp_ports:
                print("No ESP32-like devices found. Available ports:")
                for i, p in enumerate(ports):
                    print(f"{i+1}. {p.device} ({p.description})")
                choice = int(input(f"Select port for {device_type} (1-{len(ports)}): ")) - 1
                return ports[choice].device

            if len(esp_ports) == 1:
                return esp_ports[0].device

            # Multiple ESP-like devices found
            print(f"Multiple ESP32-like devices found. Please select port for {device_type}:")
            for i, p in enumerate(esp_ports):
                print(f"{i+1}. {p.device} ({p.description})")
            choice = int(input(f"Enter number (1-{len(esp_ports)}): ")) - 1
            return esp_ports[choice].device

        except Exception as e:
            print(f"Error detecting device port: {e}")
            return input(f"Please manually enter the port for {device_type} (e.g., /dev/ttyUSB0): ")
    
    def check_port(self, port):
        """Check if a port exists"""
        return os.path.exists(port) if port else False
        
    def show_build_logs(self, build_dir):
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
                    stderr_content = f.readlines()
                    print("STDERR (last 20 lines):")
                    for line in stderr_content[-20:]:
                        print(line.strip())

            # Show stdout log
            stdout_log = os.path.join(log_dir, "idf_py_stdout_output_*")
            stdout_files = glob.glob(stdout_log)
            if stdout_files:
                with open(stdout_files[0], "r") as f:
                    stdout_content = f.readlines()
                    print("STDOUT (last 20 lines):")
                    for line in stdout_content[-20:]:
                        print(line.strip())
        except Exception as e:
            print(f"Couldn't read log files: {e}")
