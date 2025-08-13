#!/usr/bin/env python

import json
import os
from pathlib import Path
import importlib.util

def main():
    print("Running video generator with original code plus music selection...")

    # Load the client data from the JSON file
    json_path = "Shannon_Birch_fitness_wrapped_data.json"
    with open(json_path, 'r') as f:
        client_data = json.load(f)

    print(f"Loaded client data for: {client_data.get('name', 'unknown client')}")

    # Load the modified module
    spec = importlib.util.spec_from_file_location("fixed_fwv", "fixed_fwv_with_music.py")
    fixed_fwv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixed_fwv)

    # Create the generator instance
    generator = fixed_fwv.FitnessWrappedGenerator(client_data)

    # Generate the video
    print("Building fitness wrapped video with original approach...")
    result = generator.build_video()

    if result:
        print(f"Success! Video created and saved to: {generator.output_path}")
    else:
        print("Error: Failed to create video.")

if __name__ == "__main__":
    main()
