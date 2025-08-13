#!/usr/bin/env python
"""
Fix Simple Blue Video Client Folders Script

This script copies the video generation code from simple_blue_video_optimized.py
to simple_blue_video_client_folders.py to ensure it can run properly.

Run this script once to prepare the client-folder-aware video generation script.
"""

import os
import re
from pathlib import Path


def fix_video_script():
    """
    Copy the necessary video generation code from the original script to the client folder version
    """
    print("Fixing simple_blue_video_client_folders.py...")

    # Base directory
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Source and destination files
    source_file = base_dir / "simple_blue_video_optimized.py"
    dest_file = base_dir / "simple_blue_video_client_folders.py"

    if not source_file.exists():
        print(f"Error: Source file {source_file} does not exist.")
        return

    if not dest_file.exists():
        print(f"Error: Destination file {dest_file} does not exist.")
        return

    # Read source file
    try:
        with open(source_file, 'r') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading source file: {e}")
        return

    # Read destination file
    try:
        with open(dest_file, 'r') as f:
            dest_code = f.read()
    except Exception as e:
        print(f"Error reading destination file: {e}")
        return

    # Extract all the video generation functions from the source file
    # Find functions after the imports and before main()
    function_pattern = r'def\s+([a-zA-Z0-9_]+)\s*\([^)]*\):\s*(?:""".*?""")?\s*(.*?)(?=\ndef\s+|\Z)'
    functions = re.findall(function_pattern, source_code, re.DOTALL)

    # Filter out functions that are already in the destination file
    existing_functions = re.findall(function_pattern, dest_code, re.DOTALL)
    existing_function_names = {name for name, _ in existing_functions}

    # Functions to copy (excluding functions already in the destination)
    functions_to_copy = [
        (name, code) for name, code in functions if name not in existing_function_names and name != "main"]

    # Find the placeholder comment in the destination file
    placeholder = "# Define core video generation functions (these would come from simple_blue_video_optimized.py)"
    placeholder_with_comment = f"{placeholder}\n# For brevity, I'll include just placeholders - in the actual implementation, you'd copy\n# all the video generation functions from simple_blue_video_optimized.py here"

    if placeholder_with_comment not in dest_code:
        print(f"Error: Could not find placeholder in destination file.")
        return

    # Replace the placeholder with the actual functions
    new_functions_code = f"{placeholder}\n"
    for name, code in functions_to_copy:
        new_functions_code += f"\ndef {name}{code}\n"

    updated_dest_code = dest_code.replace(
        placeholder_with_comment, new_functions_code)

    # Also update the generate_blue_video function to use the actual video generation code
    generate_video_pattern = r'def\s+generate_blue_video\s*\([^)]*\):\s*(?:""".*?""")?\s*(.*?)(?=\ndef\s+|\Z)'
    generate_video_match = re.search(
        generate_video_pattern, dest_code, re.DOTALL)

    if generate_video_match:
        original_implementation = generate_video_match.group(1)
        # Find the placeholder comment in the function
        placeholder_in_function = "# Here you would include all the video generation code from simple_blue_video_optimized.py"

        if placeholder_in_function in original_implementation:
            # Find the corresponding function in the source code
            source_generate_video = None
            for func_name, func_code in functions:
                if func_name == "generate_blue_background_video" or func_name == "generate_video":
                    source_generate_video = func_code
                    break

            if source_generate_video:
                # Extract the main video generation logic
                video_logic = source_generate_video.strip()

                # Adapt the code for client folders
                adapted_logic = video_logic.replace("return output_path", """
    # Copy the video to the client folder if needed
    if output_path != str(default_video_path):
        try:
            shutil.copy2(output_path, str(default_video_path))
            logger.info(f"Copied video to client folder: {default_video_path}")
        except Exception as e:
            logger.error(f"Error copying video to client folder: {e}")
    
    return output_path""")

                # Replace the placeholder in the function with the actual code
                new_implementation = original_implementation.replace(
                    f"{placeholder_in_function}\n    # ...",
                    adapted_logic
                )

                updated_dest_code = updated_dest_code.replace(
                    original_implementation, new_implementation)

    # Write the updated code back to the destination file
    try:
        with open(dest_file, 'w') as f:
            f.write(updated_dest_code)
        print(
            f"Successfully updated {dest_file} with video generation functions.")
    except Exception as e:
        print(f"Error writing to destination file: {e}")
        return


if __name__ == "__main__":
    fix_video_script()
