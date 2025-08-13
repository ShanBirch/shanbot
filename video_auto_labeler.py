#!/usr/bin/env python

"""
Fitness Video Auto-Labeler
Monitors a directory for new fitness videos, analyzes filenames to identify exercises,
and automatically adds text overlays with technique tips.
"""

import os
import sys
import time
import json
import argparse
import threading
import queue
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import custom modules
from exercise_database import exercise_db
from text_overlay_generator import text_overlay

# Default monitoring directory
DEFAULT_MONITOR_DIR = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\Content Videos"

# Configuration file
CONFIG_FILE = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'data', 'auto_labeler_config.json')

# Default configuration
DEFAULT_CONFIG = {
    "monitor_directory": DEFAULT_MONITOR_DIR,
    "text_style": "minimal",
    "hook_position": "center_focus",
    "tip_position": "bottom_banner",
    "processed_subdirectory": "processed",
    "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".wmv"],
    "auto_process_existing": False
}

# Global video processing queue
video_queue = queue.Queue()


class Config:
    """
    Configuration manager for the auto labeler app.
    """

    def __init__(self):
        """Initialize configuration, loading from file or creating default."""
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from file or create default."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as file:
                    self.config = json.load(file)
                    print(f"Loaded configuration from {CONFIG_FILE}")
            else:
                # Initialize with default configuration
                self.config = DEFAULT_CONFIG
                self.save_config()
                print(f"Created new configuration file at {CONFIG_FILE}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = DEFAULT_CONFIG

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as file:
                json.dump(self.config, file, indent=4)
            print(f"Saved configuration to {CONFIG_FILE}")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def get(self, key, default=None):
        """Get configuration value by key."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value by key and save to file."""
        self.config[key] = value
        self.save_config()


# Create configuration singleton
config = Config()


class VideoHandler(FileSystemEventHandler):
    """
    Watchdog event handler for monitoring new video files.
    """

    def __init__(self, monitor_dir, video_extensions):
        """
        Initialize the video handler.

        Args:
            monitor_dir (str): Directory to monitor
            video_extensions (list): List of video file extensions to process
        """
        self.monitor_dir = monitor_dir
        self.video_extensions = video_extensions
        self.processed_files = set()

        # Load list of already processed files if exists
        self.processed_log_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'processed_videos.json'
        )
        self.load_processed_files()

    def load_processed_files(self):
        """Load the list of already processed files."""
        try:
            if os.path.exists(self.processed_log_path):
                with open(self.processed_log_path, 'r') as file:
                    self.processed_files = set(json.load(file))
                print(
                    f"Loaded {len(self.processed_files)} processed files from log")
        except Exception as e:
            print(f"Error loading processed files log: {e}")

    def save_processed_files(self):
        """Save the list of processed files."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(
                self.processed_log_path), exist_ok=True)

            with open(self.processed_log_path, 'w') as file:
                json.dump(list(self.processed_files), file)
        except Exception as e:
            print(f"Error saving processed files log: {e}")

    def is_video_file(self, path):
        """Check if a file is a video based on extension."""
        return os.path.isfile(path) and any(path.lower().endswith(ext) for ext in self.video_extensions)

    def is_in_processed_folder(self, path):
        """Check if a file is in the processed folder."""
        processed_dir = os.path.join(os.path.dirname(
            path), config.get("processed_subdirectory"))
        return processed_dir in path

    def on_created(self, event):
        """Handle new file creation events."""
        if not event.is_directory and self.is_video_file(event.src_path) and not self.is_in_processed_folder(event.src_path):
            # Allow some time for the file to be fully written
            time.sleep(2)

            if event.src_path not in self.processed_files:
                print(f"New video detected: {event.src_path}")
                # Add to processing queue
                video_queue.put(event.src_path)

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and self.is_video_file(event.src_path) and not self.is_in_processed_folder(event.src_path):
            if event.src_path not in self.processed_files:
                print(f"Video modified: {event.src_path}")
                # Add to processing queue
                video_queue.put(event.src_path)

    def mark_as_processed(self, file_path):
        """Mark a file as processed."""
        self.processed_files.add(file_path)
        self.save_processed_files()


def video_processor_worker():
    """Worker thread for processing videos from the queue."""
    while True:
        try:
            # Get video from queue with 1-second timeout
            video_path = video_queue.get(timeout=1)

            # Process the video
            print(f"Processing video from queue: {video_path}")

            # Get settings from config
            text_style = config.get("text_style", "minimal")
            hook_position = config.get("hook_position", "center_focus")
            tip_position = config.get("tip_position", "bottom_banner")

            # Process the video
            output_path, caption = text_overlay.process_video(
                video_path,
                text_style=text_style,
                hook_position=hook_position,
                tip_position=tip_position
            )

            if output_path:
                # Mark as processed
                video_handler.mark_as_processed(video_path)

                # Save caption to a text file
                if caption:
                    caption_path = os.path.splitext(
                        output_path)[0] + "_caption.txt"
                    with open(caption_path, 'w', encoding='utf-8') as f:
                        f.write(caption)
                    print(f"Caption saved to: {caption_path}")

            # Mark task as done
            video_queue.task_done()

        except queue.Empty:
            # Queue is empty, just continue the loop
            continue
        except Exception as e:
            print(f"Error in video processor worker: {e}")
            # Mark task as done even if it failed
            try:
                video_queue.task_done()
            except:
                pass


def process_existing_videos(directory, video_extensions):
    """
    Process existing videos in the monitoring directory.

    Args:
        directory (str): Directory to scan for videos
        video_extensions (list): List of video file extensions to process
    """
    print(f"Scanning for existing videos in {directory}...")

    try:
        for root, _, files in os.walk(directory):
            # Skip the processed subdirectory
            if config.get("processed_subdirectory") in root:
                continue

            for filename in files:
                filepath = os.path.join(root, filename)

                # Check if it's a video file and not already processed
                if any(filename.lower().endswith(ext) for ext in video_extensions) and filepath not in video_handler.processed_files:
                    print(f"Found existing video: {filepath}")
                    video_queue.put(filepath)
    except Exception as e:
        print(f"Error scanning for existing videos: {e}")


def start_monitoring(args):
    """
    Start monitoring the directory for new videos.

    Args:
        args (Namespace): Command-line arguments
    """
    global video_handler

    # Update configuration based on command-line arguments
    if args.directory:
        config.set("monitor_directory", args.directory)

    if args.style:
        config.set("text_style", args.style)

    if args.hook_position:
        config.set("hook_position", args.hook_position)

    if args.tip_position:
        config.set("tip_position", args.tip_position)

    if args.process_existing is not None:
        config.set("auto_process_existing", args.process_existing)

    # Get monitoring directory and video extensions
    monitor_dir = config.get("monitor_directory")
    video_extensions = config.get("video_extensions")

    # Ensure monitoring directory exists
    if not os.path.exists(monitor_dir):
        try:
            os.makedirs(monitor_dir, exist_ok=True)
            print(f"Created monitoring directory: {monitor_dir}")
        except Exception as e:
            print(f"Error creating monitoring directory: {e}")
            sys.exit(1)

    # Initialize video handler
    video_handler = VideoHandler(monitor_dir, video_extensions)

    # Start video processor worker thread
    processor_thread = threading.Thread(
        target=video_processor_worker, daemon=True)
    processor_thread.start()

    # Process existing videos if enabled
    if config.get("auto_process_existing") or args.process_now:
        process_existing_videos(monitor_dir, video_extensions)

    # Start directory observer
    observer = Observer()
    observer.schedule(video_handler, monitor_dir, recursive=True)
    observer.start()

    print(f"Monitoring directory: {monitor_dir}")
    print("Waiting for new videos...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        observer.stop()

    observer.join()


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Fitness Video Auto-Labeler')

    parser.add_argument('--directory', '-d', type=str,
                        help='Directory to monitor for new videos')

    parser.add_argument('--style', '-s', type=str, choices=['minimal', 'bold_statement', 'fitness_pro', 'instagram_classic'],
                        help='Text style preset to use')

    parser.add_argument('--hook-position', type=str, choices=list(text_overlay.TEXT_POSITIONS.keys()),
                        help='Position for hook text')

    parser.add_argument('--tip-position', type=str, choices=list(text_overlay.TEXT_POSITIONS.keys()),
                        help='Position for technique tips')

    parser.add_argument('--process-existing', type=bool,
                        help='Whether to process existing videos in the directory')

    parser.add_argument('--process-now', action='store_true',
                        help='Process existing videos once without changing the configuration')

    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()

    # Start monitoring
    start_monitoring(args)
