#!/usr/bin/env python

import json
import os
import random
from pathlib import Path
import importlib.util


def main():
    print("Reverting to previous video generation approach...")

    # Load the client data from the JSON file
    json_path = "Shannon_Birch_fitness_wrapped_data.json"
    with open(json_path, 'r') as f:
        client_data = json.load(f)

    print(
        f"Loaded client data for: {client_data.get('name', 'unknown client')}")

    # Load the fwv module
    try:
        spec = importlib.util.spec_from_file_location("fwv", "fwv.py")
        fwv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fwv)
        print("Successfully loaded fwv.py module")
    except Exception as e:
        print(f"Error loading fwv.py: {e}")
        return

    # Add the select_random_music method to FitnessWrappedGenerator
    def select_random_music(self):
        """Select a random music file from the music directory"""
        # Get all mp3 files in the music directory
        mp3_files = list(self.music_dir.glob("*.mp3"))

        # If no mp3 files found, return the default music path
        if not mp3_files:
            print("No music files found. Using default.")
            return self.music_path

        # Select a random music file
        random_music = random.choice(mp3_files)
        print(f"Selected random music track: {random_music.name}")
        return random_music

    # Monkey patch the class with our new method
    fwv.FitnessWrappedGenerator.select_random_music = select_random_music

    # Patch the build_video method to use our random music selector
    original_build_video = fwv.FitnessWrappedGenerator.build_video

    def patched_build_video(self):
        """Patched build_video method to use random music"""
        # Select random music file
        self.music_path = self.select_random_music()
        # Call the original method
        return original_build_video(self)

    # Apply the patch
    fwv.FitnessWrappedGenerator.build_video = patched_build_video

    # Create the generator instance
    generator = fwv.FitnessWrappedGenerator(client_data)

    # Generate the video
    print("Building fitness wrapped video...")
    result = generator.build_video()

    if result:
        print(f"Success! Video created and saved to: {generator.output_path}")
    else:
        print("Error: Failed to create video.")


if __name__ == "__main__":
    main()
