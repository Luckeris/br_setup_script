#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from esp_thread_common import ESPThreadCommon

class DatasetCreator(ESPThreadCommon):
    def __init__(self):
        super().__init__()
        
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
        if self.border_router_port is None or not self.check_port(self.border_router_port):
            print("Border Router port not found or not set. Let's detect it now.")
            self.border_router_port = self.find_device_port("ESP Thread Border Router")
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

if __name__ == "__main__":
    dataset_creator = DatasetCreator()
    
    if not dataset_creator.check_prerequisites():
        sys.exit(1)
        
    try:
        if dataset_creator.create_dataset():
            print("Thread network dataset created successfully!")
        else:
            print("Dataset creation failed.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\nError occurred during setup: {e}")
        sys.exit(1)
