import os
import re
import sys


def update_paths_in_file(file_path, old_path, new_path):
    """Update hardcoded paths in a file."""
    # Skip binary files
    if file_path.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe', '.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return 0

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}, skipping...")
        return 0

    # Track original content to check if changes were made
    original_content = content

    # Handle various path formats

    # Standard path with backslashes
    content = content.replace(old_path, new_path)

    # Path with forward slashes (often used in code)
    old_path_fwd = old_path.replace('\\', '/')
    new_path_fwd = new_path.replace('\\', '/')
    content = content.replace(old_path_fwd, new_path_fwd)

    # Path with escaped backslashes (as in string literals)
    old_path_escaped = old_path.replace('\\', '\\\\')
    new_path_escaped = new_path.replace('\\', '\\\\')
    content = content.replace(old_path_escaped, new_path_escaped)

    # Raw string notation r"path"
    raw_old_path = 'r"' + old_path + '"'
    raw_new_path = 'r"' + new_path + '"'
    content = content.replace(raw_old_path, raw_new_path)

    # Raw string with escaped backslashes
    raw_old_path_escaped = 'r"' + old_path_escaped + '"'
    raw_new_path_escaped = 'r"' + new_path_escaped + '"'
    content = content.replace(raw_old_path_escaped, raw_new_path_escaped)

    # Check if any changes were made
    if content != original_content:
        try:
            # Create backup of original file
            backup_path = file_path + '.bak'
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                backup_file.write(original_content)

            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            print(
                f"Updated paths in {file_path} (backup created at {backup_path})")
            return 1
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            return 0

    return 0


def find_and_update_paths(directory, old_path, new_path):
    """Find all relevant files in a directory and update paths in them."""
    total_files_updated = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.txt', '.md', '.json', '.html', '.js', '.css', '.bat', '.cmd')):
                file_path = os.path.join(root, file)
                updated = update_paths_in_file(file_path, old_path, new_path)
                total_files_updated += updated

    return total_files_updated


def main():
    # Change these paths to correctly reflect Desktop (old) and shanbot (new)
    old_path = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"
    new_path = "C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\shanbot"

    print("This script will update hardcoded paths in your files.")
    print(f"From: {old_path}")
    print(f"To: {new_path}")
    print("\nIMPORTANT: Backups of modified files will be created with .bak extension.")

    confirm = input("Do you want to continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return

    # We'll search in the shanbot directory
    directory = new_path

    print(f"\nSearching for files in {directory}...")
    total_files_updated = find_and_update_paths(directory, old_path, new_path)

    if total_files_updated > 0:
        print(f"\nDone! Updated paths in {total_files_updated} files.")
        print("Backups of the original files were created with .bak extension.")
    else:
        print("\nNo files were updated. Either no hardcoded paths were found or there was an issue.")


if __name__ == "__main__":
    main()
