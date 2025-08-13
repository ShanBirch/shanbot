import os
import shutil
import tkinter as tk
from tkinter import filedialog

def copy_and_rename_templates():
    # Create templates directory if it doesn't exist
    if not os.path.exists("templates"):
        os.makedirs("templates")
        print("Created 'templates' directory.")

    # Source directory (your Canva exports)
    source_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\shanbot\shanbot\shanbot\canva"
    
    # Let user confirm or change the source directory
    print(f"The script will look for images in: {source_dir}")
    change = input("Would you like to change this directory? (y/n): ")
    
    if change.lower() == 'y':
        # Use a file dialog to select the directory
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        source_dir = filedialog.askdirectory(title="Select folder containing your Canva images")
        root.destroy()
    
    if not source_dir or not os.path.exists(source_dir):
        print("Invalid directory. Please run the script again.")
        return
    
    # List all image files in the source directory
    image_files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"No image files found in {source_dir}")
        return
    
    print("\nFound the following image files:")
    for i, file in enumerate(image_files, 1):
        print(f"{i}. {file}")
    
    print("\nPlease match each file to the corresponding template:")
    print("(Enter the number of the file, or 0 to skip)")
    
    # Template names
    templates = [
        "template_intro.png",               # "Your Week At Coco's"
        "template_progress.png",            # "Let's Check your Progress"
        "template_weight_goal.png",         # "Lets Check your Body Weight Goal!"
        "template_current_weight.png",      # "Your now 94 kgs"
        "template_workout_count.png",       # "You Trained 7 Times"
        "template_workout_total.png",       # "In total you powered through"
        "template_workout_stats.png",       # "650 reps, 78 sets, 1069Kgs"
        "template_workload.png",            # "117.19% Total Workload Increase"
        "template_exercise_level.png",      # "You took several exercises to the next level!!"
        "template_strength_gains.png",      # "Bench Press Increase 10%..." etc.
        "template_nutrition.png",           # "Your Nutrition was on point!!"
        "template_calories.png",            # "2700 cals consistently"
        "template_steps.png",               # "Step Count 10k Every Day"
        "template_sleep.png",               # "Sleep Check 8-9 Hours Most Nights"
        "template_photos.png",     # "Progress Photos Updated"
        "template_conclusion.png",          # Final slide with personalized message
        "template_motivational.png"         # "Keep Moving!" with bunny
    ]
    
    template_descriptions = [
        "Your Week At Coco's (intro slide)",
        "Let's Check your Progress (date range slide)",
        "Lets Check your Body Weight Goal! (weight goal slide)",
        "Your now X kgs (current weight slide)",
        "You Trained 7 Times (workout count slide)",
        "In total you powered through (workout total slide)",
        "650 reps, 78 sets, 1069Kgs (workout stats slide)",
        "117.19% Total Workload Increase (workload slide)",
        "You took several exercises to the next level!! (exercise level slide)",
        "Bench Press/Strength gains (strength gains slide)",
        "Your Nutrition was on point!! (nutrition slide)",
        "2700 cals consistently (calories slide)",
        "Step Count 10k Every Day (steps slide)",
        "Sleep Check 8-9 Hours Most Nights (sleep slide)",
        "Progress Photos Updated (photos slide)",
        "Conclusion slide with personalized message",
        "Keep Moving! with bunny (motivational slide)"
    ]
    
    # Keep track of which source files have been used
    used_files = set()
    
    # Process each template
    for template_name, description in zip(templates, template_descriptions):
        print(f"\nFor {description}")
        print(f"Which file corresponds to {template_name}?")
        
        while True:
            try:
                choice = int(input("Enter number (0 to skip): "))
                if choice == 0:
                    print(f"Skipping {template_name}")
                    break
                
                if 1 <= choice <= len(image_files):
                    source_file = image_files[choice - 1]
                    
                    if source_file in used_files:
                        print("This file has already been used. Please select a different file or enter 0 to skip.")
                    else:
                        source_path = os.path.join(source_dir, source_file)
                        dest_path = os.path.join("templates", template_name)
                        
                        shutil.copy2(source_path, dest_path)
                        used_files.add(source_file)
                        print(f"Copied {source_file} to {dest_path}")
                        break
                else:
                    print(f"Please enter a number between 0 and {len(image_files)}")
            except ValueError:
                print("Please enter a valid number")
    
    print("\nTemplate setup complete!")
    print("You can now run the fitness_wrapped_final_updated.py script.")

if __name__ == "__main__":
    copy_and_rename_templates()