import fs from 'fs';

// Read the original script
const originalScript = fs.readFileSync('./setup_esp_threadweb.py', 'utf8');

// Common imports and utility functions that will be needed in all scripts
const commonCode = `#!/usr/bin/env python3
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
# Utility functions

def check_port(port):
    """Check if a port exists"""
    return os.path.exists(port) if port else False

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

def show_build_logs(build_dir):
    """Display relevant build logs when failures occur"""
    log_dir = os.path.join(build_dir, "log")
    if not os.path.exists(log_dir):
        print("No log directory found")
        return

    print("\\n=== Last 20 lines of build logs ===")
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
#--------------------------------------------------------------------------------------------------
`;

// Extract the class initialization code
const initCode = originalScript.match(/def __init__$$self$$:([\s\S]*?)def /)[1];

// Create the config script that will store shared data
const configScript = `${commonCode}
class ESPThreadConfig:
    def __init__(self):
${initCode.replace(/        /g, '        ')}
        self.dataset = None
        self.skip_repositories = False
        
    def save_config(self):
        """Save configuration to a file"""
        config = {
            'home_dir': self.home_dir,
            'esp_idf_path': self.esp_idf_path,
            'esp_thread_br_path': self.esp_thread_br_path,
            'border_router_port': self.border_router_port,
            'cli_port': self.cli_port,
            'dataset': self.dataset,
            'skip_repositories': self.skip_repositories
        }
        
        with open('esp_thread_config.json', 'w') as f:
            json.dump(config, f, indent=4)
        print("Configuration saved to esp_thread_config.json")
        
    def load_config(self):
        """Load configuration from a file"""
        try:
            with open('esp_thread_config.json', 'r') as f:
                config = json.load(f)
                
            self.home_dir = config.get('home_dir', self.home_dir)
            self.esp_idf_path = config.get('esp_idf_path', self.esp_idf_path)
            self.esp_thread_br_path = config.get('esp_thread_br_path', self.esp_thread_br_path)
            self.border_router_port = config.get('border_router_port', None)
            self.cli_port = config.get('cli_port', None)
            self.dataset = config.get('dataset', None)
            self.skip_repositories = config.get('skip_repositories', False)
            
            print("Configuration loaded from esp_thread_config.json")
            return True
        except FileNotFoundError:
            print("No configuration file found. Using default values.")
            return False
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

# Create a global config instance
config = ESPThreadConfig()

if __name__ == "__main__":
    print("ESP Thread Setup Configuration")
    print("==============================")
    
    # Try to load existing config
    config.load_config()
    
    # Allow user to update configuration
    print("\\nCurrent Configuration:")
    print(f"Home Directory: {config.home_dir}")
    print(f"ESP-IDF Path: {config.esp_idf_path}")
    print(f"ESP Thread BR Path: {config.esp_thread_br_path}")
    print(f"Border Router Port: {config.border_router_port}")
    print(f"CLI Port: {config.cli_port}")
    
    print("\\nUpdate Configuration (press Enter to keep current value):")
    
    new_idf_path = input(f"ESP-IDF Path [{config.esp_idf_path}]: ")
    if new_idf_path:
        config.esp_idf_path = new_idf_path
        
    new_br_path = input(f"ESP Thread BR Path [{config.esp_thread_br_path}]: ")
    if new_br_path:
        config.esp_thread_br_path = new_br_path
    
    # Save the updated configuration
    config.save_config()
    print("Configuration updated and saved.")
`;

// Extract the check_prerequisites function
const checkPrerequisitesCode = originalScript.match(/def check_prerequisites$$self$$:([\s\S]*?)def /)[1];

// Create the check prerequisites script
const checkPrerequisitesScript = `${commonCode}
from esp_thread_config import config

def check_prerequisites():
${checkPrerequisitesCode.replace(/        /g, '    ').replace(/self\./g, 'config.')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the check
    if check_prerequisites():
        print("\\nPrerequisites check completed successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nPrerequisites check failed. Please address the issues and try again.")
        sys.exit(1)
`;

// Extract the download_repositories function
const downloadReposCode = originalScript.match(/def download_repositories$$self$$:([\s\S]*?)def /)[1];

