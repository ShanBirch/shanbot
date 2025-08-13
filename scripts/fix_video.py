#!/usr/bin/env python

import json
import os
import random
import sys
from pathlib import Path
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile

print("Starting enhanced video fix script...")

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
output_path = output_dir / f"{client_name}_fitness_wrapped_fixed.mp4"

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

# Function to add text to an image


def add_text_to_image(image_path, text_elements, output_path):
    try:
        # Open image
        img = Image.open(image_path).convert("RGBA")
        width, height = img.size

        # Create drawing context
        draw = ImageDraw.Draw(img)

        # Process text elements
        for element in text_elements:
            text = element.get("text", "")
            font_size = element.get("font_size", 36)
            position = element.get("position", (width//2, height//2))
            color = element.get("color", (255, 255, 255))

            # Load font
            try:
                font = ImageFont.truetype(str(font_path), font_size)
            except:
                font = ImageFont.load_default()

            # Get text dimensions - updated for newer PIL versions
            try:
                # For newer PIL versions
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
            except AttributeError:
                # Fallback for older PIL versions
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except:
                    # If all else fails
                    text_width, text_height = font_size * \
                        len(text) // 2, font_size

            # Center text if position is None or has None component
            if position[0] is None:
                position = (width//2 - text_width//2, position[1])
            if position[1] is None:
                position = (position[0], height//2 - text_height//2)

            # Draw text
            draw.text(position, text, fill=color, font=font)

        # Save image
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error adding text to image: {str(e)}")
        return False


# Create clips from templates with overlay data
clips = []

# Dictionary to map template base names to handler functions
template_handlers = {
    "template_intro": lambda: [
        {"text": f"{client_data.get('name', 'Client')}'s", "position": (
            None, 180), "font_size": 54},
        {"text": "FITNESS WRAPPED", "position": (None, 250), "font_size": 72},
        {"text": client_data.get('date_range', 'Past Week'), "position": (
            None, 350), "font_size": 36}
    ],
    "template_conclusion": lambda: [
        {"text": client_data.get('personalized_message', 'Great work this week!'), "position": (
            None, 180), "font_size": 32}
    ],
    "template_current_weight": lambda: [
        {"text": f"Current Weight: {client_data.get('current_weight', 'N/A')}kg", "position": (
            None, 200), "font_size": 48},
        {"text": f"Weight Lost: {client_data.get('weight_loss', 'N/A')}kg", "position": (
            None, 280), "font_size": 48}
    ],
    "template_weight_goal": lambda: [
        {"text": f"Goal: {client_data.get('weight_goal', 'N/A')}kg",
         "position": (None, 200), "font_size": 48},
        {"text": "You're making progress!",
            "position": (None, 280), "font_size": 42}
    ],
    "template_workout_count": lambda: [
        {"text": str(client_data.get('workouts_this_week', '0')),
         "position": (None, 240), "font_size": 120},
        {"text": "WORKOUTS COMPLETED", "position": (
            None, 350), "font_size": 42}
    ],
    "template_strength_gains": lambda: [
        {"text": "TOP EXERCISES", "position": (None, 150), "font_size": 54},
        {"text": client_data.get('top_exercises', [{}])[0].get(
            'name', 'Exercise 1'), "position": (None, 230), "font_size": 36},
        {"text": f"+{client_data.get('top_exercises', [{}])[0].get('improvement', '0')}%", "position": (
            None, 280), "font_size": 42},
        {"text": client_data.get('top_exercises', [{}, {}])[1].get(
            'name', 'Exercise 2'), "position": (None, 350), "font_size": 36},
        {"text": f"+{client_data.get('top_exercises', [{}, {}])[1].get('improvement', '0')}%", "position": (
            None, 400), "font_size": 42}
    ],
}

# Process all templates
template_files = list(template_dir.glob("*.png"))
print(f"Found {len(template_files)} template files.")

# Sort templates in a logical order
template_order = [
    "template_intro",
    "template_workout_count",
    "template_current_weight",
    "template_weight_goal",
    "template_strength_gains",
    "template_conclusion"
]

# Filter and sort templates
ordered_templates = []
for template_name in template_order:
    matches = [t for t in template_files if template_name in t.name.lower()]
    if matches:
        ordered_templates.append(matches[0])

# Add any remaining templates not in our ordered list
for template in template_files:
    if not any(template_name in template.name.lower() for template_name in template_order):
        ordered_templates.append(template)

print(f"Ordered {len(ordered_templates)} templates.")

# Create clips from templates
for template_file in ordered_templates:
    # Determine which handler to use
    handler_key = None
    for key in template_handlers:
        if key in template_file.name.lower():
            handler_key = key
            break

    # Get text elements for this template
    text_elements = []
    if handler_key and handler_key in template_handlers:
        text_elements = template_handlers[handler_key]()

    # Create temp file for text overlay
    temp_output = temp_dir / f"temp_{template_file.name}"

    # Add text to image
    if text_elements:
        success = add_text_to_image(template_file, text_elements, temp_output)
        if success:
            # Use the temp file with text
            img_path = str(temp_output)
        else:
            # Fall back to original template
            img_path = str(template_file)
    else:
        # No text to add, use original template
        img_path = str(template_file)

    # Create clip
    duration = 4.0  # 4 seconds per slide
    img_clip = ImageClip(img_path).set_duration(duration)
    clips.append(img_clip)

if not clips:
    print("No clips created. Aborting.")
    sys.exit(1)

print(f"Created {len(clips)} image clips.")

# Concatenate clips
try:
    print("Concatenating clips...")
    final_clip = concatenate_videoclips(clips, method="compose")

    # Add music if available
    if music_file and music_file.exists():
        print("Adding background music...")
        audio = AudioFileClip(str(music_file))

        # Loop or trim audio to match video length
        if audio.duration < final_clip.duration:
            print(
                f"Looping audio to match video duration of {final_clip.duration:.2f} seconds")
            audio = audio.fx(vfx.loop, duration=final_clip.duration)
        else:
            print(
                f"Trimming audio to match video duration of {final_clip.duration:.2f} seconds")
            audio = audio.subclip(0, final_clip.duration)

        final_clip = final_clip.set_audio(audio)

    print(f"Writing video file to {output_path}...")
    final_clip.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )

    print(f"Video successfully created at {output_path}")
    print(f"Open with: explorer {output_path}")
except Exception as e:
    print(f"Error creating video: {str(e)}")
    sys.exit(1)

# Clean up temp files
for temp_file in temp_dir.glob("temp_*.png"):
    try:
        os.remove(temp_file)
    except:
        pass
