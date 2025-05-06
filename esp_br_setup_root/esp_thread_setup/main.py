#!/usr/bin/env python3
"""
Main entry point for the ESP Thread Setup utility.
"""
import os
import sys
import pprint

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Debugging sys.path
print("\n=== Debugging sys.path ===")
pprint.pprint(sys.path)
print("===========================\n")

# Import using the full path
from esp_br_setup_root.esp_thread_setup.setup.prerequisites import check_prerequisites
from esp_br_setup_root.esp_thread_setup.repositories.download import download_repositories
from esp_br_setup_root.esp_thread_setup.firmware.rcp import build_rcp_firmware, create_fallback_rcp_files
from esp_br_setup_root.esp_thread_setup.firmware.br import setup_border_router
from esp_br_setup_root.esp_thread_setup.firmware.cli import build_and_flash_cli
from esp_br_setup_root.esp_thread_setup.network.dataset import create_dataset
from esp_br_setup_root.esp_thread_setup.network.cli_config import configure_cli
from esp_br_setup_root.esp_thread_setup.web.gui import setup_web_gui
from esp_br_setup_root.esp_thread_setup.utils.ports import check_port
from esp_br_setup_root.esp_thread_setup.utils.logs import print_error

# Rest of your code...

class ESPThreadSetup:
    def __init__(self):
        self.border_router_port = None
        self.cli_port = None
        self.dataset = None
        self.skip_repositories = False

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
            download_repositories(self.skip_repositories)
        elif choice == '2':
            build_rcp_firmware()
        elif choice == '3':
            success, self.border_router_port = setup_border_router()
        elif choice == '4':
            success, self.cli_port = build_and_flash_cli()
        elif choice == '5':
            success, self.dataset, self.border_router_port = create_dataset(self.border_router_port)
        elif choice == '6':
            configure_cli(self.cli_port, self.dataset)
        elif choice == '7':
            setup_web_gui(self.border_router_port)
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
        """Run all setup steps sequentially and verify the setup"""
        print("\n=== Running Complete Setup Process ===")
        print("This will guide you through the entire setup process step by step.")
        print("You'll need both your ESP Thread Border Router and ESP32C6 CLI devices.")
        print("At different stages, you'll be prompted to connect one or both devices.")

        # Check prerequisites
        prereq_success, self.skip_repositories = check_prerequisites()
        if not prereq_success:
            return False

        # Download repositories if needed
        if not download_repositories(self.skip_repositories):
            return False

        # Build RCP firmware
        if not build_rcp_firmware():
            # Try fallback mechanism
            create_fallback_rcp_files()

        # Setup Border Router
        success, self.border_router_port = setup_border_router()
        if not success:
            return False

        # Setup CLI
        success, self.cli_port = build_and_flash_cli()
        if not success:
            return False

        print("\n=== Preparing for Network Configuration ===")
        print("For the next steps, you'll need BOTH devices connected to your computer simultaneously.")
        print("This is necessary to create the Thread network and configure the devices to communicate.")
        input("Press Enter when you're ready to continue...")

        # Create dataset
        success, self.dataset, self.border_router_port = create_dataset(self.border_router_port)
        if not success:
            return False

        # Configure CLI
        if not configure_cli(self.cli_port, self.dataset):
            return False

        # Setup Web GUI
        setup_web_gui(self.border_router_port)

        print("\n=== Setup Complete! ===")
        print("Your OpenThread Border Router system is now set up and running.")

        # --- Verification ---
        print("\n=== Verifying Setup ===")
        print("Performing basic verification checks...")

        # 1. Check if ports are valid
        if not check_port(self.border_router_port):
            print("ERROR: Border Router port is not valid.")
            return False
        print("✓ Border Router port verified.")

        if not check_port(self.cli_port):
            print("ERROR: CLI port is not valid.")
            return False
        print("✓ CLI port verified.")

        # 2. Check for dataset file
        import os
        from esp_thread_setup.config.constants import ESP_THREAD_BR_PATH
        dataset_file = os.path.join(ESP_THREAD_BR_PATH, "examples/basic_thread_border_router/thread_dataset.txt")
        if not os.path.exists(dataset_file):
            print("ERROR: Thread dataset file not found.")
            return False
        print("✓ Thread dataset file found.")

        print("\nBorder Router (ESP32S3 with RCP) on", self.border_router_port)
        print("CLI (ESP32C6) on", self.cli_port)
        print("Thread Network Dataset has been saved to thread_dataset.txt")

        print("\nTo further verify the Thread network:")
        print("1. Use the Web GUI (if enabled and IP is accessible) to check the status of the Thread network and connected devices.")
        print("2. Open the CLI console and use Thread CLI commands (e.g., `state`, `ping`) to verify communication within the Thread network.")

        print("\nYou now have a working Thread network with:")
        print("1. A Border Router that connects your Thread network to your WiFi network")
        print("2. A CLI device that can communicate over the Thread network")
        print("\nYou can use this setup as a self-made Thread dongle for your projects.")

        return True

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

        # Check prerequisites
        prereq_success, self.skip_repositories = check_prerequisites()
        if not prereq_success:
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
        print_error(f"Error occurred during setup: {e}")
        sys.exit(1)