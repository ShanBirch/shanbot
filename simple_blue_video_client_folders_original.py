#!/usr/bin/env python
"""
Optimized version of simple_blue_video.py
This version includes performance improvements such as:
- Parallel processing for multiple client files
- Video caching to reduce loading times
- Font caching to speed up text rendering
- Optimized video export settings
- Memory optimization
"""
import sys
import os
import json
import argparse
import glob
import gc
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from moviepy.editor import *
import random
import traceback
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
import tempfile
import cv2
import shutil
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'video_generation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple_blue_video')

# Global caches
_VIDEO_CLIP_CACHE = {}
_FONT_CACHE = {}
_TEMP_FILES = []


def get_cached_video_clip(video_path, duration=3.0, audio=False):
    """Get a cached video clip to avoid reloading the same clip multiple times"""
    cache_key = f"{video_path}_{duration}_{audio}"
    if cache_key not in _VIDEO_CLIP_CACHE:
        _VIDEO_CLIP_CACHE[cache_key] = VideoFileClip(
            video_path, audio=audio).subclip(0, duration)
    return _VIDEO_CLIP_CACHE[cache_key].copy()


def get_cached_font(font_name, font_size):
    """Get a cached font to avoid reloading the same font multiple times"""
    cache_key = f"{font_name}_{font_size}"
    if cache_key not in _FONT_CACHE:
        try:
            _FONT_CACHE[cache_key] = ImageFont.truetype(font_name, font_size)
        except:
            # Fallback fonts in order of preference
            font_paths = [
                font_name,
                "arial.ttf",
                "Montserrat-VariableFont_wght.ttf",
                os.path.join("fonts", "Montserrat-VariableFont_wght.ttf"),
                os.path.join("media", "fonts",
                             "Montserrat-VariableFont_wght.ttf"),
                "DejaVuSans.ttf"
            ]
            for fallback in font_paths:
                try:
                    _FONT_CACHE[cache_key] = ImageFont.truetype(
                        fallback, font_size)
                    break
                except:
                    pass
            else:
                _FONT_CACHE[cache_key] = ImageFont.load_default()
    return _FONT_CACHE[cache_key]


