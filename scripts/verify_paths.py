import os
import re


def check_file_for_old_paths(file_path, old_path):
    """Check if a file contains any references to the old path."""
    # Skip binary files and backup files
    if file_path.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.bak')):
        return []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}, skipping...")
        return []

    found_paths = []

    # Check for various path formats

    # Standard path with backslashes
    if old_path in content:
        found_paths.append(f"Standard path: {old_path}")

    # Path with forward slashes (often used in code)
    old_path_fwd = old_path.replace('\\', '/')
    if old_path_fwd in content:
        found_paths.append(f"Forward slash path: {old_path_fwd}")

    # Path with escaped backslashes (as in string literals)
    old_path_escaped = old_path.replace('\\', '\\\\')
    if old_path_escaped in content:
        found_paths.append(f"Escaped backslash path: {old_path_escaped}")

    # Raw string notation r"path"
    raw_old_path = 'r"' + old_path + '"'
    if raw_old_path in content:
        found_paths.append(f"Raw string path: {raw_old_path}")

    # Only report if paths were found
    if found_paths:
        return [f"In file {file_path}:"] + found_paths

    return []


# Set the path to check for
old_path = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"
directory = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\shanbot"

print("Checking for remaining Desktop paths in files...")
print(f"Looking for: {old_path}")
print(f"In directory: {directory}")
print("-" * 50)

# Variables to track findings
remaining_paths_found = 0
files_with_paths = 0

# Process files
for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(('.py', '.txt', '.md', '.json', '.html', '.js', '.css', '.bat', '.cmd')):
            file_path = os.path.join(root, file)

            # Skip the update and verification scripts
            if os.path.basename(file_path) in ['update_paths.py', 'update_paths_auto.py', 'verify_paths.py']:
                continue

            found_paths = check_file_for_old_paths(file_path, old_path)
            if found_paths:
                files_with_paths += 1
                # Subtract 1 for the filename line
                remaining_paths_found += len(found_paths) - 1

                # Print the findings
                for line in found_paths:
                    print(line)
                print()  # Empty line between files

# Print summary
print("-" * 50)
if remaining_paths_found > 0:
    print(f"Found {remaining_paths_found} instances of Desktop paths still remaining in {files_with_paths} files.")
    print("Check the output above for details.")
else:
    print("Great news! No Desktop paths were found in your files.")
    print("The path update was successful.")

print("Verification completed.")