// Create the download repositories script
const downloadReposScript = `${commonCode}
from esp_thread_config import config

def download_repositories():
${downloadReposCode.replace(/        /g, '    ').replace(/self\./g, 'config.')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the download
    if download_repositories():
        print("\\nRepositories downloaded successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to download repositories. Please check your internet connection and try again.")
        sys.exit(1)
`;

// Extract the build_rcp_firmware function
const buildRcpCode = originalScript.match(/def build_rcp_firmware$$self$$:([\s\S]*?)def /)[1];

// Create the build RCP firmware script
const buildRcpScript = `${commonCode}
from esp_thread_config import config

def build_rcp_firmware():
${buildRcpCode.replace(/        /g, '    ').replace(/self\./g, 'config.').replace(/self._show_build_logs/g, 'show_build_logs')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the build
    if build_rcp_firmware():
        print("\\nRCP firmware built successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to build RCP firmware. Please check the logs and try again.")
        sys.exit(1)
`;

// Extract the setup_border_router function
const setupBrCode = originalScript.match(/def setup_border_router$$self$$:([\s\S]*?)def /)[1];

// Create the setup border router script
const setupBrScript = `${commonCode}
from esp_thread_config import config

def setup_border_router():
${setupBrCode.replace(/        /g, '    ').replace(/self\./g, 'config.').replace(/self._find_device_port/g, 'find_device_port')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the setup
    if setup_border_router():
        print("\\nBorder Router set up successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to set up Border Router. Please check the logs and try again.")
        sys.exit(1)
`;

// Extract the build_and_flash_cli function
const buildCliCode = originalScript.match(/def build_and_flash_cli$$self$$:([\s\S]*?)def /)[1];

// Create the build and flash CLI script
const buildCliScript = `${commonCode}
from esp_thread_config import config

def build_and_flash_cli():
${buildCliCode.replace(/        /g, '    ').replace(/self\./g, 'config.').replace(/self._find_device_port/g, 'find_device_port').replace(/self._show_build_logs/g, 'show_build_logs')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the build and flash
    if build_and_flash_cli():
        print("\\nCLI built and flashed successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to build and flash CLI. Please check the logs and try again.")
        sys.exit(1)
`;

// Extract the create_dataset function
const createDatasetCode = originalScript.match(/def create_dataset$$self$$:([\s\S]*?)def /)[1];

// Create the create dataset script
const createDatasetScript = `${commonCode}
from esp_thread_config import config

def create_dataset():
${createDatasetCode.replace(/        /g, '    ').replace(/self\./g, 'config.').replace(/self._find_device_port/g, 'find_device_port').replace(/self._check_port/g, 'check_port')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the dataset creation
    if create_dataset():
        print("\\nThread network dataset created successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to create Thread network dataset. Please check the logs and try again.")
        sys.exit(1)
`;

// Extract the configure_cli function
const configureCliCode = originalScript.match(/def configure_cli$$self$$:([\s\S]*?)def /)[1];

// Create the configure CLI script
const configureCliScript = `${commonCode}
from esp_thread_config import config

def configure_cli():
${configureCliCode.replace(/        /g, '    ').replace(/self\./g, 'config.').replace(/self._find_device_port/g, 'find_device_port').replace(/self._check_port/g, 'check_port').replace(/return self.configure_cli$$$$/g, 'return configure_cli()')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the CLI configuration
    if configure_cli():
        print("\\nCLI configured successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to configure CLI. Please check the logs and try again.")
        sys.exit(1)
`;

// Extract the setup_web_gui function
const setupWebGuiCode = originalScript.match(/def setup_web_gui$$self$$:([\s\S]*?)def /)[1];

// Create the setup web GUI script
const setupWebGuiScript = `${commonCode}
from esp_thread_config import config

def setup_web_gui():
${setupWebGuiCode.replace(/        /g, '    ').replace(/self\./g, 'config.')}

if __name__ == "__main__":
    # Load configuration
    config.load_config()
    
    # Run the web GUI setup
    if setup_web_gui():
        print("\\nWeb GUI set up successfully.")
        # Save any updates to the configuration
        config.save_config()
    else:
        print("\\nFailed to set up Web GUI. Please check the logs and try again.")
        sys.exit(1)
`;

