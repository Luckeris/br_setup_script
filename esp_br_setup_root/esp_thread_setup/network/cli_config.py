﻿
#!/usr/bin/env python3
"""
Configure the CLI device to join the Thread network.
"""
import os
import subprocess
from esp_thread_setup.config.constants import ESP_IDF_PATH, ESP_THREAD_BR_PATH
from esp_thread_setup.utils.ports import check_port
from esp_thread_setup.network.dataset import parse_dataset

def configure_cli(cli_port, dataset=None):
    """Configure the CLI device with the network dataset"""
    print("\n=== Configuring OpenThread CLI to Join Network ===")
    print("\n⚠️ IMPORTANT: Both devices should still be connected to your computer.")
    print("We'll now configure the CLI device to join the Thread network created by the Border Router.")
    
    # Verify CLI device is connected
    if not check_port(cli_port):
        print("CLI device not found at previous port. Let's detect it again.")
        from esp_thread_setup.utils.ports import find_device_port
        cli_port = find_device_port("ESP32C6 CLI")
        if not cli_port:
            print("ERROR: CLI device not found. Please reconnect and try again.")
            return False

    # Change to the CLI example directory in ESP-IDF
    cli_example_dir = os.path.join(ESP_IDF_PATH, "examples/openthread/ot_cli")
    os.chdir(cli_example_dir)

    # Check if we have a dataset
    if not dataset:
        dataset_file = os.path.join(ESP_THREAD_BR_PATH, "examples/basic_thread_border_router/thread_dataset.txt")
        if os.path.exists(dataset_file):
            with open(dataset_file, "r") as f:
                dataset = f.read()
            print("Loaded dataset from file.")
        else:
            print("ERROR: No dataset available. Please run the 'Create Thread network dataset' step first.")
            return False

    # Parse the dataset
    dataset_params = parse_dataset(dataset)
    
    print("\n=== CLI Console Instructions ===")
    print("After the console opens, we'll try THREE different methods to set the dataset.")
    print("If one method fails, try the next one.")
    
    print("\nMETHOD 1: Use individual commands to set each parameter")
    print("Run these commands one by one:")
    print(f"   dataset networkname {dataset_params['network_name']}")
    print(f"   dataset extpanid {dataset_params['ext_pan_id']}")
    print(f"   dataset panid {dataset_params['pan_id']}")
    print(f"   dataset networkkey {dataset_params['network_key']}")
    print(f"   dataset channel {dataset_params['channel']}")
    if dataset_params['mesh_local_prefix']:
        print(f"   dataset meshlocalprefix {dataset_params['mesh_local_prefix']}")
    print("   dataset commit active")
    
    print("\nMETHOD 2: Use the multi-line dataset input")
    print("Run this command:")
    print("   dataset set active -")
    print("Then paste each line of the dataset (exactly as shown below) and press Enter after each line:")
    for line in dataset_params['dataset_lines']:
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
    subprocess.run(["idf.py", "-p", cli_port, "monitor"], check=False)

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
            return configure_cli(cli_port, dataset)
        return False

    print("✓ OpenThread CLI configured successfully")
    return True