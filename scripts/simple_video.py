#!/usr/bin/env python
import sys
import os
import json
import argparse
from pathlib import Path
from moviepy.editor import *
import moviepy.audio.fx as afx
import random
import traceback
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("Starting video generator with blue2.mp4 background...")

# Load the JSON data
json_path = "Shannon_Birch_fitness_wrapped_data.json"
with open(json_path, 'r') as f:
    client_data = json.load(f)

print(f"Loaded client data for: {client_data.get('name', 'Unknown Client')}")

# Set up directories
base_dir = Path(".")
template_dir = base_dir / "templates"
font_dir = base_dir / "fonts"
output_dir = base_dir / "output"
music_dir = base_dir / "music"
temp_dir = base_dir / "temp"

# Ensure directories exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

# Set output path
client_name = client_data.get("name", "client").replace(" ", "_")
output_path = output_dir / f"{client_name}_fitness_wrapped_simple.mp4"

print(f"Will save video to: {output_path}")

# Choose a background music file
mp3_files = list(music_dir.glob("*.mp3"))
if mp3_files:
    music_file = random.choice(mp3_files)
    print(f"Selected music: {music_file.name}")
else:
    music_file = None
    print("No music files found.")

# Font setup
font_path = font_dir / "NunitoSans-Bold.ttf"
if not font_path.exists():
    alt_font_path = Path("C:/Windows/Fonts/Arial.ttf")
    if alt_font_path.exists():
        font_path = alt_font_path
    else:
        print("Warning: No font found. Using default.")

print(f"Using font: {font_path}")


def create_text_image(text, size=(1920, 1080), font_size=60, color=(255, 255, 255)):
    # Create a black image
    img = Image.new('RGB', size, color=(0, 0, 128))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position to center the text
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2

    # Draw text
    draw.text((x, y), text, font=font, fill=color)

    return np.array(img)


