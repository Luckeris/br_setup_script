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

class ESPThreadSetup:
    def __init__(self):
        self.home_dir = str(Path.home())
        self.esp_idf_path = os.environ.get('IDF_PATH', f"{self.home_dir}/esp/esp-idf")
        self.esp_thread_br_path = f"{self.home_dir}/esp/esp-thread-br"
        self.border_router_port = None
        self.cli_port = None
        self.dataset = None
        self.skip_repositories = False

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
        
        # Check if repositories are already installed
        br_exists = os.path.exists(self.esp_thread_br_path)
        
        if br_exists:
            print("\nDetected existing repositories:")
            print(f"- ESP Thread Border Router found at: {self.esp_thread_br_path}")
                
            response = input("\nDo you want to skip repository setup and use existing ones? (y/n): ")
            if response.lower() == 'y':
                self.skip_repositories = True
                print("✓ Will use existing repositories")
            else:
                print("Will download/update repositories...")
        
        return True

    def download_repositories(self):
        """Download all necessary repositories as ZIP files instead of git clone"""
        if self.skip_repositories:
            print("\n=== Skipping Repository Download (Using Existing Repositories) ===")
            return True
            
        print("\n=== Downloading Repositories ===")
        
        # Create esp directory if it doesn't exist
        os.makedirs(f"{self.home_dir}/esp", exist_ok=True)
        
        repositories = [
            ("esp-thread-br", "https://github.com/espressif/esp-thread-br/archive/refs/heads/main.zip", self.esp_thread_br_path)
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

    def setup_border_router(self):
        """Flash the Thread Border Router using example images as per the tutorial"""
        print("\n=== Setting up ESP Thread Border Router/Zigbee Gateway V1.2 ===")
        input("Connect your ESP Thread Border Router/Zigbee Gateway V1.2 device and press Enter to continue...")
        
        # Get the port
        self.border_router_port = self._find_device_port("ESP Thread Border Router")
        if not self.border_router_port:
            print("ERROR: ESP Thread Border Router device not found")
            return False
            
        print(f"ESP Thread Border Router found at port: {self.border_router_port}")
        
        # First, flash the RCP firmware to ESP32H2 using the IDF example
        print("\n1. Flashing the RCP firmware to ESP32H2 from IDF examples...")
        
        # Check if the OT RCP example directory exists in ESP-IDF
        rcp_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_rcp")
        if not os.path.exists(rcp_example_dir):
            print(f"ERROR: RCP example directory not found at {rcp_example_dir}")
            print("Please make sure the ESP-IDF repository is complete with examples")
            return False
        
        # Change to the RCP example directory
        os.chdir(rcp_example_dir)
        
        # Flash the RCP firmware to ESP32H2 using the example
        flash_rcp_cmd = [
            "idf.py", 
            "set-target", "esp32h2",
            "-p", self.border_router_port, 
            "flash"
        ]
        
        if subprocess.run(flash_rcp_cmd, check=True).returncode != 0:
            print("ERROR: Failed to flash RCP firmware example")
            return False
            
        print("✓ RCP firmware flashed to ESP32H2 successfully")
        
        # Then, flash the Border Router firmware to ESP32S3 using the example
        print("\n2. Flashing the Border Router firmware to ESP32S3 from examples...")
        
        # Change to the Border Router example directory
        br_example_dir = os.path.join(self.esp_thread_br_path, "examples/basic_thread_border_router")
        if not os.path.exists(br_example_dir):
            print(f"ERROR: Border Router example directory not found at {br_example_dir}")
            print("Please make sure the ESP Thread Border Router repository was properly downloaded")
            return False
        
        os.chdir(br_example_dir)
        
        flash_br_cmd = [
            "idf.py", 
            "set-target", "esp32s3", 
            "-p", self.border_router_port, 
            "flash"
        ]
        
        if subprocess.run(flash_br_cmd, check=True).returncode != 0:
            print("ERROR: Failed to flash Border Router firmware example")
            return False
            
        print("✓ Border Router firmware flashed to ESP32S3 successfully")
        return True

    def build_and_flash_cli(self):
        """Flash the CLI using ESP32C6 example image from ESP-IDF"""
        print("\n=== Setting up CLI (ESP32C6) ===")
        input("Connect your ESP32C6 (CLI) device and press Enter to continue...")
        
        # Get the port
        self.cli_port = self._find_device_port("ESP32C6 CLI")
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
        
        # Flash the CLI example
        print("Flashing OpenThread CLI example...")
        flash_cmd = [
            "idf.py", 
            "set-target", "esp32c6", 
            "-p", self.cli_port, 
            "flash"
        ]
        
        if subprocess.run(flash_cmd, check=True).returncode != 0:
            print("ERROR: Failed to flash OpenThread CLI example")
            return False
            
        print("✓ OpenThread CLI (ESP32C6) flashed successfully from example")
        return True

    def create_dataset(self):
        """Create a Thread network dataset"""
        print("\n=== Creating Thread Network Dataset ===")
        
        # Generate a unique network name
        network_name = f"ESP-Thread-{int(time.time()) % 10000}"
        
        # Connect to the border router to create a dataset
        br_example_dir = os.path.join(self.esp_thread_br_path, "examples/basic_thread_border_router")
        os.chdir(br_example_dir)
        
        print(f"Creating Thread network: {network_name}")
        print("Opening Border Router console...")
        print("After the console opens, please run these commands:")
        print("1. dataset init new")
        print(f"2. dataset networkname {network_name}")
        print("3. dataset commit active")
        print("4. dataset")
        print("5. Copy the entire dataset output")
        print("\nPress Ctrl+] to exit the console when done")
        
        input("\nPress Enter to open the Border Router console...")
        
        # Open console
        subprocess.run(["idf.py", "-p", self.border_router_port, "monitor"], check=False)
        
        # Get dataset from user
        self.dataset = input("\nPaste the dataset output here: ")
        
        if not self.dataset or "Active Timestamp:" not in self.dataset:
            print("ERROR: Invalid dataset. Please ensure you copied the entire output.")
            return False
        
        # Save dataset to file
        with open("thread_dataset.txt", "w") as f:
            f.write(self.dataset)
        
        print(f"✓ Thread network dataset created and saved to thread_dataset.txt")
        return True

    def configure_cli(self):
        """Configure the CLI device with the network dataset"""
        print("\n=== Configuring OpenThread CLI to Join Network ===")
        
        if not self._check_port(self.cli_port):
            print("ERROR: CLI device not found. Please reconnect and try again.")
            return False
        
        # Change to the CLI example directory in ESP-IDF
        cli_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_cli")
        os.chdir(cli_example_dir)
        
        print("Opening CLI console...")
        print("After the console opens, please run these commands to join the Thread network:")
        print("1. dataset set active <paste the dataset here>")
        print("2. ifconfig up")
        print("3. thread start")
        print("\nPress Ctrl+] to exit the console when done")
        
        input("\nPress Enter to open the CLI console...")
        
        # Open CLI console
        subprocess.run(["idf.py", "-p", self.cli_port, "monitor"], check=False)
        
        response = input("\nDid the CLI successfully join the Thread network? (y/n): ")
        if response.lower() != 'y':
            print("Please try to reconfigure the CLI device.")
            return False
        
        print("✓ OpenThread CLI configured successfully")
        return True

    def _find_device_port(self, device_type):
        """Find the port for a specific ESP32 device"""
        try:
            # Run dmesg to find recently connected devices
            result = subprocess.run(["dmesg"], capture_output=True, text=True, check=True)
            output = result.stdout
            
            # Look for CP210x or CH340 USB to serial converters commonly used with ESP32
            usb_serial_lines = [line for line in output.split('\n') if 'cp210x' in line.lower() or 'ch340' in line.lower() or 'ftdi' in line.lower()]
            
            # Get the most recently connected device
            if usb_serial_lines:
                # Extract ttyUSB or ttyACM device
                for line in reversed(usb_serial_lines):
                    match = re.search(r'tty(USB|ACM)[0-9]+', line)
                    if match:
                        port = f"/dev/{match.group(0)}"
                        return port
            
            # If not found with dmesg, try listing all ttyUSB devices
            devices = os.listdir('/dev')
            usb_devices = [dev for dev in devices if dev.startswith('ttyUSB') or dev.startswith('ttyACM')]
            
            if usb_devices:
                # Ask user to select the correct port
                print(f"Multiple USB devices found. Please select the port for your {device_type}:")
                for i, dev in enumerate(usb_devices):
                    print(f"{i+1}. /dev/{dev}")
                
                choice = int(input("Enter number: ")) - 1
                if 0 <= choice < len(usb_devices):
                    return f"/dev/{usb_devices[choice]}"
            
            # If still not found, ask user to input manually
            port = input(f"Could not automatically detect {device_type} port. Please enter the port (e.g., /dev/ttyUSB0): ")
            return port.strip()
            
        except Exception as e:
            print(f"Error detecting device port: {e}")
            port = input(f"Please manually enter the port for {device_type} (e.g., /dev/ttyUSB0): ")
            return port.strip()

    def _check_port(self, port):
        """Check if a port exists"""
        return os.path.exists(port) if port else False

    def setup_web_gui(self):
        """Setup the Web GUI for the Border Router"""
        print("\n=== Setting up Web GUI ===")
        print("The Border Router provides a web interface for configuration and monitoring.")
        print("To access the web interface:")
        
        # Get the IP address of the Border Router
        ip_address = input("Please enter the IP address of your Border Router (check your router's DHCP list): ")
        
        print(f"\nYou can access the Web GUI at http://{ip_address}")
        print("Use the web interface to:")
        print("1. Monitor the Thread network status")
        print("2. Configure network settings")
        print("3. View connected devices")
        
        return True

    def show_steps_menu(self):
        """Show a menu to let user select which steps to perform"""
        print("\n=== ESP Thread Border Router Setup Steps ===")
        print("Please select which steps you want to perform:")
        print("1. Download/update repositories")
        print("2. Setup Border Router (ESP32S3) and RCP (ESP32H2) from examples")
        print("3. Setup CLI (ESP32C6) from examples")
        print("4. Create Thread network dataset")
        print("5. Configure CLI to join Thread network")
        print("6. Setup Web GUI")
        print("7. Run all steps (1-6)")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            self.download_repositories()
        elif choice == '2':
            self.setup_border_router()
        elif choice == '3':
            self.build_and_flash_cli()
        elif choice == '4':
            self.create_dataset()
        elif choice == '5':
            self.configure_cli()
        elif choice == '6':
            self.setup_web_gui()
        elif choice == '7':
            self.run_all_steps()
        elif choice == '8':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
            self.show_steps_menu()
            
        # Return to the menu after completing a step
        self.show_steps_menu()

    def run_all_steps(self):
        """Run all setup steps sequentially"""
        if not self.download_repositories():
            return False
        
        if not self.setup_border_router():
            return False
        
        if not self.build_and_flash_cli():
            return False
        
        if not self.create_dataset():
            return False
        
        if not self.configure_cli():
            return False
        
        self.setup_web_gui()
        
        print("\n=== Setup Complete! ===")
        print("Your OpenThread Border Router system is now set up and running.")
        print("Border Router (ESP32S3) and RCP (ESP32H2) on", self.border_router_port)
        print("CLI (ESP32C6) on", self.cli_port)
        print("Thread Network Dataset has been saved to thread_dataset.txt")
        
        return True

    def run(self):
        """Run the setup process"""
        print("=== ESP Thread Border Router Setup Script ===")
        print("This script will guide you through setting up your OpenThread Border Router system.")
        print("Following the official Espressif tutorial: https://docs.espressif.com/projects/esp-thread-br/en/latest/dev-guide/build_and_run.html")
        print("Using the example locations from the tutorial:")
        print("- RCP: $IDF_PATH/examples/openthread/ot_rcp")
        print("- Border Router: esp-thread-br/examples/basic_thread_border_router")
        print("- CLI: $IDF_PATH/examples/openthread/ot_cli")
        
        if not self.check_prerequisites():
            return False
        
        # Show interactive menu to let user choose which steps to perform
        mode = input("\nDo you want to run all steps automatically (a) or select specific steps to perform (s)? (a/s): ")
        if mode.lower() == 's':
            self.show_steps_menu()
        else:
            self.run_all_steps()
        
        return True


if __name__ == "__main__":
    setup = ESPThreadSetup()
    
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred during setup: {e}")
        sys.exit(1)
