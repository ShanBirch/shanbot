#!/usr/bin/env python3
"""
Test Elena Green's video generation with goal completion slide
"""

import os
import json
from simple_blue_video import process_client_data


def main():
    print("🎬 TESTING ELENA GREEN'S VIDEO WITH GOAL COMPLETION SLIDE")
    print("=" * 65)

    # File paths
    elena_file = r"output\checkin_reviews\Elena_Green_2025-06-08_fitness_wrapped_data.json"
    video_path = "blue2.mp4"
    output_dir = "output"

    # Check if files exist
    if not os.path.exists(elena_file):
        print(f"❌ Elena's data file not found: {elena_file}")
        return 1

    if not os.path.exists(video_path):
        print(f"❌ Video template not found: {video_path}")
        return 1

    print(f"📁 Processing: {elena_file}")
    print(f"🎬 Video template: {video_path}")
    print(f"📤 Output directory: {output_dir}")

    # Process Elena's video
    result = process_client_data(elena_file, video_path, output_dir)

    if result:
        print(f"\n✅ SUCCESS! Video created: {result}")
    else:
        print(f"\n❌ FAILED to create Elena's video")

    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
