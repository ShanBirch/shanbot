#!/usr/bin/env python
"""
Data File Organizer

This script moves data files created by checkin_lastweek.py to the appropriate client folders.
Run this script after checkin_lastweek.py finishes to organize the data files.
"""

import os
import shutil
import glob
from pathlib import Path
import re
from datetime import datetime


def organize_data_files():
    """
    Find all fitness wrapped data files in the root directory and move them to client folders
    """
    print("Organizing data files into client folders...")

    # Base directory
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Patterns to look for
    patterns = [
        "*_fitness_wrapped_data.json",
        "*_lastweek_fitness_wrapped_data.json"
    ]

    # Count of files moved
    moved_count = 0

    # Find all matching files in the root directory
    data_files = []
    for pattern in patterns:
        data_files.extend(list(base_dir.glob(pattern)))

    # Create client folders if needed
    from setup_client_folders import setup_client_folders
    setup_client_folders()

    # Process each file
    for file_path in data_files:
        filename = file_path.name

        # Extract client name
        # Filename format: client_name_date_fitness_wrapped_data.json or
        # client_name_lastweek_fitness_wrapped_data.json
        match = re.match(
            r'(.+?)_(?:\d{4}-\d{2}-\d{2}|lastweek)_fitness_wrapped_data\.json', filename)

        if match:
            client_name = match.group(1)

            # Destination path
            client_dir = base_dir / "clients" / client_name
            client_data_dir = client_dir / "data"

            # Make sure directories exist
            if not client_dir.exists():
                client_dir.mkdir(exist_ok=True)
                print(f"Created client directory: {client_dir}")

            if not client_data_dir.exists():
                client_data_dir.mkdir(exist_ok=True)
                print(f"Created client data directory: {client_data_dir}")

            # If filename contains "lastweek", rename it with a date
            if "lastweek" in filename:
                # Get last week's Sunday date
                today = datetime.now()
                days_since_sunday = today.weekday() + 1
                last_sunday = today - timedelta(days=days_since_sunday)
                date_str = last_sunday.strftime("%Y-%m-%d")

                # Create new filename with the date
                new_filename = f"{client_name}_{date_str}_fitness_wrapped_data.json"
                dest_path = client_data_dir / new_filename
            else:
                # Keep original filename
                dest_path = client_data_dir / filename

            # Copy to client folder
            try:
                shutil.copy2(str(file_path), str(dest_path))
                print(f"Copied {filename} to {dest_path}")
                moved_count += 1
            except Exception as e:
                print(f"Error copying {filename}: {e}")

    print(
        f"\nOrganization complete! Moved {moved_count} data files to client folders.")


if __name__ == "__main__":
    from datetime import timedelta
    organize_data_files()
