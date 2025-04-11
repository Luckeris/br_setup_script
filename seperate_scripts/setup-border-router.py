#!/usr/bin/env python3
import os
import sys
import subprocess
from esp_thread_common import ESPThreadCommon

class BorderRouterSetup(ESPThreadCommon):
    def __init__(self):
        super().__init__()
        
    def setup_border_router(self):
        """Flash the Thread Border Router firmware with RCP auto-update disabled and Web GUI enabled"""
        print("\n=== Setting up ESP Thread Border Router ===")
        print("IMPORTANT: For this step, you only need to connect the Border Router device.")
        print("The CLI device will be set up in a later step.")
        input("Connect your ESP Thread Border Router device and press Enter to continue...")

        self.border_router_port = self.find_device_port("ESP Thread Border Router")
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

        # Disable RCP auto-update and Enable Web GUI by modifying the sdkconfig file
        print("Disabling RCP auto-update and Enabling Web GUI...")
        try:
            sdkconfig_path = os.path.join(br_example_dir, "sdkconfig")
            if not os.path.exists(sdkconfig_path):
                sdkconfig_path = os.path.join(br_example_dir, "sdkconfig.defaults")
                if not os.path.exists(sdkconfig_path):
                    print("Warning: Neither sdkconfig nor sdkconfig.defaults found.")
                    return True  # Cannot disable, but continue

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
                elif line.startswith("CONFIG_OPENTHREAD_BR_WEB_GUI_ENABLE="):  # Add this condition
                    new_content.append("CONFIG_OPENTHREAD_BR_WEB_GUI_ENABLE=y\n")
                    found_web_gui = True
                else:
                    new_content.append(line)

            if not found_auto_update:
                new_content.append("\nCONFIG_OPENTHREAD_BR_AUTO_UPDATE_RCP=n\n")
            if not found_update_sequence:
                new_content.append("CONFIG_OPENTHREAD_BR_UPDATE_SEQUENCE=0\n")
            if not found_web_gui:  # If not found, add it
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
            return False

        # Flash the Border Router
        print("Flashing Border Router firmware...")
        flash_cmd = ["idf.py", "-p", self.border_router_port, "flash"]
        try:
            subprocess.run(flash_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Flashing failed: {e}")
            return False

        print("✓ Border Router firmware flashed successfully")
        return True

if __name__ == "__main__":
    br_setup = BorderRouterSetup()
    
    if not br_setup.check_prerequisites():
        sys.exit(1)
        
    try:
        if br_setup.setup_border_router():
            print("Border Router setup completed successfully!")
        else:
            print("Border Router setup failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred during setup: {e}")
        sys.exit(1)