// Create a main script that can run all steps
const mainScript = `${commonCode}
from esp_thread_config import config
import check_prerequisites
import download_repositories
import build_rcp_firmware
import setup_border_router
import build_and_flash_cli
import create_dataset
import configure_cli
import setup_web_gui

def run_all_steps():
    """Run all setup steps sequentially"""
    print("\\n=== Running Complete Setup Process ===")
    print("This will guide you through the entire setup process step by step.")
    print("You'll need both your ESP Thread Border Router and ESP32C6 CLI devices.")
    print("At different stages, you'll be prompted to connect one or both devices.")
    
    # Load configuration
    config.load_config()
    
    # Run each step
    if not check_prerequisites.check_prerequisites():
        return False
        
    if not download_repositories.download_repositories():
        return False
        
    if not build_rcp_firmware.build_rcp_firmware():
        return False
        
    if not setup_border_router.setup_border_router():
        return False
        
    if not build_and_flash_cli.build_and_flash_cli():
        return False
        
    print("\\n=== Preparing for Network Configuration ===")
    print("For the next steps, you'll need BOTH devices connected to your computer simultaneously.")
    print("This is necessary to create the Thread network and configure the devices to communicate.")
    input("Press Enter when you're ready to continue...")
    
    if not create_dataset.create_dataset():
        return False
        
    if not configure_cli.configure_cli():
        return False
        
    if not setup_web_gui.setup_web_gui():
        return False
        
    print("\\n=== Setup Complete! ===")
    print("Your OpenThread Border Router system is now set up and running.")
    
    # Verification
    print("\\n=== Verifying Setup ===")
    print("Performing basic verification checks...")
    
    # Check if ports are valid
    if not check_port(config.border_router_port):
        print("ERROR: Border Router port is not valid.")
        return False
    print("✓ Border Router port verified.")
    
    if not check_port(config.cli_port):
        print("ERROR: CLI port is not valid.")
        return False
    print("✓ CLI port verified.")
    
    # Check for dataset file
    dataset_file = os.path.join(config.esp_thread_br_path, "examples/basic_thread_border_router/thread_dataset.txt")
    if not os.path.exists(dataset_file):
        print("ERROR: Thread dataset file not found.")
        return False
    print("✓ Thread dataset file found.")
    
    print("\\nBorder Router (ESP32S3 with RCP) on", config.border_router_port)
    print("CLI (ESP32C6) on", config.cli_port)
    print("Thread Network Dataset has been saved to thread_dataset.txt")
    
    print("\\nTo further verify the Thread network:")
    print("1. Use the Web GUI (if enabled and IP is accessible) to check the status of the Thread network and connected devices.")
    print("2. Open the CLI console and use Thread CLI commands (e.g., \`state\`, \`ping\`) to verify communication within the Thread network.")
    
    print("\\nYou now have a working Thread network with:")
    print("1. A Border Router that connects your Thread network to your WiFi network")
    print("2. A CLI device that can communicate over the Thread network")
    print("\\nYou can use this setup as a self-made Thread dongle for your projects.")
    
    return True

def show_menu():
    """Show a menu to let user select which steps to perform"""
    print("\\n=== ESP Thread Border Router Setup Steps ===")
    print("Please select which steps you want to perform:")
    print("1. Check prerequisites")
    print("2. Download/update repositories")
    print("3. Build RCP firmware (required before building Border Router)")
    print("4. Setup Border Router (ESP32S3 with RCP)")
    print("5. Setup CLI (ESP32C6)")
    print("6. Create Thread network dataset (requires BOTH devices connected)")
    print("7. Configure CLI to join Thread network (requires BOTH devices connected)")
    print("8. Setup Web GUI")
    print("9. Run all steps (1-8)")
    print("0. Exit")
    
    choice = input("\\nEnter your choice (0-9): ")
    
    if choice == '1':
        check_prerequisites.check_prerequisites()
    elif choice == '2':
        download_repositories.download_repositories()
    elif choice == '3':
        build_rcp_firmware.build_rcp_firmware()
    elif choice == '4':
        setup_border_router.setup_border_router()
    elif choice == '5':
        build_and_flash_cli.build_and_flash_cli()
    elif choice == '6':
        create_dataset.create_dataset()
    elif choice == '7':
        configure_cli.configure_cli()
    elif choice == '8':
        setup_web_gui.setup_web_gui()
    elif choice == '9':
        run_all_steps()
    elif choice == '0':
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")
    
    # Return to the menu after completing a step
    show_menu()

if __name__ == "__main__":
    print("=== ESP Thread Border Router Setup ===")
    print("\\nThis script will guide you through setting up an OpenThread Border Router using ESP devices.")
    print("\\nIMPORTANT: For some steps, you'll need to connect BOTH devices to your computer.")
    print("This is necessary for creating the Thread network and configuring the devices to communicate.")
    
    print("\\n=== Software Components ===")
    print("- Border Router: esp-thread-br/examples/basic_thread_border_router")
    print("- RCP: $IDF_PATH/examples/openthread/ot_rcp")
    print("- CLI: $IDF_PATH/examples/openthread/ot_cli")
    
    # Load configuration
    config.load_config()
    
    # Show interactive menu
    mode = input("\\nDo you want to run all steps automatically (a) or select specific steps to perform (s)? (a/s): ")
    if mode.lower() == 's':
        show_menu()
    else:
        run_all_steps()
`;

