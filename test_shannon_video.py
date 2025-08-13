#!/usr/bin/env python
"""
Test script to generate a video for Shannon Birch only
"""

import os
import sys
from pathlib import Path
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_script')


def main():
    """Generate a test video for Shannon Birch using the client folder structure"""
    # Import here to avoid import errors
    from simple_blue_video_client_folders import generate_blue_video

    # Client name to test
    client_name = "Shannon_Birch"

    # Base directory
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Path to the blue video template
    video_path = base_dir / "blue2.mp4"
    if not video_path.exists():
        # Check other possible locations
        alternate_paths = [
            base_dir / "media" / "templates" / "blue2.mp4",
            base_dir / "media" / "blue2.mp4",
            base_dir / "templates" / "blue2.mp4"
        ]

        for path in alternate_paths:
            if path.exists():
                video_path = path
                break
        else:
            print("Error: Could not find blue2.mp4 template video!")
            return 1

    print(f"Using video template: {video_path}")

    # Output directory
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)

    # Custom output path (so we can easily find and play the video)
    output_path = output_dir / f"{client_name}_test_video.mp4"

    print(f"Generating video for {client_name}...")
    print(f"Output will be saved to: {output_path}")

    # Generate the video
    start_time = time.time()
    result_path = generate_blue_video(client_name, str(output_path))
    end_time = time.time()

    if result_path:
        print(
            f"\nSuccess! Video generated in {end_time - start_time:.2f} seconds")
        print(f"Video saved to: {result_path}")

        # Also mention where the client folder video is
        client_dir = base_dir / "clients" / client_name
        client_video = client_dir / "weekly_checkin.mp4"
        if client_video.exists():
            print(
                f"The video was also saved to the client folder: {client_video}")
    else:
        print("\nError: Failed to generate video!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