def create_slide_with_text(video_path, text_elements, duration=3.0):
    """Create a slide using the video template with text overlays"""
    print(f"Creating slide from video: {video_path}")

    try:
        # Use cached video clip instead of loading new one every time
        video_clip = get_cached_video_clip(video_path, duration, audio=False)

        print(
            f"Successfully loaded video: {video_path}, duration: {video_clip.duration}s")
        print(f"Video dimensions: {video_clip.size[0]}x{video_clip.size[1]}")

        # Create text clips
        text_clips = []

        for text_elem in text_elements:
            text = text_elem.get("text", "")
            font_size = text_elem.get("font_size", 60)
            position = text_elem.get(
                "position", (video_clip.size[0]//2, video_clip.size[1]//2))

            print(f"Adding text: '{text}' at position {position}")

            try:
                # Create a transparent PIL Image for the text
                # Create a transparent image with the same size as the video
                txt_img = Image.new(
                    'RGBA', (video_clip.size[0], video_clip.size[1]), (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_img)

                # Use cached font instead of loading new one every time
                font = get_cached_font("arial.ttf", font_size)

                # If position has None for x, center horizontally
                x, y = position
                if x is None:
                    # Calculate text width to center it
                    text_width, text_height = draw.textsize(text, font=font)
                    x = (video_clip.size[0] - text_width) // 2

                # Draw text with shadow for better visibility
                shadow_offset = 2
                shadow_color = (0, 0, 0, 180)  # Semi-transparent black

                # Draw shadow first (slightly offset from the main text)
                draw.text((x + shadow_offset, y + shadow_offset),
                          text, font=font, fill=shadow_color)

                # Draw the main text
                draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

                # Convert PIL Image to numpy array
                txt_array = np.array(txt_img)

                # Create ImageClip from the numpy array
                txt_clip = ImageClip(txt_array, transparent=True)

                # Set the duration of the text clip to match the video
                txt_clip = txt_clip.set_duration(video_clip.duration)

                text_clips.append(txt_clip)
                print(
                    f"✓ Successfully added text clip: '{text}' at ({x}, {y})")

            except Exception as e:
                print(f"Error adding text '{text}': {e}")
                traceback.print_exc()

        # Create a CompositeVideoClip with the video and all text clips
        composite_clip = CompositeVideoClip([video_clip] + text_clips)
        print(f"Creating composite clip with {len(text_clips)} text elements")
        print("✓ Successfully created composite clip")

        return composite_clip

    except Exception as e:
        print(f"Error creating slide: {e}")
        traceback.print_exc()
        return None


def process_client_data(client_data_file, video_path, output_dir):
    """Process a single client's data and create a video"""
    print(f"\n{'='*80}")
    print(f"Processing client data from: {client_data_file}")
    print(f"{'='*80}")

    try:
        # Load client data
        with open(client_data_file, 'r') as f:
            client_data = json.load(f)

        # Set default business name if not present
        if 'business_name' not in client_data:
            client_data['business_name'] = "Coco's"

        print(f"Loaded client data for: {client_data['name']}\n")

        # Create slides
        print("Creating slides...")
        slides = []

        # Get video dimensions for text positioning
        temp_clip = get_cached_video_clip(video_path, 0.1, audio=False)
        width, height = temp_clip.size

        center_x = width // 2
        center_y = height // 2
        line_height = 100  # Approximate line height for text

        # 1. Intro slide
        intro_text = [
            {
                "text": "Your Week",
                "position": (None, center_y - line_height),
                "font_size": 100
            },
            {
                "text": f"At {client_data['business_name']}",
                "position": (None, center_y + line_height),
                "font_size": 80
            }
        ]
        intro_slide = create_slide_with_text(video_path, intro_text)
        if intro_slide:
            slides.append(intro_slide)
            print("✓ Added intro slide")

        # 2. Progress slide
        progress_text = [
            {
                "text": "Let's Check Your Progress",
                "position": (None, center_y - line_height//2),
                "font_size": 70
            },
            {
                "text": f"{client_data.get('date_range', 'This Week')}",
                "position": (None, center_y + line_height),
                "font_size": 50
            }
        ]
        progress_slide = create_slide_with_text(video_path, progress_text)
        if progress_slide:
            slides.append(progress_slide)
            print("✓ Added progress slide")

        # 3. Weight slide (if available)
        bodyweight_data = client_data.get('bodyweight_analysis', None)
        if bodyweight_data and bodyweight_data != "No data available":
            # Extract key information
            current_weight = client_data.get('current_weight', 'Not available')
            weight_change = client_data.get('weight_change', 'No change')

            weight_text = [
                {
                    "text": "Body Weight",
                    "position": (None, center_y - line_height*2),
                    "font_size": 80
                }
            ]

            if current_weight != 'Not available':
                weight_text.append({
                    "text": f"Current: {current_weight}",
                    "position": (None, center_y - line_height//2),
                    "font_size": 70
                })

            if weight_change != 'No change':
                weight_text.append({
                    "text": f"Change: {weight_change}",
                    "position": (None, center_y + line_height),
                    "font_size": 60
                })

            weight_slide = create_slide_with_text(video_path, weight_text)
            if weight_slide:
                slides.append(weight_slide)
                print("✓ Added weight slide")

        # 4. Nutrition slide - Part 1: Let's Check Your Nutrition
        if "nutrition_analysis" in client_data and client_data["nutrition_analysis"]:
            nutrition_text = client_data["nutrition_analysis"].get("text", "")
            nutrition_value = client_data["nutrition_analysis"].get(
                "value", "")

            # First nutrition slide - introduces the nutrition section
            nutrition_intro_slide_text = [
                {
                    "text": "Let's Check Your",
                    "font_size": 70,
                    # Reduced vertical spacing
                    "position": ("center", center_y - 50)
                },
                {
                    "text": "Nutrition",
                    "font_size": 100,
                    # Moved up to be closer to the first text
                    "position": ("center", center_y + 20)
                }
            ]
            nutrition_intro_slide = create_slide_with_text(
                video_path, nutrition_intro_slide_text)
            if nutrition_intro_slide:
                slides.append(nutrition_intro_slide)
                print("✓ Added nutrition intro slide")

            # Second nutrition slide - shows the daily intake information
            nutrition_details_slide_text = [
                {
                    "text": "Average Daily Intake",
                    "font_size": 70,
                    "position": ("center", center_y - 50)  # Positioned at top
                },
                {
                    "text": nutrition_value,
                    "font_size": 90,
                    # Good spacing below the header
                    "position": ("center", center_y + 50)
                }
            ]
            nutrition_details_slide = create_slide_with_text(
                video_path, nutrition_details_slide_text)
            if nutrition_details_slide:
                slides.append(nutrition_details_slide)
                print("✓ Added nutrition details slide")

        # 5. Steps slide
        if "steps_analysis" in client_data and client_data["steps_analysis"]:
            steps_text = client_data["steps_analysis"].get("text", "")
            steps_value = client_data["steps_analysis"].get("value", "")

            steps_slide_text = [
                {
                    "text": "Let's Check Your",
                    "font_size": 70,
                    # Reduced vertical spacing
                    "position": ("center", center_y - 50)
                },
                {
                    "text": "Steps",
                    "font_size": 100,
                    # Moved up to be closer to the first text
                    "position": ("center", center_y + 20)
                },
                {
                    "text": f"Daily Steps ({steps_value})",
                    "font_size": 60,
                    "position": ("center", center_y + 100)  # Adjusted position
                }
            ]
            steps_slide = create_slide_with_text(video_path, steps_slide_text)
            slides.append(steps_slide)

        # 6. Workout summary slide
        workout_data = client_data.get('workout_data', [])
        workout_count = len(workout_data)

        if workout_count > 0:
            # Count exercises and calculate total weight lifted
            exercise_count = 0
            total_weight = 0
            for workout in workout_data:
                for exercise in workout.get('exercises', []):
                    exercise_count += 1
                    for set_data in exercise.get('sets', []):
                        total_weight += set_data.get('weight', 0) * \
                            set_data.get('reps', 0)

            workout_text = [
                {
                    "text": "Workout Summary",
                    "position": (None, center_y - line_height*2),
                    "font_size": 80
                },
                {
                    "text": f"{workout_count} Workouts Completed",
                    "position": (None, center_y - line_height//2),
                    "font_size": 60
                }
            ]

            if exercise_count > 0:
                workout_text.append({
                    "text": f"{exercise_count} Exercises Performed",
                    "position": (None, center_y + line_height//2),
                    "font_size": 50
                })

            if total_weight > 0:
                workout_text.append({
                    "text": f"{int(total_weight)} kg Total Weight Lifted",
                    "position": (None, center_y + line_height*1.5),
                    "font_size": 50
                })

            workout_slide = create_slide_with_text(video_path, workout_text)
            if workout_slide:
                slides.append(workout_slide)
                print("✓ Added workout summary slide")

        # 6. Keep it up slide
        motivation_text = [
            {
                "text": "Keep Up The Great Work!",
                "position": (None, center_y - line_height//2),
                "font_size": 70
            },
            {
                "text": f"See You Next Week, {client_data['name'].split()[0]}!",
                "position": (None, center_y + line_height),
                "font_size": 60
            }
        ]
        motivation_slide = create_slide_with_text(video_path, motivation_text)
        if motivation_slide:
            slides.append(motivation_slide)
            print("✓ Added motivation slide")

        # Concatenate all slides
        if not slides:
            print("Error: No slides were created!")
            return False

        print(f"\nConcatenating {len(slides)} slides...")
        final_clip = concatenate_videoclips(slides)
        print("✓ Successfully concatenated slides")

        # Add background music if available
        music_dir = Path("media/music")
        if not music_dir.exists():
            music_dir = Path("music")

        music_files = []
        if music_dir.exists():
            music_files = list(music_dir.glob("*.mp3"))

        if music_files:
            try:
                # Choose a random music file
                music_file = random.choice(music_files)
                print(f"\nAdding background music: {music_file}")

                # Load the music file
                background_music = AudioFileClip(str(music_file)).subclip(
                    0, final_clip.duration)

                # Set music volume to 50%
                background_music = background_music.volumex(0.5)

                # Add music to video
                final_clip = final_clip.set_audio(background_music)
                print("✓ Added background music")
            except Exception as e:
                print(f"Warning: Could not add background music: {e}")
                print("Continuing without music...")
        else:
            print("\nNo music files found. Video will be silent.")

        # Write the final video
        client_filename = client_data['name'].replace(' ', '_')
        output_path = output_dir / f"{client_filename}_weekly_checkin.mp4"
        print(f"\nWriting video to {output_path}...")

        # Optimized video export settings
        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='fast',    # Faster encoding
            threads=8,        # More threads for parallel processing
            # Balance quality and speed
            ffmpeg_params=['-pix_fmt', 'yuv420p', '-crf', '23']
        )

        print(f"\nSuccess! Video created: {output_path}")

        # Explicitly clean up to free memory
        for slide in slides:
            slide.close()
        final_clip.close()

        # Force garbage collection
        gc.collect()

        return True

    except Exception as e:
        print(f"Error processing client data: {str(e)}")
        traceback.print_exc()
        return False


def process_client_files_parallel(client_files, video_path, output_dir, max_workers=3):
    """Process multiple client files in parallel"""
    results = {'success': 0, 'failed': 0}
    total_files = len(client_files)

    print(
        f"\nProcessing {total_files} client files with {max_workers} parallel workers")

    # Use ProcessPoolExecutor for CPU-bound tasks
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_client_data, client_file, video_path,
                                   output_dir): client_file for client_file in client_files}

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            client_file = futures[future]
            client_name = os.path.basename(client_file).split(
                '_fitness_wrapped_data.json')[0]
            try:
                print(
                    f"\nProgress: {i}/{total_files} ({int(i/total_files*100)}%)")
                if future.result():
                    results['success'] += 1
                    print(f"✓ Successfully processed {client_name}")
                else:
                    results['failed'] += 1
                    print(f"✗ Failed to process {client_name}")
            except Exception as e:
                print(f"Error processing {client_name}: {e}")
                results['failed'] += 1

    return results


def clean_up_resources():
    """Clean up cached resources to free memory"""
    global _VIDEO_CLIP_CACHE, _FONT_CACHE, _TEMP_FILES

    # Close all cached video clips
    for key, clip in _VIDEO_CLIP_CACHE.items():
        try:
            clip.close()
        except:
            pass

    # Clear caches
    _VIDEO_CLIP_CACHE = {}
    _FONT_CACHE = {}

    # Remove temporary files
    for temp_file in _TEMP_FILES:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass

    _TEMP_FILES = []

    # Force garbage collection
    gc.collect()


def main():
    parser = argparse.ArgumentParser(
        description='Generate fitness wrapped videos for clients using client folder structure')
    parser.add_argument('--client', type=str,
                        help='Client name to generate video for')
    parser.add_argument('--all', action='store_true',
                        help='Generate videos for all clients')
    parser.add_argument('--date', type=str,
                        help='Date to use for data (YYYY-MM-DD format)')
    parser.add_argument('--output', type=str,
                        help='Output directory for videos')

    args = parser.parse_args()

    # Process date if provided
    data_date = None
    if args.date:
        try:
            data_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)

    # Process base directory for setup
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Ensure logs directory exists
    logs_dir = base_dir / 'logs'
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)

    # First, make sure we have client folder structure set up
    from setup_client_folders import setup_client_folders
    setup_client_folders()

    # Generate video for a specific client
    if args.client:
        output_path = args.output if args.output else None
        generate_blue_video(args.client, output_path, data_date)

    # Generate videos for all clients
    elif args.all:
        # Get all client folders
        clients_dir = base_dir / "clients"
        if not clients_dir.exists():
            logger.error(
                "No clients directory found. Please run setup_client_folders.py first.")
            sys.exit(1)

        client_folders = [f.name for f in clients_dir.iterdir() if f.is_dir()]

        # Process each client
        for client_name in client_folders:
            try:
                output_path = None
                if args.output:
                    output_path = os.path.join(
                        args.output, f"{client_name}_weekly_checkin.mp4")

                generate_blue_video(client_name, output_path, data_date)

            except Exception as e:
                logger.error(f"Error generating video for {client_name}: {e}")

    # If no arguments provided, generate for Shannon Birch as a test
    else:
        # Create a test video for Shannon Birch
        logger.info(
            "No client specified. Generating test video for Shannon Birch...")
        output_dir = base_dir / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "Shannon_Birch_test_video.mp4"
        generate_blue_video("Shannon_Birch", str(output_path), data_date)


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        # Always clean up resources, even if there's an error
        clean_up_resources()
