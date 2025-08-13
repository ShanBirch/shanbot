#!/usr/bin/env python
import sys
import os
import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Generate Fitness Wrapped Video from JSON data')
    parser.add_argument('json_file', help='JSON file containing client fitness data')
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"Error: JSON file '{args.json_file}' not found.")
        return 1
    
    try:
        with open(args.json_file, 'r') as f:
            client_data = json.load(f)
        
        print(f"Loaded client data for: {client_data.get('name', 'unknown client')}")
        
        # Make sure FitnessWrappedGenerator.py is in the same directory or in the Python path
        try:
            # First try to import directly (if in the same directory)
            from FitnessWrappedGenerator import FitnessWrappedGenerator
        except ImportError:
            # If not found, try to add the directory to the Python path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            generator_path = os.path.join(script_dir, 'FitnessWrappedGenerator.py')
            
            if os.path.exists(generator_path):
                import sys
                sys.path.append(script_dir)
                from FitnessWrappedGenerator import FitnessWrappedGenerator
            else:
                print("Error: FitnessWrappedGenerator.py not found.")
                return 1
        
        generator = FitnessWrappedGenerator(client_data)
        
        # Print template guide for reference
        generator.print_template_guide()
        
        print("\nBuilding fitness wrapped video...")
        result = generator.build_video()
        
        if result:
            print(f"Success! Video created and saved to: {generator.output_path}")
            return 0
        else:
            print("Error: Failed to create video.")
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())