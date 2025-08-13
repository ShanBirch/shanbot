#!/usr/bin/env python
import sys
import os
import json
import argparse
from pathlib import Path
from fwv import FitnessWrappedGenerator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    try:
        # Load the client data
        json_file = 'Shannon_Birch_fitness_wrapped_data.json'
        logging.info(f"Loading data from {json_file}...")

        with open(json_file, 'r') as f:
            client_data = json.load(f)

        # Create the generator
        logging.info("Creating video generator...")
        generator = FitnessWrappedGenerator(client_data)

        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)

        # Build the video
        logging.info("Generating fitness wrapped video...")
        success = generator.build_video()

        if success:
            output_path = os.path.join(
                'output', 'Shannon_Birch_fitness_wrapped.mp4')
            logging.info(f"Video successfully generated at: {output_path}")

            # Verify the file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logging.info(
                    f"Video file verified: {os.path.getsize(output_path)} bytes")
            else:
                logging.error(
                    f"Video file is missing or too small: {output_path}")
        else:
            logging.error("Failed to generate video")

    except Exception as e:
        logging.exception("Error during video generation:")
        raise


if __name__ == "__main__":
    sys.exit(main())
