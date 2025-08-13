#!/usr/bin/env python
import subprocess
import os
import sys


def main():
    print("Running fitness check-in for Shannon Birch...")

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Run the video generation script
    video_script = os.path.join(script_dir, "simple_video.py")
    client_name = "Shannon_Birch"

    if len(sys.argv) > 1:
        client_name = sys.argv[1]

    cmd = [sys.executable, video_script, "--client", client_name]
    print(f"Executing: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print("Video generation completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error: Video generation failed with exit code {e.returncode}")
    except Exception as e:
        print(f"Error: {str(e)}")

    print("Done!")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
