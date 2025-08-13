#!/usr/bin/env python
import sys
import os
import json
import argparse
import glob
import math
from datetime import datetime, timedelta
from pathlib import Path
from moviepy.editor import *
import random
import traceback
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def create_slide_with_text(video_path, text_elements, duration=3.0):
    """Create a slide using the video template with text overlays"""
    print(f"Creating slide from video: {video_path}")

    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path).subclip(0, duration)
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
                print(
                    f"✓ Successfully added text clip: '{text}' at ({x_pos}, {y_pos})")

            except Exception as text_error:
                print(f"Error creating text clip: {str(text_error)}")
                traceback.print_exc()
                continue

        # Combine video with text overlays
        if text_clips:
            print(
                f"Creating composite clip with {len(text_clips)} text elements")
            final_clip = CompositeVideoClip([video_clip] + text_clips)
            print("✓ Successfully created composite clip")
            return final_clip
        else:
            print("Warning: No text clips were created, returning video clip only")
            return video_clip

    except Exception as e:
        print(f"Error creating slide: {str(e)}")
        traceback.print_exc()
        return None


def process_client_data(client_data_file, video_path, output_dir):
    """Process a single client data file and create a video for that client"""
    print(f"\n{'='*80}")
    print(f"Processing client data from: {client_data_file}")
    print(f"{'='*80}")

    try:
        # Load client data
        with open(client_data_file, 'r') as f:
            client_data = json.load(f)

        print(f"Loaded client data for: {client_data['name']}\n")

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
                "font_size": 70  # Reduced from 100 to match "You Trained" style
            },
            {
                "text": f"At {client_data['business_name']}",
                # Changed from center_y + line_height to center_y
                "position": (None, center_y),
                "font_size": 90  # Increased from 80 to match "X Times" style
            }
        ]

        intro_slide = create_slide_with_text(video_path, intro_text)
        if intro_slide:
            slides.append(intro_slide)
            print("✓ Added intro slide")

        # Check if client has any meaningful data
        has_weight_data = (client_data.get('has_weight_data', False) and
                           'current_weight' in client_data and
                           client_data.get('current_weight') is not None and
                           client_data.get('current_weight') != "Not Recorded")
        has_workout_data = client_data.get('workouts_this_week', 0) > 0
        has_exercise_data = client_data.get('has_exercise_data', False)
        has_nutrition_data = client_data.get('has_nutrition_data', False)
        has_steps_data = client_data.get('has_steps_data', False)
        has_sleep_data = client_data.get('has_sleep_data', False)

        # Only show progress slide if there's actual data to show
        if has_weight_data or has_workout_data or has_exercise_data or has_nutrition_data or has_steps_data or has_sleep_data:
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
            # Use Python's datetime to create a Monday-Sunday date range if not provided
            if 'date_range' not in client_data:
                today = datetime.now()
                # Find the most recent Monday (0 = Monday in weekday())
                monday = today - timedelta(days=today.weekday())
                sunday = monday + timedelta(days=6)
                date_format = "%d %b"  # Format: 01 Jan
                progress_text[1]["text"] = f"{monday.strftime(date_format)} - {sunday.strftime(date_format)}"

            progress_slide = create_slide_with_text(video_path, progress_text)
            if progress_slide:
                slides.append(progress_slide)
                print("✓ Added progress slide")
        else:
            print("Skipping progress slide because client has no meaningful data")

        # 3. Weight progress slide (if weight data exists)
        if (client_data.get('has_weight_data', False) and
            'current_weight' in client_data and
                client_data.get('current_weight') is not None and
                client_data.get('current_weight') != "Not Recorded"):
            try:
                # Convert to float to ensure it's a valid number
                current_weight = float(client_data['current_weight'])
                weight_loss = float(client_data.get('weight_loss', 0))

                weight_text = [
                    {
                        "text": "Current Weight",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": f"{math.floor(current_weight)} kg",
                        "position": (None, center_y),
                        "font_size": 90
                    },
                    {
                        "text": f"Overall Weight Loss: {math.floor(weight_loss)}+ kg",
                        "position": (None, center_y + line_height),
                        "font_size": 60
                    }
                ]

                weight_slide = create_slide_with_text(video_path, weight_text)
                if weight_slide:
                    slides.append(weight_slide)
                    print("✓ Added weight progress slide")
            except (ValueError, TypeError):
                print("Skipping weight slide because weight data is invalid")
        else:
            print("Skipping weight slide because weight data is missing")

        # 4. Training consistency slide
        if has_workout_data:
            workouts_this_week = client_data['workouts_this_week']
            training_text = [
                {
                    "text": "You Trained",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{workouts_this_week} Times",
                    "position": (None, center_y),
                    "font_size": 90
                }
            ]

            training_slide = create_slide_with_text(video_path, training_text)
            if training_slide:
                slides.append(training_slide)
                print("✓ Added training consistency slide")
        else:
            print("Skipping training consistency slide because no workout data")

        # 5. Nutrition slide
        if (has_nutrition_data and
            client_data.get("nutrition_tracking_days", 0) > 0 and
            ('calories_consumed' in client_data) and
            client_data.get('calories_consumed') != "Not Recorded" and
                client_data.get('calories_consumed') is not None):
            try:
                # Convert to float to ensure it's a valid number
                calories = float(client_data['calories_consumed'])
                protein = float(client_data.get('protein_consumed', 0))

                nutrition_text = [
                    {
                        "text": "Nutrition Tracking",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": f"{int(calories)} Calories",
                        "position": (None, center_y),
                        "font_size": 90
                    },
                    {
                        "text": f"{int(protein)}g Protein Daily",
                        "position": (None, center_y + line_height),
                        "font_size": 60
                    }
                ]

                nutrition_slide = create_slide_with_text(
                    video_path, nutrition_text)
                if nutrition_slide:
                    slides.append(nutrition_slide)
                    print("✓ Added nutrition slide")
            except (ValueError, TypeError):
                print("Skipping nutrition slide because data is invalid")
        else:
            print("Skipping nutrition slide because no nutrition data")

        # 6. Steps slide
        if (has_steps_data and
            'step_count' in client_data and
                client_data.get('step_count') != "Not Recorded" and
                client_data.get('step_count') is not None):
            try:
                # Convert to float to ensure it's a valid number
                steps = float(client_data['step_count'])
                highest_steps = float(client_data.get('highest_steps', 0))

                steps_text = [
                    {
                        "text": "Daily Steps",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": f"{int(steps)} Steps",
                        "position": (None, center_y),
                        "font_size": 90
                    },
                    {
                        "text": f"Highest: {int(highest_steps)} Steps",
                        "position": (None, center_y + line_height),
                        "font_size": 60
                    }
                ]

                steps_slide = create_slide_with_text(video_path, steps_text)
                if steps_slide:
                    slides.append(steps_slide)
                    print("✓ Added steps slide")
            except (ValueError, TypeError):
                print("Skipping steps slide because data is invalid")
        else:
            print("Skipping steps slide because no steps data")

        # 7. Sleep slide
        if (has_sleep_data and
            'sleep_hours' in client_data and
                client_data.get('sleep_hours') != "Not Recorded" and
                client_data.get('sleep_hours') is not None):
            try:
                # Convert to float to ensure it's a valid number
                sleep = float(client_data['sleep_hours'])

                sleep_text = [
                    {
                        "text": "Sleep Hours",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": f"{sleep:.1f} Hours",
                        "position": (None, center_y),
                        "font_size": 90
                    }
                ]

                sleep_slide = create_slide_with_text(video_path, sleep_text)
                if sleep_slide:
                    slides.append(sleep_slide)
                    print("✓ Added sleep slide")
            except (ValueError, TypeError):
                print("Skipping sleep slide because data is invalid")
        else:
            print("Skipping sleep slide because no sleep data")

        # 8. Most improved exercise slide
        if has_exercise_data and 'top_exercises' in client_data and client_data['top_exercises']:
            top_exercise = client_data['top_exercises'][0]

            exercise_text = [
                {
                    "text": "Most Improved Exercise",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{top_exercise['name']}",
                    "position": (None, center_y),
                    "font_size": 75  # Smaller because exercise names can be long
                },
                {
                    "text": f"{int(top_exercise['improvement'])}% Increase",
                    "position": (None, center_y + line_height),
                    "font_size": 60
                }
            ]

            exercise_slide = create_slide_with_text(video_path, exercise_text)
            if exercise_slide:
                slides.append(exercise_slide)
                print("✓ Added most improved exercise slide")
        else:
            print("Skipping most improved exercise slide because no exercise data")

        # 9. Personal message slide
        if 'personalized_message' in client_data and client_data['personalized_message']:
            message_text = [
                {
                    "text": "Personal Message",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{client_data['personalized_message']}",
                    "position": (None, center_y),
                    "font_size": 50
                }
            ]

            message_slide = create_slide_with_text(video_path, message_text)
            if message_slide:
                slides.append(message_slide)
                print("✓ Added personal message slide")
        else:
            print("Skipping personal message slide because no message")

        # Create final video file by concatenating all slides
        if slides:
            client_name = client_data['name'].replace(' ', '_')
            output_file = output_dir / f"{client_name}_weekly_checkin.mp4"
            temp_file = output_dir / f"{client_name}_weekly_checkin_temp.mp4"

            # Combine all slides
            print(f"Concatenating {len(slides)} slides...")
            final_video = concatenate_videoclips(slides)

            # Write video to temporary file first
            print(f"Writing video to temporary file: {temp_file}")
            final_video.write_videofile(
                str(temp_file), codec="libx264", fps=30, audio=False, threads=4)

            # Close the video to free resources
            final_video.close()

            # Remove any existing output file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                    print(f"Removed existing file: {output_file}")
                except Exception as e:
                    print(f"Warning: Could not remove existing file: {e}")

            # Rename the temporary file to the final filename
            try:
                os.rename(temp_file, output_file)
                print(f"✓ Successfully created video: {output_file}")
                return True
            except Exception as e:
                print(f"Error renaming temporary file: {e}")
                return False
        else:
            print("✗ No slides were created. Failed to generate video.")
            return False

    except Exception as e:
        print(f"✗ Error processing client data: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Main function that only processes Kristy Cooper's data file"""
    # Path to the blue background video
    video_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "blue2.mp4")

    # Output directory - use the same directory as the script
    output_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Kristy Cooper's file path
    kristy_file = os.path.join(
        "C:\\Users\\Shannon", "Kristy_Cooper_2025-03-22_fitness_wrapped_data.json")

    # Check if file exists
    if not os.path.exists(kristy_file):
        # Also check if it's in the shanbot directory
        shanbot_kristy_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Kristy_Cooper_2025-03-22_fitness_wrapped_data.json"
        )

        if os.path.exists(shanbot_kristy_file):
            kristy_file = shanbot_kristy_file
        else:
            print(
                f"Error: Kristy Cooper's data file not found at {kristy_file} or in the shanbot directory.")
            return 1

    print(f"Processing Kristy Cooper's data from: {kristy_file}")

    # Process the file
    success = process_client_data(kristy_file, video_path, output_dir)

    if success:
        print("\n✓ Successfully generated video for Kristy Cooper!")
        return 0
    else:
        print("\n✗ Failed to generate video for Kristy Cooper.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
