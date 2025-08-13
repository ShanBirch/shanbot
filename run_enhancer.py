"""
Run Social Media Enhancer
A launcher that keeps the console window open while processing videos
"""

import sys
import importlib
import time
import traceback


def main():
    print("Starting Social Media Video Enhancer...")

    # Import the social media enhancer module
    try:
        # Import the social media enhancer module
        import social_media_enhancer_fixed

        # Run the main function
        social_media_enhancer_fixed.main()

        # Keep the console window open while processing (if UI was closed properly)
        if social_media_enhancer_fixed.selected_options["video_path"]:
            print("\nWaiting for video processing to complete...")

            # Wait indefinitely - the program will exit when the video processing is done
            # The UI has already created a non-daemon thread for processing
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nProcess interrupted by user. Your video may not be complete.")
                print("Press Enter to exit...")
                input()
                sys.exit(1)
        else:
            print("\nExiting without video processing.")

    except Exception as e:
        print(f"Error running Social Media Video Enhancer: {e}")
        traceback.print_exc()

    # Add a pause at the end so user can see any error messages
    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
