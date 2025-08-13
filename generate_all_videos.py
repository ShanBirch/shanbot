#!/usr/bin/env python3
"""
Generate weekly videos for all clients with goal completion rates and progressive overload targets
"""

import os
import sys
import subprocess
import glob
from datetime import datetime


def main():
    print("🎬 GENERATING CLIENT VIDEOS WITH GOAL COMPLETION & PROGRESSIVE OVERLOAD")
    print("=" * 80)

    # Check if required files exist
    video_script = "simple_blue_video.py"
    if not os.path.exists(video_script):
        print(f"❌ Error: {video_script} not found!")
        return 1

    # Check for client data files
    checkin_dir = r"output\checkin_reviews"
    if not os.path.exists(checkin_dir):
        print(f"❌ Error: {checkin_dir} not found!")
        return 1

    # Find all client data files
    client_files = glob.glob(os.path.join(
        checkin_dir, "*_fitness_wrapped_data.json"))

    if not client_files:
        print("❌ No client data files found!")
        return 1

    print(f"📋 Found {len(client_files)} client data files")
    print()

    # Extract client names for summary
    client_names = []
    for file_path in client_files:
        filename = os.path.basename(file_path)
        client_name = filename.split('_fitness_wrapped_data.json')[
            0].replace('_', ' ')
        client_names.append(client_name)

    print("👥 Clients to process:")
    for i, name in enumerate(client_names, 1):
        print(f"  {i:2d}. {name}")
    print()

    # Check video template
    video_template = "blue2.mp4"
    if not os.path.exists(video_template):
        video_template = "blue.mp4"
        if not os.path.exists(video_template):
            print("❌ Error: No video template found (blue2.mp4 or blue.mp4)")
            return 1

    print(f"🎥 Using video template: {video_template}")
    print()

    # Run the video generation
    print("🚀 Starting video generation with progressive overload features...")
    print("   ✅ Goal completion rate slides")
    print("   ✅ Next week progression targets")
    print("   ✅ Exercise performance analysis")
    print("   ✅ Motivational messaging")
    print()

    try:
        # Run the simple_blue_video.py script
        cmd = [sys.executable, video_script]
        print(f"Running: {' '.join(cmd)}")
        print("-" * 60)

        result = subprocess.run(cmd, capture_output=False, text=True)

        print("-" * 60)
        print(
            f"Video generation completed with exit code: {result.returncode}")

        if result.returncode == 0:
            print("✅ SUCCESS! Videos generated for all clients")

            # Check output directory
            output_dir = "output"
            video_files = glob.glob(os.path.join(
                output_dir, "*week_summary*.mp4"))

            if video_files:
                print(f"\n📹 Generated {len(video_files)} video files:")
                for video_file in sorted(video_files):
                    filename = os.path.basename(video_file)
                    file_size = os.path.getsize(video_file) / (1024*1024)  # MB
                    print(f"   📺 {filename} ({file_size:.1f} MB)")
            else:
                print("\n⚠️  No video files found in output directory")

        else:
            print("❌ Video generation failed!")

    except Exception as e:
        print(f"❌ Error running video generation: {e}")
        return 1

    print(f"\n🎯 WHAT EACH CLIENT WILL SEE:")
    print("   • Last Week's Goal Completion Rate (%)")
    print("   • Exercises where they exceeded targets")
    print("   • Next week's progression recommendations")
    print("   • Personalized motivation messages")
    print("   • Specific weight/rep targets for each exercise")

    print(f"\n📱 Next Steps:")
    print("   1. Review generated videos in /output directory")
    print("   2. Upload videos to client platforms")
    print("   3. Update workout programs with new targets")
    print("   4. Clients will see goals in their workout apps")

    return 0


if __name__ == "__main__":
    sys.exit(main())
