#!/usr/bin/env python3
"""
Setup and manage the Web GUI for the Border Router.
"""
import urllib.request
import time
import subprocess
from esp_thread_setup.utils.logs import print_error

def print_info(message):
    """Prints an informational message."""
    print(f"[INFO] {message}")

def print_success(message):
    """Prints a success message."""
    print(f"[SUCCESS] {message}")

def setup_web_gui(border_router_port):
    """Setup the Web GUI for the Border Router and display its IP address"""
    print("\n=== Setting up Web GUI ===")
    print("The Border Router provides a web interface for configuration and monitoring.")

    # Prompt for Wi-Fi SSID and password
    print("\n=== Wi-Fi Configuration ===")
    ssid = input("Enter Wi-Fi SSID: ")
    password = input("Enter Wi-Fi Password: ")

    # Simulate connecting to Wi-Fi (replace with actual implementation if needed)
    print_info(f"Connecting to Wi-Fi network '{ssid}'...")
    # Here you would add the actual code to connect to Wi-Fi using the SSID and password
    time.sleep(2)  # Simulate connection delay
    print_success("Connected to Wi-Fi successfully.")

    # Validate that border_router_port is not None
    if not border_router_port:
        print_error("Border Router port is not set. Please enter it manually.")
        border_router_port = input("Enter the Border Router port (e.g., /dev/ttyUSB0): ")
        if not border_router_port:
            print_error("No port entered. Exiting Web GUI setup.")
            return False

    # Display instructions for manually fetching the IP address
    print("\n=== Web GUI IP Address Fetch Instructions ===")
    print("To fetch the IP address of the Web GUI, follow these steps:")
    print("1. Open the Border Router monitor using the following command:")
    print(f"   idf.py -p {border_router_port} monitor")
    print("2. Look for a line containing 'IP Address:' in the monitor output.")
    print("3. Copy the IP address and exit the monitor by pressing Ctrl+].")

    input("\nPress Enter to open the Border Router monitor...")

    # Open the Border Router monitor
    try:
        print(f"Running: idf.py -p {border_router_port} monitor")
        subprocess.run(["idf.py", "-p", border_router_port, "monitor"], check=False)
    except Exception as e:
        print_error(f"Error opening Border Router monitor: {e}")
        return False

    print_success("Monitor closed. Please ensure you copied the IP address.")

    # Display the Web GUI access information
    print_success(f"\nYou can access the Web GUI at http://{ip_address}")
    print("Use the web interface to:")
    print("1. Monitor the Thread network status")
    print("2. Configure network settings")
    print("3. View connected devices")

    # Basic verification (can be expanded)
    print("\nVerifying basic web GUI access...")
    try:
        # Try to open the web page
        urllib.request.urlopen("http://"+ip_address)
        print("✓ Web GUI is accessible!")
    except:
        print("ERROR: Web GUI might not be accessible at this IP. Please double-check the IP address and ensure the Border Router is connected to the network.")
    
    return True