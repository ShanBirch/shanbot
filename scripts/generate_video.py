import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Generate videos from existing JSON files without requiring ImageMagick"""
    # List of client JSON files to process
    client_files = ["Shannon_Birch_fitness_wrapped_data.json"]
    
    # Add more client files here if needed
    # client_files.append("Another_Client_fitness_wrapped_data.json")
    
    successful_videos = []
    
    # Process each client
    for json_file in client_files:
        if os.path.exists(json_file):
            try:
                # Extract client name from filename
                client_name = json_file.split("_fitness_wrapped_data.json")[0].replace("_", " ")
                logging.info(f"Processing client: {client_name}")
                
                # Load client data
                with open(json_file, 'r') as f:
                    client_data = json.load(f)
                
                # Create generator and build video
                logging.info(f"Creating video for {client_name}...")
                
                # Import the modified FitnessWrappedGenerator that doesn't need ImageMagick
                from fixed_fwv_no_imagemagick import FitnessWrappedGenerator
                generator = FitnessWrappedGenerator(client_data)
                
                success = generator.build_video()
                
                if success:
                    logging.info(f"Successfully created video for {client_name}")
                    successful_videos.append((client_name, generator.output_path))
                else:
                    logging.error(f"Failed to create video for {client_name}")
            
            except Exception as e:
                logging.exception(f"Error processing {json_file}: {e}")
        else:
            logging.error(f"JSON file not found: {json_file}")
    
    # Print summary
    logging.info("\n" + "="*70)
    logging.info(f"{'VIDEO GENERATION SUMMARY':^70}")
    logging.info("="*70)
    
    if successful_videos:
        logging.info("Successfully generated videos:")
        for i, (client_name, video_path) in enumerate(successful_videos, 1):
            logging.info(f"  {i}. {client_name}: {video_path}")
    else:
        logging.error("No videos were successfully generated.")
    
    logging.info("="*70)

if __name__ == "__main__":
    main()