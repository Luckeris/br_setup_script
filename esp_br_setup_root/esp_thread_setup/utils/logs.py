#!/usr/bin/env python3
"""
Logging utilities for the ESP Thread Setup.
"""
import os
import glob
import subprocess

def show_build_logs(build_dir):
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

def color_text(text, color):
    """Utility function to colorize text output."""
    colors = {
        "green": "\033[92m",  # Success
        "red": "\033[91m",    # Error
        "yellow": "\033[93m", # Warning
        "blue": "\033[94m",   # Info
        "reset": "\033[0m"     # Reset
    }
    return f"{colors.get(color, colors['reset'])}{text}{colors['reset']}"

def color_text_with_icon(text, color, icon):
    """Utility function to colorize text output with an icon."""
    colors = {
        "green": "\033[92m",  # Success
        "red": "\033[91m",    # Error
        "yellow": "\033[93m", # Warning
        "blue": "\033[94m",   # Info
        "reset": "\033[0m"     # Reset
    }
    return f"{colors.get(color, colors['reset'])}{icon} {text}{colors['reset']}"

def print_success(message):
    print(color_text_with_icon(message, "green", "✔"))  # Checkmark

def print_error(message):
    print(color_text_with_icon(message, "red", "✖"))  # Crossmark

def print_warning(message):
    print(color_text_with_icon(message, "yellow", "⚠"))  # Warning triangle

def print_info(message):
    print(color_text_with_icon(message, "blue", "ℹ"))  # Info icon

def run_command_with_minimal_output(command, description):
    """Run a shell command with minimal output, showing only key progress updates."""
    print_info(f"{description}...")
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print_success(f"✔ {description} completed successfully.")
    except subprocess.CalledProcessError as e:
        print_error(f"✖ {description} failed.")
        print_warning("Error details:")
        print(e.stderr.strip())
        raise
