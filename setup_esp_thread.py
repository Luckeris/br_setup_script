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
#--------------------------------------------------------------------------------------------------

class ESPThreadSetup:
    #-----------------------------------------------------------------------------------
    def __init__(self):
        self.home_dir = str(Path.home())
        self.esp_idf_path = os.environ.get('IDF_PATH', f"{self.home_dir}/esp/esp-idf")
        self.esp_thread_br_path = f"{self.home_dir}/esp/esp-thread-br"
        self.border_router_port = None
        self.cli_port = None
        self.dataset = None
        self.skip_repositories = False
    
    #-----------------------------------------------------------------------------------
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
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
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
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
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

        # Determine the target for RCP (you might need to adjust this logic)
        rcp_target = input("Enter the target chip for the RCP firmware (e.g., esp32c6, esp32s3): ").lower()
        if rcp_target not in ["esp32c6", "esp32s3"]:
            print("Warning: Invalid RCP target specified. Using esp32c6 as default.")
            rcp_target = "esp32c6"

        # Build the RCP firmware
        print(f"Building RCP firmware for {rcp_target} (this will take a few minutes)...")
        build_cmd = ["idf.py", "set-target", rcp_target, "build"]

        try:
            subprocess.run(build_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to build RCP firmware: {e}")
            self._show_build_logs(rcp_example_dir + "/build")
            return False  # Stop if RCP build fails

        print("✓ RCP firmware built successfully")
        return True
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
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
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def setup_border_router(self):
        """Flash the Thread Border Router firmware with RCP auto-update disabled and Web GUI enabled"""
        print("\n=== Setting up ESP Thread Border Router ===")
        print("IMPORTANT: For this step, you only need to connect the Border Router device.")
        print("The CLI device will be set up in a later step.")
        input("Connect your ESP Thread Border Router device and press Enter to continue...")

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
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def build_and_flash_cli(self):
        """Flash the CLI using ESP32C6 example image from ESP-IDF"""
        print("\n=== Setting up CLI (ESP32C6) ===")
        print("IMPORTANT: For this step, you only need to connect the ESP32C6 CLI device.")
        print("The Border Router device will be needed again in later steps.")
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
            self._show_build_logs(cli_example_dir + "/build")
            return False

        print("✓ OpenThread CLI (ESP32C6) flashed successfully")
        return True
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def create_dataset(self):
        """Create a Thread network dataset"""
        print("\n=== Creating Thread Network Dataset ===")
        print("\n⚠️ IMPORTANT: For this step, you need to connect BOTH devices to your computer:")
        print("1. The ESP Thread Border Router")
        print("2. The ESP32C6 CLI device")
        print("\nThis is necessary for creating the Thread network and configuring the CLI device.")
        print("Please ensure both devices are connected before proceeding.")
        
        input("\nConfirm that BOTH devices are connected and press Enter to continue...")

        # Check if border_router_port is None or not valid and get it if needed
        if self.border_router_port is None or not self._check_port(self.border_router_port):
            print("Border Router port not found or not set. Let's detect it now.")
            self.border_router_port = self._find_device_port("ESP Thread Border Router")
            if not self.border_router_port:
                print("ERROR: Border Router device not found. Please reconnect and try again.")
                return False
            print(f"Border Router found at port: {self.border_router_port}")

        # Generate a unique network name
        network_name = f"ESP-Thread-{int(time.time()) % 10000}"

        # Connect to the border router to create a dataset
        br_example_dir = os.path.join(self.esp_thread_br_path, "examples/basic_thread_border_router")
        if not os.path.exists(br_example_dir):
            print(f"ERROR: Border Router example directory not found at {br_example_dir}")
            print(f"Expected path: {br_example_dir}")
            print("Please make sure you've downloaded the esp-thread-br repository.")
            return False
            
        os.chdir(br_example_dir)

        print(f"Creating Thread network: {network_name}")
        print("\n=== Border Router Console Instructions ===")
        print("After the console opens, please run these commands:")
        print("1. dataset init new")
        print(f"2. dataset networkname {network_name}")
        print("3. dataset commit active")
        print("4. dataset")
        print("5. Copy the entire dataset output (select all text from 'Active Timestamp:' to the end)")
        print("\nPress Ctrl+] to exit the console when done")

        input("\nPress Enter to open the Border Router console...")

        # Open console with error handling
        try:
            print(f"Running: idf.py -p {self.border_router_port} monitor")
            subprocess.run(["idf.py", "-p", self.border_router_port, "monitor"], check=False)
        except Exception as e:
            print(f"Error opening Border Router console: {e}")
            retry = input("Would you like to manually enter the Border Router port? (y/n): ")
            if retry.lower() == 'y':
                self.border_router_port = input("Enter the Border Router port (e.g., /dev/ttyUSB0): ")
                try:
                    subprocess.run(["idf.py", "-p", self.border_router_port, "monitor"], check=False)
                except Exception as e:
                    print(f"Error opening Border Router console again: {e}")
                    return False
            else:
                return False

        # Get dataset from user
        print("\n=== Thread Network Dataset ===")
        print("Please paste the ENTIRE dataset output below.")
        print("It should start with 'Active Timestamp:' and include all network parameters.")
        self.dataset = input("\nPaste the dataset output here: ")

        if not self.dataset or "Active Timestamp:" not in self.dataset:
            print("\nERROR: Invalid dataset. The dataset should start with 'Active Timestamp:'")
            print("Please ensure you copied the entire output from the 'dataset' command.")
            retry = input("Would you like to try entering the dataset again? (y/n): ")
            if retry.lower() == 'y':
                self.dataset = input("\nPaste the dataset output here: ")
                if not self.dataset or "Active Timestamp:" not in self.dataset:
                    print("ERROR: Invalid dataset again. Please restart the dataset creation process.")
                    return False
            else:
                return False

        # Save dataset to file
        with open("thread_dataset.txt", "w") as f:
            f.write(self.dataset)

        print(f"✓ Thread network dataset created and saved to thread_dataset.txt")
        return True
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def configure_cli(self):
        """Configure the CLI device with the network dataset"""
        print("\n=== Configuring OpenThread CLI to Join Network ===")
        print("\n⚠️ IMPORTANT: Both devices should still be connected to your computer.")
        print("We'll now configure the CLI device to join the Thread network created by the Border Router.")
        
        # Verify CLI device is connected
        if not self._check_port(self.cli_port):
            print("CLI device not found at previous port. Let's detect it again.")
            self.cli_port = self._find_device_port("ESP32C6 CLI")
            if not self.cli_port:
                print("ERROR: CLI device not found. Please reconnect and try again.")
                return False

        # Change to the CLI example directory in ESP-IDF
        cli_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_cli")
        os.chdir(cli_example_dir)

        # Check if we have a dataset
        if not self.dataset:
            dataset_file = os.path.join(self.esp_thread_br_path, "examples/basic_thread_border_router/thread_dataset.txt")
            if os.path.exists(dataset_file):
                with open(dataset_file, "r") as f:
                    self.dataset = f.read()
                print("Loaded dataset from file.")
            else:
                print("ERROR: No dataset available. Please run the 'Create Thread network dataset' step first.")
                return False

        # Extract the key parameters from the dataset
        network_name = ""
        ext_pan_id = ""
        pan_id = ""
        network_key = ""
        channel = ""
        mesh_local_prefix = ""
        
        # Parse the dataset to extract key parameters
        dataset_lines = self.dataset.strip().split('\n')
        for line in dataset_lines:
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip().lower().replace(" ", "")
                value = parts[1].strip()
                
                if key == "networkname":
                    network_name = value
                elif key == "extpanid":
                    ext_pan_id = value
                elif key == "panid":
                    pan_id = value
                elif key == "networkkey":
                    network_key = value
                elif key == "channel":
                    channel = value
                elif key == "meshlocalprefix":
                    mesh_local_prefix = value.replace("/64", "").strip()
        
        print("\n=== CLI Console Instructions ===")
        print("After the console opens, we'll try THREE different methods to set the dataset.")
        print("If one method fails, try the next one.")
        
        print("\nMETHOD 1: Use individual commands to set each parameter")
        print("Run these commands one by one:")
        print(f"   dataset networkname {network_name}")
        print(f"   dataset extpanid {ext_pan_id}")
        print(f"   dataset panid {pan_id}")
        print(f"   dataset networkkey {network_key}")
        print(f"   dataset channel {channel}")
        if mesh_local_prefix:
            print(f"   dataset meshlocalprefix {mesh_local_prefix}")
        print("   dataset commit active")
        
        print("\nMETHOD 2: Use the multi-line dataset input")
        print("Run this command:")
        print("   dataset set active -")
        print("Then paste each line of the dataset (exactly as shown below) and press Enter after each line:")
        for line in dataset_lines:
            if ":" in line:
                print(f"   {line}")
        print("   (press Enter on an empty line to finish)")
        
        print("\nMETHOD 3: Try to use a hex string")
        print("Run this command:")
        print("   dataset tlvs active")
        print("Copy the hex string output, then try:")
        print("   dataset set active [paste-hex-string-here]")
        
        print("\nAfter successfully setting the dataset with ANY method, run:")
        print("   ifconfig up")
        print("   thread start")
        
        print("\nYou should see messages indicating the device is joining the Thread network.")
        print("Press Ctrl+] to exit the console when done")

        input("\nPress Enter to open the CLI console...")

        # Open CLI console
        subprocess.run(["idf.py", "-p", self.cli_port, "monitor"], check=False)

        response = input("\nDid the CLI successfully join the Thread network? (y/n): ")
        if response.lower() != 'y':
            print("\nTroubleshooting tips:")
            print("1. Make sure both devices are powered on and properly connected")
            print("2. Try resetting both devices and running the commands again")
            print("3. Try getting the active dataset from the Border Router in hex format:")
            print("   a. Connect to the Border Router console")
            print("   b. Run: 'dataset tlvs active'")
            print("   c. Copy the hex string output")
            print("   d. Connect to the CLI console")
            print("   e. Run: 'dataset set active [paste-hex-string-here]'")
            print("4. Check that the Border Router is functioning properly")
            
            retry = input("\nWould you like to try configuring the CLI again? (y/n): ")
            if retry.lower() == 'y':
                return self.configure_cli()
            return False

        print("✓ OpenThread CLI configured successfully")
        return True
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
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
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def _check_port(self, port):
        """Check if a port exists"""
        return os.path.exists(port) if port else False
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def setup_web_gui(self):
        """Setup the Web GUI for the Border Router and display its IP address"""
        print("\n=== Setting up Web GUI ===")
        print("The Border Router provides a web interface for configuration and monitoring.")

        # Get the IP address of the Border Router
        print("\nIMPORTANT: The Border Router should be connected to your WiFi network.")
        print("You can usually find the Border Router's IP address in your Wi-Fi router's device list.")
        ip_address = input("Please enter the IP address of your Border Router: ")  # User Input

        print(f"\nYou can access the Web GUI at http://{ip_address}")
        print("Use the web interface to:")
        print("1. Monitor the Thread network status")
        print("2. Configure network settings")
        print("3. View connected devices")

        # Basic verification (can be expanded)
        print("\nVerifying basic web GUI access...")
        try:
            #Try to open the web page
            urllib.request.urlopen("http://"+ip_address)
            print("✓ Web GUI is accessible!")
        except:
            print("ERROR: Web GUI might not be accessible at this IP. Please double-check the IP address and ensure the Border Router is connected to the network.")
        
        return True
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def show_steps_menu(self):
        """Show a menu to let user select which steps to perform"""
        print("\n=== ESP Thread Border Router Setup Steps ===")
        print("Please select which steps you want to perform:")
        print("1. Download/update repositories")
        print("2. Build RCP firmware (required before building Border Router)")
        print("3. Setup Border Router (ESP32S3 with RCP)")
        print("4. Setup CLI (ESP32C6)")
        print("5. Create Thread network dataset (requires BOTH devices connected)")
        print("6. Configure CLI to join Thread network (requires BOTH devices connected)")
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
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def run_all_steps(self):
        """Run all setup steps sequentially and verify the setup"""
        print("\n=== Running Complete Setup Process ===")
        print("This will guide you through the entire setup process step by step.")
        print("You'll need both your ESP Thread Border Router and ESP32C6 CLI devices.")
        print("At different stages, you'll be prompted to connect one or both devices.")

        if not self.download_repositories():
            return False

        # if not self.build_rcp_firmware():  # Skipping separate RCP build for integrated gateway
        #     return False

        if not self.setup_border_router():
            return False

        if not self.build_and_flash_cli():
            return False

        print("\n=== Preparing for Network Configuration ===")
        print("For the next steps, you'll need BOTH devices connected to your computer simultaneously.")
        print("This is necessary to create the Thread network and configure the devices to communicate.")
        input("Press Enter when you're ready to continue...")

        if not self.create_dataset():
            return False

        if not self.configure_cli():
            return False

        self.setup_web_gui()

        print("\n=== Setup Complete! ===")
        print("Your OpenThread Border Router system is now set up and running.")

        # --- Verification ---
        print("\n=== Verifying Setup ===")
        print("Performing basic verification checks...")

        # 1. Check if ports are valid (already done in individual steps, but can re-verify)
        if not self._check_port(self.border_router_port):
            print("ERROR: Border Router port is not valid.")
            return False
        print("✓ Border Router port verified.")

        if not self._check_port(self.cli_port):
            print("ERROR: CLI port is not valid.")
            return False
        print("✓ CLI port verified.")

        # 2. Check for dataset file
        dataset_file = os.path.join(self.esp_thread_br_path, "examples/basic_thread_border_router/thread_dataset.txt")
        if not os.path.exists(dataset_file):
            print("ERROR: Thread dataset file not found.")
            return False
        print("✓ Thread dataset file found.")

        print("\nBorder Router (ESP32S3 with RCP) on", self.border_router_port)
        print("CLI (ESP32C6) on", self.cli_port)
        print("Thread Network Dataset has been saved to thread_dataset.txt")

        print("\nTo further verify the Thread network:")
        print("1.  Use the Web GUI (if enabled and IP is accessible) to check the status of the Thread network and connected devices.")
        print("2.  Open the CLI console and use Thread CLI commands (e.g., `state`, `ping`) to verify communication within the Thread network.")

        print("\nYou now have a working Thread network with:")
        print("1.  A Border Router that connects your Thread network to your WiFi network")
        print("2.  A CLI device that can communicate over the Thread network")
        print("\nYou can use this setup as a self-made Thread dongle for your projects.")

        return True
    #-----------------------------------------------------------------------------------
    
    #-----------------------------------------------------------------------------------
    def create_fallback_rcp_files(self):
        """Create fallback RCP files if they don't exist"""
        print("\n=== Creating Fallback RCP Files ===")
        print("This is a fallback mechanism to ensure RCP files are available.")
        print("It's recommended to build the RCP firmware properly, but this will help in case of issues.")

        rcp_example_dir = os.path.join(self.esp_idf_path, "examples/openthread/ot_rcp")
        if not os.path.exists(rcp_example_dir):
            print(f"ERROR: RCP example directory not found at {rcp_example_dir}")
            return False

        # Create a dummy build directory if it doesn't exist
        build_dir = os.path.join(rcp_example_dir, "build")
        os.makedirs(build_dir, exist_ok=True)

        # Create dummy files if they don't exist
        rcp_bin_path_c6 = os.path.join(build_dir, "ot_rcp-esp32c6.bin")
        rcp_bin_path_s3 = os.path.join(build_dir, "ot_rcp-esp32s3.bin")

        if not os.path.exists(rcp_bin_path_c6):
            with open(rcp_bin_path_c6, "w") as f:
                f.write("This is a fallback RCP file for esp32c6.\nIt's recommended to build the RCP firmware properly.")
            print(f"Created fallback RCP file: {rcp_bin_path_c6}")

        if not os.path.exists(rcp_bin_path_s3):
            with open(rcp_bin_path_s3, "w") as f:
                f.write("This is a fallback RCP file for esp32s3.\nIt's recommended to build the RCP firmware properly.")
            print(f"Created fallback RCP file: {rcp_bin_path_s3}")

        print("✓ Fallback RCP files created/exist")
    #-----------------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------
    def execute(self):
        """Main execution function"""
        print("=== ESP Thread Border Router Setup ===")
        print("\nThis script will guide you through setting up an OpenThread Border Router using ESP devices.")
        print("\nIMPORTANT: For some steps, you'll need to connect BOTH devices to your computer.")
        print("This is necessary for creating the Thread network and configuring the devices to communicate.")
        
        print("\n=== Software Components ===")
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
    #-----------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------------