// Write all scripts to files
fs.writeFileSync('esp_thread_config.py', configScript);
fs.writeFileSync('check_prerequisites.py', checkPrerequisitesScript);
fs.writeFileSync('download_repositories.py', downloadReposScript);
fs.writeFileSync('build_rcp_firmware.py', buildRcpScript);
fs.writeFileSync('setup_border_router.py', setupBrScript);
fs.writeFileSync('build_and_flash_cli.py', buildCliScript);
fs.writeFileSync('create_dataset.py', createDatasetScript);
fs.writeFileSync('configure_cli.py', configureCliScript);
fs.writeFileSync('setup_web_gui.py', setupWebGuiScript);
fs.writeFileSync('main.py', mainScript);

// Create a README file
const readmeContent = `# ESP Thread Setup Scripts

This is a collection of scripts to set up an ESP Thread Border Router system. The original monolithic script has been split into separate modules for better maintainability and flexibility.

## Scripts Overview

1. **esp_thread_config.py** - Manages configuration settings shared across all scripts
2. **check_prerequisites.py** - Checks if ESP-IDF environment is properly set up
3. **download_repositories.py** - Downloads all necessary repositories
4. **build_rcp_firmware.py** - Builds the RCP (Radio Co-Processor) firmware
5. **setup_border_router.py** - Sets up and flashes the Border Router
6. **build_and_flash_cli.py** - Builds and flashes the CLI device
7. **create_dataset.py** - Creates a Thread network dataset
8. **configure_cli.py** - Configures the CLI to join the Thread network
9. **setup_web_gui.py** - Sets up the Web GUI for the Border Router
10. **main.py** - Main script that can run all steps or provide a menu

## Usage

You can either run the individual scripts for specific tasks or use the main script to run all steps:

\`\`\`bash
# Run the main script with menu
python main.py

# Or run individual scripts
python check_prerequisites.py
python download_repositories.py
# etc.
\`\`\`

## Requirements

- Python 3.6+
- ESP-IDF environment properly set up
- pySerial library (\`pip install pyserial\`)
- ESP32S3 device (for Border Router)
- ESP32C6 device (for CLI)

## Configuration

All scripts share configuration through the \`esp_thread_config.py\` module. You can run this script directly to update your configuration:

\`\`\`bash
python esp_thread_config.py
\`\`\`

Configuration is saved to \`esp_thread_config.json\` and loaded automatically by all scripts.
`;

fs.writeFileSync('README.md', readmeContent);

console.log("Successfully created the following scripts:");
console.log("1. esp_thread_config.py - Configuration management");
console.log("2. check_prerequisites.py - Check ESP-IDF environment");
console.log("3. download_repositories.py - Download repositories");
console.log("4. build_rcp_firmware.py - Build RCP firmware");
console.log("5. setup_border_router.py - Setup Border Router");
console.log("6. build_and_flash_cli.py - Build and flash CLI");
console.log("7. create_dataset.py - Create Thread network dataset");
console.log("8. configure_cli.py - Configure CLI to join network");
console.log("9. setup_web_gui.py - Setup Web GUI");
console.log("10. main.py - Main script with all steps");
console.log("11. README.md - Documentation");