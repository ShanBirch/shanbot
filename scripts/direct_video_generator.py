#!/usr/bin/env python
"""
Direct Video Generator
---------------------
This script directly implements the necessary functionality to generate the fitness wrapped video
without relying on importing the simple_blue_video.py module.
"""

import os
import json
import argparse
from pathlib import Path
import tempfile
import shutil


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate fitness wrapped video directly')
    parser.add_argument('--input', type=str, default="Shannon_Birch_fitness_wrapped_data.json",
                        help='Input JSON file containing fitness wrapped data')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    args = parser.parse_args()

    verbose = args.verbose

    if verbose:
        print(f"Looking for input file: {args.input}")

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found")
        return 1

    try:
        # Install moviepy if not already installed
        try:
            import pip
            pip.main(['install', 'moviepy'])
            if verbose:
                print("Installed moviepy successfully")
        except Exception as e:
            print(f"Warning: Failed to install moviepy: {e}")
            print("Continuing anyway...")

        # Import required modules
        try:
            from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
            import moviepy.audio.fx.all as afx
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            if verbose:
                print("Successfully imported all required modules")
        except ImportError as e:
            print(f"Error importing required modules: {e}")
            return 1

        # Load client data
        try:
            with open(args.input, 'r') as f:
                client_data = json.load(f)
            if verbose:
                print(
                    f"Loaded client data for: {client_data.get('name', 'unknown client')}")
        except Exception as e:
            print(f"Error loading client data: {e}")
            return 1

        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Check if template video exists
        video_path = "blue2.mp4"
        if not os.path.exists(video_path):
            print(f"Error: Video file '{video_path}' not found.")
            fallback_video = "blue.mp4"
            if os.path.exists(fallback_video):
                print(f"Using fallback video: {fallback_video}")
                video_path = fallback_video
            else:
                print(
                    "No fallback video found. Please ensure blue2.mp4 or blue.mp4 exists.")
                return 1

        if verbose:
            print(f"Using video template: {video_path}")

        # Define function to create slides
        def create_slide_with_text(video_path, text_elements, duration=3.0):
            """Create a slide using the video template with text overlays"""
            if verbose:
                print(f"Creating slide from video: {video_path}")

            try:
                # Load the video clip
                video_clip = VideoFileClip(video_path).subclip(0, duration)

                if verbose:
                    print(
                        f"Successfully loaded video: {video_path}, duration: {video_clip.duration}s")
                    print(
                        f"Video dimensions: {video_clip.size[0]}x{video_clip.size[1]}")

                # Create text clips
                text_clips = []

                for text_elem in text_elements:
                    text = text_elem.get("text", "")
                    font_size = text_elem.get("font_size", 60)
                    position = text_elem.get("position", (None, None))
                    color = text_elem.get("color", 'white')

                    # Calculate horizontal position if None
                    if position[0] is None:
                        position = (video_clip.size[0] // 2, position[1])

                    if verbose:
                        print(f"Adding text: '{text}' at position {position}")

                    try:
                        text_clip = TextClip(text, fontsize=font_size, color=color,
                                             font='Arial-Bold', align='center')
                        text_clip = text_clip.set_position(
                            (position[0] - text_clip.size[0] // 2, position[1]))
                        text_clip = text_clip.set_duration(video_clip.duration)
                        text_clips.append(text_clip)

                        if verbose:
                            print(
                                f"✓ Successfully added text clip: '{text}' at {position}")
                    except Exception as e:
                        print(f"Error creating text clip: {e}")

                # Combine video and text clips
                if verbose:
                    print(
                        f"Creating composite clip with {len(text_clips)} text elements")

                composite_clip = CompositeVideoClip([video_clip] + text_clips)

                if verbose:
                    print("✓ Successfully created composite clip")

                return composite_clip

            except Exception as e:
                print(f"Error creating slide: {e}")
                return None

        # Get video dimensions for text positioning
        with VideoFileClip(video_path) as clip:
            width, height = clip.size

        # Define center positions and spacing
        center_x = width // 2
        center_y = height // 2
        line_height = 70  # Vertical space between lines

        if verbose:
            print(f"Video dimensions: {width}x{height}")
            print(f"Center position: ({center_x}, {center_y})")
            print("Starting slide creation...")

        # Create slides
        slides = []

        # 1. Intro slide
        intro_text = [
            {
                "text": "Your Week",
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": "At Coco's",
                "position": (None, center_y + line_height),
                "font_size": 90
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
                "position": (None, center_y - line_height),
                "font_size": 70
            },
            {
                "text": "From 3 March - 9 March",
                "position": (None, center_y + line_height),
                "font_size": 60
            }
        ]
        progress_slide = create_slide_with_text(video_path, progress_text)
        if progress_slide:
            slides.append(progress_slide)
            print("✓ Added progress slide")

        # 3. Weight progress slide (if available)
        if client_data.get('current_weight') and client_data.get('weight_change'):
            weight_text = [
                {
                    "text": "Current Weight",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{client_data['current_weight']} kg",
                    "position": (None, center_y),
                    "font_size": 60
                }
            ]

            # Add change information if available
            if client_data.get('weight_change'):
                weight_change = client_data['weight_change']
                weight_text.append({
                    "text": f"{'Down' if weight_change > 0 else 'Up'} {abs(weight_change):.1f} kg",
                    "position": (None, center_y + line_height),
                    "font_size": 60
                })

            weight_slide = create_slide_with_text(video_path, weight_text)
            if weight_slide:
                slides.append(weight_slide)
                print("✓ Added weight progress slide")

        # 4. Workout count slide (if available)
        if client_data.get('workouts_this_week') is not None:
            workout_count_text = [
                {
                    "text": "You Trained",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{client_data['workouts_this_week']} Times",
                    "position": (None, center_y),
                    "font_size": 60
                }
            ]
            workout_count_slide = create_slide_with_text(
                video_path, workout_count_text)
            if workout_count_slide:
                slides.append(workout_count_slide)
                print("✓ Added workout count slide")

        # 5. Workout stats slide (if available)
        if any(k in client_data for k in ['total_reps', 'total_sets', 'total_weight_lifted']):
            workout_stats_text = [
                {
                    "text": "Your Workout Stats",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                }
            ]

            # Add stats with vertical spacing
            y_offset = 0
            if client_data.get('total_reps') is not None:
                workout_stats_text.append({
                    "text": f"{client_data['total_reps']} Total Reps",
                    "position": (None, center_y + y_offset),
                    "font_size": 60
                })
                y_offset += line_height

            if client_data.get('total_sets') is not None:
                workout_stats_text.append({
                    "text": f"{client_data['total_sets']} Total Sets",
                    "position": (None, center_y + y_offset),
                    "font_size": 60
                })
                y_offset += line_height

            if client_data.get('total_weight_lifted') is not None:
                workout_stats_text.append({
                    "text": f"{client_data['total_weight_lifted']} kg Lifted",
                    "position": (None, center_y + y_offset),
                    "font_size": 60
                })

            workout_stats_slide = create_slide_with_text(
                video_path, workout_stats_text)
            if workout_stats_slide:
                slides.append(workout_stats_slide)
                print("✓ Added workout stats slide")

        # 6. Workload slide (if available)
        if client_data.get('workload_increase') is not None:
            workload_text = [
                {
                    "text": "Your Overall Workload",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": f"{abs(client_data['workload_increase']):.2f}%",
                    "position": (None, center_y),
                    "font_size": 60
                },
                {
                    "text": "(compared to last week)",
                    "position": (None, center_y + 0.5 * line_height),
                    "font_size": 40
                },
                {
                    "text": f"{'Higher' if client_data['workload_increase'] > 0 else 'Lower'}",
                    "position": (None, center_y + 1.5 * line_height),
                    "font_size": 60
                }
            ]
            workload_slide = create_slide_with_text(video_path, workload_text)
            if workload_slide:
                slides.append(workload_slide)
                print("✓ Added workload slide")

        # 6b. Nutrition intro slide (if available)
        if client_data.get('has_nutrition_data', False):
            nutrition_intro_text = [
                {
                    "text": "Let's Check Your",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": "Nutrition",
                    "position": (None, center_y + line_height),
                    "font_size": 90
                }
            ]
            nutrition_intro_slide = create_slide_with_text(
                video_path, nutrition_intro_text)
            if nutrition_intro_slide:
                slides.append(nutrition_intro_slide)
                print("✓ Added nutrition intro slide")

            # 6c. Calories slide (if available)
            if client_data.get('calories_consumed'):
                calories_text = [
                    {
                        "text": "Average Daily Intake",
                        "position": (None, center_y - line_height),
                        "font_size": 70
                    },
                    {
                        "text": f"{client_data['calories_consumed']} calories",
                        "position": (None, center_y + line_height),
                        "font_size": 60
                    }
                ]
                calories_slide = create_slide_with_text(
                    video_path, calories_text)
                if calories_slide:
                    slides.append(calories_slide)
                    print("✓ Added calories slide")

        # 6d. Steps slide (if available)
        if client_data.get('has_steps_data', False):
            steps_text = [
                {
                    "text": "Daily Steps",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": str(client_data['step_count']),
                    "position": (None, center_y),
                    "font_size": 90
                }
            ]
            steps_slide = create_slide_with_text(video_path, steps_text)
            if steps_slide:
                slides.append(steps_slide)
                print("✓ Added steps slide")

        # 6e. Sleep slide (if available)
        if client_data.get('has_sleep_data', False):
            sleep_text = [
                {
                    "text": "Sleep Check",
                    "position": (None, center_y - line_height),
                    "font_size": 70
                },
                {
                    "text": client_data['sleep_hours'],
                    "position": (None, center_y),
                    "font_size": 60
                }
            ]
            sleep_slide = create_slide_with_text(video_path, sleep_text)
            if sleep_slide:
                slides.append(sleep_slide)
                print("✓ Added sleep slide")

        # 7. Final message slide - Two 3-second slides back-to-back
        if client_data.get('personalized_message'):
            message = client_data['personalized_message']
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
            # Moved down by 1 line height
            start_y = center_y - \
                (total_lines * line_height * 0.7) // 2 + line_height

            for i, line in enumerate(message_lines):
                message_text.append({
                    "text": line,
                    "position": (None, start_y + i * line_height * 0.7),
                    "font_size": 45 if i == 0 else 40
                })

            # Create the slide with 3 seconds duration
            message_slide = create_slide_with_text(
                video_path, message_text, duration=3.0)
            if message_slide:
                slides.append(message_slide)

                # Add a duplicate slide to give appearance of 6 seconds
                duplicate_message_slide = create_slide_with_text(
                    video_path, message_text, duration=3.0)
                if duplicate_message_slide:
                    slides.append(duplicate_message_slide)
                    print(
                        "✓ Added final message slides (two 3-second slides back-to-back)")
                else:
                    print("✓ Added final message slide (3 second duration)")

        # 8. Motivational slide
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
            return 1

        # Concatenate all slides
        print(f"\nCombining {len(slides)} slides...")
        final_clip = concatenate_videoclips(slides)
        print("✓ Successfully combined slides")

        # Add background music if available
        music_files = []

        # Check current directory for mp3 files
        for file in os.listdir():
            if file.endswith('.mp3'):
                music_files.append(file)

        if music_files:
            try:
                # Use the first music file found
                music_file = music_files[0]
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

        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            threads=4,
            ffmpeg_params=['-pix_fmt', 'yuv420p']
        )

        print(f"\nFinal video saved to: {output_path}")
        return 0

    except Exception as e:
        print(f"Error generating video: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
