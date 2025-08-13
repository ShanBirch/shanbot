#!/usr/bin/env python
"""
Set up client folders and organize existing data files
This script:
1. Creates a clients/ directory if it doesn't exist
2. Creates a folder for each client
3. Creates data/ subdirectory within each client's folder
4. Moves existing JSON data files to the appropriate client folders
"""
import os
import shutil
import glob
import json
from pathlib import Path


def setup_client_folders():
    """
    Set up client folders and organize existing data
    """
    print("Setting up client folder structure...")

    # Create base clients directory
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    clients_dir = base_dir / "clients"
    data_dir = base_dir / "data"

    if not clients_dir.exists():
        clients_dir.mkdir(exist_ok=True)
        print(f"Created clients directory: {clients_dir}")

    # List of all clients (extract from existing data files or use a predefined list)
    client_names_from_files = set()

    # Look for data files in both root and data directory
    data_patterns = ["*_fitness_wrapped_data.json"]
    search_dirs = [base_dir]

    if data_dir.exists():
        search_dirs.append(data_dir)

    # Find all client data files
    all_data_files = []
    for search_dir in search_dirs:
        for pattern in data_patterns:
            all_data_files.extend(list(search_dir.glob(pattern)))

    # Extract client names from filenames
    for file_path in all_data_files:
        filename = file_path.name
        # Extract client name from filename format: ClientName_Date_fitness_wrapped_data.json
        parts = filename.split('_fitness_wrapped_data.json')[0].split('_')

        # The client name could have underscores, so we need to be careful
        # Try to extract by looking at the date pattern
        date_index = -1
        for i, part in enumerate(parts):
            if len(part) == 10 and part.count('-') == 2:  # YYYY-MM-DD format
                date_index = i
                break

        if date_index > 0:
            # Client name is everything before the date
            client_name = '_'.join(parts[:date_index])
            client_names_from_files.add(client_name)
        else:
            # If we can't find a date, use all parts except possibly the last one
            client_name = '_'.join(parts[:-1]) if len(parts) > 1 else parts[0]
            client_names_from_files.add(client_name)

    # Additionally, use the predefined client list to ensure we have folders for all clients
    predefined_clients = [
        "Shannon_Birch",
        "Ben_Pryke",
        "Alice_Forster",
        "Sarika_Ramani",
        "Helen_Forster",
        "Nicole_Lynch",
        "Conor_Beveridge",
        "Rebecca_DAngelo",
        "Rick_Preston",
        "Claire_Ruberu",
        "Kylie_Pinder",
        "Jo_Foy",
        "Manny_Le-ray",
        "Tony_Strupl",
        "Heath_Kilgour",
        "Anna_Somogyi",
        "Danny_Birch",
        "MJ_Devine",
        "Ben_Norman",
        "Adri_Rivera",
        "Amanda_Buckingham",
        "Naman_Tiwari",
        "Kelly_Smith",
        "Shane_Minahan"
    ]

    # Combine the two client lists
    all_clients = set(predefined_clients) | client_names_from_files

    # Create folders for each client
    for client_name in all_clients:
        # Create client directory
        client_dir = clients_dir / client_name
        client_data_dir = client_dir / "data"

        if not client_dir.exists():
            client_dir.mkdir(exist_ok=True)
            print(f"Created client directory: {client_dir}")

        if not client_data_dir.exists():
            client_data_dir.mkdir(exist_ok=True)
            print(f"Created client data directory: {client_data_dir}")

    # Move existing data files to client folders
    moved_count = 0
    for file_path in all_data_files:
        filename = file_path.name
        # Extract client name using the same logic as above
        parts = filename.split('_fitness_wrapped_data.json')[0].split('_')

        date_index = -1
        for i, part in enumerate(parts):
            if len(part) == 10 and part.count('-') == 2:  # YYYY-MM-DD format
                date_index = i
                break

        if date_index > 0:
            client_name = '_'.join(parts[:date_index])
        else:
            client_name = '_'.join(parts[:-1]) if len(parts) > 1 else parts[0]

        # Destination path
        client_dir = clients_dir / client_name
        if not client_dir.exists():
            print(
                f"Warning: Client directory {client_dir} does not exist. Creating it.")
            client_dir.mkdir(exist_ok=True)
            (client_dir / "data").mkdir(exist_ok=True)

        dest_path = client_dir / "data" / filename

        # Copy file if it doesn't exist in the destination
        if not dest_path.exists():
            try:
                shutil.copy2(str(file_path), str(dest_path))
                print(f"Copied {filename} to {dest_path}")
                moved_count += 1
            except Exception as e:
                print(f"Error copying {filename}: {e}")

    print(
        f"\nSetup complete! Created folders for {len(all_clients)} clients and moved {moved_count} data files.")
    return clients_dir


if __name__ == "__main__":
    setup_client_folders()
