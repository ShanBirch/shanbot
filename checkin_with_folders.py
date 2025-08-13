#!/usr/bin/env python
"""
Checkin Script with Client Folder Support
This script is a modified version of checkin.py that organizes data into client folders.
It collects client data and saves it to the appropriate client folder structure.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Function to ensure client folders exist


def ensure_client_folders_exist(client_name):
    """
    Ensure client folders exist for organizing data

    Args:
        client_name (str): Name of the client

    Returns:
        tuple: Paths to client directory and data directory
    """
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    clients_dir = base_dir / "clients"
    client_dir = clients_dir / client_name
    client_data_dir = client_dir / "data"

    # Create directories if they don't exist
    if not clients_dir.exists():
        clients_dir.mkdir(exist_ok=True)
        print(f"Created clients directory: {clients_dir}")

    if not client_dir.exists():
        client_dir.mkdir(exist_ok=True)
        print(f"Created client directory: {client_dir}")

    if not client_data_dir.exists():
        client_data_dir.mkdir(exist_ok=True)
        print(f"Created client data directory: {client_data_dir}")

    return client_dir, client_data_dir

# Function to save data to client folder


def save_data_to_client_folder(client_name, data, date_str=None):
    """
    Save client data to the appropriate client folder

    Args:
        client_name (str): Name of the client
        data (dict): Client data to save
        date_str (str, optional): Date string for the filename

    Returns:
        str: Path to the saved file
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Ensure client folders exist
    _, client_data_dir = ensure_client_folders_exist(client_name)

    # Create filename
    filename = f"{client_name}_{date_str}_fitness_wrapped_data.json"
    file_path = client_data_dir / filename

    # Save data
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Saved data for {client_name} to {file_path}")
    return str(file_path)

# This patching function can be added to the original checkin.py or checkin_lastweek.py


def patch_data_saving_function():
    """
    Patch the data saving function to use client folders

    This function can be used to monkey patch the save_data function in the original script.

    Example usage:

    # At the top of checkin.py or checkin_lastweek.py
    original_save_data = save_data  # Store the original function

    # After importing this module
    from checkin_with_folders import patch_data_saving_function, save_data_to_client_folder

    # Replace the save_data function with our new one
    save_data = save_data_to_client_folder
    """
    return save_data_to_client_folder


# Example script modification to checkin_lastweek.py:
"""
To modify checkin_lastweek.py to use client folders:

1. Import the folder functions
from checkin_with_folders import ensure_client_folders_exist, save_data_to_client_folder

2. Find where the data is saved in the client processing loop
   Usually in a method like process_client() or similar

3. Replace the save_data call with save_data_to_client_folder:

   # Original:
   data_file = f"{client_name}_{date_str}_fitness_wrapped_data.json"
   with open(data_file, 'w') as f:
       json.dump(data, f, indent=4)

   # Replace with:
   file_path = save_data_to_client_folder(client_name, data, date_str)
"""

# Example implementation for checkin_lastweek.py:


def get_last_week_dates():
    """Get start and end dates for last week (Monday to Sunday)"""
    today = datetime.now()
    # Calculate days since last Sunday
    days_since_sunday = today.weekday() + 1
    end_date = today - timedelta(days=days_since_sunday)  # Last Sunday
    start_date = end_date - timedelta(days=6)  # Last Monday
    return start_date, end_date


def save_data_for_last_week(client_name, client_data):
    """
    Save the client data for last week using the client folder structure

    Args:
        client_name (str): Name of the client
        client_data (dict): Client data to save

    Returns:
        str: Path to the saved file
    """
    # Get last week's date range
    start_date, end_date = get_last_week_dates()

    # Use the end date (Sunday) for the filename
    date_str = end_date.strftime("%Y-%m-%d")

    # Save using client folder structure
    return save_data_to_client_folder(client_name, client_data, date_str)


if __name__ == "__main__":
    print("This is a utility module to be imported by checkin.py or checkin_lastweek.py")
    print("To use it directly, import its functions in those scripts.")
    print("\nExample usage:")
    print("from checkin_with_folders import save_data_to_client_folder")
    print("...")
    print("# When saving client data:")
    print("file_path = save_data_to_client_folder(client_name, client_data, date_str)")
