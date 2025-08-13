import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
import logging
import tempfile
import shutil
import random

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

        # Music path
        self.music_path = self.music_dir / "background_music.mp3"

        # Find available templates and fonts
        self.available_templates = self.find_available_templates()
        self.available_fonts = self.find_available_fonts()

        # Default slide duration in seconds
        self.slide_duration = 3.0

        # Set default font file
        self.ensure_default_font()
        self.model = None

    def select_random_music(self):
        """Select a random music file from the music directory"""
        # Get all mp3 files in the music directory
        mp3_files = list(self.music_dir.glob("*.mp3"))

        # If no mp3 files found, return the default music path
        if not mp3_files:
            print("No music files found. Using default.")
            return self.music_path

        # Select a random music file
        random_music = random.choice(mp3_files)
        print(f"Selected random music track: {random_music.name}")
        return random_music

    def prepare_data(self, client_data):
        """
        Prepare and validate the input data for the FitnessWrappedGenerator.
        This ensures the data meets the requirements and provides fallbacks when needed.
        """
        import copy

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

        # Calculate weight_loss if not provided
        if 'weight_loss' not in data and has['weight_data']:
            try:
                data['weight_loss'] = data['start_weight'] - \
                    data['current_weight']
            except (TypeError, ValueError):
                data['weight_loss'] = 0

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

    def add_text_to_image(self, image_path, text_elements, output_path):
        """
        Add text elements to an image with improved positioning and wrapping

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

                # Find the font - prioritize system fonts if needed
                font_path = None
                if font_name in self.available_fonts:
                    font_path = self.available_fonts[font_name]
                elif "default" in self.available_fonts:
                    font_path = self.available_fonts["default"]
                elif os.path.exists("C:\\Windows\\Fonts\\arial.ttf"):  # Windows
                    font_path = "C:\\Windows\\Fonts\\arial.ttf"
                elif os.path.exists("/Library/Fonts/Arial.ttf"):  # macOS
                    font_path = "/Library/Fonts/Arial.ttf"
                elif os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):  # Linux
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

                # Last resort - use default system font
                try:
                    if font_path:
                        font = ImageFont.truetype(font_path, font_size)
                    else:
                        font = ImageFont.load_default()
                        if hasattr(font, "font_variant"):
                            font = font.font_variant(size=font_size)
                except Exception as e:
                    print(f"Font error, using default: {e}")
                    font = ImageFont.load_default()

                # Handle text wrapping for long lines
                words = text.split()
                lines = []
                current_line = []

                for word in words:
                    # Try adding this word to the current line
                    test_line = ' '.join(current_line + [word])

                    # Check if the line would be too long
                    line_width = 0
                    try:
                        if hasattr(font, "getbbox"):
                            bbox = font.getbbox(test_line)
                            line_width = bbox[2] - bbox[0]
                        elif hasattr(font, "getsize"):
                            line_width, _ = font.getsize(test_line)
                        else:
                            line_width, _ = draw.textsize(test_line, font=font)
                    except Exception:
                        # Rough estimate if we can't calculate properly
                        line_width = len(test_line) * (font_size // 2)

                    # If line is too wide, start a new line
                    # 75px margin on each side
                    if line_width > (img.width - 150) and current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        current_line.append(word)

                # Add the last line
                if current_line:
                    lines.append(' '.join(current_line))

                # If no linebreaks were needed, use the original text
                final_text = '\n'.join(lines) if lines else text

                # Calculate text dimensions for positioning
                try:
                    if hasattr(font, "getbbox"):
                        # For multiline text, we need to calculate the largest width and total height
                        max_width = 0
                        total_height = 0
                        for line in final_text.split('\n'):
                            bbox = font.getbbox(line)
                            line_width = bbox[2] - bbox[0]
                            line_height = bbox[3] - bbox[1]
                            max_width = max(max_width, line_width)
                            total_height += line_height

                        text_width = max_width
                        text_height = total_height
                    elif hasattr(font, "getsize"):
                        # For older Pillow versions
                        lines = final_text.split('\n')
                        widths, heights = zip(
                            *[font.getsize(line) for line in lines])
                        text_width = max(widths)
                        text_height = sum(heights)
                    else:
                        # Even older versions
                        text_width = draw.textsize(final_text, font=font)[0]
                        text_height = draw.textsize(final_text, font=font)[
                            1] * final_text.count('\n') + 1
                except Exception as e:
                    print(f"Error calculating text size: {e}")
                    # Rough estimate as fallback
                    text_width = len(final_text.split('\n')
                                     [0]) * (font_size // 2)
                    text_height = font_size * (1 + final_text.count('\n'))

                # Handle position
                x, y = 0, 0  # Default position
                if position == "center":
                    x = (img.width - text_width) // 2
                    y = (img.height - text_height) // 2
                elif position == "top_center":
                    x = (img.width - text_width) // 2
                    y = img.height // 4
                elif position == "bottom_center":
                    x = (img.width - text_width) // 2
                    y = (img.height * 3) // 4
                elif isinstance(position, tuple) and len(position) == 2:
                    x, y = position
                    # If x is None, center horizontally
                    if x is None:
                        x = (img.width - text_width) // 2

                # Ensure text stays within bounds (with margins)
                margin = 75  # 75px margin from edge
                x = max(margin, min(x, img.width - text_width - margin))

                # Draw the text
                try:
                    # Use align parameter for alignment
                    draw.text((x, y), final_text, font=font,
                              fill=color, align=align)
                except Exception as e:
                    print(f"Error drawing text: {e}, trying fallback method")
                    try:
                        draw.text((x, y), final_text, fill=color)
                    except Exception as e2:
                        print(f"Critical error drawing text: {e2}")

            # Save to a temporary file
            img.save(output_path)
            return output_path

        except Exception as e:
            print(f"Error adding text to image {image_path}: {e}")
            return image_path

    def create_slide(self, template_key, text_elements=None, duration=None):
        """Create a slide with text elements on a template background image"""
        if template_key not in self.available_templates:
            print(f"Template {template_key} not found in available templates.")
            return None

        template_path = self.available_templates[template_key]
        if not os.path.exists(template_path):
            print(f"Template file not found: {template_path}")
            return None

        # Create a temporary copy of the image with text
        temp_dir = tempfile.mkdtemp()
        temp_image_path = os.path.join(temp_dir, f"{template_key}_temp.png")

        # Copy the template to our temp location
        try:
            # Add text to image if provided
            if text_elements:
                # Check if text has animation properties
                has_animation = any(
                    "animation" in text_elem for text_elem in text_elements)

                if has_animation:
                    # Create the base image with text
                    self.add_text_to_image(
                        template_path, text_elements, temp_image_path)

                    # Create animation clips for each text element
                    animation_clips = []
                    base_clip = ImageClip(
                        temp_image_path, duration=duration or 3)

                    for text_elem in text_elements:
                        if "animation" in text_elem:
                            # Handle different animation types
                            anim_type = text_elem.get("animation", "fade_in")
                            delay = text_elem.get("animation_delay", 0)

                            if anim_type == "fade_in":
                                # Create a fade-in effect
                                text_clip = TextClip(
                                    text_elem["text"],
                                    fontsize=text_elem.get("font_size", 40),
                                    color="white",
                                    font=str(self.default_font_path),
                                    method='label'
                                )

                                # Position the text
                                position = text_elem.get(
                                    "position", (None, None))
                                if position[0] is None:  # Center horizontally
                                    x_pos = 'center'
                                else:
                                    x_pos = position[0]

                                if position[1] is None:  # Center vertically
                                    y_pos = 'center'
                                else:
                                    y_pos = position[1]

                                # Set position and start time
                                text_clip = (text_clip
                                             .set_position((x_pos, y_pos))
                                             .set_start(delay)
                                             .set_duration(duration or 3 - delay)
                                             .fadein(0.5))  # 0.5 second fade in

                                animation_clips.append(text_clip)

                            elif anim_type == "slide_up":
                                # Create a slide-up effect
                                text_clip = TextClip(
                                    text_elem["text"],
                                    fontsize=text_elem.get("font_size", 40),
                                    color="white",
                                    font=str(self.default_font_path),
                                    method='label'
                                )

                                # Get position
                                position = text_elem.get(
                                    "position", (None, None))
                                if position[0] is None:
                                    x_pos = 'center'
            else:
                                    x_pos = position[0]

                                # For slide up, start lower and move up
                                start_y = position[1] + \
                                    100 if position[1] is not None else 'center'
                                end_y = position[1] if position[1] is not None else 'center'

                                # Create animation
                                def slide_up(t):
                                    if t < 0.5:  # Animation takes 0.5 seconds
                                        progress = t / 0.5
                                        current_y = start_y + \
                                            (end_y - start_y) * progress
                                            return (x_pos, current_y)
                else:
                                            return (x_pos, end_y)

                                text_clip = (text_clip
                                             .set_position(slide_up)
                                             .set_start(delay)
                                             .set_duration(duration or 3 - delay))

                                animation_clips.append(text_clip)

                    # Combine base clip with animations
                    if animation_clips:
                        final_clip = CompositeVideoClip(
                            [base_clip] + animation_clips)
                        return final_clip
                        else:
                        return base_clip
                        else:
                    # No animations, use standard method
                    self.add_text_to_image(
                        template_path, text_elements, temp_image_path)
                    clip = ImageClip(temp_image_path, duration=duration or 3)
                    return clip
                    else:
                # No text, just use the template as is
                shutil.copy(template_path, temp_image_path)
                clip = ImageClip(temp_image_path, duration=duration or 3)
                return clip

        except Exception as e:
            print(f"Error creating slide from {template_key}: {e}")
            return None

    def build_video(self):
        """Build and save the final video"""
        # If no slides have been created, return early
        if not hasattr(self, 'slides') or not self.slides:
            print("No slides to include in video. Aborting.")
            return False
            
        try:
            slides = []
            # Create clips for each slide
            slide_clips = []
            for slide in self.slides:
                image_path = slide.get('image_path')
                duration = slide.get('duration', 5)  # Default 5 seconds
                transition = slide.get('transition')
                transition_duration = self.transition_duration  # Default set in init

                # Create the base clip
                clip = ImageClip(str(image_path)).set_duration(duration)

                # Apply any custom transition if specified
                if transition:
                    clip = transition(clip)

                slide_clips.append(clip)

            # Concatenate all slide clips
            final_clip = concatenate_videoclips(slide_clips, method="compose")

            # Select a random music track
            music_path = self.select_random_music()

            # Add background music
            if music_path and music_path.exists():
                audio = AudioFileClip(str(music_path))
                # Loop the audio if it's shorter than the video
                if audio.duration < final_clip.duration:
                    audio = afx.audio_loop(audio, duration=final_clip.duration)
                    else:
                    # Trim audio if it's longer than the video
                    audio = audio.subclip(0, final_clip.duration)
                final_clip = final_clip.set_audio(audio)
        
        # Write the final video file
        final_clip.write_videofile(
            str(self.output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                threads=4
            )

            print(f"Successfully created video at {self.output_path}")
            return True

        except Exception as e:
            print(f"Error creating video: {str(e)}")
            return False

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