def create_slide_with_text(video_path, text_elements, duration=3.0):
    """Create a slide using the video template with text overlays"""
    print(f"Creating slide with duration: {duration}s")

    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path).subclip(0, duration)

        # Create text clips
        text_clips = []

        for text_elem in text_elements:
            text = text_elem.get("text", "")
            font_size = text_elem.get("font_size", 60)
            position = text_elem.get(
                "position", (video_clip.size[0]//2, video_clip.size[1]//2))

            try:
                # Create a transparent PIL Image for the text
                txt_img = Image.new(
                    'RGBA', (video_clip.size[0], video_clip.size[1]), (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_img)

                # Try to use Arial font, fallback to default if not available
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                # Get text size
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Calculate position
                x_pos = position[0] if position[0] is not None else (
                    video_clip.size[0] - text_width) // 2
                # Center vertically around the specified y position
                y_pos = position[1] - text_height // 2

                # Draw text with white color
                draw.text((x_pos, y_pos), text, font=font,
                          fill=(255, 255, 255, 255))

                # Convert PIL image to numpy array
                txt_array = np.array(txt_img)

                # Create VideoClip from the image array
                txt_clip = ImageClip(txt_array, duration=duration)
                text_clips.append(txt_clip)

            except Exception as text_error:
                print(f"Error creating text clip: {str(text_error)}")
                traceback.print_exc()
                continue

        # Combine video with text overlays
        if text_clips:
            final_clip = CompositeVideoClip([video_clip] + text_clips)
            return final_clip
        else:
            return video_clip

    except Exception as e:
        print(f"Error creating slide: {str(e)}")
        traceback.print_exc()
        return None


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate fitness wrapped video')
    parser.add_argument('--client', type=str, default="Shannon_Birch",
                        help='Client name to generate video for')
    args = parser.parse_args()

    client_name = args.client

    # Check if blue2.mp4 exists
    video_path = "blue2.mp4"
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        # Check if blue.mp4 exists as fallback
        fallback_video = "blue.mp4"
        if os.path.exists(fallback_video):
            print(f"Using fallback video: {fallback_video}")
            video_path = fallback_video
        else:
            print("No fallback video found. Please ensure blue2.mp4 or blue.mp4 exists.")
            return 1

    # Check if client data exists
    json_file = f"{client_name}_fitness_wrapped_data.json"
    if not os.path.exists(json_file):
        print(f"Error: Client data file '{json_file}' not found.")
        return 1

    # Load client data
    with open(json_file, 'r') as f:
        client_data = json.load(f)

    print(f"Loaded client data for: {client_data['name']}\n")

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Create slides
    print("Creating slides...")
    slides = []

    # Get video dimensions for text positioning
    with VideoFileClip(video_path) as clip:
        width, height = clip.size

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
            "text": f"From {client_data.get('date_range', 'This Week')}",
            "position": (None, center_y + line_height),
            "font_size": 50
        }
    ]
    progress_slide = create_slide_with_text(video_path, progress_text)
    if progress_slide:
        slides.append(progress_slide)
        print("✓ Added progress slide")

    # 3. Weight progress slide (if weight data exists)
    if client_data.get('has_weight_data', True):
        weight_text = [
            {
                "text": "Current Weight",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": f"{client_data.get('current_weight', 0)} kg",
                "position": (None, center_y),
                "font_size": 90
            },
            {
                "text": f"Down {client_data.get('weight_loss', 0)} kg",
                "position": (None, center_y + line_height),
                "font_size": 60
            }
        ]
        weight_slide = create_slide_with_text(video_path, weight_text)
        if weight_slide:
            slides.append(weight_slide)
            print("✓ Added weight progress slide")

    # 4. Workout count slide
    if client_data.get('workouts_this_week', 0) > 0:
        workout_text = [
            {
                "text": "You Trained",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": f"{client_data.get('workouts_this_week', 0)} Times",
                "position": (None, center_y),
                "font_size": 90
            }
        ]
        workout_slide = create_slide_with_text(video_path, workout_text)
        if workout_slide:
            slides.append(workout_slide)
            print("✓ Added workout count slide")

    # 5. Workout stats slide
    if client_data.get('has_workout_data', False):
        stats_text = [
            {
                "text": "Your Workout Stats",
                "position": (None, center_y - line_height*1.5),
                "font_size": 70
            },
            {
                "text": f"{client_data.get('total_reps', 0)} Total Reps",
                "position": (None, center_y - line_height*0.5),
                "font_size": 50
            },
            {
                "text": f"{client_data.get('total_sets', 0)} Total Sets",
                "position": (None, center_y + line_height*0.5),
                "font_size": 50
            },
            {
                "text": f"{client_data.get('total_weight_lifted', 0)} kg Lifted",
                "position": (None, center_y + line_height*1.5),
                "font_size": 50
            }
        ]
        stats_slide = create_slide_with_text(video_path, stats_text)
        if stats_slide:
            slides.append(stats_slide)
            print("✓ Added workout stats slide")

    # 6. Workload slide
    if client_data.get('workload_increase', 0) != 0:
        workload_text = [
            {
                "text": "Your Overall Workload",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": f"{abs(client_data.get('workload_increase', 0))}%",
                "position": (None, center_y + line_height*0.5),
                "font_size": 60
            },
            {
                "text": "(compared to last week)",
                "position": (None, center_y + line_height*1.2),
                "font_size": 35
            },
            {
                "text": "Lower" if client_data.get('workload_increase', 0) < 0 else "Higher",
                "position": (None, center_y + line_height*2),
                "font_size": 50
            }
        ]
        workload_slide = create_slide_with_text(video_path, workload_text)
        if workload_slide:
            slides.append(workload_slide)
            print("✓ Added workload slide")

    # 7. Top exercises slide
    if client_data.get('top_exercises'):
        exercises_text = [
            {
                "text": "Your Top Exercises",
                "position": (None, center_y - line_height*2),
                "font_size": 70
            }
        ]

        start_y = center_y - line_height*0.5
        spacing = line_height * 0.8

        for i, exercise in enumerate(client_data['top_exercises'][:3]):
            exercises_text.extend([
                {
                    "text": f"{exercise['name']}",
                    "position": (None, start_y + i*spacing*2),
                    "font_size": 50
                },
                {
                    "text": f"{abs(exercise['improvement'])}% Increase",
                    "position": (None, start_y + i*spacing*2 + spacing),
                    "font_size": 40
                }
            ])

        exercises_slide = create_slide_with_text(video_path, exercises_text)
        if exercises_slide:
            slides.append(exercises_slide)
            print("✓ Added top exercises slide")

    # 8. Nutrition slide
    if client_data.get('has_nutrition_data', False):
        nutrition_text = [
            {
                "text": "Nutrition",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": f"Average Calories: {client_data.get('calories_consumed', 'N/A')}",
                "position": (None, center_y + line_height*0.5),
                "font_size": 50
            }
        ]
        nutrition_slide = create_slide_with_text(video_path, nutrition_text)
        if nutrition_slide:
            slides.append(nutrition_slide)
            print("✓ Added nutrition slide")

    # 9. Steps slide
    if client_data.get('has_steps_data', False):
        steps_text = [
            {
                "text": "Daily Steps",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": f"{client_data.get('step_count', 'N/A')}",
                "position": (None, center_y + line_height*0.5),
                "font_size": 60
            }
        ]
        steps_slide = create_slide_with_text(video_path, steps_text)
        if steps_slide:
            slides.append(steps_slide)
            print("✓ Added steps slide")

    # 10. Sleep slide
    if client_data.get('has_sleep_data', False):
        sleep_text = [
            {
                "text": "Sleep",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": f"{client_data.get('sleep_hours', 'N/A')}",
                "position": (None, center_y + line_height*0.5),
                "font_size": 50
            }
        ]
        sleep_slide = create_slide_with_text(video_path, sleep_text)
        if sleep_slide:
            slides.append(sleep_slide)
            print("✓ Added sleep slide")

    # 11. Conclusion slide with DOUBLE DURATION (6 seconds)
    conclusion_text = [
        {
            "text": "Keep Up The Great Work!",
            "position": (None, center_y - line_height),
            "font_size": 70
        },
        {
            "text": f"See You Next Week {client_data['name'].split()[0]}!",
            "position": (None, center_y + line_height),
            "font_size": 60
        }
    ]
    # Note the 6.0 duration for conclusion slide
    conclusion_slide = create_slide_with_text(
        video_path, conclusion_text, duration=6.0)
    if conclusion_slide:
        slides.append(conclusion_slide)
        print("✓ Added conclusion slide (6 second duration)")

    # Concatenate all slides
    if not slides:
        print("Error: No slides were created.")
        return 1

    # Create final video
    print("\nConcatenating slides...")
    final_clip = concatenate_videoclips(slides)
    print(f"✓ Created final video (Duration: {final_clip.duration:.1f}s)")

    # Find music files
    music_files = []
    music_dirs = ['.', 'music', 'output']

    for dir_path in music_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith('.mp3'):
                    music_files.append(os.path.join(dir_path, file))

    if music_files:
        try:
            # Choose a random music file
            music_file = random.choice(music_files)
            print(f"\nAdding background music from: {music_file}")
            background_music = AudioFileClip(music_file)

            # Loop or trim music to match video length
            if background_music.duration < final_clip.duration:
                background_music = afx.audio_loop(
                    background_music, duration=final_clip.duration)
            else:
                background_music = background_music.subclip(
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
    output_path = output_dir / \
        f"{client_data['name'].replace(' ', '_')}_fitness_wrapped.mp4"
    print(f"\nWriting video to {output_path}...")

    # Optimized settings for faster rendering
    final_clip.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        fps=24,  # Lower fps for faster rendering
        preset='ultrafast',  # Fastest encoding preset
        threads=4,  # Use multiple threads
        bitrate='2000k'  # Lower bitrate for faster encoding
    )

    print(f"\n✅ Video created successfully: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Clean up temp files
for temp_file in temp_dir.glob("temp_*.png"):
    try:
        os.remove(temp_file)
    except:
        pass
