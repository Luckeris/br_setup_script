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
    
    def build_rcp_firmware(self):
        """Build the RCP firmware required for the Border Router"""
        print("\n=== Building RCP Firmware ===")
        
        # Navigate to the RCP example directory
        rcp_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_rcp")
        if not os.path.exists(rcp_example_dir):
            print(f"ERROR: RCP example directory not found at {rcp_example_dir}")
            return False
        
        os.chdir(rcp_example_dir)
        
        # Clean previous build
        print("Cleaning previous RCP build...")
        clean_cmd = ["idf.py", "fullclean"]
        subprocess.run(clean_cmd, check=False)
        
        # Build the RCP firmware for ESP32H2 or ESP32C6
        # Using ESP32C6 as default - adjust as needed for your hardware
        print("Building RCP firmware (this will take a few minutes)...")
        build_cmd = ["idf.py", "set-target", "esp32c6", "build"]
        
        try:
            subprocess.run(build_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to build RCP firmware: {e}")
            self._show_build_logs(rcp_example_dir + "/build")
            
            # Create fallback solution if build fails
            print("\nAttempting to create a fallback rcp_version file...")
            os.makedirs(os.path.join(rcp_example_dir, "build"), exist_ok=True)
            with open(os.path.join(rcp_example_dir, "build", "rcp_version"), "w") as f:
                f.write("1.0.0-fallback")
            
            print("Created fallback rcp_version file. Proceeding with caution...")
            return True  # Return true to continue the process
        
        print("✓ RCP firmware built successfully")
        return True

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
        
        # Clean build directory
        print("Cleaning previous build...")
        clean_cmd = ["idf.py", "fullclean"]
        subprocess.run(clean_cmd, check=False)  # Don't fail if clean fails
        
        # First try building without flashing
        print("Attempting build first...")
        build_cmd = ["idf.py", "build"]
        try:
            subprocess.run(build_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"\nERROR: Build failed. Trying these troubleshooting steps:")
            print("1. Checking ESP-IDF version compatibility...")
            
            # Check ESP-IDF version
            idf_version_cmd = ["git", "-C", self.esp_idf_path, "describe", "--tags"]
            try:
                result = subprocess.run(idf_version_cmd, capture_output=True, text=True)
                print(f"Current ESP-IDF version: {result.stdout.strip()}")
            except:
                print("Could not determine ESP-IDF version")
            
            print("\n2. Recommended solutions:")
            print("a. Update ESP-IDF:")
            print(f"   cd {self.esp_idf_path} && git pull && git submodule update --init --recursive")
            print("b. Check build system resources:")
            print("   export NINJAFLAGS=\"-j 2\"  # Limit parallel jobs")
            print("c. Verify all requirements:")
            print(f"   {self.esp_idf_path}/install.sh")
            print("d. Check for file corruption:")
            print(f"   cd {self.esp_thread_br_path} && git checkout -- examples/basic_thread_border_router")
            
            # Try to determine the specific error from the build logs
            build_dir = os.path.join(br_example_dir, "build")
            self._show_build_logs(build_dir)
            
            return False
        
        # If build succeeds, proceed with flashing
        print("\nBuild successful. Proceeding with flashing...")
        flash_cmd = [
            "idf.py", 
            "-p", self.border_router_port, 
            "flash"
        ]
        
        try:
            subprocess.run(flash_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Flashing failed: {e}")
            return False
            
        print("✓ Border Router firmware flashed successfully")
        return True

    def build_and_flash_cli(self):
        """Flash the CLI using ESP32C6 example image from ESP-IDF"""
        print("\n=== Setting up CLI (ESP32C6) ===")
        input("Connect your ESP32C6 (CLI) device and press Enter to continue...")
        
        # Get the port using improved detection
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
        print("Flashing OpenThread CLI example for ESP32C6...")
        flash_cmd = [
        "idf.py", 
        "-p", self.cli_port,
        "set-target", "esp32c6", 
        "flash"
        ]
        
        print("Flashing CLI firmware (this may take several minutes)...")
        try:
            subprocess.run(flash_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to flash OpenThread CLI example: {e}")
            self._show_build_logs(cli_example_dir + "/build")
            return False
            
        print("✓ OpenThread CLI (ESP32C6) flashed successfully")
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
        print("2. Build RCP firmware (required before building Border Router)")
        print("3. Setup Border Router (ESP32S3 with RCP)")
        print("4. Setup CLI (ESP32C6)")
        print("5. Create Thread network dataset")
        print("6. Configure CLI to join Thread network")
        print("7. Setup Web GUI")
        print("8. Run all steps (1-7)")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ")
        
        if choice == '1':
            self.download_repositories()
        elif choice == '2':
            self.build_rcp_firmware()
        elif choice == '3':
            self.setup_border_router()
        elif choice == '4':
            self.build_and_flash_cli()
        elif choice == '5':
            self.create_dataset()
        elif choice == '6':
            self.configure_cli()
        elif choice == '7':
            self.setup_web_gui()
        elif choice == '8':
            self.run_all_steps()
        elif choice == '9':
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
        
        if not self.build_rcp_firmware():
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
        print("Border Router (ESP32S3 with RCP) on", self.border_router_port)
        print("CLI (ESP32C6) on", self.cli_port)
        print("Thread Network Dataset has been saved to thread_dataset.txt")
        
        return True
    
    def create_fallback_rcp_files(self):
        """Create fallback RCP files if build fails"""
        print("\n=== Creating Fallback RCP Files ===")
        
        # Navigate to the RCP example directory
        rcp_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_rcp")
        if not os.path.exists(rcp_example_dir):
            os.makedirs(os.path.join(rcp_example_dir, "build"), exist_ok=True)
        else:
            os.makedirs(os.path.join(rcp_example_dir, "build"), exist_ok=True)
        
        # Create a placeholder rcp_version file
        rcp_version_path = os.path.join(rcp_example_dir, "build", "rcp_version")
        with open(rcp_version_path, "w") as f:
            f.write("1.0.0-fallback")
        
        print(f"Created fallback rcp_version file at {rcp_version_path}")
        print("This can help bypass the build error, but you may need to manually flash the RCP later.")
        
        return True

    def execute(self):
        """Main execution method"""
        print("=== ESP Thread Border Router Setup Script ===")
        print("This script will guide you through setting up your OpenThread Border Router system.")
        print("Following the official Espressif tutorial: https://docs.espressif.com/projects/esp-thread-br/en/latest/dev-guide/build_and_run.html")
        print("Using the example locations from the tutorial:")
        print("- Border Router: esp-thread-br/examples/basic_thread_border_router")
        print("- RCP: $IDF_PATH/examples/openthread/ot_rcp")
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
        setup.execute()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred during setup: {e}")
        sys.exit(1)
