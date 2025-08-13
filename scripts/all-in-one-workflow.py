import os
import json
import logging
from pathlib import Path
from moviepy.editor import *
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FitnessVideoGenerator:
    def __init__(self, json_file, background_video=None):
        """Initialize with JSON data file and optional background video path"""
        self.json_file = json_file
        
        # Default background video path
        if background_video is None:
            self.background_video_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\shanbot\shanbot\shanbot\blue2.mp4"
        else:
            self.background_video_path = background_video
        
        # Load client data
        try:
            with open(json_file, 'r') as f:
                self.client_data = json.load(f)
                logging.info(f"Successfully loaded data from {json_file}")
        except Exception as e:
            logging.error(f"Failed to load JSON data: {e}")
            raise
        
        # Extract client name
        self.client_name = self.client_data.get("name", "Client")
        logging.info(f"Generating video for client: {self.client_name}")
        
        # Set output path
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_path = os.path.join(self.output_dir, f"{self.client_name.replace(' ', '_')}_fitness_wrapped.mp4")
        
        # Set slide parameters
        self.slide_duration = 3.0  # seconds
        self.positions = {
            'top': 200,
            'center': 700,
            'bottom': 900
        }
        self.line_height = 100
        
        # Background video object
        self.background_video = None
    
    def create_text_overlay(self, text_elements, size=(1080, 1920)):
        """Create a text overlay using PIL"""
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
                        # Use PIL's default font
                        font = ImageFont.load_default()
                        logging.warning("Using PIL default font (text may look small)")
                except:
                    # Last resort fallback to default PIL font
                    font = ImageFont.load_default()
                
                # Calculate position
                if position == "center":
                    # PIL's textsize is deprecated, use textbbox or getbbox for newer versions
                    try:
                        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
                    except AttributeError:
                        try:
                            text_width, text_height = draw.textsize(text, font=font)
                        except:
                            # Rough estimate if all else fails
                            text_width = len(text) * font_size // 2
                            text_height = font_size
                    
                    x = (size[0] - text_width) // 2
                    y = (size[1] - text_height) // 2
                elif isinstance(position, tuple) and len(position) == 2:
                    x, y = position
                    if x is None:
                        try:
                            text_width = draw.textbbox((0, 0), text, font=font)[2]
                        except AttributeError:
                            try:
                                text_width, _ = draw.textsize(text, font=font)
                            except:
                                text_width = len(text) * font_size // 2
                        x = (size[0] - text_width) // 2
                
                # Draw text with black outline for better visibility
                # Draw text 4 times offset by 1 pixel for outline effect
                draw.text((x-2, y-2), text, font=font, fill="black")
                draw.text((x+2, y-2), text, font=font, fill="black")
                draw.text((x-2, y+2), text, font=font, fill="black")
                draw.text((x+2, y+2), text, font=font, fill="black")
                
                # Draw main text
                draw.text((x, y), text, font=font, fill=color)
            
            # Convert PIL Image to numpy array for MoviePy
            frame = np.array(overlay)
            return frame
            
        except Exception as e:
            logging.exception(f"Error creating text overlay: {e}")
            # Return a blank transparent frame as fallback
            return np.zeros((size[1], size[0], 4), dtype=np.uint8)

    def create_slide(self, text_elements=None, duration=None):
        """Create a slide with background video and text overlay"""
        slide_duration = duration or self.slide_duration
        
        try:
            # Load background video if not already loaded
            if self.background_video is None:
                if os.path.exists(self.background_video_path):
                    logging.info(f"Loading background video: {self.background_video_path}")
                    self.background_video = VideoFileClip(self.background_video_path)
                    # Increase brightness
                    self.background_video = self.background_video.fx(vfx.colorx, 1.3)
                    logging.info(f"Background video loaded. Duration: {self.background_video.duration}s")
                else:
                    logging.error(f"Background video not found at {self.background_video_path}")
                    # Create a solid color clip as fallback
                    self.background_video = ColorClip((1080, 1920), color=(0, 0, 128), duration=10)
                    logging.info("Created fallback blue background")
            
            # Create a subclip of the background video
            if self.background_video is not None:
                # Loop the background video if it's shorter than the slide duration
                if self.background_video.duration < slide_duration:
                    logging.info("Background video shorter than slide duration. Looping...")
                    repeats = int(slide_duration / self.background_video.duration) + 1
                    background_clip = concatenate_videoclips([self.background_video] * repeats)
                    background_clip = background_clip.subclip(0, slide_duration)
                else:
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
                color_clip = ColorClip(size=(1080, 1920), color=(0, 0, 128))
                return color_clip.set_duration(slide_duration)

        except Exception as e:
            logging.exception(f"Error creating slide: {e}")
            return None
    
    def build_video(self):
        """Build the fitness wrapped video with all slides"""
        logging.info("Building fitness wrapped video...")
        logging.info(f"Using client data for: {self.client_name}")
        slides = []
        
        # Define positions for easy access
        center_y = self.positions['center']
        top_y = self.positions['top']
        bottom_y = self.positions['bottom']
        line_height = self.line_height
        
        # Check for presence of real data
        has_weight_data = self.client_data.get('has_weight_data', False)
        has_workout_data = self.client_data.get('workouts_this_week', 0) > 0
        has_nutrition_data = self.client_data.get('has_nutrition_data', False)
        has_steps_data = self.client_data.get('has_steps_data', False)
        has_sleep_data = self.client_data.get('has_sleep_data', False)
        has_workload_data = self.client_data.get('workload_increase', 0) > 0
        
        logging.info(f"Data availability: Weight={has_weight_data}, Workouts={has_workout_data}, Nutrition={has_nutrition_data}, " +
                    f"Steps={has_steps_data}, Sleep={has_sleep_data}, Workload={has_workload_data}")
        
        # --- ALWAYS INCLUDE SLIDES ---
        
        # 1. Create intro slide - "Your Week at Coco's"
        intro_text = [
            {
                "text": "Your Week",
                "position": (None, center_y - line_height),
                "font_size": 100
            },
            {
                "text": f"At {self.client_data.get('business_name', 'Coco\\'s')}",
                "position": (None, center_y),
                "font_size": 80
            }
        ]
        intro_slide = self.create_slide(intro_text, duration=4.0)
        if intro_slide:
            slides.append(intro_slide)
            logging.info("Added intro slide")
        
        # 2. Create progress slide - "Let's Check Your Progress"
        progress_text = [
            {
                "text": "Let's Check your Progress",
                "position": (None, center_y),
                "font_size": 70
            },
            {
                "text": f"From {self.client_data.get('date_range', 'This Week')}",
                "position": (None, bottom_y),
                "font_size": 50
            }
        ]
        progress_slide = self.create_slide(progress_text, duration=4.0)
        if progress_slide:
            slides.append(progress_slide)
            logging.info("Added progress slide")
        
        # --- CONDITIONAL SLIDES ---
        
        # 3. Create workout count slide - ONLY if workout data exists
        if has_workout_data:
            workout_count_text = [
                {
                    "text": "You Trained",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{self.client_data.get('workouts_this_week', 0)} Times",
                    "position": (None, center_y),
                    "font_size": 90
                },
            ]
            workout_count_slide = self.create_slide(workout_count_text)
            if workout_count_slide:
                slides.append(workout_count_slide)
                logging.info("Added workout count slide")
        
        # Add more conditional slides following the same pattern
        # (I'm showing just a few key ones to keep the script manageable)
        
        # Weight slide - ONLY if weight data exists
        if has_weight_data:
            # Format weight values with one decimal place
            current_weight = f"{self.client_data.get('current_weight', 0):.1f}"
            weight_loss = f"{self.client_data.get('weight_loss', 0):.1f}"
            
            # Create a progress message based on weight loss
            if 'weight_loss' in self.client_data and self.client_data['weight_loss'] > 0:
                weight_progress_text = f"Weight's still trending down nicely. {weight_loss} kilos down already, v nice progress!"
            else:
                weight_progress_text = "Weight's trending well with your fitness goals!"
            
            weight_text = [
                {
                    "text": "You're now",
                    "position": (None, center_y - 50),
                    "font_size": 70,
                },
                {
                    "text": f"{current_weight} kgs",
                    "position": (None, center_y + 50),
                    "font_size": 80,
                },
                {
                    "text": weight_progress_text,
                    "position": (None, center_y + line_height*2),
                    "font_size": 40,
                },
                {
                    "text": "Keep doing what you're doing!",
                    "position": (None, center_y + line_height*3.5),
                    "font_size": 40,
                }
            ]
            weight_slide = self.create_slide(weight_text, duration=4.0)
            if weight_slide:
                slides.append(weight_slide)
                logging.info("Added weight slide")
        
        # Final motivational slide (always include)
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
            logging.info("Added motivational slide")
        
        # Combine all slides
        if not slides:
            logging.error("Error: No valid slides could be created.")
            return False
        
        logging.info(f"Combining {len(slides)} slides...")
        try:
            # Validate slides
            valid_slides = []
            for i, slide in enumerate(slides):
                if slide is not None and hasattr(slide, 'duration'):
                    try:
                        test_frame = slide.get_frame(0)
                        if test_frame is not None:
                            valid_slides.append(slide)
                            logging.info(f"Slide {i+1} validated")
                        else:
                            logging.warning(f"Slide {i+1} cannot produce frames, skipping")
                    except Exception as e:
                        logging.warning(f"Slide {i+1} validation failed: {e}")
                else:
                    logging.warning(f"Slide {i+1} is invalid, skipping")
            
            if not valid_slides:
                logging.error("Error: No valid slides to combine")
                return False
            
            logging.info(f"Proceeding with {len(valid_slides)} valid slides")
            
            # Store all clips to close later
            clips_to_close = valid_slides.copy()
            
            # Concatenate slides
            logging.info("Creating concatenated clip...")
            final_clip = concatenate_videoclips(valid_slides)
            clips_to_close.append(final_clip)
            logging.info(f"Final clip duration: {final_clip.duration}s")
            
            # Write the final video file
            logging.info(f"Writing video to {self.output_path}...")
            try:
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
                
                # Write the video
                final_clip.write_videofile(
                    self.output_path,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    preset='ultrafast',
                    threads=4,
                    bitrate='2000k',
                    ffmpeg_params=['-pix_fmt', 'yuv420p']
                )
                logging.info(f"Video successfully created and saved to {self.output_path}")
                return True
                
            except Exception as e:
                logging.exception(f"Error writing video file: {e}")
                return False
                
        except Exception as e:
            logging.exception(f"Error in video composition: {e}")
            return False
        finally:
            # Clean up resources
            if hasattr(self, 'background_video') and self.background_video is not None:
                try:
                    self.background_video.close()
                except:
                    pass

def main():
    try:
        # JSON file to use
        json_file = "Shannon_Birch_fitness_wrapped_data.json"
        
        if not os.path.exists(json_file):
            logging.error(f"JSON file not found: {json_file}")
            return
        
        # Create generator and build video
        generator = FitnessVideoGenerator(json_file)
        success = generator.build_video()
        
        if success:
            logging.info("\n" + "="*70)
            logging.info(f"{'SUCCESS!':^70}")
            logging.info("="*70)
            logging.info(f"Video successfully created for {generator.client_name}")
            logging.info(f"Video saved to: {generator.output_path}")
            logging.info("="*70)
        else:
            logging.error("\n" + "="*70)
            logging.error(f"{'FAILED':^70}")
            logging.error("="*70)
            logging.error("Video generation failed. Check logs for details.")
            logging.error("="*70)
            
    except Exception as e:
        logging.exception(f"Error in main function: {e}")

if __name__ == "__main__":
    main()