import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from moviepy.video.io.ImageClip import ImageClip
from moviepy.video.compositing.transitions import crossfadein

class FitnessWrappedGenerator:
    def __init__(self, client_data, base_dir="."):
        """Initialize the generator with client data and directories"""
        self.client_data = client_data
        self.base_dir = Path(base_dir)
        
        # Define directories
        self.template_dir = self.base_dir / "templates"
        self.font_dir = self.base_dir / "fonts"
        self.output_dir = self.base_dir / "output"
        self.music_dir = self.base_dir / "music"
        
        # Create directories if they don't exist
        self.ensure_directories()
        
        # Default font settings
        self.default_font_path = self.font_dir / "NunitoSans-Bold.ttf"
        
        # Set default transition duration
        self.transition_duration = 0.5
        
        # Set output path
        client_name = self.client_data.get("name", "client").replace(" ", "_")
        self.output_path = self.output_dir / f"{client_name}_fitness_wrapped.mp4"
        
        # Music path
        self.music_path = self.music_dir / "background_music.mp3"
        
        # Find available templates and fonts
        self.available_templates = self.find_available_templates()
        self.available_fonts = self.find_available_fonts()
        
        # Default slide duration in seconds
        self.slide_duration = 3.0

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.template_dir, self.font_dir, self.output_dir, self.music_dir]:
            if not directory.exists():
                directory.mkdir(parents=True)
                print(f"Created '{directory}' directory.")

    def find_available_templates(self):
        """Find template images in the templates directory"""
        available = {}
        
        if not self.template_dir.exists():
            print(f"Warning: Template directory {self.template_dir} doesn't exist.")
            return available
        
        # Look for image files with appropriate naming conventions
        for file_path in self.template_dir.glob("*.png"):
            key = file_path.stem  # Use filename without extension as key
            available[key] = file_path
            
        # Also check for jpg files if no png found
        if not available:
            for file_path in self.template_dir.glob("*.jpg"):
                key = file_path.stem
                available[key] = file_path
                
        return available

    def find_available_fonts(self):
        """Find available fonts in the fonts directory"""
        fonts = {}
        
        if not self.font_dir.exists():
            print(f"Warning: Font directory {self.font_dir} doesn't exist.")
            return fonts
        
        for file_path in self.font_dir.glob("*.ttf"):
            name = file_path.stem
            fonts[name] = file_path
            
        # If no fonts available, download a default font
        if not fonts:
            print("No fonts found. Using system font.")
            # Use a system font as fallback
            try:
                # Try to find a system font location
                system_fonts = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                    "/Library/Fonts/Arial.ttf",  # macOS
                    "C:\\Windows\\Fonts\\arial.ttf"  # Windows
                ]
                
                for font_path in system_fonts:
                    if os.path.exists(font_path):
                        fonts["default"] = font_path
                        break
            except Exception as e:
                print(f"Error finding system font: {e}")
                
        return fonts

    def add_text_to_image(self, image_path, text_elements):
        """
        Add text elements to an image
        
        Each text_element is a dictionary with:
        - text: The text to add
        - position: (x, y) tuple or 'center'
        - font_size: Size of the font
        - font_name: Name of the font file (optional)
        - color: RGB tuple (default: white)
        - align: Text alignment ('left', 'center', 'right')
        """
        try:
            # Open the image
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # Process each text element
            for element in text_elements:
                text = str(element.get("text", ""))
                position = element.get("position", "center")
                font_size = element.get("font_size", 60)
                font_name = element.get("font_name", "default")
                color = element.get("color", (255, 255, 255))
                align = element.get("align", "center")
                
                # Find the font
                font_path = None
                if font_name in self.available_fonts:
                    font_path = self.available_fonts[font_name]
                elif "default" in self.available_fonts:
                    font_path = self.available_fonts["default"]
                
                if not font_path and self.default_font_path.exists():
                    font_path = self.default_font_path
                
                # If still no font, try to use a PIL default
                if not font_path:
                    print("Warning: No font found. Text may not appear correctly.")
                    try:
                        font = ImageFont.load_default()
                    except:
                        print("Error: Cannot load default font. Skipping text overlay.")
                        continue
                else:
                    try:
                        font = ImageFont.truetype(str(font_path), font_size)
                    except Exception as e:
                        print(f"Error loading font: {e}")
                        font = ImageFont.load_default()
                
                # Calculate text size and position
                text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else font.getsize(text)
                
                # Handle position
                if position == "center":
                    position = ((img.width - text_width) // 2, (img.height - text_height) // 2)
                elif position == "top_center":
                    position = ((img.width - text_width) // 2, img.height // 4)
                elif position == "bottom_center":
                    position = ((img.width - text_width) // 2, img.height * 3 // 4)
                
                # Draw the text
                try:
                    # Use textbbox for newer PIL versions
                    if hasattr(draw, 'textbbox'):
                        bbox = draw.textbbox(position, text, font=font)
                        draw.text(position, text, font=font, fill=color, align=align)
                    else:
                        # Fallback for older PIL versions
                        draw.text(position, text, font=font, fill=color, align=align)
                except Exception as e:
                    print(f"Error drawing text: {e}")
            
            # Save to a temporary file
            temp_file = f"temp_{os.path.basename(image_path)}"
            img.save(temp_file)
            return temp_file
            
        except Exception as e:
            print(f"Error adding text to image {image_path}: {e}")
            return image_path

    def create_slide(self, template_key, text_elements=None, duration=None):
        """Create a slide from a template with optional text overlays"""
        if template_key not in self.available_templates:
            print(f"Template '{template_key}' not found. Skipping this slide.")
            return None
            
        image_path = self.available_templates[template_key]
        slide_duration = duration or self.slide_duration
        
        # If text elements provided, add them to the image
        if text_elements:
            try:
                temp_image_path = self.add_text_to_image(image_path, text_elements)
                clip = ImageClip(temp_image_path).set_duration(slide_duration)
                
                # Schedule the temporary file for removal after creating the clip
                if temp_image_path != image_path:
                    os.remove(temp_image_path)
            except Exception as e:
                print(f"Error creating slide with text: {e}")
                clip = ImageClip(str(image_path)).set_duration(slide_duration)
        else:
            # Create a slide without text overlays
            clip = ImageClip(str(image_path)).set_duration(slide_duration)
            
        return clip

    def build_video(self):
        """Build the fitness wrapped video with all slides"""
        print("Building fitness wrapped video...")
        slides = []
        
        # Create intro slide
        if "intro" in self.available_templates:
            intro_text = [
                {
                    "text": f"{self.client_data['name']}'s Week at {self.client_data['business_name']}",
                    "position": "center",
                    "font_size": 80
                },
                {
                    "text": self.client_data['date_range'],
                    "position": (None, 550),  # Centered horizontally, fixed vertical
                    "font_size": 50,
                    "position": "bottom_center"
                }
            ]
            intro_slide = self.create_slide("intro", intro_text, duration=4.0)
            if intro_slide:
                slides.append(intro_slide)
        
        # Create progress slide
        if "progress" in self.available_templates:
            progress_text = [
                {
                    "text": "Let's Check Your Progress",
                    "position": "top_center",
                    "font_size": 70
                }
            ]
            progress_slide = self.create_slide("progress", progress_text)
            if progress_slide:
                slides.append(progress_slide)
                
        # Create weight goal slide
        if "weight_goal" in self.available_templates:
            weight_diff = self.client_data['current_weight'] - self.client_data['start_weight']
            weight_text = [
                {
                    "text": "Let's Check Your Body Weight Goal!",
                    "position": "top_center",
                    "font_size": 60
                },
                {
                    "text": f"Started: {self.client_data['start_weight']} kg",
                    "position": (None, 300),
                    "font_size": 50,
                    "position": (400, 300)
                },
                {
                    "text": f"Current: {self.client_data['current_weight']} kg ({weight_diff:+.1f} kg)",
                    "position": (None, 400),
                    "font_size": 50,
                    "position": (400, 400)
                },
                {
                    "text": f"Goal: {self.client_data['weight_goal']} kg",
                    "position": (None, 500),
                    "font_size": 50,
                    "position": (400, 500)
                }
            ]
            weight_slide = self.create_slide("weight_goal", weight_text)
            if weight_slide:
                slides.append(weight_slide)
                
        # Create current weight message slide
        if "current_weight" in self.available_templates and "current_weight_message" in self.client_data:
            weight_msg_text = [
                {
                    "text": self.client_data['current_weight_message'],
                    "position": "center",
                    "font_size": 50
                }
            ]
            weight_msg_slide = self.create_slide("current_weight", weight_msg_text)
            if weight_msg_slide:
                slides.append(weight_msg_slide)
                
        # Create workout count slide
        if "workout_count" in self.available_templates:
            workout_count_text = [
                {
                    "text": f"You Trained {self.client_data['workouts_this_week']} Times",
                    "position": "center",
                    "font_size": 70
                }
            ]
            workout_count_slide = self.create_slide("workout_count", workout_count_text)
            if workout_count_slide:
                slides.append(workout_count_slide)
                
        # Create workout types slide
        if "workout_total" in self.available_templates:
            workout_types = ", ".join(self.client_data['workout_types'])
            workout_total_text = [
                {
                    "text": "In total you powered through",
                    "position": "top_center",
                    "font_size": 60
                },
                {
                    "text": workout_types,
                    "position": "center",
                    "font_size": 50
                }
            ]
            workout_total_slide = self.create_slide("workout_total", workout_total_text)
            if workout_total_slide:
                slides.append(workout_total_slide)
                
        # Create workout stats slide
        if "workout_stats" in self.available_templates:
            workout_stats_text = [
                {
                    "text": f"{self.client_data['total_reps']} reps",
                    "position": (400, 300),
                    "font_size": 60
                },
                {
                    "text": f"{self.client_data['total_sets']} sets",
                    "position": (400, 400),
                    "font_size": 60
                },
                {
                    "text": f"{self.client_data['total_weight_lifted']} kgs",
                    "position": (400, 500),
                    "font_size": 60
                }
            ]
            workout_stats_slide = self.create_slide("workout_stats", workout_stats_text)
            if workout_stats_slide:
                slides.append(workout_stats_slide)
                
        # Create workload increase slide
        if "workload" in self.available_templates:
            workload_text = [
                {
                    "text": f"{self.client_data['workload_increase']}%",
                    "position": "center",
                    "font_size": 90
                },
                {
                    "text": "Total Workload Increase",
                    "position": "bottom_center",
                    "font_size": 50
                }
            ]
            workload_slide = self.create_slide("workload", workload_text)
            if workload_slide:
                slides.append(workload_slide)
                
        # Create nutrition slide
        if "nutrition" in self.available_templates:
            nutrition_text = [
                {
                    "text": "Your Nutrition Was On Point!!",
                    "position": "center",
                    "font_size": 70
                }
            ]
            nutrition_slide = self.create_slide("nutrition", nutrition_text)
            if nutrition_slide:
                slides.append(nutrition_slide)
                
        # Create calories slide
        if "calories" in self.available_templates:
            calories_text = [
                {
                    "text": f"{self.client_data['calories_consumed']} cals",
                    "position": "center",
                    "font_size": 80
                },
                {
                    "text": "consistently",
                    "position": "bottom_center",
                    "font_size": 50
                }
            ]
            calories_slide = self.create_slide("calories", calories_text)
            if calories_slide:
                slides.append(calories_slide)
                
        # Create steps slide
        if "steps" in self.available_templates:
            steps_text = [
                {
                    "text": "Step Count",
                    "position": "top_center",
                    "font_size": 60
                },
                {
                    "text": f"{self.client_data['step_count']}",
                    "position": "center",
                    "font_size": 80
                },
                {
                    "text": "Every Day",
                    "position": "bottom_center",
                    "font_size": 50
                }
            ]
            steps_slide = self.create_slide("steps", steps_text)
            if steps_slide:
                slides.append(steps_slide)
                
        # Create sleep slide
        if "sleep" in self.available_templates:
            sleep_text = [
                {
                    "text": "Sleep Check",
                    "position": "top_center",
                    "font_size": 60
                },
                {
                    "text": self.client_data['sleep_hours'],
                    "position": "center",
                    "font_size": 70
                }
            ]
            sleep_slide = self.create_slide("sleep", sleep_text)
            if sleep_slide:
                slides.append(sleep_slide)
                
        # Create conclusion slide
        if "conclusion" in self.available_templates:
            conclusion_text = [
                {
                    "text": self.client_data['personalized_message'],
                    "position": "center",
                    "font_size": 50
                }
            ]
            conclusion_slide = self.create_slide("conclusion", conclusion_text, duration=5.0)
            if conclusion_slide:
                slides.append(conclusion_slide)
                
        # Create motivational slide
        if "motivational" in self.available_templates:
            motivational_text = [
                {
                    "text": "Keep Moving!",
                    "position": "center",
                    "font_size": 90
                }
            ]
            motivational_slide = self.create_slide("motivational", motivational_text, duration=4.0)
            if motivational_slide:
                slides.append(motivational_slide)
        
        if not slides:
            print("Error: No valid slides could be created.")
            return False
            
        # Add transitions between slides
        print("Adding transitions between slides...")
        clips_with_transitions = [slides[0]]
        
        for i in range(1, len(slides)):
            slides[i] = slides[i].set_start(clips_with_transitions[-1].end - self.transition_duration)
            slides[i] = slides[i].crossfadein(self.transition_duration)
            clips_with_transitions.append(slides[i])
            
        # Concatenate all slides with transitions
        print("Combining slides...")
        final_clip = CompositeVideoClip(clips_with_transitions)
        
        # Add background music if available
        if self.music_path.exists():
            print("Adding background music...")
            try:
                audio = AudioFileClip(str(self.music_path))
                
                # Loop or trim audio as needed
                if audio.duration < final_clip.duration:
                    audio = afx.audio_loop(audio, duration=final_clip.duration)
                else:
                    audio = audio.subclip(0, final_clip.duration)
                
                # Set volume
                audio = audio.volumex(0.5)
                
                # Add audio to the video
                final_clip = final_clip.set_audio(audio)
            except Exception as e:
                print(f"Error adding music: {e}")
                print("Continuing without background music.")
        else:
            print("No background music found. Video will be silent.")
        
        # Write the final video file
        print(f"Writing video to {self.output_path}...")
        final_clip.write_videofile(
            str(self.output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac" if self.music_path.exists() else None,
            preset="medium"
        )
        
        print(f"Video successfully created and saved to {self.output_path}")
        return True

    def print_template_guide(self):
        """Print a guide for naming templates"""
        print("\nTemplate Naming Guide:")
        print("-" * 50)
        print("The script looks for these template names:")
        
        template_descriptions = {
            "intro": "Introduction slide for client name and date range",
            "progress": "Progress check intro slide",
            "weight_goal": "Weight progress tracking slide",
            "current_weight": "Current weight status message slide",
            "workout_count": "Number of workouts completed slide",
            "workout_total": "Workout types summary slide",
            "workout_stats": "Detailed workout statistics slide (reps, sets, weight)",
            "workload": "Workload increase percentage slide",
            "exercise_level": "Exercise progression slide",
            "strength_gains": "Strength improvements slide",
            "nutrition": "Nutrition header slide",
            "calories": "Calorie consumption slide",
            "steps": "Step count slide",
            "sleep": "Sleep tracking slide",
            "progress_photos": "Progress photos slide",
            "conclusion": "Final slide with personalized message",
            "motivational": "Motivational ending slide"
        }
        
        for key, description in template_descriptions.items():
            available = "✓" if key in self.available_templates else "✗"
            print(f"{available} {key}.png - {description}")
            
        print("\nAvailable templates:")
        for i, (key, path) in enumerate(self.available_templates.items(), 1):
            print(f"{i}. {key} - {path}")

def load_client_data(json_path=None):
    """Load client data from a JSON file or use default data"""
    default_data = {
        "name": "Ben",                      
        "business_name": "Coco's",          
        "date_range": "3 March - 9th March",
        "start_weight": 87,                 
        "current_weight": 94,               
        "weight_goal": 90,                  
        "current_weight_message": "Weight's trending down nicely, which is awesome! Keep doing what you're doing!",
        "workouts_this_week": 7,            
        "workout_types": ["Back", "Chest", "Lower", "Arms"],  
        "total_reps": 650,                  
        "total_sets": 78,                   
        "total_weight_lifted": 1069,        
        "workload_increase": 117.19,        
        "calories_consumed": 2700,          
        "step_count": 10000,                
        "sleep_hours": "8-9 Hours Most Nights",
        "personalized_message": "Another fantastic week! Your workload has increased by over 25%\nYour nutrition is on point, and your weight is dropping. What more could you ask for! Keep pushing, and you'll reach that goal weight in no time!"
    }
    
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                client_data = json.load(f)
                print(f"Loaded client data from {json_path}")
                return client_data
        except Exception as e:
            print(f"Error loading client data from {json_path}: {e}")
            print("Using default client data instead.")
    
    return default_data

def download_font():
    """Download a free font if none are available"""
    try:
        import requests
        from io import BytesIO
        
        # Create fonts directory if it doesn't exist
        fonts_dir = Path("fonts")
        if not fonts_dir.exists():
            fonts_dir.mkdir(parents=True)
            
        # URL for a free font (Nunito Sans from Google Fonts)
        font_url = "https://github.com/google/fonts/raw/main/ofl/nunitosans/NunitoSans%5BYOPQ%2Cwght%5D.ttf"
        font_path = fonts_dir / "NunitoSans-Bold.ttf"
        
        if not font_path.exists():
            print("Downloading a free font...")
            response = requests.get(font_url)
            
            if response.status_code == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                print(f"Font downloaded to {font_path}")
            else:
                print(f"Failed to download font: {response.status_code}")
        else:
            print(f"Font already exists at {font_path}")
            
    except Exception as e:
        print(f"Error downloading font: {e}")
        print("Continuing without downloading font.")

def list_directory_contents():
    """List contents of key directories"""
    directories = ["templates", "fonts", "music", "output"]
    
    for directory in directories:
        dir_path = Path(directory)
        print(f"\nContents of '{directory}' directory:")
        
        if not dir_path.exists():
            print(f"  Directory doesn't exist.")
            continue
            
        files = list(dir_path.glob("*"))
        
        if not files:
            print("  No files found.")
        else:
            for i, file in enumerate(files, 1):
                print(f"  {i}. {file.name}")

def save_sample_client_data():
    """Save a sample client data JSON file"""
    sample_data = {
        "name": "John",
        "business_name": "Fitness First",
        "date_range": "10 March - 16 March",
        "start_weight": 95,
        "current_weight": 92,
        "weight_goal": 85,
        "current_weight_message": "Great progress so far! You're on track to reach your goal weight.",
        "workouts_this_week": 5,
        "workout_types": ["Upper Body", "Lower Body", "HIIT", "Cardio"],
        "total_reps": 720,
        "total_sets": 86,
        "total_weight_lifted": 1125,
        "workload_increase": 105.5,
        "calories_consumed": 2500,
        "step_count": 12000,
        "sleep_hours": "7-8 Hours Most Nights",
        "personalized_message": "Awesome week, John! Your consistency is paying off. The increase in strength and endurance is impressive. Let's keep the momentum going next week!"
    }
    
    try:
        with open("sample_client_data.json", 'w') as f:
            json.dump(sample_data, f, indent=4)
        print("Sample client data saved to 'sample_client_data.json'")
    except Exception as e:
        print(f"Error saving sample client data: {e}")

def main():
    """Main function to run the fitness wrapped generator"""
    print("=" * 50)
    print("Fitness Wrapped Video Generator")
    print("=" * 50)
    
    # List directory contents
    list_directory_contents()
    
    # Try to download a font if needed
    try:
        download_font()
    except:
        print("Font download failed. Will use system fonts if available.")
    
    # Create a sample client data file for reference
    save_sample_client_data()
    
    # Ask for client data file
    print("\nOptions for client data:")
    print("1. Use default client data")
    print("2. Use sample client data (sample_client_data.json)")
    print("3. Specify a custom JSON file")
    
    data_choice = input("Choose client data option (1-3): ").strip()
    
    client_data_file = None
    if data_choice == "2":
        client_data_file = "sample_client_data.json"
    elif data_choice == "3":
        client_data_file = input("Enter path to client data JSON file: ").strip()
    
    # Load client data
    client_data = load_client_data(client_data_file)
    
    # Create the generator
    generator = FitnessWrappedGenerator(client_data)
    
    # Print template guide
    generator.print_template_guide()
    
    # Ask if user wants to continue
    print("\nThis script will create a video from the available templates with client data overlays.")
    continue_prompt = input("Continue? (y/n): ")
    
    if continue_prompt.lower() == 'y':
        generator.build_video()
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()