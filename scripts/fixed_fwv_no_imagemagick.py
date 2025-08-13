import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
import logging
import random
from datetime import datetime, timedelta
import numpy as np

# After imports, before class definitions
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class FitnessWrappedGenerator:
    def __init__(self, client_data, base_dir="."):
        """Initialize the generator with client data and directories"""
        # Prepare and validate input data
        self.client_data = self.prepare_data(client_data)
        self.base_dir = Path(base_dir)

        # Define directories
        self.template_dir = self.base_dir / "templates"
        self.font_dir = self.base_dir / "fonts"
        self.output_dir = self.base_dir / "output"
        self.music_dir = self.base_dir / "music"

        # Set background video path - MODIFIED to use the specific path
        self.background_video_path = Path(r"C:\Users\Shannon\OneDrive\Desktop\shanbot\shanbot\shanbot\shanbot\blue2.mp4")
        if not self.background_video_path.exists():
            print(
                f"Warning: Background video not found at {self.background_video_path}")
            self.background_video_path = None

        # Create directories if they don't exist
        self.ensure_directories()

        # Default font settings
        self.default_font_path = self.font_dir / "NunitoSans-Bold.ttf"

        # Set default transition duration
        self.transition_duration = 0.5

        # Set output path
        client_name = self.client_data.get("name", "client").replace(" ", "_")
        self.output_path = self.output_dir / \
            f"{client_name}_fitness_wrapped.mp4"

        # Music path - look for any MP3 in the workspace root
        music_files = [f for f in os.listdir(
            self.base_dir) if f.lower().endswith('.mp3')]
        if music_files:
            self.music_path = self.base_dir / random.choice(music_files)
        else:
            self.music_path = None
            print("No music files found in workspace directory")

        # Find available templates and fonts
        self.available_templates = self.find_available_templates()
        self.available_fonts = self.find_available_fonts()

        # Default slide duration in seconds
        self.slide_duration = 3.0

        # Define standard vertical positions (moved up by 300 pixels)
        self.positions = {
            'top': 200,      # Was 500
            'center': 700,   # Was 1000
            'bottom': 900    # Was 1200
        }
        self.line_height = 100  # Was 120

        # Set default font file
        self.ensure_default_font()
        self.model = None

    def prepare_data(self, client_data):
        """
        Prepare and validate the input data for the FitnessWrappedGenerator.
        This ensures the data meets the requirements and provides fallbacks when needed.
        """
        import copy
        from datetime import datetime, timedelta

        # Create a copy of the data to avoid modifying the original
        data = copy.deepcopy(client_data)

        # Required fields with fallbacks
        defaults = {
            "name": "Client",
            "business_name": "Coco's",
            "date_range": "This Week",
            "start_weight": 90.0,
            "current_weight": 90.0,
            "weight_goal": 85.0,
            "current_weight_message": "Weight's trending in the right direction!",
            "workouts_this_week": 0,
            "workout_types": [],
            "total_reps": 0,
            "total_sets": 0,
            "total_weight_lifted": 0,
            "workload_increase": 0.0,
            "calories_consumed": "2500",
            "step_count": "10000",
            "sleep_hours": "8 Hours",
            "personalized_message": "Keep up the great work!"
        }

        # Apply defaults for missing fields
        for field, default_value in defaults.items():
            if field not in data or data[field] is None:
                data[field] = default_value
                print(f"Using default value for {field}: {default_value}")

        # Data availability flags
        has = {
            "weight_data": data.get('has_weight_data', False),
            "workout_data": data.get('workouts_this_week', 0) > 0,
            "nutrition_data": data.get('has_nutrition_data', False),
            "steps_data": data.get('has_steps_data', False),
            "sleep_data": data.get('has_sleep_data', False),
            # Add this line
            "up_to_date_photos": data.get('has_up_to_date_photos', False),
            "workload_data": data.get('workload_increase', 0) > 0,
            # Add this line
            "exercise_data": 'top_exercises' in data and len(data.get('top_exercises', [])) >= 3
        }

        # Store availability flags in the data
        data['data_availability'] = has

        # If data flags aren't provided, infer them from the data
        if 'has_weight_data' not in data:
            # Check if weight data appears to be real/custom and not default
            has['weight_data'] = (data['current_weight'] != defaults['current_weight'] or
                                  data['start_weight'] != defaults['start_weight'])
            data['has_weight_data'] = has['weight_data']

        if 'has_nutrition_data' not in data:
            # Check if nutrition/calories data appears to be real and not default
            has['nutrition_data'] = data['calories_consumed'] != defaults['calories_consumed']
            data['has_nutrition_data'] = has['nutrition_data']

        if 'has_steps_data' not in data:
            # Check if steps data appears to be real and not default
            has['steps_data'] = data['step_count'] != defaults['step_count']
            data['has_steps_data'] = has['steps_data']

        if 'has_sleep_data' not in data:
            # Check if sleep data appears to be real and not default
            has['sleep_data'] = data['sleep_hours'] != defaults['sleep_hours']
            data['has_sleep_data'] = has['sleep_data']

        # FIX: Check and correct weight data if it appears to be swapped
        # Sometimes current_weight and weight_loss are swapped or confused
        if has['weight_data'] and 'weight_loss' in data:
            # If current_weight is very small (likely actually the weight loss)
            if data['current_weight'] < 20 and data['start_weight'] > 50:
                # Store the original value as weight_loss
                data['weight_loss'] = data['current_weight']
                # Calculate the correct current_weight
                data['current_weight'] = data['start_weight'] - \
                    data['weight_loss']
                print(
                    f"Corrected weight values: current_weight={data['current_weight']}, weight_loss={data['weight_loss']}")

        # Calculate weight_loss if not provided
        if 'weight_loss' not in data and has['weight_data']:
            try:
                data['weight_loss'] = data['start_weight'] - \
                    data['current_weight']
            except (TypeError, ValueError):
                data['weight_loss'] = 0

        # Update date_range to current week automatically
        # Get the current date and calculate the start of the current week (Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Format as "1 January - 7 January" (day month - day month)
        date_format = "%-d %B"  # Unix format
        if os.name == 'nt':  # Windows
            date_format = "%#d %B"  # Windows format

        current_date_range = f"{start_of_week.strftime(date_format)} - {end_of_week.strftime(date_format)}"
        data['date_range'] = current_date_range
        print(f"Updated date range to current week: {current_date_range}")

        # Store the "has" flags directly in the data for easy access
        data['data_availability'] = has

        # Log what data we have
        print("Data availability for video:")
        for key, value in has.items():
            print(f"  {key}: {value}")

        return data

    def generate_personalized_message(self, bodyweight_analysis, nutrition_analysis, sleep_analysis):
        """Generate a personalized message based on client data."""
        if not self.model:
            # Default message if Gemini is not available
            message = "Another fantastic week! Your workload has increased nicely.\n"
            message += "Your nutrition is on point, and your weight is trending in the right direction.\n"
            message += "Keep pushing, and you'll reach that goal weight in no time!"
            return message

        try:
            prompt = f"""Generate a personalized, encouraging message (5-7 sentences) for a fitness client's weekly wrap-up video.
            Base it on this data:
            
            Bodyweight Analysis: {bodyweight_analysis}
            
            Nutrition Analysis: {nutrition_analysis}
            
            Sleep Analysis: {sleep_analysis}
            
            The message should be motivational, highlight their progress, and encourage them to keep going. 
            Mention specific achievements if possible. Format with line breaks for better readability on video slides.
            """

            response = self.model.generate_content(
                contents=prompt,
                generation_config={"max_output_tokens": 250}
            )

            return response.text
        except Exception as e:
            logging.exception(f"Error generating personalized message: {e}")
            # Fallback message
            return "Another fantastic week! Your workload has increased by over 25%\nYour nutrition is on point,\nand your weight is dropping.\nWhat more could you ask for!\nKeep pushing, and you'll reach\nthat goal weight in no time!"

    def save_fitness_wrapped_data(self, client_name, fitness_wrapped_data):
        """Save the prepared data to a JSON file."""
        import json

        filename = f"{client_name.replace(' ', '_')}_fitness_wrapped_data.json"
        try:
            with open(filename, 'w') as f:
                json.dump(fitness_wrapped_data, f, indent=4)
            logging.info(f"Saved fitness wrapped data to {filename}")
            return filename
        except Exception as e:
            logging.exception(f"Error saving fitness wrapped data: {e}")
            return None

    def generate_fitness_wrapped_video(self, fitness_wrapped_data):
        """Generate a fitness wrapped video using the provided data."""
        try:
            generator = FitnessWrappedGenerator(fitness_wrapped_data)
            video_result = generator.build_video()

            if video_result:
                logging.info(
                    f"Successfully created fitness wrapped video for {fitness_wrapped_data['name']}")
                logging.info(f"Video saved to: {generator.output_path}")
                return True, generator.output_path
            else:
                logging.error(
                    f"Failed to create fitness wrapped video for {fitness_wrapped_data['name']}")
                return False, None
        except Exception as e:
            logging.exception(f"Error generating fitness wrapped video: {e}")
            return False, None

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.template_dir, self.font_dir, self.output_dir, self.music_dir]:
            if not directory.exists():
                directory.mkdir(parents=True)
                print(f"Created '{directory}' directory.")

    def ensure_default_font(self):
        """Ensure a default font file exists to use as fallback"""
        if not self.default_font_path.exists():
            # Create a simple default font file if needed
            try:
                download_font()
            except Exception as e:
                print(f"Warning: Could not download default font: {e}")
                print("Will attempt to use system fonts.")

    def find_available_templates(self):
        """Find template images in the templates directory"""
        available = {}
        template_mapping = {
            "template_intro": "intro",
            "template_progress": "progress",
            "template_weight_goal": "weight_goal",
            "template_current_weight": "current_weight",
            "template_workout_count": "workout_count",
            "template_workout_total": "workout_total",
            "template_workout_stats": "workout_stats",
            "template_workload": "workload",
            "template_exercise_level": "exercise_level",
            "template_strength_gains": "strength_gains",
            "template_nutrition": "nutrition",
            "template_calories": "calories",
            "template_steps": "steps",
            "template_sleep": "sleep",
            "template_photos": "progress_photos",
            "template_progress_photos": "progress_photos",
            "template_conclusion": "conclusion",
            "template_motivational": "motivational"
        }

        if not self.template_dir.exists():
            print(
                f"Warning: Template directory {self.template_dir} doesn't exist.")
            return available

        # Look for image files with template_ prefix and map them to expected keys
        for file_path in self.template_dir.glob("*.png"):
            file_stem = file_path.stem
            if file_stem in template_mapping:
                # Map to the expected key name
                key = template_mapping[file_stem]
                available[key] = str(file_path)  # Convert Path to string
            else:
                # Also include with original name for flexibility
                available[file_stem] = str(file_path)  # Convert Path to string

        # Also check for jpg files if needed
        if not available:
            for file_path in self.template_dir.glob("*.jpg"):
                file_stem = file_path.stem
                if file_stem in template_mapping:
                    key = template_mapping[file_stem]
                    available[key] = str(file_path)  # Convert Path to string
                else:
                    # Convert Path to string
                    available[file_stem] = str(file_path)

        return available

    def find_available_fonts(self):
        """Find available fonts in the fonts directory"""
        fonts = {}

        if not self.font_dir.exists():
            print(f"Warning: Font directory {self.font_dir} doesn't exist.")
            return fonts

        for file_path in self.font_dir.glob("*.ttf"):
            name = file_path.stem
            fonts[name] = str(file_path)  # Convert Path to string

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

    # MODIFIED: Using PIL to create text frames instead of TextClip (avoids ImageMagick dependency)
    def create_text_overlay(self, text_elements, size=(1080, 1920)):
        """Create a text overlay image for slides using PIL instead of TextClip"""
        try:
            # Create a transparent RGBA image
            overlay = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Use system font if available
            try:
                system_font = "C:\\Windows\\Fonts\\Arial.ttf"  # Windows
                if not os.path.exists(system_font):
                    system_font = "/Library/Fonts/Arial.ttf"  # macOS
                if not os.path.exists(system_font):
                    system_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Linux
                
                # Fall back to a font we know exists
                if not os.path.exists(system_font):
                    system_font = None
            except:
                system_font = None
                
            # Process each text element
            for element in text_elements:
                text = str(element.get("text", ""))
                position = element.get("position", "center")
                font_size = element.get("font_size", 60)
                color = element.get("color", '#ffffff')  # White color
                
                # Try to load system font or use default font
                try:
                    if system_font and os.path.exists(system_font):
                        font = ImageFont.truetype(system_font, font_size)
                    else:
                        font = ImageFont.truetype(str(self.default_font_path), font_size)
                except:
                    # Last resort fallback to default PIL font
                    font = ImageFont.load_default()
                
                # Calculate position
                if position == "center":
                    text_width, text_height = draw.textsize(text, font=font)
                    x = (size[0] - text_width) // 2
                    y = (size[1] - text_height) // 2
                elif isinstance(position, tuple) and len(position) == 2:
                    x, y = position
                    if x is None:
                        text_width, _ = draw.textsize(text, font=font)
                        x = (size[0] - text_width) // 2
                
                # Draw text with black outline for better visibility
                # Draw text 4 times offset by 1 pixel for outline effect
                draw.text((x-1, y-1), text, font=font, fill="black")
                draw.text((x+1, y-1), text, font=font, fill="black")
                draw.text((x-1, y+1), text, font=font, fill="black")
                draw.text((x+1, y+1), text, font=font, fill="black")
                
                # Draw main text
                draw.text((x, y), text, font=font, fill=color)
            
            # Convert PIL Image to numpy array for MoviePy
            frame = np.array(overlay)
            return frame
            
        except Exception as e:
            print(f"Error creating text overlay: {e}")
            # Return a blank frame as fallback
            return np.zeros((size[1], size[0], 4), dtype=np.uint8)

    def create_slide(self, text_elements=None, duration=None):
        """Create a slide with background video and optional text overlays"""
        slide_duration = duration or self.slide_duration

        try:
            # First load the background video if not already loaded
            if not hasattr(self, 'background_video'):
                if self.background_video_path and self.background_video_path.exists():
                    print(
                        f"Loading background video: {self.background_video_path}")
                    self.background_video = VideoFileClip(
                        str(self.background_video_path))
                    # Increase brightness of background video
                    self.background_video = self.background_video.fx(
                        vfx.colorx, 1.3)
                    print(
                        f"Background video loaded successfully. Duration: {self.background_video.duration}s")
                else:
                    print("Background video not found")
                    self.background_video = None
                    
            # Create a subclip of the background video with the desired duration
            if self.background_video is not None:
                background_clip = self.background_video.subclip(0, min(slide_duration, self.background_video.duration))
                
                # If text elements exist, create an overlay
                if text_elements:
                    # Create a function that returns a text overlay frame for each time t
                    def make_frame(t):
                        # Get background frame
                        bg_frame = background_clip.get_frame(t)
                        
                        # Create text overlay (with transparency)
                        text_overlay = self.create_text_overlay(text_elements, size=(background_clip.w, background_clip.h))
                        
                        # Composite the frames - only apply text where alpha channel > 0
                        mask = text_overlay[:,:,3] > 0
                        result = bg_frame.copy()
                        
                        # Where text exists, blend with background (simulate alpha)
                        alpha = text_overlay[:,:,3] / 255.0
                        for c in range(3):  # RGB channels
                            result[:,:,c] = bg_frame[:,:,c] * (1 - alpha) + text_overlay[:,:,c] * alpha
                            
                        return result
                    
                    # Create a video clip from the make_frame function
                    final_clip = VideoClip(make_frame, duration=slide_duration)
                    
                    # Set audio from background clip (if any)
                    if background_clip.audio is not None:
                        final_clip = final_clip.set_audio(background_clip.audio)
                    
                    return final_clip
                else:
                    # No text, just return the background clip
                    return background_clip.set_duration(slide_duration)
            else:
                # No background video, create a solid color clip with text
                color_clip = ColorClip(size=(1080, 1920), color=(0, 0, 0))
                return color_clip.set_duration(slide_duration)

        except Exception as e:
            print(f"Error creating slide: {e}")
            return None

    def build_video(self):
        """Build the fitness wrapped video with all slides in the client's preferred order, skipping all slides without real data"""
        print("Building fitness wrapped video in vertical/story format...")
        print(f"Using client data for: {self.client_data['name']}")
        slides = []

        # Use the new position values
        center_y = self.positions['center']
        top_y = self.positions['top']
        bottom_y = self.positions['bottom']
        line_height = self.line_height

        # Check for presence of real data (with reasonable defaults for what counts as "real")
        has_weight_data = self.client_data.get('has_weight_data', False)
        has_workout_data = self.client_data.get('workouts_this_week', 0) > 0
        has_nutrition_data = self.client_data.get('has_nutrition_data', False)
        has_steps_data = self.client_data.get('has_steps_data', False)
        has_sleep_data = self.client_data.get('has_sleep_data', False)
        has_workload_data = self.client_data.get('workload_increase', 0) > 0

        print(f"Data availability: Weight={has_weight_data}, Workouts={has_workout_data}, Nutrition={has_nutrition_data}, " +
              f"Steps={has_steps_data}, Sleep={has_sleep_data}, Workload={has_workload_data}")

        # --- ALWAYS INCLUDE SLIDES ---

        # 1. Create intro slide - "Your Week at Coco's" (always include)
        intro_text = [
            {
                "text": "Your Week",
                "position": (None, center_y - line_height),
                "font_size": 100
            },
            {
                "text": f"At {self.client_data['business_name']}",
                "position": (None, center_y),
                "font_size": 80
            }
        ]
        intro_slide = self.create_slide(intro_text, duration=4.0)
        if intro_slide:
            slides.append(intro_slide)

        # 2. Create progress slide - "Let's Check Your Progress" (always include)
        progress_text = [
            {
                "text": "Let's Check your Progress",
                "position": (None, center_y),
                "font_size": 70
            },
            {
                "text": f"From {self.client_data['date_range']}",
                "position": (None, bottom_y),
                "font_size": 50
            }
        ]
        progress_slide = self.create_slide(progress_text, duration=4.0)
        if progress_slide:
            slides.append(progress_slide)

        # --- CONDITIONAL SLIDES BASED ON REAL DATA ---

        # 3. Create workout count slide - ONLY if workout data exists
        if has_workout_data:
            workout_count_text = [
                {
                    "text": "You Trained",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{self.client_data['workouts_this_week']} Times",
                    "position": (None, center_y),
                    "font_size": 90
                },
            ]
            workout_count_slide = self.create_slide(workout_count_text)
            if workout_count_slide:
                slides.append(workout_count_slide)

        # 4. Create workout types slide - ONLY if workout data exists
        if has_workout_data and self.client_data.get('workout_types', []):
            workout_total_text = [
                {
                    "text": "In total you powered through",
                    "position": (None, center_y),
                    "font_size": 60
                }
            ]
            workout_total_slide = self.create_slide(workout_total_text)
            if workout_total_slide:
                slides.append(workout_total_slide)

        # 5. Create workout stats slide - ONLY if workout data exists
        if has_workout_data and self.client_data.get('total_reps', 0) > 0:
            workout_stats_text = [
                {
                    "text": f"{self.client_data['total_reps']} reps",
                    "position": (None, center_y - line_height),
                    "font_size": 60
                },
                {
                    "text": f"{self.client_data['total_sets']} sets",
                    "position": (None, center_y),
                    "font_size": 60
                },
                {
                    "text": f"{self.client_data['total_weight_lifted']}Kgs",
                    "position": (None, center_y + line_height),
                    "font_size": 60
                }
            ]
            workout_stats_slide = self.create_slide(workout_stats_text)
            if workout_stats_slide:
                slides.append(workout_stats_slide)

        # 6. Create workload increase slide - ONLY if workload data exists
        if has_workload_data:
            workload_text = [
                {
                    "text": f"{self.client_data['workload_increase']}% Total",
                    "position": (None, center_y - 50),
                    "font_size": 70
                },
                {
                    "text": "Workload Increase",
                    "position": (None, center_y + 50),
                    "font_size": 70
                },
                {
                    "text": "R-E-S-P-E-C-T",
                    "position": (None, bottom_y),
                    "font_size": 40
                }
            ]
            workload_slide = self.create_slide(workload_text)
            if workload_slide:
                slides.append(workload_slide)

        # 7. Create exercise level slide - ONLY if workout data exists
        if has_workout_data:
            exercise_level_text = [
                {
                    "text": "You took several",
                    "position": (None, center_y - 50),
                    "font_size": 60
                },
                {
                    "text": "exercises to the",
                    "position": (None, center_y + 50),
                    "font_size": 60
                },
                {
                    "text": "next level!!",
                    "position": (None, center_y + 150),
                    "font_size": 60
                }
            ]
            exercise_level_slide = self.create_slide(exercise_level_text)
            if exercise_level_slide:
                slides.append(exercise_level_slide)

        # 8. Create strength gains slide - ONLY if exercise data exists
        if self.client_data.get('data_availability', {}).get('exercise_data', has_workout_data):

            # Get the top exercises from client data (no fallbacks)
            top_exercises = self.client_data.get('top_exercises', [])[:3]

            # If we don't have enough exercises (at least 3), skip the slide
            if len(top_exercises) < 3:
                print("Skipping strength gains slide - insufficient exercise data")
            else:
                print(
                    f"Creating strength gains slide with top exercises: {top_exercises}")

                # Create the slide text elements with the dynamic exercise data
                strength_gains_text = [
                    # Exercise 1
                    {

                    },
                    {
                        # Always use 'Increase'
                        "text": f"{top_exercises[0]['name']} Increase",
                        "position": (None, center_y - line_height*1.5),
                        "font_size": 50
                    },
                    {
                        # Remove minus sign with abs()
                        "text": f"{abs(top_exercises[0]['improvement'])}%",
                        "position": (None, center_y - line_height*0.8),
                        "font_size": 50
                    },
                    # Exercise 2


                    {
                        # Always use 'Increase'
                        "text": f"{top_exercises[1]['name']} Increase",
                        "position": (None, center_y),
                        "font_size": 50
                    },
                    {
                        # Remove minus sign with abs()
                        "text": f"{abs(top_exercises[1]['improvement'])}%",
                        "position": (None, center_y + line_height*0.7),
                        "font_size": 50
                    },
                    # Exercise 3



                    {
                        # Always use 'Increase'
                        "text": f"{top_exercises[2]['name']} Increase",
                        "position": (None, center_y + line_height*1.5),
                        "font_size": 50
                    },
                    {
                        # Remove minus sign with abs()
                        "text": f"{abs(top_exercises[2]['improvement'])}%",
                        "position": (None, center_y + line_height*2.2),
                        "font_size": 50
                    }
                ]
                strength_gains_slide = self.create_slide(strength_gains_text)
                if strength_gains_slide:
                    slides.append(strength_gains_slide)
                    print("Added strength gains slide to video")
                else:
                    print("Failed to create strength gains slide")

        # 9. Create nutrition slide - ONLY if nutrition data exists
        if has_nutrition_data:
            nutrition_text = [
                {
                    "text": "Let's Check your",
                    "position": (None, center_y - 50),
                    "font_size": 60
                },
                {
                    "text": "Nutrition",
                    "position": (None, center_y + 50),
                    "font_size": 60
                }
            ]
            nutrition_slide = self.create_slide(nutrition_text)
            if nutrition_slide:
                slides.append(nutrition_slide)

        # 10. Create calories slide - ONLY if nutrition data exists
        if has_nutrition_data:
            calories_text = [
                {
                    "text": f"{self.client_data['calories_consumed']} cals",
                    "position": (None, center_y),
                    "font_size": 80
                },
                {
                    "text": "average daily intake",
                    "position": (None, center_y + line_height),
                    "font_size": 50
                },
            ]
            calories_slide = self.create_slide(calories_text)
            if calories_slide:
                slides.append(calories_slide)

        # 11. Create weight goal slide - ONLY if weight data exists
        if has_weight_data:
            weight_goal_text = [
                {
                    "text": "Let's Check your",
                    "position": (None, center_y - 50),
                    "font_size": 60
                },
                {
                    "text": "Body Weight Goal!",
                    "position": (None, center_y + 50),
                    "font_size": 60
                },
                {
                    "text": f"Remember we are looking for {self.client_data['weight_goal']}kgs",
                    "position": (None, bottom_y),
                    "font_size": 40
                }
            ]
            weight_goal_slide = self.create_slide(weight_goal_text)
            if weight_goal_slide:
                slides.append(weight_goal_slide)

        # 12. Create current weight slide - ONLY if weight data exists
        if has_weight_data:
            # Format weight values with one decimal place
            current_weight = f"{self.client_data['current_weight']:.1f}"
            weight_loss = f"{self.client_data.get('weight_loss', 0):.1f}"

            # Create a progress message based on weight loss
            if 'weight_loss' in self.client_data and self.client_data['weight_loss'] > 0:
                weight_progress_text = f"Weight's still trending down nicely. {weight_loss} kilos down already, v nice progress!"
            else:
                weight_progress_text = "Weight's trending well with your fitness goals!"

            current_weight_text = [
                {
                    "text": "You're now",
                    # Move down to the middle of the slide
                    "position": (None, center_y - 50),
                    "font_size": 70,
                    "align": "center"
                },
                {
                    # Use current_weight correctly
                    "text": f"{current_weight} kgs",
                    # Position below first line
                    "position": (None, center_y + 50),
                    "font_size": 80,
                    "align": "center"
                },
                {
                    "text": weight_progress_text,
                    # Position further down
                    "position": (None, center_y + line_height*2),
                    "font_size": 40,
                    "align": "center"
                },
                {
                    "text": "Keep doing what you're doing!",
                    # Position at bottom
                    "position": (None, center_y + line_height*3.5),
                    "font_size": 40,
                    "align": "center"
                }
            ]
            current_weight_slide = self.create_slide(
                current_weight_text, duration=4.0)
            if current_weight_slide:
                slides.append(current_weight_slide)

        # 14. Create sleep slide - ONLY if sleep data exists
        if has_sleep_data:
            sleep_text = [
                {
                    "text": "Sleep Check",
                    "position": (None, center_y - 100),
                    "font_size": 70
                },
                {
                    "text": self.client_data['sleep_hours'],
                    "position": (None, center_y),
                    "font_size": 70
                },
            ]
            sleep_slide = self.create_slide(sleep_text)
            if sleep_slide:
                slides.append(sleep_slide)

        # 15. Create progress photos slide - ONLY if photos data exists
        if self.client_data.get('data_availability', {}).get('up_to_date_photos', False):
            photos_text = [
                {
                    "text": "Progress",
                    "position": (None, center_y - 50),
                    "font_size": 70
                },
                {
                    "text": "Photos Updated",
                    "position": (None, center_y + 50),
                    "font_size": 70
                },
                {
                    "text": "Looking amazing!",
                    "position": (None, bottom_y),
                    "font_size": 40
                }
            ]
            photos_slide = self.create_slide(photos_text)
            if photos_slide:
                slides.append(photos_slide)

        # 16. Create first conclusion slide - personalized message (3 seconds)
        # Split the personalized message by newlines to create multiple text elements
        message_lines = self.client_data['personalized_message'].split('\n')
        conclusion_text = []

        # Calculate appropriate vertical position
        vertical_offset = 100  # Pixels to move text down
        start_y = center_y - (len(message_lines) * line_height) // 2 + vertical_offset

        # Limit to 7 lines max
        for i, line in enumerate(message_lines[:7]):
            conclusion_text.append({
                "text": line,
                "position": (None, start_y + (i * line_height)),
                "font_size": 45 if i == 0 else 40,  # First line slightly bigger
                "align": "center"  # Ensure text is centered
            })

        # Create the first conclusion slide (3 seconds)
        conclusion_slide = self.create_slide(conclusion_text, duration=3.0)
        if conclusion_slide:
            slides.append(conclusion_slide)

        # Immediately create and add the second conclusion slide (3 seconds)
        if conclusion_slide:
            final_conclusion_slide = self.create_slide(conclusion_text, duration=3.0)
            if final_conclusion_slide:
                slides.append(final_conclusion_slide)

        # 17. Create motivational slide with bunny - "Keep Moving!" (last slide)
        motivational_text = [
            {
                "text": "Keep Moving!",
                "position": (None, center_y + line_height*4),
                "font_size": 70
            }
        ]
        motivational_slide = self.create_slide(motivational_text, duration=4.0)
        if motivational_slide:
            slides.append(motivational_slide)

        # Rest of the build_video function (combining slides, adding music, etc.)
        if not slides:
            print("Error: No valid slides could be created.")
            return False

        # Concatenate all slides with simple transitions
        print(f"Combining {len(slides)} slides...")
        try:
            # First validate all slides
            valid_slides = []
            for i, slide in enumerate(slides):
                if slide is not None and hasattr(slide, 'duration'):
                    try:
                        # Test that the clip can produce a frame
                        test_frame = slide.get_frame(0)
                        if test_frame is not None:
                            valid_slides.append(slide)
                        else:
                            print(
                                f"Warning: Slide {i} cannot produce frames, skipping")
                    except Exception as e:
                        print(f"Warning: Slide {i} validation failed: {e}")
                else:
                    print(f"Warning: Slide {i} is invalid, skipping")

            if not valid_slides:
                print("Error: No valid slides to combine")
                return False

            print(f"Proceeding with {len(valid_slides)} valid slides")

            # Create a list to store all clips that need to be closed later
            clips_to_close = valid_slides.copy()

            # Use simple concatenation without transitions
            print("Creating concatenated clip...")
            final_clip = concatenate_videoclips(valid_slides)
            clips_to_close.append(final_clip)
            print(f"Final clip duration: {final_clip.duration}s")

            # Verify the final clip
            try:
                test_frame = final_clip.get_frame(0)
                if test_frame is None:
                    raise ValueError("Final clip cannot produce frames")
            except Exception as e:
                print(f"Error: Final clip validation failed: {e}")
                # Clean up and return
                for clip in clips_to_close:
                    try:
                        if clip is not None:
                            clip.close()
                    except:
                        pass
                return False

        except Exception as e:
            print(f"Error in video composition: {e}")
            return False

        # Add background music if available
        audio = None
        if self.music_path and os.path.exists(self.music_path):
            print(f"Adding background music from: {self.music_path}")
            try:
                audio = AudioFileClip(str(self.music_path))
                print(f"Audio duration: {audio.duration}s")

                # Loop or trim audio as needed
                if audio.duration < final_clip.duration:
                    print("Looping audio to match video duration...")
                    audio = afx.audio_loop(audio, duration=final_clip.duration)
                else:
                    print("Trimming audio to match video duration...")
                    audio = audio.subclip(0, final_clip.duration)

                # Set volume
                audio = audio.volumex(0.5)
                print("Audio prepared successfully")

                # Add audio to the video
                final_clip = final_clip.set_audio(audio)
                clips_to_close.append(audio)
            except Exception as e:
                print(f"Error adding music: {e}")
                print("Continuing without background music.")
                if audio:
                    try:
                        audio.close()
                    except:
                        pass
        else:
            print("No background music found. Video will be silent.")

        # Write the final video file
        print(f"Writing video to {self.output_path}...")
        try:
            # Make sure output directory exists
            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)

            # Write the video with more compatible settings
            print("Starting video write process...")
            final_clip.write_videofile(
                str(self.output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                threads=4,
                bitrate='2000k',
                ffmpeg_params=['-pix_fmt', 'yuv420p']  # Ensure compatibility
            )
            print(
                f"Video successfully created and saved to {self.output_path}")
            return True

        except Exception as e:
            print(f"Error writing video file: {e}")
            print("Stack trace:", e.__class__.__name__)
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up all resources in the finally block
            print("Cleaning up resources...")
            for clip in clips_to_close:
                try:
                    if clip is not None:
                        clip.close()
                except Exception as e:
                    print(f"Error closing clip: {e}")

            # Clean up the background video
            if hasattr(self, 'background_video') and self.background_video is not None:
                try:
                    self.background_video.close()
                except:
                    pass

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
    # Skip font download if fonts already exist
    fonts_dir = Path("fonts")
    if fonts_dir.exists() and list(fonts_dir.glob("*.ttf")):
        print("Font files already exist. Skipping download.")
        return

    try:
        import requests

        # Create fonts directory if it doesn't exist
        if not fonts_dir.exists():
            fonts_dir.mkdir(parents=True)

        # Updated URL for a free font (Nunito Sans from Google Fonts)
        font_url = "https://github.com/google/fonts/raw/main/ofl/nunitosans/static/NunitoSans_7pt-Bold.ttf"
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
                # Alternate source
                try:
                    alternate_url = "https://fonts.gstatic.com/s/nunitosans/v12/pe03MImSLYBIv1o4X1M8cc8GBs5tU1E.ttf"
                    response = requests.get(alternate_url)
                    if response.status_code == 200:
                        with open(font_path, 'wb') as f:
                            f.write(response.content)
                        print(
                            f"Font downloaded from alternate source to {font_path}")
                    else:
                        print(
                            "All font download attempts failed. Using system fonts.")
                except Exception as e:
                    print(f"Error downloading from alternate source: {e}")
        else:
            print(f"Font already exists at {font_path}")

    except Exception as e:
        print(f"Error downloading font: {e}")
        print("Continuing with existing fonts instead.")

        # Create a simple fallback font if possible
        try:
            from PIL import Image, ImageDraw, ImageFont
            # Force PIL to create a default font file we can use
            default_font = ImageFont.load_default()
            # In newer PIL versions, we don't need to do anything else
            print("Using PIL's default font as fallback.")
        except Exception as e:
            print(f"Error setting up fallback font: {e}")


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
        client_data_file = input(
            "Enter path to client data JSON file: ").strip()

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