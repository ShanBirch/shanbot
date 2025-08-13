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
import logging
import re

# Progressive Overload AI Integration
try:
    from progressive_overload_video_integration import enhance_video_data_with_progressions, ProgressionVideoIntegrator
    from enhanced_video_slides import create_progression_slides
    PROGRESSIVE_OVERLOAD_AVAILABLE = True
    print("✓ Progressive Overload AI integration loaded successfully")
except ImportError as e:
    print(f"⚠️  Progressive Overload AI integration not available: {e}")
    PROGRESSIVE_OVERLOAD_AVAILABLE = False


def get_text_dimensions(text, font):
    """Get the width and height of text with a given font"""
    # Create a temporary image to measure text
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def get_optimal_font_size(text, max_width, max_height, max_font_size=100, min_font_size=20):
    """Calculate optimal font size to fit text within given dimensions"""
    for font_size in range(max_font_size, min_font_size - 1, -2):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        width, height = get_text_dimensions(text, font)

        if width <= max_width and height <= max_height:
            return font_size, font

    # If no size fits, return minimum size
    try:
        font = ImageFont.truetype("arial.ttf", min_font_size)
    except:
        font = ImageFont.load_default()
    return min_font_size, font


def wrap_text(text, max_width, font, max_lines=3):
    """Wrap text to fit within specified width, return list of lines"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = current_line + [word]
        test_text = ' '.join(test_line)
        width, _ = get_text_dimensions(test_text, font)

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word is too long, add it anyway
                lines.append(word)

            # Stop if we've reached max lines
            if len(lines) >= max_lines:
                break

    # Add remaining words
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))

    return lines


def shorten_exercise_name(exercise_name, max_length=25):
    """Shorten exercise names that are too long for display"""
    if len(exercise_name) <= max_length:
        return exercise_name

    # Common abbreviations for fitness terms
    abbreviations = {
        'Dumbbell': 'DB',
        'Barbell': 'BB',
        'Machine': 'Mach',
        'Cable': 'Cable',
        'Seated': 'Seated',
        'Standing': 'Stand',
        'Incline': 'Inc',
        'Decline': 'Dec',
        'Press': 'Press',
        'Extension': 'Ext',
        'Curl': 'Curl',
        'Pulldown': 'PD',
        'Pullover': 'PO',
        'Lateral': 'Lat',
        'Overhead': 'OH',
        'Romanian': 'RDL',
        'Bulgarian': 'Bulg',
        'Single': 'Single',
        'Double': 'Double',
        'Reverse': 'Rev',
        'Close': 'Close',
        'Wide': 'Wide',
        'Narrow': 'Narrow'
    }

    # Apply abbreviations
    shortened = exercise_name
    for full_word, abbrev in abbreviations.items():
        if full_word in shortened:
            shortened = shortened.replace(full_word, abbrev)
            if len(shortened) <= max_length:
                return shortened

    # If still too long, truncate and add "..."
    if len(shortened) > max_length:
        return shortened[:max_length-3] + "..."

    return shortened


def create_slide_with_text(video_path, text_elements, duration=3.0):
    """Create a slide using the video template with text overlays and animations"""
    print(f"Creating slide from video: {video_path}")

    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path).subclip(0, duration)
        print(
            f"Successfully loaded video: {video_path}, duration: {video_clip.duration}s")
        print(f"Video dimensions: {video_clip.size[0]}x{video_clip.size[1]}")

        # Get video dimensions for calculations
        video_width, video_height = video_clip.size
        margin = 40  # Margin from edges
        safe_width = video_width - (2 * margin)
        safe_height = video_height - (2 * margin)

        # Create text clips with animations
        text_clips = []

        for i, text_elem in enumerate(text_elements):
            text = text_elem.get("text", "")
            font_size = text_elem.get("font_size", 60)
            position = text_elem.get(
                "position", (video_width//2, video_height//2))
            animation_type = text_elem.get("animation", "fade_in")
            delay = text_elem.get("delay", i * 0.3)

            print(
                f"Adding animated text: '{text}' at position {position} with {animation_type}")

            try:
                # Calculate maximum text area (leave space for other text elements)
                max_text_width = safe_width
                max_text_height = safe_height // max(len(text_elements), 1)

                # Get optimal font size for this text
                optimal_font_size, font = get_optimal_font_size(
                    text, max_text_width, max_text_height,
                    max_font_size=font_size, min_font_size=20
                )

                # Check if text needs wrapping
                text_width, text_height = get_text_dimensions(text, font)

                if text_width > max_text_width:
                    # Wrap text if it's too wide
                    wrapped_lines = wrap_text(text, max_text_width, font)
                    if len(wrapped_lines) > 1:
                        # Recalculate font size for wrapped text
                        total_height = len(wrapped_lines) * text_height * 1.2
                        if total_height > max_text_height:
                            optimal_font_size, font = get_optimal_font_size(
                                max(wrapped_lines, key=len), max_text_width,
                                max_text_height // len(wrapped_lines),
                                max_font_size=optimal_font_size, min_font_size=15
                            )
                            text_width, text_height = get_text_dimensions(
                                max(wrapped_lines, key=len), font)
                else:
                    wrapped_lines = [text]

                print(
                    f"Using font size {optimal_font_size} for text: '{text}'")
                if len(wrapped_lines) > 1:
                    print(f"Text wrapped into {len(wrapped_lines)} lines")

                # Create a transparent PIL Image for the text
                txt_img = Image.new(
                    'RGBA', (video_width, video_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(txt_img)

                # Calculate positions for all lines
                total_text_height = len(wrapped_lines) * text_height * 1.2

                # Adjust starting Y position if needed
                if position[1] is not None:
                    start_y = position[1] - (total_text_height // 2)
                else:
                    start_y = (video_height - total_text_height) // 2

                # Ensure text doesn't go off screen
                start_y = max(margin, min(
                    start_y, video_height - total_text_height - margin))

                for line_idx, line in enumerate(wrapped_lines):
                    line_width, line_height = get_text_dimensions(line, font)

                    # Calculate X position for this line
                    if position[0] is not None:
                        x_pos = position[0] - (line_width // 2)
                    else:
                        x_pos = (video_width - line_width) // 2

                    # Ensure text doesn't go off screen horizontally
                    x_pos = max(margin, min(
                        x_pos, video_width - line_width - margin))

                    y_pos = start_y + (line_idx * line_height * 1.2)

                    # Draw text with shadow
                    # Shadow
                    draw.text((x_pos + 2, y_pos + 2), line,
                              font=font, fill=(0, 0, 0, 128))
                    # Main text
                    draw.text((x_pos, y_pos), line, font=font,
                              fill=(255, 255, 255, 255))

                # Convert PIL image to numpy array
                txt_array = np.array(txt_img)

                # Create base VideoClip from the image array
                base_txt_clip = ImageClip(txt_array, duration=duration)

                # Apply animation based on type
                if animation_type == "fade_in":
                    txt_clip = base_txt_clip.crossfadein(0.5).set_start(delay)

                elif animation_type == "slide_from_left":
                    def slide_left_position(t):
                        progress = min(1.0, t * 2)
                        start_x = -max_text_width
                        return (start_x + (0 - start_x) * progress, 0)

                    txt_clip = (base_txt_clip
                                .set_position(slide_left_position)
                                .crossfadein(0.3)
                                .set_start(delay))

                elif animation_type == "slide_from_right":
                    def slide_right_position(t):
                        progress = min(1.0, t * 2)
                        start_x = video_width
                        return (start_x + (0 - start_x) * progress, 0)

                    txt_clip = (base_txt_clip
                                .set_position(slide_right_position)
                                .crossfadein(0.3)
                                .set_start(delay))

                elif animation_type == "slide_from_top":
                    def slide_top_position(t):
                        progress = min(1.0, t * 2)
                        start_y_anim = -total_text_height
                        return (0, start_y_anim + (0 - start_y_anim) * progress)

                    txt_clip = (base_txt_clip
                                .set_position(slide_top_position)
                                .crossfadein(0.3)
                                .set_start(delay))

                elif animation_type == "slide_from_bottom":
                    def slide_bottom_position(t):
                        progress = min(1.0, t * 2)
                        start_y_anim = video_height
                        return (0, start_y_anim + (0 - start_y_anim) * progress)

                    txt_clip = (base_txt_clip
                                .set_position(slide_bottom_position)
                                .crossfadein(0.3)
                                .set_start(delay))

                elif animation_type == "zoom_in":
                    def zoom_position(t):
                        scale = max(0.1, min(1.0, t * 2))
                        offset_x = int((1 - scale) * max_text_width / 2)
                        offset_y = int((1 - scale) * total_text_height / 2)
                        return (offset_x, offset_y)

                    txt_clip = (base_txt_clip
                                .set_position(zoom_position)
                                .crossfadein(0.3)
                                .set_start(delay))

                elif animation_type == "bounce_in":
                    def bounce_position(t):
                        if t < 0.5:
                            bounce_scale = t * 2.4
                        else:
                            bounce_scale = 1.2 - 0.2 * (t - 0.5) * 2

                        offset = int((1 - min(bounce_scale, 1.0)) * 20)
                        return (0, offset)

                    txt_clip = (base_txt_clip
                                .set_position(bounce_position)
                                .crossfadein(0.2)
                                .set_start(delay))

                elif animation_type == "typewriter":
                    typewriter_clips = []
                    chars_per_frame = max(1, len(text) // int(duration * 10))

                    for char_count in range(1, len(text) + 1, chars_per_frame):
                        partial_text = text[:char_count]

                        # Create image for partial text using same positioning logic
                        partial_img = Image.new(
                            'RGBA', (video_width, video_height), (0, 0, 0, 0))
                        partial_draw = ImageDraw.Draw(partial_img)

                        for line_idx, line in enumerate(wrapped_lines):
                            # +1 for spaces
                            chars_used = sum(
                                len(wrapped_lines[j]) + 1 for j in range(line_idx))
                            chars_in_line = max(0, char_count - chars_used)

                            if chars_in_line > 0 and chars_in_line <= len(line):
                                partial_line = line[:chars_in_line]

                                line_width, line_height = get_text_dimensions(
                                    partial_line, font)
                                x_pos = (video_width - line_width) // 2
                                y_pos = start_y + \
                                    (line_idx * line_height * 1.2)

                                # Shadow
                                partial_draw.text(
                                    (x_pos + 2, y_pos + 2), partial_line, font=font, fill=(0, 0, 0, 128))
                                # Main text
                                partial_draw.text(
                                    (x_pos, y_pos), partial_line, font=font, fill=(255, 255, 255, 255))

                        partial_array = np.array(partial_img)
                        char_duration = duration / len(text) * chars_per_frame
                        char_start = delay + \
                            (char_count - 1) / len(text) * (duration - delay)

                        char_clip = ImageClip(
                            partial_array, duration=char_duration).set_start(char_start)
                        typewriter_clips.append(char_clip)

                    txt_clip = CompositeVideoClip(typewriter_clips)

                else:  # Default to fade_in
                    txt_clip = base_txt_clip.crossfadein(0.5).set_start(delay)

                text_clips.append(txt_clip)
                print(
                    f"✓ Successfully added animated text clip: '{text}' with {animation_type}")

            except Exception as text_error:
                print(f"Error creating text clip: {str(text_error)}")
                traceback.print_exc()
                continue

        # Combine video with text overlays
        if text_clips:
            print(
                f"Creating composite clip with {len(text_clips)} animated text elements")
            final_clip = CompositeVideoClip(
                [video_clip] + text_clips).crossfadeout(0.3)
            print("✓ Successfully created composite clip with animations")
            return final_clip
        else:
            print("Warning: No text clips were created, returning video clip only")
            return video_clip.crossfadeout(0.3)

    except Exception as e:
        print(f"Error creating slide: {str(e)}")
        traceback.print_exc()
        return None


def create_transition_effect(clip1, clip2, transition_type="crossfade", duration=0.5):
    """Create smooth transitions between clips"""
    if transition_type == "crossfade":
        return concatenate_videoclips([clip1, clip2], method="compose")
    elif transition_type == "slide_left":
        # Slide transition (simplified version)
        return concatenate_videoclips([clip1.crossfadeout(duration), clip2.crossfadein(duration)])
    else:
        return concatenate_videoclips([clip1, clip2])


def process_client_data(client_data_file, video_path, output_dir):
    """Process a single client data file and create a video for that client"""
    print(f"\n{'='*80}")

    try:
        # Load client data
        with open(client_data_file, 'r') as f:
            client_data = json.load(f)

        print(f"Loaded client data for: {client_data['name']}\n")

        # 🔥 NEW: Progressive Overload AI Analysis Integration
        if PROGRESSIVE_OVERLOAD_AVAILABLE:
            print("🧠 Running Progressive Overload AI Analysis...")
            try:
                enhanced_client_data = enhance_video_data_with_progressions(
                    client_data, client_data.get('name', 'Client'))
                print("✓ Progressive Overload analysis completed!")

                # Log what was found
                if enhanced_client_data.get('progression_analysis', {}).get('has_progression_data'):
                    prog_data = enhanced_client_data['progression_analysis']
                    print(
                        f"  📊 Goal Completion: {prog_data.get('goal_completion_rate', 0):.1%}")
                    print(
                        f"  📈 Exercises Improved: {len(prog_data.get('exercises_improved', []))}")
                    print(
                        f"  ➡️  Exercises Maintained: {len(prog_data.get('exercises_maintained', []))}")
                    print(
                        f"  📉 Exercises Declined: {len(prog_data.get('exercises_declined', []))}")
                    print(
                        f"  🎯 Next Week Progressions: {len(prog_data.get('next_week_progressions', []))}")
                else:
                    print("  ℹ️  No workout data available for progression analysis")

                # Use enhanced data for the rest of the process
                client_data = enhanced_client_data

            except Exception as e:
                print(f"  ⚠️  Progressive Overload analysis failed: {e}")
                print("  📝 Continuing with original client data...")
                # Continue with original client_data if analysis fails
        else:
            print("  ℹ️  Progressive Overload AI not available, using standard workflow")

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
                "font_size": 70,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": f"At {client_data.get('business_name', 'Cocos Personal Training')}",
                "position": (None, center_y),
                "font_size": 90,
                "animation": "fade_in",
                "delay": 0.5
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

        # 2. "Let's Check Your Progress" slide - ALWAYS show if there's any meaningful data
        if has_weight_data or has_workout_data or has_exercise_data or has_nutrition_data or has_steps_data or has_sleep_data:
            progress_text = [
                {
                    "text": "Let's Check Your Progress",
                    "position": (None, center_y - line_height//2),
                    "font_size": 70,
                    "animation": "fade_in",
                    "delay": 0.0
                },
                {
                    "text": f"{client_data.get('date_range', 'This Week')}",
                    "position": (None, center_y + line_height),
                    "font_size": 50,
                    "animation": "fade_in",
                    "delay": 0.8
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

        # 3. "You lifted weights X times" slide - show if has workout data
        if has_workout_data:
            workouts_count = client_data.get('workouts_this_week', 0)
            workout_count_text = [
                {
                    "text": "You Lifted Weights",
                    "position": (None, center_y - line_height),
                    "font_size": 70,
                    "animation": "fade_in",
                    "delay": 0.0
                },
                {
                    "text": f"{workouts_count} Times This Week!",
                    "position": (None, center_y + line_height//2),
                    "font_size": 60,
                    "animation": "fade_in",
                    "delay": 0.8
                }
            ]
            workout_count_slide = create_slide_with_text(
                video_path, workout_count_text)
            if workout_count_slide:
                slides.append(workout_count_slide)
                print("✓ Added workout count slide")

        # 4. "Your Workout Stats" slide
        if has_workout_data and client_data.get('has_exercise_data', False):
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
                        "font_size": 70,
                        "animation": "fade_in",
                        "delay": 0.0
                    },
                    {
                        "text": f"{total_reps} Total Reps",
                        "position": (None, center_y + line_height*0.5),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 0.5
                    },
                    {
                        "text": f"{total_sets} Total Sets",
                        "position": (None, center_y + line_height*1.5),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 0.8
                    },
                    {
                        "text": f"{int(total_weight_lifted)} kg Lifted",
                        "position": (None, center_y + line_height*2.5),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 1.1
                    }
                ]
                stats_slide = create_slide_with_text(video_path, stats_text)
                if stats_slide:
                    slides.append(stats_slide)
                    print("✓ Added workout stats slide")

        # 5. Goal Completion Slide (if workout data available)
        if has_workout_data and client_data.get('has_exercise_data', False):
            try:
                print("🎯 Creating Goal Completion slide...")
                goal_completion_rate = calculate_goal_completion_rate(
                    client_data)

                if goal_completion_rate is not None:
                    goal_text = [
                        {
                            "text": "Last Week's Goal Results",
                            "position": (None, center_y - line_height * 1.5),
                            "font_size": 65,
                            "animation": "fade_in",
                            "delay": 0.0
                        },
                        {
                            "text": f"{goal_completion_rate:.0f}% Goal Completion Rate!",
                            "position": (None, center_y - line_height * 0.5),
                            "font_size": 55,
                            "animation": "fade_in",
                            "delay": 0.6
                        }
                    ]

                    # Add performance summary
                    goal_summary = get_goal_summary(client_data)
                    if goal_summary:
                        goal_text.append({
                            "text": goal_summary,
                            "position": (None, center_y + line_height * 0.7),
                            "font_size": 45,
                            "animation": "fade_in",
                            "delay": 1.2
                        })

                    goal_slide = create_slide_with_text(video_path, goal_text)
                    if goal_slide:
                        slides.append(goal_slide)
                        print(
                            f"✓ Added Goal Completion slide: {goal_completion_rate:.1f}%")

            except Exception as e:
                print(f"  ⚠️  Error creating goal completion slide: {e}")

        # 6. Exercise Improvements Detail slide (if workout data available)
        if has_workout_data and client_data.get('has_exercise_data', False):
            try:
                print("🎯 Creating Exercise Improvements Detail slide...")
                improvement_details = get_exercise_improvement_details(
                    client_data)

                if improvement_details and len(improvement_details) > 0:
                    detail_text = [
                        {
                            "text": "Exercise Improvements",
                            "position": (None, center_y - line_height * 2.8),
                            "font_size": 55,
                            "animation": "fade_in",
                            "delay": 0.0
                        }
                    ]

                    # Add all exercise improvements with simple format (up to 6 to fit nicely)
                    max_exercises = min(6, len(improvement_details))
                    current_y_offset = -1.5

                    for i, improvement in enumerate(improvement_details[:max_exercises]):
                        exercise_name = improvement['exercise_name']
                        performance_detail = improvement['performance_detail']

                        # Single line: Exercise name + improvement
                        detail_text.append({
                            "text": f"{exercise_name} {performance_detail}",
                            "position": (None, center_y + line_height * current_y_offset),
                            "font_size": 45,
                            "animation": "fade_in",
                            "delay": 0.5 + (i * 0.3)
                        })

                        # Move to next exercise position
                        current_y_offset += 0.7

                    detail_slide = create_slide_with_text(
                        video_path, detail_text, duration=6.0)  # Longer duration for reading
                    if detail_slide:
                        slides.append(detail_slide)
                        print(
                            f"✓ Added Exercise Improvements Detail slide with {len(improvement_details[:max_exercises])} improvements")

            except Exception as e:
                print(
                    f"  ⚠️  Error creating exercise improvements detail slide: {e}")

        # Skip Progressive Overload slides - they add unnecessary fluff
        # The goal completion slide above already shows the important progression info

        # 7. Most Improved Exercise slide
        most_improved_data = client_data.get('most_improved_exercise')
        if most_improved_data and most_improved_data.get('name', 'N/A') != 'N/A' and has_workout_data:
            exercise_name = most_improved_data.get('name')
            # Shorten exercise name if too long
            display_exercise_name = shorten_exercise_name(
                exercise_name, max_length=35)
            current_perf_desc = most_improved_data.get(
                'current_performance_desc', 'N/A')

            star_performer_text = [
                {
                    "text": "Most Improved Exercise",
                    "position": (None, center_y - line_height * 1.5),
                    "font_size": 70,
                    "animation": "fade_in",
                    "delay": 0.0
                },
                {
                    "text": display_exercise_name,
                    "position": (None, center_y - line_height * 0.5),
                    "font_size": 55,
                    "animation": "fade_in",
                    "delay": 0.5
                },
                {
                    "text": f"Achieved: {current_perf_desc}",
                    "position": (None, center_y + line_height * 0.5),
                    "font_size": 40,
                    "animation": "fade_in",
                    "delay": 1.0
                }
            ]
            star_performer_slide = create_slide_with_text(
                video_path, star_performer_text)
            if star_performer_slide:
                slides.append(star_performer_slide)
                print(
                    f"✓ Added Most Improved Exercise slide for {display_exercise_name}")

            # 10. Exercise Technique Tip slide
            technique_tip = generate_exercise_technique_tip(exercise_name)
            if technique_tip:
                # Break technique tip into multiple lines for better readability
                tip_lines = break_technique_tip_into_lines(technique_tip)

                tip_text = [
                    {
                        "text": "Technique Tip",
                        "position": (None, center_y - line_height * 2.5),
                        "font_size": 65,
                        "animation": "fade_in",
                        "delay": 0.0
                    },
                    {
                        "text": f"For {display_exercise_name}:",
                        "position": (None, center_y - line_height * 1.7),
                        "font_size": 45,
                        "animation": "fade_in",
                        "delay": 0.5
                    }
                ]

                # Add each line of the technique tip
                for i, line in enumerate(tip_lines):
                    tip_text.append({
                        "text": line,
                        "position": (None, center_y - line_height * 0.5 + (i * line_height * 0.6)),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 1.0 + (i * 0.3)
                    })

                tip_slide = create_slide_with_text(
                    video_path, tip_text, duration=6.0)  # Longer duration for reading
                if tip_slide:
                    slides.append(tip_slide)
                print(
                    f"✓ Added Technique Tip slide for {display_exercise_name}")

        # 11. Weight analysis slide
        if client_data.get('has_weight_data', False):
            try:
                current_weight_val = client_data['current_weight']
                if isinstance(current_weight_val, (int, float)):
                    weight_text = [
                        {
                            "text": "Bodyweight Update",
                            "position": (None, center_y - line_height * 1.5),
                            "font_size": 70,
                            "animation": "fade_in",
                            "delay": 0.0
                        },
                        {
                            "text": f"{math.floor(current_weight_val)} kg",
                            "position": (None, center_y - line_height * 0.5),
                            "font_size": 90,
                            "animation": "fade_in",
                            "delay": 0.6
                        },
                        {
                            "text": client_data.get('current_weight_message', 'Keep tracking your progress!'),
                            "position": (None, center_y + line_height * 0.7),
                            "font_size": 50,
                            "animation": "fade_in",
                            "delay": 1.2
                        }
                    ]
                    weight_slide = create_slide_with_text(
                        video_path, weight_text)
                    if weight_slide:
                        slides.append(weight_slide)
                        print("✓ Added weight analysis slide")
            except Exception as e:
                print(f"Error creating weight slide: {e}")

        # 12. Steps analysis slide
        if client_data.get('has_steps_data', False):
            try:
                steps_text = []
                steps_text.append({
                    "text": "Steps Analysis",
                    "position": (None, center_y - line_height * 1.5),
                    "font_size": 70,
                    "animation": "fade_in",
                    "delay": 0.0
                })

                if 'current_steps_avg' in client_data and client_data['current_steps_avg'] is not None:
                    avg_steps = int(client_data['current_steps_avg'])
                    steps_text.append({
                        "text": f"Daily Average: {avg_steps:,} steps",
                        "position": (None, center_y - line_height * 0.3),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 0.6
                    })

                steps_message = client_data.get(
                    'current_steps_message', 'Keep moving forward!')
                steps_text.append({
                    "text": steps_message,
                    "position": (None, center_y + line_height * 0.7),
                    "font_size": 45,
                    "animation": "fade_in",
                    "delay": 1.2
                })

                steps_slide = create_slide_with_text(video_path, steps_text)
                if steps_slide:
                    slides.append(steps_slide)
                    print("✓ Added steps analysis slide")
            except Exception as e:
                print(f"Error creating steps slide: {e}")

        # 13. Nutrition analysis slide
        if client_data.get('has_nutrition_data', False):
            try:
                nutrition_text = [
                    {
                        "text": "Nutrition Analysis",
                        "position": (None, center_y - line_height * 1.5),
                        "font_size": 70,
                        "animation": "fade_in",
                        "delay": 0.0
                    }
                ]

                nutrition_message = client_data.get(
                    'current_nutrition_message', 'Keep focusing on your nutrition!')
                nutrition_text.append({
                    "text": nutrition_message,
                    "position": (None, center_y + line_height * 0.2),
                    "font_size": 45,
                    "animation": "fade_in",
                    "delay": 0.8
                })

                nutrition_slide = create_slide_with_text(
                    video_path, nutrition_text)
                if nutrition_slide:
                    slides.append(nutrition_slide)
                    print("✓ Added nutrition analysis slide")
            except Exception as e:
                print(f"Error creating nutrition slide: {e}")

        # 14. Sleep analysis slide
        if client_data.get('has_sleep_data', False):
            try:
                sleep_text = [
                    {
                        "text": "Sleep Analysis",
                        "position": (None, center_y - line_height * 1.5),
                        "font_size": 70,
                        "animation": "fade_in",
                        "delay": 0.0
                    }
                ]

                if 'current_sleep_avg' in client_data and client_data['current_sleep_avg'] is not None:
                    avg_sleep = client_data['current_sleep_avg']
                    sleep_text.append({
                        "text": f"Average: {avg_sleep:.1f} hours/night",
                        "position": (None, center_y - line_height * 0.3),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 0.6
                    })

                sleep_message = client_data.get(
                    'current_sleep_message', 'Quality sleep supports your goals!')
                sleep_text.append({
                    "text": sleep_message,
                    "position": (None, center_y + line_height * 0.7),
                    "font_size": 45,
                    "animation": "fade_in",
                    "delay": 1.2
                })

                sleep_slide = create_slide_with_text(video_path, sleep_text)
                if sleep_slide:
                    slides.append(sleep_slide)
                    print("✓ Added sleep analysis slide")
            except Exception as e:
                print(f"Error creating sleep slide: {e}")

        # 15. Motivational closing slide
        motivational_text = [
            {
                "text": "Keep Going!",
                "position": (None, center_y - line_height//2),
                "font_size": 80,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": "You're doing amazing!",
                "position": (None, center_y + line_height//2),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.8
            }
        ]
        motivational_slide = create_slide_with_text(
            video_path, motivational_text)
        if motivational_slide:
            slides.append(motivational_slide)
            print("✓ Added motivational closing slide")

        # Rest of the function continues unchanged...
        if not slides:
            print("❌ No slides created - client may not have enough data")
            return None

        print(f"\n📊 Created {len(slides)} slides total")

        # Create final video by concatenating all slides
        print("Combining slides into final video...")
        final_video = concatenate_videoclips(slides, method='compose')

        # Generate output filename
        client_name_clean = re.sub(r'[<>:"/\\|?*]', '_', client_data['name'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{client_name_clean}_week_summary_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        # Write the final video
        final_video.write_videofile(
            output_path, codec='libx264', audio_codec='aac')

        # Clean up
        for slide in slides:
            slide.close()
        final_video.close()

        print(f"\n✅ Video created successfully!")
        print(f"📁 Output: {output_path}")
        print(f"🎬 Duration: {final_video.duration:.1f} seconds")
        print(f"📊 Slides: {len(slides)}")

        return output_path

    except Exception as e:
        print(f"❌ Error processing {client_data_file}: {e}")
        traceback.print_exc()
        return None


def calculate_goal_completion_rate(client_data):
    """Calculate goal completion rate from workout breakdown data"""
    try:
        workout_breakdown = client_data.get('workout_breakdown', [])
        if not workout_breakdown:
            return None

        # Track unique exercises only to avoid double counting
        unique_exercises = {}

        for workout in workout_breakdown:
            for session in workout.get('sessions_current_week', []):
                for exercise in session.get('exercises', []):
                    exercise_name = exercise.get('name', '')
                    workload_improvement = exercise.get(
                        'workload_improvement_vs_previous', 0)
                    current_workload = exercise.get('workload_current', 0)

                    # Skip exercises with no meaningful workload
                    if current_workload <= 0:
                        continue

                    # Track best performance for each unique exercise
                    if exercise_name not in unique_exercises:
                        unique_exercises[exercise_name] = workload_improvement
                    else:
                        # Keep the best improvement for this exercise
                        unique_exercises[exercise_name] = max(
                            unique_exercises[exercise_name], workload_improvement)

        if not unique_exercises:
            return None

        total_exercises = len(unique_exercises)
        improved = sum(
            1 for improvement in unique_exercises.values() if improvement > 0)
        maintained = sum(
            1 for improvement in unique_exercises.values() if improvement == 0)

        # Calculate goal completion (improved + 50% credit for maintained)
        goals_met = improved + (maintained * 0.5)
        goal_completion_rate = (goals_met / total_exercises) * 100

        return goal_completion_rate

    except Exception as e:
        print(f"Error calculating goal completion rate: {e}")
        return None


def get_goal_summary(client_data):
    """Get a summary message for goal performance"""
    try:
        workout_breakdown = client_data.get('workout_breakdown', [])
        if not workout_breakdown:
            return None

        # Track unique exercises only to avoid double counting
        unique_exercises = {}

        for workout in workout_breakdown:
            for session in workout.get('sessions_current_week', []):
                for exercise in session.get('exercises', []):
                    exercise_name = exercise.get('name', '')
                    workload_improvement = exercise.get(
                        'workload_improvement_vs_previous', 0)
                    current_workload = exercise.get('workload_current', 0)

                    # Skip exercises with no meaningful workload
                    if current_workload <= 0:
                        continue

                    # Track best performance for each unique exercise
                    if exercise_name not in unique_exercises:
                        unique_exercises[exercise_name] = workload_improvement
                    else:
                        # Keep the best improvement for this exercise
                        unique_exercises[exercise_name] = max(
                            unique_exercises[exercise_name], workload_improvement)

        if not unique_exercises:
            return None

        improved = sum(
            1 for improvement in unique_exercises.values() if improvement > 0)
        maintained = sum(
            1 for improvement in unique_exercises.values() if improvement == 0)
        declined = sum(
            1 for improvement in unique_exercises.values() if improvement < 0)

        # Create summary message (without emojis to avoid square box display issues)
        if improved > 0 and maintained > 0:
            return f"You IMPROVED {improved} exercises and MAINTAINED {maintained}!"
        elif improved > 0:
            return f"You IMPROVED {improved} exercises this week!"
        elif maintained > 0:
            return f"You MAINTAINED {maintained} exercises!"
        else:
            return "Focus week - building stronger foundations!"

    except Exception as e:
        print(f"Error creating goal summary: {e}")
        return None


def get_exercise_improvement_details(client_data):
    """Get detailed list of exercise improvements with specific amounts"""
    try:
        workout_breakdown = client_data.get('workout_breakdown', [])
        if not workout_breakdown:
            return []

        # Use a dictionary to track improvements for each exercise
        exercise_improvements = {}

        for workout in workout_breakdown:
            for session in workout.get('sessions_current_week', []):
                for exercise in session.get('exercises', []):
                    exercise_name = exercise.get('name', '')
                    workload_improvement = exercise.get(
                        'workload_improvement_vs_previous', 0)
                    current_workload = exercise.get('workload_current', 0)

                    # Skip exercises with no meaningful workload
                    if current_workload <= 0:
                        continue

                    # Only show improvements (positive changes)
                    if workload_improvement > 0:
                        if exercise_name not in exercise_improvements:
                            exercise_improvements[exercise_name] = {
                                'improvement': workload_improvement,
                                'exercise_data': exercise,
                                'count': 1
                            }
                        else:
                            # Count multiple improvements of same exercise
                            exercise_improvements[exercise_name]['count'] += 1
                            # Keep the best improvement
                            if workload_improvement > exercise_improvements[exercise_name]['improvement']:
                                exercise_improvements[exercise_name]['improvement'] = workload_improvement
                                exercise_improvements[exercise_name]['exercise_data'] = exercise

                # Convert to display format with full names and details
        improvements = []
        for exercise_name, data in exercise_improvements.items():
            improvement_detail = determine_improvement_type(
                data['exercise_data'], data['improvement'])

            # Use full exercise name - no abbreviation
            full_name = exercise_name

            # Format as multi-line entry for better readability
            improvements.append({
                'exercise_name': full_name,
                'performance_detail': improvement_detail,
                'improvement': data['improvement']
            })

        # Sort by improvement percentage (descending) and return full details
        improvements.sort(key=lambda x: x['improvement'], reverse=True)
        return improvements  # Return all improvements with full details

    except Exception as e:
        print(f"Error getting exercise improvement details: {e}")
        return []


def determine_improvement_type(exercise, improvement_percentage):
    """Get simple improvement information - just weight or rep increase"""
    try:
        sets_current = exercise.get('sets_current', [])
        if not sets_current:
            return f"(+{improvement_percentage:.0f}%)"

        # Get current performance details
        weights = [s.get('weight', 0) for s in sets_current]
        reps = [s.get('reps', 0) for s in sets_current]
        avg_weight = sum(weights) / len(weights) if weights else 0
        total_reps = sum(reps)

        # Estimate the actual improvement based on percentage
        if avg_weight > 0:
            # Weight-based exercise - estimate weight increase
            estimated_weight_increase = max(
                1.0, avg_weight * improvement_percentage / 100 / 2)
            return f"(+{estimated_weight_increase:.1f}kg)"
        else:
            # Bodyweight exercise - estimate rep increase
            estimated_rep_increase = max(
                1, int(total_reps * improvement_percentage / 100 / 3))
            return f"(+{estimated_rep_increase} reps)"

    except Exception as e:
        return f"(+{improvement_percentage:.0f}%)"


def break_technique_tip_into_lines(technique_tip, max_chars_per_line=35):
    """Break technique tip into multiple lines for better readability"""
    if not technique_tip:
        return ["Focus on proper form"]

    words = technique_tip.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        # If adding this word would exceed the limit, start a new line
        if current_length + len(word) + 1 > max_chars_per_line and current_line:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + (1 if current_line else 0)

    # Add the last line
    if current_line:
        lines.append(' '.join(current_line))

    # Limit to 4 lines maximum
    return lines[:4]


def generate_exercise_technique_tip(exercise_name):
    """Generate a technique tip for the most improved exercise using AI"""
    try:
        # Common technique tips for popular exercises
        technique_tips = {
            # Chest exercises
            "barbell bench press": "Keep your shoulder blades retracted and maintain a slight arch in your lower back.",
            "dumbbell bench press": "Lower the weights until you feel a stretch in your chest, then press up smoothly.",
            "incline dumbbell press": "Set the bench to 30-45 degrees and focus on squeezing your upper chest at the top.",
            "chest fly": "Keep a slight bend in your elbows and focus on the stretch at the bottom.",

            # Back exercises
            "pull ups": "Engage your lats by pulling your elbows down and back, not just up.",
            "lat pulldown": "Pull the bar to your upper chest while keeping your torso upright.",
            "seated row": "Pull your shoulder blades together and keep your core engaged throughout.",
            "barbell row": "Keep your back straight and pull the bar to your lower chest.",

            # Shoulder exercises
            "shoulder press": "Keep your core tight and press straight up, not forward.",
            "lateral raise": "Lift with control and pause briefly at the top for maximum muscle activation.",
            "rear delt fly": "Focus on squeezing your shoulder blades together at the top.",

            # Leg exercises
            "squat": "Keep your knees tracking over your toes and your chest up throughout the movement.",
            "deadlift": "Keep the bar close to your body and drive through your heels.",
            "lunge": "Step forward into a position where both knees form 90-degree angles.",
            "leg press": "Place your feet shoulder-width apart and press through your heels.",

            # Arm exercises
            "bicep curl": "Keep your elbows stationary and focus on squeezing your biceps at the top.",
            "tricep extension": "Keep your elbows close to your head and extend only at the elbow joint.",
            "hammer curl": "Maintain a neutral grip and control the weight on both the up and down phases.",

            # Core exercises
            "plank": "Keep your body in a straight line from head to heels, engaging your core.",
            "crunches": "Focus on bringing your ribs to your hips, not your head to your knees.",
            "russian twist": "Keep your feet off the ground and rotate from your core, not your arms."
        }

        # Clean exercise name for matching
        clean_name = exercise_name.lower().strip()

        # Direct match
        if clean_name in technique_tips:
            return technique_tips[clean_name]

        # Fuzzy matching for partial matches
        for key, tip in technique_tips.items():
            if any(word in clean_name for word in key.split()) or any(word in key for word in clean_name.split()):
                return tip

        # Generic tip if no specific match found
        return "Focus on controlled movements and proper form over speed or weight."

    except Exception as e:
        print(f"Error generating technique tip: {e}")
        return "Focus on proper form and controlled movements for best results."


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
