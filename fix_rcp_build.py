#!/usr/bin/env python3
import os
import sys
import subprocess
import re

def patch_radio_spinel_file():
    """Patch the esp_openthread_radio_spinel.cpp file to fix the compatibility issue"""
    print("\n=== Patching OpenThread Radio Spinel File ===")
    
    # Determine ESP-IDF path
    esp_idf_path = os.environ.get('IDF_PATH')
    if not esp_idf_path:
        esp_idf_path = os.path.expanduser("~/esp/esp-idf")
        if not os.path.exists(esp_idf_path):
            print("ERROR: Could not find ESP-IDF path. Please set IDF_PATH environment variable.")
            return False
    
    # Path to the file that needs patching
    radio_spinel_path = os.path.join(esp_idf_path, "components/openthread/src/port/esp_openthread_radio_spinel.cpp")
    
    if not os.path.exists(radio_spinel_path):
        print(f"ERROR: File not found: {radio_spinel_path}")
        return False
    
    # Read the file content
    with open(radio_spinel_path, 'r') as f:
        content = f.read()
    
    # Check if the problematic line exists
    if "SetCompatibilityErrorCallback" in content:
        # Create backup
        backup_path = radio_spinel_path + ".backup"
        print(f"Creating backup at {backup_path}")
        with open(backup_path, 'w') as f:
            f.write(content)
        
        # Remove the problematic function and its call
        # First, remove the function definition
        content = re.sub(r'static void ot_spinel_compatibility_error_callback$$void \*context$$\s*\{[^}]*\}', '', content)
        
        # Then, comment out the line that calls SetCompatibilityErrorCallback
        content = content.replace(
            "s_radio.SetCompatibilityErrorCallback(ot_spinel_compatibility_error_callback, esp_openthread_get_instance());",
            "// Compatibility callback removed: s_radio.SetCompatibilityErrorCallback(...)"
        )
        
        # Write the modified content back
        with open(radio_spinel_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Successfully patched {radio_spinel_path}")
        return True
    else:
        print("The file doesn't contain the problematic code or has already been patched.")
        return True

def main():
    print("=== ESP Thread RCP Build Fix ===")
    print("This script will patch the OpenThread Radio Spinel file to fix the compilation error.")
    
    if not patch_radio_spinel_file():
        print("Failed to patch the file.")
        return 1
    
    print("\nThe patch has been applied. Now you can try building the RCP firmware again.")
    print("Run: cd ~/esp/esp-idf/examples/openthread/ot_rcp && idf.py set-target esp32s3 build")
    
    retry = input("\nWould you like to attempt building the RCP firmware now? (y/n): ")
    if retry.lower() == 'y':
        # Get the target
        target = input("Enter the target chip (esp32s3, esp32c6): ").strip()
        if not target:
            target = "esp32s3"
        
        # Change to the RCP example directory
        rcp_dir = os.path.expanduser("~/esp/esp-idf/examples/openthread/ot_rcp")
        if not os.path.exists(rcp_dir):
            print(f"ERROR: RCP example directory not found at {rcp_dir}")
            return 1
        
        os.chdir(rcp_dir)
        
        # Clean previous build
        print("Cleaning previous build...")
        subprocess.run(["idf.py", "fullclean"], check=False)
        
        # Build the RCP firmware
        print(f"Building RCP firmware for {target}...")
        try:
            subprocess.run(["idf.py", "set-target", target, "build"], check=True)
            print("✓ RCP firmware built successfully!")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Build failed: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
