#!/usr/bin/env python
"""
Script to generate Shannon's recent check-in week video.
This uses the simple_blue_video_client_folders.py module to create the video.
"""
import os
import sys
from pathlib import Path
import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(
            'logs', 'shannon_video_generation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('shannon_video_generator')


def main():
    # Base paths
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Client info
    client_name = 'Shannon_Birch'

    # Data file path (using the most recent data file)
    client_dir = base_dir / 'clients' / client_name
    data_dir = client_dir / 'data'

    # Find the most recent data file
    data_files = list(data_dir.glob(
        f"{client_name}_*_fitness_wrapped_data.json"))
    if not data_files:
        logger.error(f"No data files found for {client_name}")
        return

    # Sort by date in filename (most recent first)
    data_files.sort(reverse=True)
    data_file = data_files[0]

    logger.info(f"Using data file: {data_file}")

    # Output file path
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    output_dir = base_dir / 'output'
    output_file = output_dir / \
        f"{client_name}_checkin_video_{current_date}.mp4"

    # Make sure output directory exists
    if not output_dir.exists():
        os.makedirs(output_dir)

    # Import the video generation function
    sys.path.append(str(base_dir))
    try:
        from simple_blue_video_client_folders import process_client_data

        # Generate the video
        logger.info(f"Generating video for {client_name}")
        logger.info(f"Input data: {data_file}")
        logger.info(f"Output file: {output_file}")

        process_client_data(str(data_file), str(output_file), None)

        logger.info(f"Video generation complete! Output file: {output_file}")
        print(f"Video successfully created at: {output_file}")

    except Exception as e:
        logger.error(f"Error generating video: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"Error generating video: {e}")


if __name__ == "__main__":
    main()
