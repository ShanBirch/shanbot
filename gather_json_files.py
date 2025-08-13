import os
import shutil
import glob

# Source directory to search
source_dir = r"C:\Users\Shannon"

# Target directory to copy files to
target_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\output\checkin_reviews"

# Create target directory if it doesn't exist
os.makedirs(target_dir, exist_ok=True)
print(f"Target directory: {target_dir}")

# Find all JSON files with the date "2025-03-16" in their filename
search_pattern = os.path.join(
    source_dir, "*2025-03-16*fitness_wrapped_data.json")
matching_files = glob.glob(search_pattern)

print(f"Found {len(matching_files)} matching JSON files")

# Copy each file to the target directory
copied_files = 0
for file_path in matching_files:
    file_name = os.path.basename(file_path)
    target_path = os.path.join(target_dir, file_name)

    try:
        shutil.copy2(file_path, target_path)
        print(f"Copied: {file_name}")
        copied_files += 1
    except Exception as e:
        print(f"Error copying {file_name}: {e}")

print(f"\nSuccessfully copied {copied_files} files to {target_dir}")
