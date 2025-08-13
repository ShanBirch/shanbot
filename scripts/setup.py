import os
import shutil
import sys

def setup_directories():
    """Creates necessary directory structure and moves image files if needed"""
    # Create directories if they don't exist
    directories = ["templates", "fonts", "music", "output"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created '{directory}' directory")
    
    # Source directory containing Canva images
    source_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\shanbot\shanbot\shanbot\canva"
    if not os.path.exists(source_dir):
        print(f"Warning: Source directory '{source_dir}' not found.")
        source_dir = input("Enter the path to your Canva images folder: ")
        if not os.path.exists(source_dir):
            print("Invalid directory. Exiting.")
            sys.exit(1)
    
    # Check if templates directory is empty
    if len(os.listdir("templates")) == 0:
        print("\nThe 'templates' directory is empty.")
        print(f"Would you like to copy images from '{source_dir}' to 'templates'?")
        copy = input("Enter y/n: ")
        
        if copy.lower() == 'y':
            # Get all image files from source directory
            images = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if not images:
                print(f"No image files found in {source_dir}")
                return
            
            print(f"\nFound {len(images)} images in {source_dir}:")
            for i, img in enumerate(images, 1):
                print(f"{i}. {img}")
            
            print("\nCopying files to 'templates' directory...")
            
            for img in images:
                src_path = os.path.join(source_dir, img)
                dest_path = os.path.join("templates", img)
                shutil.copy2(src_path, dest_path)
                print(f"Copied: {img}")
    else:
        print("\nThe 'templates' directory already contains files.")

if __name__ == "__main__":
    setup_directories()
    print("\nDirectory setup complete.")
    print("Next steps:")
    print("1. Make sure your template images have the correct names (see naming guide)")
    print("2. Run the fitness_wrapped_final_updated.py script")