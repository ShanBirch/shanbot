#!/usr/bin/env python
import os
import shutil
from pathlib import Path
import re


def create_directory(dir_path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")


def organize_files():
    """Organize the shanbot folder into a cleaner structure"""
    # Base directory
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    print(f"Organizing directory: {base_dir}")

    # Create subdirectories
    directories = {
        "scripts": base_dir / "scripts",
        "data": base_dir / "data",
        "logs": base_dir / "logs",
        "media": base_dir / "media",
        "media_music": base_dir / "media" / "music",
        "media_templates": base_dir / "media" / "templates",
        "output": base_dir / "output",
        "backups": base_dir / "backups",
        "batch": base_dir / "batch",
    }

    for dir_path in directories.values():
        create_directory(dir_path)

    # Files to keep in the root directory
    keep_in_root = [
        "checkin.py",
        "simple_blue_video.py",
        "organize_folder.py",  # This script
        "README.md",
        "requirements.txt"
    ]

    # Create a simple README if it doesn't exist
    readme_path = base_dir / "README.md"
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write("# ShanBot Fitness Automation\n\n")
            f.write(
                "This folder contains scripts for automating fitness client data collection and video generation.\n\n")
            f.write("## Main Scripts\n\n")
            f.write(
                "- **checkin.py**: Collects fitness data from Trainerize for all clients\n")
            f.write(
                "- **simple_blue_video.py**: Generates videos from the collected fitness data\n\n")
            f.write("## Usage\n\n")
            f.write("1. Run `python checkin.py` to collect client data\n")
            f.write("2. Run `python simple_blue_video.py` to generate videos\n")
        print(f"Created README.md")

    # Move files to appropriate directories
    for file_path in base_dir.iterdir():
        if not file_path.is_file():
            continue  # Skip directories

        filename = file_path.name

        # Skip files that should stay in root
        if filename in keep_in_root:
            continue

        # Determine destination based on file type
        destination = None

        # Backup files
        if filename.endswith('.bak'):
            destination = directories["backups"]

        # Log files
        elif "log" in filename.lower() or filename.endswith('.log') or filename.endswith('.txt'):
            if "trainerize_log" in filename.lower():
                destination = directories["logs"]
            elif not (filename == "requirements.txt" or filename == "README.txt"):
                destination = directories["logs"]

        # JSON data files
        elif filename.endswith('.json'):
            if "fitness_wrapped_data" in filename:
                destination = directories["data"]
            elif filename in ["credentials.json", "settings.yaml"]:
                # Keep configuration files in root
                continue

        # Batch and PowerShell files
        elif filename.endswith('.bat') or filename.endswith('.ps1'):
            destination = directories["batch"]

        # Media files
        elif filename.endswith(('.mp4', '.mp3', '.png', '.jpg', '.jpeg')):
            if filename.endswith('.mp3'):
                destination = directories["media_music"]
            elif filename.endswith('.mp4'):
                destination = directories["media_templates"]
            else:
                destination = directories["media"]

        # Python scripts (except main ones)
        elif filename.endswith('.py') and filename not in keep_in_root:
            destination = directories["scripts"]

        # Move the file if destination was determined
        if destination:
            target_path = destination / filename
            # Don't overwrite existing files
            if not os.path.exists(target_path):
                try:
                    shutil.move(str(file_path), str(destination))
                    print(f"Moved {filename} to {destination}")
                except Exception as e:
                    print(f"Error moving {filename}: {e}")

    # Create a consolidated settings file
    create_settings_file(base_dir)

    # Update imports in the main scripts to reflect the new folder structure
    update_scripts_for_new_structure(base_dir)

    print("\nFolder organization complete!")
    print("\nREMINDER: You may need to update import statements or file paths in your scripts.")
    print("Check the scripts directory for any utility scripts that might be imported by the main scripts.")


def create_settings_file(base_dir):
    """Create a consolidated settings file for paths and configurations"""
    settings_path = base_dir / "settings.yaml"

    # Don't overwrite if exists
    if os.path.exists(settings_path):
        return

    with open(settings_path, "w") as f:
        f.write("# ShanBot Settings\n\n")
        f.write("# Paths\n")
        f.write("paths:\n")
        f.write("  data_dir: data\n")
        f.write("  output_dir: output\n")
        f.write("  media_dir: media\n")
        f.write("  logs_dir: logs\n\n")
        f.write("# Trainerize credentials\n")
        f.write("trainerize:\n")
        f.write("  username: Shannonbirch@cocospersonaltraining.com\n")
        f.write(
            "  # Note: For security, consider using environment variables for passwords\n\n")
        f.write("# Video settings\n")
        f.write("video:\n")
        f.write("  template: media/templates/blue2.mp4\n")
        f.write("  fallback_template: media/templates/blue.mp4\n")
        f.write("  music_dir: media/music\n")

    print(f"Created settings.yaml with default configuration")


def update_scripts_for_new_structure(base_dir):
    """Create adapter module to help with the transition to the new folder structure"""
    adapter_path = base_dir / "path_adapter.py"

    with open(adapter_path, "w") as f:
        f.write("""#!/usr/bin/env python
\"\"\"
Path adapter module to help with the transition to the new folder structure.
Import this in your scripts to get proper paths to files in the new structure.
\"\"\"
import os
import yaml
from pathlib import Path

# Get the base directory
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Paths to subdirectories
PATHS = {
    "data": BASE_DIR / "data",
    "scripts": BASE_DIR / "scripts",
    "logs": BASE_DIR / "logs",
    "media": BASE_DIR / "media",
    "media_music": BASE_DIR / "media" / "music",
    "media_templates": BASE_DIR / "media" / "templates",
    "output": BASE_DIR / "output",
    "batch": BASE_DIR / "batch",
}

# Load settings if available
SETTINGS = {}
settings_file = BASE_DIR / "settings.yaml"
if os.path.exists(settings_file):
    try:
        with open(settings_file, 'r') as f:
            SETTINGS = yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load settings file: {e}")

def get_path(name):
    \"\"\"Get the path to a subdirectory\"\"\"
    return PATHS.get(name, BASE_DIR)

def get_data_file_path(filename):
    \"\"\"Get the path to a data file\"\"\"
    return PATHS["data"] / filename

def get_template_video_path():
    \"\"\"Get the path to the template video\"\"\"
    # First try the settings
    if SETTINGS and "video" in SETTINGS and "template" in SETTINGS["video"]:
        template_path = BASE_DIR / SETTINGS["video"]["template"]
        if os.path.exists(template_path):
            return template_path
    
    # Then try the default locations
    template_path = PATHS["media_templates"] / "blue2.mp4"
    if os.path.exists(template_path):
        return template_path
        
    fallback_path = PATHS["media_templates"] / "blue.mp4"
    if os.path.exists(fallback_path):
        return fallback_path
        
    # Finally try the root directory
    root_template = BASE_DIR / "blue2.mp4"
    if os.path.exists(root_template):
        return root_template
        
    root_fallback = BASE_DIR / "blue.mp4"
    if os.path.exists(root_fallback):
        return root_fallback
    
    return None
""")

    print(f"Created path_adapter.py to help with the transition to the new folder structure")


if __name__ == "__main__":
    try:
        organize_files()
    except Exception as e:
        print(f"Error organizing files: {e}")
