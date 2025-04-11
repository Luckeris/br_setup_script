#!/usr/bin/env python3
import os
import sys
import subprocess
from esp_thread_common import ESPThreadCommon

class CLIBuilder(ESPThreadCommon):
    def __init__(self):
        super().__init__()
        
    def build_and_flash_cli(self):
        """Flash the CLI using ESP32C6 example image from ESP-IDF"""
        print("\n=== Setting up CLI (ESP32C6) ===")
        print("IMPORTANT: For this step, you only need to connect the ESP32C6 CLI device.")
        print("The Border Router device will be needed again in later steps.")
        input("Connect your ESP32C6 (CLI) device and press Enter to continue...")

        # Get the port using improved detection
        self.cli_port = self.find_device_port("ESP32C6 CLI")
        if not self.cli_port:
            print("ERROR: ESP32C6 device not found")
            return False

        print(f"ESP32C6 device found at port: {self.cli_port}")

        # Check if the OT CLI example directory exists in ESP-IDF
        cli_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_cli")
        if not os.path.exists(cli_example_dir):
            print(f"ERROR: CLI example directory not found at {cli_example_dir}")
            print("Please make sure the ESP-IDF repository is complete with examples")
            return False

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
            "-p", self.cli_port,  # Port specification comes first
            "set-target", "esp32c6",
            "flash"
        ]

        try:
            subprocess.run(flash_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to flash OpenThread CLI example: {e}")
            self.show_build_logs(cli_example_dir + "/build")
            return False

        print("✓ OpenThread CLI (ESP32C6) flashed successfully")
        return True
        
if __name__ == "__main__":
    cli_builder = CLIBuilder()
    
    if not cli_builder.check_prerequisites():
        sys.exit(1)
        
    try:
        if cli_builder.build_and_flash_cli():
            print("CLI setup completed successfully!")
        else:
            print("CLI setup failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred during setup: {e}")
        sys.exit(1)
