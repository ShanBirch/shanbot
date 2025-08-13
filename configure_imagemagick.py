"""
Configure MoviePy to use ImageMagick

This script will update MoviePy's configuration to properly use ImageMagick.
"""

import os
from moviepy.config import change_settings
import sys


def configure_moviepy():
    # Common installation paths for ImageMagick on Windows
    possible_paths = [
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
        r"C:\Program Files\ImageMagick-7.0.8-Q16\magick.exe",
        r"C:\Program Files\ImageMagick-6.9.13-Q16\convert.exe"
    ]

    # Check if any of these paths exist
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found ImageMagick at: {path}")
            change_settings({"IMAGEMAGICK_BINARY": path})
            print("MoviePy configuration updated successfully!")
            return True

    # If no path was found, ask the user
    print("ImageMagick not found at common locations.")
    print("Please install ImageMagick from: https://imagemagick.org/script/download.php")
    print("When installing, make sure to check 'Install legacy utilities' option.")
    print("")
    manual_path = input(
        "After installation, enter the full path to magick.exe or convert.exe: ")

    if os.path.exists(manual_path):
        change_settings({"IMAGEMAGICK_BINARY": manual_path})
        print("MoviePy configuration updated successfully!")
        return True
    else:
        print(f"Path not found: {manual_path}")
        print("Configuration failed. Please verify the path and try again.")
        return False


if __name__ == "__main__":
    print("Configuring MoviePy to use ImageMagick...")
    success = configure_moviepy()
    if success:
        print("\nYou can now run the video auto-labeler with:")
        print("python fixed_video_auto_labeler.py --process-now")
    else:
        print("\nInstallation instructions:")
        print("1. Download ImageMagick from: https://imagemagick.org/script/download.php")
        print("2. During installation, make sure to check 'Install legacy utilities'")
        print("3. After installation, run this script again")

    sys.exit(0 if success else 1)
