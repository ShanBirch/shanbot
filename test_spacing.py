#!/usr/bin/env python
"""
Simple test script to generate a video for Shannon Birch
This script deliberately keeps the needed parts simple
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont


def create_slide(video_path, text_elements, duration=3.0):
    """Create a slide with text overlays using PIL for text rendering"""
    print(f"Creating slide with {len(text_elements)} text elements")

    # Load the video template
    video = VideoFileClip(video_path).subclip(0, duration)
    width, height = video.size

    # Create text clips
    text_clips = []
    temp_files = []

    for i, text_elem in enumerate(text_elements):
        # Extract text properties
        text = text_elem.get("text", "")
        font_size = text_elem.get("font_size", 70)
        position = text_elem.get("position", ("center", "center"))

        # Create a temporary transparent image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Try to load the font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype(
                    "Montserrat-VariableFont_wght.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        if position[0] == "center":
            x_pos = width // 2 - text_width // 2
        else:
            x_pos = position[0]

        if position[1] == "center":
            y_pos = height // 2 - text_height // 2
        else:
            y_pos = position[1]

        # Draw text with shadow for better visibility
        shadow_offset = 2
        shadow_color = (0, 0, 0, 180)  # Semi-transparent black

        # Draw shadow first
        draw.text((x_pos + shadow_offset, y_pos + shadow_offset),
                  text, font=font, fill=shadow_color)

        # Draw the main text
        draw.text((x_pos, y_pos), text, font=font, fill=(255, 255, 255, 255))

        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        temp_file.close()
        temp_files.append(temp_file.name)

        # Create clip from the image
        txt_clip = ImageClip(temp_file.name).set_duration(duration)

        text_clips.append(txt_clip)
        print(f"Added text: '{text}' at position {(x_pos, y_pos)}")

    # Combine video and text clips
    final_clip = CompositeVideoClip([video] + text_clips)

    # Clean up temporary files when done
    def cleanup_temp_files():
        for file in temp_files:
            try:
                os.unlink(file)
            except:
                pass

    final_clip.cleanup = cleanup_temp_files

    return final_clip


def generate_test_video():
    """Generate a test video for Shannon Birch to check text spacing"""

    # Set up paths
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    video_path = base_dir / "blue2.mp4"
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "spacing_test.mp4"

    # Check if template exists
    if not video_path.exists():
        print(f"Error: Video template {video_path} not found")
        return 1

    # Load test data for Shannon Birch
    client_data_path = base_dir / "clients" / "Shannon_Birch" / \
        "data" / "Shannon_Birch_2025-03-10_fitness_wrapped_data.json"

    if not client_data_path.exists():
        print(f"Error: Client data {client_data_path} not found")
        return 1

    with open(client_data_path, 'r') as f:
        client_data = json.load(f)

    # Create the slides
    slides = []

    # Video dimensions (for positioning text)
    temp_video = VideoFileClip(str(video_path)).subclip(0, 0.1)
    width, height = temp_video.size
    center_y = height // 2
    temp_video.close()

    # Test slide 1: Let's Check Your Nutrition
    nutrition_intro_slide = create_slide(
        str(video_path),
        [
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
        ],
        duration=3  # Standard duration
    )
    slides.append(nutrition_intro_slide)

    # Test slide 2: Nutrition Details (Average Daily Intake)
    nutrition_value = client_data.get(
        "nutrition_analysis", {}).get("value", "2500 calories")

    nutrition_details_slide = create_slide(
        str(video_path),
        [
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
        ],
        duration=3  # Standard duration
    )
    slides.append(nutrition_details_slide)

    # Combine all slides
    print(f"Combining {len(slides)} slides...")
    final_clip = concatenate_videoclips(slides)

    # Write the final video
    print(f"Writing video to {output_path}...")
    final_clip.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        fps=24
    )

    # Clean up any temporary files
    for slide in slides:
        if hasattr(slide, 'cleanup'):
            slide.cleanup()

    print(f"Video saved to {output_path}")
    return 0


if __name__ == "__main__":
    print("Generating test video to check text spacing...")
    start_time = time.time()
    result = generate_test_video()
    end_time = time.time()
    print(
        f"Process completed in {end_time - start_time:.2f} seconds with exit code {result}")
