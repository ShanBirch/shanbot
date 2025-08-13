#!/usr/bin/env python
"""
Adapter script for simple_blue_video.py that works with the new folder structure.
This script finds files in the new folder structure and runs simple_blue_video.py with the right paths.
"""
import os
import sys
import glob
import shutil
import argparse
from pathlib import Path
import subprocess
from datetime import datetime


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Run simple_blue_video.py with the new folder structure')
    parser.add_argument('--upload', action='store_true',
                        help='Upload the videos to Google Drive after creation')
    parser.add_argument('--folder', type=str,
                        help='Google Drive folder name to upload to')
    parser.add_argument('--date', type=str,
                        help='Date to look for client files (YYYY-MM-DD format). If not provided, uses today\'s date.')
    args = parser.parse_args()

    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    data_dir = base_dir / "data"
    media_dir = base_dir / "media"
    templates_dir = media_dir / "templates"
    output_dir = base_dir / "output"

    # Make sure directories exist
    for dir_path in [data_dir, templates_dir, output_dir]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")

    # Determine date string for file finding
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            date_str = target_date.strftime('%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format. Please use YYYY-MM-DD format.")
            return 1
    else:
        target_date = datetime.now().date()
        date_str = target_date.strftime('%Y-%m-%d')

    print(f"Looking for client data from {date_str}...")

    # Find template video file
    video_path = None

    # First check in templates directory
    if os.path.exists(templates_dir / "blue2.mp4"):
        video_path = templates_dir / "blue2.mp4"
    elif os.path.exists(templates_dir / "blue.mp4"):
        video_path = templates_dir / "blue.mp4"
    # Then check in base directory
    elif os.path.exists(base_dir / "blue2.mp4"):
        video_path = base_dir / "blue2.mp4"
        # Also copy it to templates directory for future use
        try:
            shutil.copy(str(video_path), str(templates_dir / "blue2.mp4"))
            print(f"Copied {video_path} to {templates_dir}")
        except Exception as e:
            print(
                f"Warning: Could not copy template video to templates directory: {e}")
    elif os.path.exists(base_dir / "blue.mp4"):
        video_path = base_dir / "blue.mp4"
        # Also copy it to templates directory for future use
        try:
            shutil.copy(str(video_path), str(templates_dir / "blue.mp4"))
            print(f"Copied {video_path} to {templates_dir}")
        except Exception as e:
            print(
                f"Warning: Could not copy template video to templates directory: {e}")

    if video_path is None:
        print("Error: No template video found. Please ensure blue2.mp4 or blue.mp4 exists.")
        return 1

    print(f"Using template video: {video_path}")

    # Find client data files
    # First check in data directory
    data_files = list(data_dir.glob(f"*_{date_str}_fitness_wrapped_data.json"))
    if not data_files:
        data_files = list(data_dir.glob("*_fitness_wrapped_data.json"))

    # Then check in base directory
    if not data_files:
        base_data_files = list(base_dir.glob(
            f"*_{date_str}_fitness_wrapped_data.json"))
        if not base_data_files:
            base_data_files = list(base_dir.glob(
                "*_fitness_wrapped_data.json"))

        # Copy files to data directory
        for file_path in base_data_files:
            target_path = data_dir / file_path.name
            if not target_path.exists():
                try:
                    shutil.copy(str(file_path), str(target_path))
                    print(f"Copied {file_path.name} to {data_dir}")
                    data_files.append(target_path)
                except Exception as e:
                    print(
                        f"Warning: Could not copy {file_path.name} to data directory: {e}")
                    # Still add it to the list so we can process it
                    data_files.append(file_path)
            else:
                data_files.append(target_path)

    if not data_files:
        print("No client data files found! Please run the checkin.py script first to generate client data.")
        return 1

    print(f"Found {len(data_files)} client data files.")

    # Create symbolic links in base directory for compatibility with simple_blue_video.py
    for data_file in data_files:
        target_path = base_dir / data_file.name
        if not target_path.exists() and data_file.parent != base_dir:
            try:
                # On Windows, creating symbolic links requires admin privileges
                # So we'll copy the files instead
                shutil.copy(str(data_file), str(target_path))
                print(f"Created copy of {data_file.name} for compatibility")
            except Exception as e:
                print(
                    f"Warning: Could not create compatibility copy for {data_file.name}: {e}")

    # Run the simple_blue_video.py script
    cmd = [sys.executable, str(base_dir / "simple_blue_video.py")]

    # Add command line arguments
    if args.date:
        cmd.extend(["--date", args.date])
    if args.upload:
        cmd.append("--upload")
    if args.folder:
        cmd.extend(["--folder", args.folder])

    print(f"\nRunning: {' '.join(cmd)}")

    # Run the process
    process = subprocess.run(cmd)

    # Clean up temporary copies in base directory
    for data_file in data_files:
        temp_path = base_dir / data_file.name
        if temp_path.exists() and data_file.parent != base_dir:
            try:
                os.remove(temp_path)
                print(f"Removed temporary file: {temp_path}")
            except Exception as e:
                print(
                    f"Warning: Could not remove temporary file {temp_path}: {e}")

    return process.returncode


if __name__ == "__main__":
    sys.exit(main())
