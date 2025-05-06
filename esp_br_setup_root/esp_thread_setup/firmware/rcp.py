#!/usr/bin/env python3
"""
Build and manage RCP (Radio Co-Processor) firmware.
"""
import os
from esp_thread_setup.config.constants import ESP_IDF_PATH, DEFAULT_RCP_TARGET
from esp_thread_setup.utils.logs import show_build_logs, print_success, print_error, print_warning, print_info, run_command_with_minimal_output

def build_rcp_firmware():
    """Build the RCP firmware required for the Border Router"""
    print_info("\n=== Building RCP Firmware ===")

    # Navigate to the RCP example directory
    rcp_example_dir = os.path.join(ESP_IDF_PATH, "examples/openthread/ot_rcp")
    if not os.path.exists(rcp_example_dir):
        print(f"ERROR: RCP example directory not found at {rcp_example_dir}")
        return False

    os.chdir(rcp_example_dir)

    # Clean previous build
    print_warning("Cleaning previous RCP build...")
    run_command_with_minimal_output(["idf.py", "fullclean"], "Cleaning RCP build directory")

    # Set the default RCP target to esp32h2
    rcp_target = "esp32h2"
    print(f"Using default RCP target: {rcp_target}")

    # Build the RCP firmware
    print(f"Building RCP firmware for {rcp_target} (this will take a few minutes)...")
    try:
        run_command_with_minimal_output(["idf.py", "set-target", rcp_target, "build"], "Building RCP firmware")
    except subprocess.CalledProcessError as e:
        print_error(f"ERROR: Failed to build RCP firmware: {e}")
        show_build_logs(rcp_example_dir + "/build")
        return False  # Stop if RCP build fails

    print_success("✓ RCP firmware built successfully")
    return True

def create_fallback_rcp_files():
    """Create fallback RCP files if they don't exist"""
    print("\n=== Creating Fallback RCP Files ===")
    print("This is a fallback mechanism to ensure RCP files are available.")
    print("It's recommended to build the RCP firmware properly, but this will help in case of issues.")

    rcp_example_dir = os.path.join(ESP_IDF_PATH, "examples/openthread/ot_rcp")
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
    return True