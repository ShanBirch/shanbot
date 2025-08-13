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

        # 4. Workload slide - Moved before workout count
        if client_data.get('workload_increase', 0) != 0:
            workload_text = [
                {
                    "text": "Your Overall Workload",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{abs(client_data['workload_increase'])}%",
                    "position": (None, center_y + line_height*0.5),
                    "font_size": 60
                },
                {
                    "text": "(compared to last week)",
                    "position": (None, center_y + line_height*1.2),
                    "font_size": 35  # Smaller font size
                },
                {
                    "text": "Lower" if client_data['workload_increase'] < 0 else "Higher",
                    "position": (None, center_y + line_height*2),
                    "font_size": 50
                }
            ]
            workload_slide = create_slide_with_text(video_path, workload_text)
            if workload_slide:
                slides.append(workload_slide)
                print("✓ Added workload slide")

        # 5. Workout count slide
        if client_data.get('workouts_this_week', 0) > 0:
            workout_text = [
                {
                    "text": "You Trained",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{client_data['workouts_this_week']} Times",
                    "position": (None, center_y),
                    "font_size": 90
                }
            ]
            workout_slide = create_slide_with_text(video_path, workout_text)
            if workout_slide:
                slides.append(workout_slide)
                print("✓ Added workout count slide")

        # 6. Workout stats slide - Adjusted positioning
        if client_data.get('has_workout_data', False):
            # Check if all stats are zero
            total_reps = client_data.get('total_reps', 0)
            total_sets = client_data.get('total_sets', 0)
            total_weight_lifted = client_data.get('total_weight_lifted', 0)

            # Only show the slide if at least one stat is greater than zero
            if total_reps > 0 or total_sets > 0 or total_weight_lifted > 0:
                stats_text = [
                    {
                        "text": "Your Workout Stats",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": f"{total_reps} Total Reps",
                        # Moved down to where sets was
                        "position": (None, center_y + line_height*0.5),
                        "font_size": 50
                    },
                    {
                        "text": f"{total_sets} Total Sets",
                        # Moved down one position
                        "position": (None, center_y + line_height*1.5),
                        "font_size": 50
                    },
                    {
                        "text": f"{total_weight_lifted} kg Lifted",
                        # Moved down one position
                        "position": (None, center_y + line_height*2.5),
                        "font_size": 50
                    }
                ]
                stats_slide = create_slide_with_text(video_path, stats_text)
                if stats_slide:
                    slides.append(stats_slide)
                    print("✓ Added workout stats slide")
            else:
                print("Skipping workout stats slide because all stats are zero")

        # NOTE: Exercise level intro slide moved to be conditional on top_exercises slide
        # Only show if top_exercises is available

        # 6. Top exercises slide - Adjusted spacing between title and exercises
        if client_data.get('top_exercises'):
            # Filter out exercises with 0% improvement
            filtered_exercises = [exercise for exercise in client_data['top_exercises']
                                  if exercise.get('improvement', 0) != 0]

            # Only show exercise slides if client actually has workouts
            # and there are actually exercises with improvements
            if filtered_exercises and client_data.get('workouts_this_week', 0) > 0:
                # 5c. Exercise level intro slide (NEW) - Only shown if top_exercises exists with non-zero improvements
                exercise_intro_text = [
                    {
                        "text": "You took several",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": "exercises to the",
                        "position": (None, center_y),
                        "font_size": 70
                    },
                    {
                        "text": "next level!",
                        "position": (None, center_y + line_height),
                        "font_size": 70
                    }
                ]
                exercise_intro_slide = create_slide_with_text(
                    video_path, exercise_intro_text)
                if exercise_intro_slide:
                    slides.append(exercise_intro_slide)
                    print("✓ Added exercise level intro slide")

                # Now add the top exercises slide
                exercises_text = [
                    {
                        "text": "Your Top Exercises",
                        # Keep title position
                        "position": (None, center_y - line_height*3.5),
                        "font_size": 70
                    }
                ]

                # Increase the gap between title and first exercise
                # Move the starting position for exercises down to where the percentage increase was
                # This creates a bigger gap after the title
                start_y = center_y - line_height*1.5
                spacing = line_height * 0.8  # Keep the same spacing between items

                for i, exercise in enumerate(filtered_exercises[:3]):
                    exercises_text.extend([
                        {
                            "text": f"{exercise['name']}",
                            # Double spacing between exercises
                            "position": (None, start_y + i*spacing*2),
                            "font_size": 50
                        },
                        {
                            "text": f"{abs(exercise['improvement'])}% Increase",
                            # Position improvement text below exercise name
                            "position": (None, start_y + i*spacing*2 + spacing),
                            "font_size": 40
                        }
                    ])

                exercises_slide = create_slide_with_text(
                    video_path, exercises_text)
                if exercises_slide:
                    slides.append(exercises_slide)
                    print("✓ Added top exercises slide")
            else:
                print(
                    "Skipping exercise improvement slides - no valid exercises with improvements found")

        # 6b. Nutrition intro slide (NEW)
        if client_data.get('has_nutrition_data', False):
            # Check if values are default
            calories_consumed = client_data.get('calories_consumed', '')
            protein_consumed = client_data.get('protein_consumed', '')
            fats_consumed = client_data.get('fats_consumed', '')
            carbs_consumed = client_data.get('carbs_consumed', '')

            # Check if nutrition data is default values
            default_calories = calories_consumed in [
                "2700", "2600", "Not Recorded"]
            default_macros = (protein_consumed == "Tracking" or protein_consumed == "Not Recorded" or
                              fats_consumed == "Tracking" or fats_consumed == "Not Recorded" or
                              carbs_consumed == "Tracking" or carbs_consumed == "Not Recorded")

            # Only show nutrition slides if we have non-default data
            if not (default_calories and default_macros):
                nutrition_intro_text = [
                    {
                        "text": "Let's Check Your",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": "Nutrition",
                        # Changed from center_y + line_height to center_y
                        "position": (None, center_y),
                        "font_size": 90  # Font size already matches
                    }
                ]
                nutrition_intro_slide = create_slide_with_text(
                    video_path, nutrition_intro_text)
                if nutrition_intro_slide:
                    slides.append(nutrition_intro_slide)
                    print("✓ Added nutrition intro slide")

                # 6c. Calories slide (NEW) - Only show if calories aren't default
                if not default_calories:
                    calories_text = [
                        {
                            "text": "Average Daily Intake",  # Changed from "Average Daily Intake"
                            "position": (None, center_y - line_height),
                            "font_size": 70
                        },
                        {
                            # Kept "calories" text
                            "text": f"{calories_consumed} calories",
                            "position": (None, center_y),
                            "font_size": 90
                        }
                    ]
                    calories_slide = create_slide_with_text(
                        video_path, calories_text)
                    if calories_slide:
                        slides.append(calories_slide)
                        print("✓ Added calories slide")
                else:
                    print(
                        "Skipping calories slide because default values were detected")
            else:
                print("Skipping nutrition slides because default values were detected")

        # 6d. Steps slide (NEW)
        if client_data.get('has_steps_data', False):
            # Check if highest_steps is visible (not "not visible" or "Not visible")
            highest_steps = client_data.get(
                'highest_steps', client_data.get('step_count', ''))

            # Skip if steps are default values (10000 is a common default)
            default_steps = highest_steps in [
                "10000", "Not visible", "not visible", "", "Not Recorded"]

            if highest_steps and not default_steps:
                steps_text = [
                    {
                        "text": "Highest Step Day",  # Changed from "Daily Steps"
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        # Use highest_steps with fallback to step_count
                        "text": str(highest_steps),
                        "position": (None, center_y),
                        "font_size": 90
                    }
                ]
                steps_slide = create_slide_with_text(video_path, steps_text)
                if steps_slide:
                    slides.append(steps_slide)
                    print("✓ Added highest steps slide")
            else:
                print(
                    "Skipping highest steps slide because steps data is default or not visible")

        # 6e. Sleep slide (NEW)
        if client_data.get('has_sleep_data', False):
            sleep_hours = client_data.get('sleep_hours', '')

            # Skip default values
            default_sleep = sleep_hours in [
                "8-9 Hours Most Nights", "7-9 hours", "", "Not Recorded"]

            if sleep_hours and not default_sleep:
                sleep_text = [
                    {
                        "text": "Sleep Check",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": sleep_hours,
                        "position": (None, center_y),
                        "font_size": 60
                    }
                ]
                sleep_slide = create_slide_with_text(video_path, sleep_text)
                if sleep_slide:
                    slides.append(sleep_slide)
                    print("✓ Added sleep slide")
            else:
                print("Skipping sleep slide because data is default or missing")

        # 7. Final message slide - Reduced duration to 3 seconds and will duplicate
        message = client_data.get('personalized_message', '')

        # Only add message slide if there is an actual message
        if message and message.strip():
            words = message.split()
            message_lines = []
            current_line = []

            for word in words:
                current_line.append(word)
                if len(current_line) == 5:  # Force 5 words per line
                    message_lines.append(' '.join(current_line))
                    current_line = []

            # Add any remaining words
            if current_line:
                message_lines.append(' '.join(current_line))

            message_text = []
            total_lines = len(message_lines)

            # Adjust the starting position to be between previous and current
            start_y = center_y - (total_lines * line_height * 0.7) // 2 + \
                line_height  # Moved down by 1 line height

            for i, line in enumerate(message_lines):
                message_text.append({
                    "text": line,
                    "position": (None, start_y + i * line_height * 0.7),
                    "font_size": 45 if i == 0 else 40
                })

            # Create the slide with 3 seconds duration instead of 6
            message_slide = create_slide_with_text(
                video_path, message_text, duration=3.0)
            if message_slide:
                # Add the same slide twice
                slides.append(message_slide)
                slides.append(message_slide)
                print("✓ Added final message slide (3 second duration, played twice)")
        else:
            print("Skipping personalized message slide because message is empty")

        # Create most improved slide (to be added later)
        most_improved_slide = None
        if client_data.get('most_improved_client', {}).get('name'):
            most_improved_name = client_data['most_improved_client']['name']
            improvement_percentage = client_data['most_improved_client']['improvement_percentage']

            # Make spacing more compact to match intro slide
            compact_spacing = line_height * 0.6  # Adjusted spacing for two text elements

            # Make sure all clients see the most improved information with compact spacing
            most_improved_text = [
                {
                    "text": "This Week's Most Improved",
                    "position": (None, center_y - compact_spacing),
                    "font_size": 70
                },
                {
                    "text": f"{improvement_percentage:.1f}% increased workload",
                    "position": (None, center_y + compact_spacing),
                    "font_size": 60
                }
            ]

            most_improved_slide = create_slide_with_text(
                video_path, most_improved_text)
            if most_improved_slide:
                print("✓ Created most improved client slide (will be added later)")

        # Add the "This Week's Most Improved" slide if it was created
        if most_improved_slide:
            slides.append(most_improved_slide)
            print("✓ Added most improved client slide")

        # Special most improved slide with custom video - add for ALL clients, not just the most improved
        # Path to the custom most improved video
        most_improved_video_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\mostimproved.mp4"

        # Check if the video file exists
        if os.path.exists(most_improved_video_path):
            try:
                # Create text for the most improved member slide
                member_name_text = [
                    {
                        "text": most_improved_name,  # Use the most improved client's name from JSON
                        "position": (None, center_y),
                        "font_size": 90
                    }
                ]

                # Create slide with the custom video and member's name
                most_improved_member_slide = create_slide_with_text(
                    most_improved_video_path, member_name_text)
                if most_improved_member_slide:
                    slides.append(most_improved_member_slide)
                    print(
                        "✓ Added special most improved member slide with custom video")
            except Exception as e:
                print(f"Error creating most improved member slide: {str(e)}")
                traceback.print_exc()
        else:
            print(
                f"Warning: Most improved video file not found at {most_improved_video_path}")

        # 8. Motivational slide - Adjusted positioning
        motivational_text = [
            {
                "text": "Keep Moving!",
                "position": (None, center_y - line_height),  # Moved up
                "font_size": 90
            }
        ]
        motivational_slide = create_slide_with_text(
            video_path, motivational_text)
        if motivational_slide:
            slides.append(motivational_slide)
            print("✓ Added motivational slide")

        # Check if we have any slides
        if not slides:
            print("Error: No slides were created!")
            return False

        # Concatenate all slides
        print(f"\nCombining {len(slides)} slides...")
        final_clip = concatenate_videoclips(slides)
        print("✓ Successfully combined slides")

        # Add background music if available
        music_files = []
        # Update the path to include the "music" subfolder
        shanbot_music_dir = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\music"

        # Seed random with current timestamp for better randomness
        random.seed(datetime.now().timestamp())

        # Check shanbot directory for mp3 files
        if os.path.exists(shanbot_music_dir):
            for file in os.listdir(shanbot_music_dir):
                if file.endswith('.mp3'):
                    music_files.append(os.path.join(shanbot_music_dir, file))

            if music_files:
                try:
                    # Print available music files for debugging
                    print(f"\nFound {len(music_files)} music files:")
                    for i, music in enumerate(music_files):
                        print(f"  {i+1}. {os.path.basename(music)}")

                    # Randomly select a music file from the shanbot folder
                    music_file = random.choice(music_files)
                    print(
                        f"\nSelected background music: {os.path.basename(music_file)}")
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
                print(
                    f"\nNo music files found in {shanbot_music_dir}. Looking elsewhere...")

                # Fallback to checking current directory for mp3 files
                for file in os.listdir():
                    if file.endswith('.mp3'):
                        music_files.append(file)

                # Check output directory for mp3 files
                if os.path.exists('output'):
                    for file in os.listdir('output'):
                        if file.endswith('.mp3'):
                            music_files.append(os.path.join('output', file))

                if music_files:
                    try:
                        # Randomly select a music file
                        music_file = random.choice(music_files)
                        print(
                            f"\nAdding random background music from: {music_file}")
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
        else:
            print(
                f"\nShanbot directory not found at {shanbot_music_dir}. Looking elsewhere for music...")

            # Fallback to checking current directory for mp3 files
            for file in os.listdir():
                if file.endswith('.mp3'):
                    music_files.append(file)

            # Check output directory for mp3 files
            if os.path.exists('output'):
                for file in os.listdir('output'):
                    if file.endswith('.mp3'):
                        music_files.append(os.path.join('output', file))

            if music_files:
                try:
                    # Randomly select a music file
                    music_file = random.choice(music_files)
                    print(
                        f"\nAdding random background music from: {music_file}")
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
        client_filename = client_data['name'].replace(' ', '_')
        output_path = output_dir / f"{client_filename}_weekly_checkin.mp4"
        print(f"\nWriting video to {output_path}...")

        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            threads=4,
            ffmpeg_params=['-pix_fmt', 'yuv420p']
        )

        print(f"\nSuccess! Video created: {output_path}")
        return True

    except Exception as e:
        print(f"Error processing client data: {str(e)}")
        traceback.print_exc()
        return False


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate fitness wrapped videos for multiple clients')
    parser.add_argument('--upload', action='store_true',
                        help='Upload the videos to Google Drive after creation')
    parser.add_argument('--folder', type=str,
                        help='Google Drive folder name to upload to')
    parser.add_argument('--date', type=str,
                        help='Date to look for client files (YYYY-MM-DD format). If not provided, uses today\'s date.')
    args = parser.parse_args()

    # Set target date for finding client files (today by default)
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            today_str = target_date.strftime('%Y-%m-%d')
            yesterday = target_date - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            two_days_ago = target_date - timedelta(days=2)
            two_days_ago_str = two_days_ago.strftime('%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format. Please use YYYY-MM-DD format.")
            return 1
    else:
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        yesterday = today - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        two_days_ago = today - timedelta(days=2)
        two_days_ago_str = two_days_ago.strftime('%Y-%m-%d')

    print(f"Looking for client data files...")

    # Set the current directory to shanbot directory for finding video files
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if blue2.mp4 exists
    video_path = os.path.join(script_dir, "blue2.mp4")
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        # Check if blue.mp4 exists as fallback
        fallback_video = os.path.join(script_dir, "blue.mp4")
        if os.path.exists(fallback_video):
            print(f"Using fallback video: {fallback_video}")
            video_path = fallback_video
        else:
            print("No fallback video found. Please ensure blue2.mp4 or blue.mp4 exists.")
            return 1

    # Create output directory if it doesn't exist
    output_dir = Path(os.path.join(script_dir, "output"))
    output_dir.mkdir(exist_ok=True)

    # Find all client data files in order of priority
    client_files = []

    # Set the JSON files directory to C:\\Users\\Shannon
    # Use the specified path exclusively
    json_files_dir = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\output\\checkin_reviews"

    # First look for files with today's date
    today_files = glob.glob(os.path.join(
        json_files_dir, f"*_{today_str}_fitness_wrapped_data.json"))
    if today_files:
        print(
            f"Found {len(today_files)} client files from today ({today_str}).")
        client_files.extend(today_files)

    # If not enough files, look for yesterday's files
    if not client_files:
        yesterday_files = glob.glob(
            os.path.join(json_files_dir, f"*_{yesterday_str}_fitness_wrapped_data.json"))
        if yesterday_files:
            print(
                f"Found {len(yesterday_files)} client files from yesterday ({yesterday_str}).")
            client_files.extend(yesterday_files)

    # If still not enough, look for files from two days ago
    if not client_files:
        two_days_ago_files = glob.glob(
            os.path.join(json_files_dir, f"*_{two_days_ago_str}_fitness_wrapped_data.json"))
        if two_days_ago_files:
            print(
                f"Found {len(two_days_ago_files)} client files from two days ago ({two_days_ago_str}).")
            client_files.extend(two_days_ago_files)

    # If still no files, look for any matching client files
    if not client_files:
        any_files = glob.glob(os.path.join(
            json_files_dir, "*_fitness_wrapped_data.json"))
        if any_files:
            print(
                f"No recent date-specific files found. Using {len(any_files)} available client files.")
            client_files.extend(any_files)

    if not client_files:
        print("No client data files found! Please run the checkin.py script first to generate client data.")
        return 1

    print(f"Total client files found: {len(client_files)}")

    # Process each client file
    successful_videos = 0
    failed_videos = 0

    for client_file in client_files:
        print(f"\nProcessing file: {client_file}")
        success = process_client_data(client_file, video_path, output_dir)
        if success:
            successful_videos += 1
        else:
            failed_videos += 1

    # Final summary
    print(f"\n{'='*80}")
    print(f"Video Generation Summary")
    print(f"{'='*80}")
    print(f"Total client files processed: {len(client_files)}")
    print(f"Successfully generated videos: {successful_videos}")
    print(f"Failed video generations: {failed_videos}")

    if args.upload and successful_videos > 0:
        # Import the upload module
        upload_script = Path('upload_to_drive.py')
        if not upload_script.exists():
            print("\nError: upload_to_drive.py script not found!")
            print("Please ensure the script is in the same directory.")
            return 1

        try:
            print("\nUploading videos to Google Drive...")

            # Process only the MP4 files we just created
            for client_file in client_files:
                client_name = os.path.basename(client_file).split(
                    '_fitness_wrapped_data.json')[0]
                video_file = output_dir / f"{client_name}_weekly_checkin.mp4"

                if not video_file.exists():
                    print(
                        f"Warning: Video file for {client_name} not found, skipping upload.")
                    continue

                print(f"Uploading {video_file}...")

                # Build the command to run the upload script
                cmd = [sys.executable, str(upload_script), str(video_file)]

                # Add folder name if provided
                if args.folder:
                    cmd.append(args.folder)

                # Run the upload script as a subprocess
                import subprocess
                result = subprocess.run(cmd, capture_output=True, text=True)

                # Print the output from the upload script
                print(result.stdout)

                if result.returncode != 0:
                    print(
                        f"Error during upload of {client_name}'s video: {result.stderr}")

        except Exception as e:
            print(f"\nError uploading to Google Drive: {e}")
            traceback.print_exc()
            return 1

    if successful_videos > 0:
        print(f"\nVideos have been saved to the '{output_dir}' directory.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
