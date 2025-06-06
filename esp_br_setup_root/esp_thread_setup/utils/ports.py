﻿
#!/usr/bin/env python3
"""
Utilities for detecting and managing serial ports.
"""
import os
import serial.tools.list_ports

def find_device_port(device_type):
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

def check_port(port):
    """Check if a port exists"""
    return os.path.exists(port) if port else False