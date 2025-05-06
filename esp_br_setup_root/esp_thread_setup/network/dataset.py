#!/usr/bin/env python3
"""
Create and manage Thread network datasets.
"""
import os
import time
import subprocess
from esp_thread_setup.config.constants import ESP_THREAD_BR_PATH
from esp_thread_setup.utils.ports import check_port
from esp_thread_setup.utils.logs import print_success, print_error, print_warning, print_info, color_text

def create_dataset(border_router_port):
    """Create a Thread network dataset"""
    print_info("\n=== Creating Thread Network Dataset ===")
    print_warning("\n⚠️ IMPORTANT: For this step, you need to connect BOTH devices to your computer:")
    print("1. The ESP Thread Border Router")
    print("2. The ESP32C6 CLI device")
    print("\nThis is necessary for creating the Thread network and configuring the CLI device.")
    print("Please ensure both devices are connected before proceeding.")
    
    input("\nConfirm that BOTH devices are connected and press Enter to continue...")

    # Check if border_router_port is None or not valid and get it if needed
    if border_router_port is None or not check_port(border_router_port):
        print("Border Router port not found or not set. Let's detect it now.")
        from esp_thread_setup.utils.ports import find_device_port
        border_router_port = find_device_port("ESP Thread Border Router")
        if not border_router_port:
            print("ERROR: Border Router device not found. Please reconnect and try again.")
            return False, None, None
        print(f"Border Router found at port: {border_router_port}")

    # Generate a unique network name
    network_name = f"ESP-Thread-{int(time.time()) % 10000}"

    # Connect to the border router to create a dataset
    br_example_dir = os.path.join(ESP_THREAD_BR_PATH, "examples/basic_thread_border_router")
    if not os.path.exists(br_example_dir):
        print(f"ERROR: Border Router example directory not found at {br_example_dir}")
        print(f"Expected path: {br_example_dir}")
        print("Please make sure you've downloaded the esp-thread-br repository.")
        return False, None, None
            
    os.chdir(br_example_dir)

    # Check if a dataset already exists
    dataset_file_path = os.path.join(br_example_dir, "thread_dataset.txt")
    
    # Always delete the existing dataset file at the start
    if os.path.exists(dataset_file_path):
        os.remove(dataset_file_path)
        print(f"Deleted existing dataset file: {dataset_file_path}")

    # Check if a dataset already exists
    if os.path.exists(dataset_file_path):
        print(f"✓ Existing Thread network dataset found at {dataset_file_path}")
        with open(dataset_file_path, "r") as f:
            dataset = f.read()
        return True, dataset, border_router_port

    print(f"Creating Thread network: {network_name}")
    print(color_text("\n=== Border Router Console Instructions ===", "yellow"))
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
        print(f"Running: idf.py -p {border_router_port} monitor")
        subprocess.run(["idf.py", "-p", border_router_port, "monitor"], check=False)
    except Exception as e:
        print(f"Error opening Border Router console: {e}")
        retry = input("Would you like to manually enter the Border Router port? (y/n): ")
        if retry.lower() == 'y':
            border_router_port = input("Enter the Border Router port (e.g., /dev/ttyUSB0): ")
            try:
                subprocess.run(["idf.py", "-p", border_router_port, "monitor"], check=False)
            except Exception as e:
                print(f"Error opening Border Router console again: {e}")
                return False, None, None
        else:
            return False, None, None

    # Get dataset from user
    print(color_text("\n=== Thread Network Dataset ===", "yellow"))
    print("Please paste the ENTIRE dataset output below.")
    print("It should start with 'Active Timestamp:' and include all network parameters.")
    print("Press Enter twice to finish input.")

    # Accept multi-line input for the dataset
    print("\nPaste the dataset output here:")
    dataset_lines = []
    while True:
        line = input()
        if line.strip() == "":  # Stop on empty line
            break
        dataset_lines.append(line)

    dataset = "\n".join(dataset_lines)

    if not dataset or "Active Timestamp:" not in dataset:
        print("\nERROR: Invalid dataset. The dataset should start with 'Active Timestamp:'")
        print("Please ensure you copied the entire output from the 'dataset' command.")
        retry = input("Would you like to try entering the dataset again? (y/n): ")
        if retry.lower() == 'y':
            return create_dataset(border_router_port)
        else:
            return False, None, None

    # Save dataset to file
    dataset_file_path = os.path.join(br_example_dir, "thread_dataset.txt")
    with open(dataset_file_path, "w") as f:
        f.write(dataset)

    print_success(f"✓ Thread network dataset created and saved to {dataset_file_path}")

    # Parse the dataset to extract key parameters
    parsed_dataset = parse_dataset(dataset)

    # Display the extracted parameters
    print_info("\n=== Parsed Dataset Parameters ===")
    for key, value in parsed_dataset.items():
        if key != "dataset_lines":  # Skip raw dataset lines
            print(f"{key.replace('_', ' ').capitalize()}: {value}")

    # Save parsed parameters to a file (optional)
    parsed_dataset_file_path = os.path.join(br_example_dir, "parsed_thread_dataset.txt")
    with open(parsed_dataset_file_path, "w") as f:
        for key, value in parsed_dataset.items():
            if key != "dataset_lines":
                f.write(f"{key}: {value}\n")

    print_success(f"✓ Parsed dataset parameters saved to {parsed_dataset_file_path}")

    # Display instructions for manually fetching the dataset from the Border Router
    print_info("\n=== Border Router Dataset Fetch Instructions ===")
    print("To fetch the active dataset from the Border Router, follow these steps:")
    print("1. Open the Border Router monitor using the following command:")
    print(f"   idf.py -p {border_router_port} monitor")
    print("2. Once the monitor is open, enter the following command:")
    print("   dataset active -x")
    print("3. Copy the entire dataset output (select all text from 'Active Timestamp:' to the end).")
    print("4. Exit the monitor by pressing Ctrl+].")

    input("\nPress Enter to open the Border Router monitor...")

    # Open the Border Router monitor
    try:
        print(f"Running: idf.py -p {border_router_port} monitor")
        subprocess.run(["idf.py", "-p", border_router_port, "monitor"], check=False)
    except Exception as e:
        print_error(f"Error opening Border Router monitor: {e}")
        return False, None, None

    # Prompt the user to paste the dataset
    print_info("\n=== Paste the Active Dataset ===")
    print("Please paste the ENTIRE dataset output below.")
    print("It should start with 'Active Timestamp:' and include all network parameters.")
    print("Press Enter twice to finish input.")

    # Accept multi-line input for the dataset
    print("\nPaste the dataset output here:")
    dataset_lines = []
    while True:
        line = input()
        if line.strip() == "":  # Stop on empty line
            break
        dataset_lines.append(line)

    dataset = "\n".join(dataset_lines)

    # Ensure the dataset is properly captured and processed
    dataset_output = dataset.strip()
    if not dataset_output:
        print_error("Invalid dataset. The dataset is empty.")
        return None, None, None  # Return None to avoid unpacking issues

    # Check if the dataset is in hexadecimal format (numbers only)
    if dataset_output.startswith("0e"):
        print_warning("Dataset appears to be in compact hexadecimal format. Proceeding...")
    else:
        print_success("Dataset is in expanded key-value format.")

    print_success("Active dataset fetched successfully.")
    return dataset_output, None, None  # Return placeholders for the other two values

def parse_dataset(dataset):
    """Parse a Thread network dataset to extract key parameters"""
    network_name = ""
    ext_pan_id = ""
    pan_id = ""
    network_key = ""
    channel = ""
    mesh_local_prefix = ""
    
    # Parse the dataset to extract key parameters
    dataset_lines = dataset.strip().split('\n')
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
    
    return {
        "network_name": network_name,
        "ext_pan_id": ext_pan_id,
        "pan_id": pan_id,
        "network_key": network_key,
        "channel": channel,
        "mesh_local_prefix": mesh_local_prefix,
        "dataset_lines": dataset_lines
    }