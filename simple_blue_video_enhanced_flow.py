#!/usr/bin/env python3
"""
Enhanced Simple Blue Video Generator with Optimized Flow
Creates personalized weekly fitness videos for clients with:
1. Intro slide
2. "Let's check your progress"
3. "You lifted weights X times"
4. "Your workout stats"
5-8. Progressive overload slides
9. Most improved exercise
10. Exercise technique tip
11. Weight analysis
12. Steps analysis  
13. Nutrition analysis
14. Sleep analysis
15. Motivational closing
"""

import os
import sys
import json
import math
import re
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import argparse

# Try to import progressive overload functionality
PROGRESSIVE_OVERLOAD_AVAILABLE = False
try:
    from progressive_overload_video_integration import enhance_video_data_with_progressions, create_progression_slides
    PROGRESSIVE_OVERLOAD_AVAILABLE = True
    print("✓ Progressive Overload AI integration available")
except ImportError as e:
    print(f"ℹ️  Progressive Overload AI not available: {e}")
    print("   Continuing with standard video generation...")


def get_text_dimensions(text, font):
    """Get the width and height of text when rendered with a specific font"""
    # Create a temporary image to measure text
    temp_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def get_optimal_font_size(text, max_width, max_height, max_font_size=100, min_font_size=20):
    """Find the optimal font size that fits within the given dimensions"""
    for font_size in range(max_font_size, min_font_size - 1, -2):
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype(
                    "C:/Windows/Fonts/arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

        width, height = get_text_dimensions(text, font)

        if width <= max_width and height <= max_height:
            return font_size

    return min_font_size


def wrap_text(text, max_width, font, max_lines=3):
    """Wrap text to fit within max_width, up to max_lines"""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        width, _ = get_text_dimensions(test_line, font)

        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word is too long, just add it
                lines.append(word)
                current_line = ""

        if len(lines) >= max_lines:
            break

    if current_line and len(lines) < max_lines:
        lines.append(current_line)

    # If we exceeded max_lines, truncate the last line and add "..."
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1] + "..."

    return "\n".join(lines)


def shorten_exercise_name(exercise_name, max_length=25):
    """Shorten exercise name by removing common words and abbreviating"""
    if len(exercise_name) <= max_length:
        return exercise_name

    # Common words to remove or abbreviate
    replacements = {
        "Dumbbell": "DB",
        "Barbell": "BB",
        "Machine": "",
        "Cable": "",
        "Seated": "",
        "Standing": "",
        "Incline": "Inc",
        "Decline": "Dec",
        "Overhead": "OH",
        "Single Arm": "SA",
        "Bulgarian": "Bulg",
        "Romanian": "Rom",
        "Extension": "Ext",
        "Lateral": "Lat",
        "Eccentric": "Ecc",
        "Concentric": "Con"
    }

    shortened = exercise_name
    for full, abbrev in replacements.items():
        shortened = shortened.replace(full, abbrev)

    # Remove extra spaces
    shortened = " ".join(shortened.split())

    # If still too long, truncate
    if len(shortened) > max_length:
        shortened = shortened[:max_length-3] + "..."

    return shortened


def create_slide_with_text(video_path, text_elements, duration=3.0):
    """Create a slide with multiple text elements overlaid on the video"""
    try:
        # Load the background video
        background = VideoFileClip(video_path).subclip(0, duration)

        # Get video dimensions
        width, height = background.size

        # Create text clips
        text_clips = []

        for element in text_elements:
            text = element['text']
            position = element.get('position', (width//2, height//2))
            font_size = element.get('font_size', 60)
            font_color = element.get('font_color', 'white')
            animation = element.get('animation', 'fade_in')
            delay = element.get('delay', 0.0)

            # Handle auto-centering for x-position
            if position[0] is None:
                x_pos = 'center'
            else:
                x_pos = position[0]

            y_pos = position[1]

            # Create text clip
            txt_clip = TextClip(text,
                                fontsize=font_size,
                                color=font_color,
                                font='Arial-Bold',
                                stroke_color='black',
                                stroke_width=2)

            # Apply animation based on type
            if animation == 'fade_in':
                txt_clip = txt_clip.set_position(
                    (x_pos, y_pos)).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)
                txt_clip = txt_clip.crossfadein(0.5)

            elif animation == 'slide_up':
                def slide_up_position(t):
                    start_y = y_pos + 100
                    end_y = y_pos
                    progress = min(t / 1.0, 1)  # 1 second animation
                    current_y = start_y + (end_y - start_y) * progress
                    return (x_pos, current_y)

                txt_clip = txt_clip.set_position(
                    slide_up_position).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            elif animation == 'slide_left':
                def slide_left_position(t):
                    start_x = width + 100
                    end_x = x_pos if x_pos != 'center' else width//2
                    progress = min(t / 1.0, 1)
                    current_x = start_x + (end_x - start_x) * progress
                    return (current_x, y_pos)

                txt_clip = txt_clip.set_position(
                    slide_left_position).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            elif animation == 'slide_right':
                def slide_right_position(t):
                    start_x = -txt_clip.w - 100
                    end_x = x_pos if x_pos != 'center' else width//2
                    progress = min(t / 1.0, 1)
                    current_x = start_x + (end_x - start_x) * progress
                    return (current_x, y_pos)

                txt_clip = txt_clip.set_position(
                    slide_right_position).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            elif animation == 'slide_top':
                def slide_top_position(t):
                    start_y = -txt_clip.h - 100
                    end_y = y_pos
                    progress = min(t / 1.0, 1)
                    current_y = start_y + (end_y - start_y) * progress
                    return (x_pos, current_y)

                txt_clip = txt_clip.set_position(
                    slide_top_position).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            elif animation == 'slide_bottom':
                def slide_bottom_position(t):
                    start_y = height + 100
                    end_y = y_pos
                    progress = min(t / 1.0, 1)
                    current_y = start_y + (end_y - start_y) * progress
                    return (x_pos, current_y)

                txt_clip = txt_clip.set_position(
                    slide_bottom_position).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            elif animation == 'zoom':
                def zoom_position(t):
                    progress = min(t / 1.0, 1)
                    scale = 0.1 + 0.9 * progress
                    return (x_pos, y_pos)

                txt_clip = txt_clip.resize(
                    lambda t: 0.1 + 0.9 * min(t / 1.0, 1))
                txt_clip = txt_clip.set_position(
                    (x_pos, y_pos)).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            elif animation == 'bounce':
                def bounce_position(t):
                    if t < 1.0:
                        # Bounce down and up
                        bounce_factor = abs(math.sin(t * math.pi * 4)) * 20
                        return (x_pos, y_pos - bounce_factor)
                    else:
                        return (x_pos, y_pos)

                txt_clip = txt_clip.set_position(
                    bounce_position).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)
            else:
                # Default positioning
                txt_clip = txt_clip.set_position(
                    (x_pos, y_pos)).set_duration(duration - delay)
                if delay > 0:
                    txt_clip = txt_clip.set_start(delay)

            text_clips.append(txt_clip)

        # Combine background with text
        final_clip = CompositeVideoClip([background] + text_clips)
        return final_clip

    except Exception as e:
        print(f"Error creating slide: {e}")
        return None


def create_transition_effect(clip1, clip2, transition_type="crossfade", duration=0.5):
    """Create transition effects between clips"""
    try:
        if transition_type == "crossfade":
            return concatenate_videoclips([clip1, clip2.crossfadein(duration)])
        else:
            return concatenate_videoclips([clip1, clip2])
    except:
        return concatenate_videoclips([clip1, clip2])


def generate_exercise_technique_tip(exercise_name):
    """Generate a technique tip for the most improved exercise"""
    try:
        # Common technique tips for popular exercises
        technique_tips = {
            # Chest exercises
            "barbell bench press": "Keep your shoulder blades retracted and maintain a slight arch in your lower back.",
            "barbell bench": "Keep your shoulder blades retracted and maintain a slight arch in your lower back.",
            "bench press": "Keep your shoulder blades retracted and maintain a slight arch in your lower back.",
            "dumbbell bench press": "Lower the weights until you feel a stretch in your chest, then press up smoothly.",
            "dumbbell bench": "Lower the weights until you feel a stretch in your chest, then press up smoothly.",
            "incline dumbbell press": "Set the bench to 30-45 degrees and focus on squeezing your upper chest at the top.",
            "incline press": "Set the bench to 30-45 degrees and focus on squeezing your upper chest at the top.",
            "chest fly": "Keep a slight bend in your elbows and focus on the stretch at the bottom.",
            "dumbbell fly": "Keep a slight bend in your elbows and focus on the stretch at the bottom.",

            # Back exercises
            "pull ups": "Engage your lats by pulling your elbows down and back, not just up.",
            "chin ups": "Engage your lats by pulling your elbows down and back, not just up.",
            "lat pulldown": "Pull the bar to your upper chest while keeping your torso upright.",
            "lat pull down": "Pull the bar to your upper chest while keeping your torso upright.",
            "seated row": "Pull your shoulder blades together and keep your core engaged throughout.",
            "barbell row": "Keep your back straight and pull the bar to your lower chest.",
            "bent over row": "Keep your back straight and pull the bar to your lower chest.",
            "t-bar row": "Keep your chest up and pull with your elbows close to your body.",

            # Shoulder exercises
            "shoulder press": "Keep your core tight and press straight up, not forward.",
            "overhead press": "Keep your core tight and press straight up, not forward.",
            "military press": "Keep your core tight and press straight up, not forward.",
            "lateral raise": "Lift with control and pause briefly at the top for maximum muscle activation.",
            "side raise": "Lift with control and pause briefly at the top for maximum muscle activation.",
            "rear delt fly": "Focus on squeezing your shoulder blades together at the top.",
            "reverse fly": "Focus on squeezing your shoulder blades together at the top.",
            "face pulls": "Pull to your face level and squeeze your rear delts at the end.",

            # Leg exercises
            "squat": "Keep your knees tracking over your toes and your chest up throughout the movement.",
            "back squat": "Keep your knees tracking over your toes and your chest up throughout the movement.",
            "front squat": "Keep your elbows high and your core engaged throughout the movement.",
            "deadlift": "Keep the bar close to your body and drive through your heels.",
            "romanian deadlift": "Push your hips back and keep a slight bend in your knees.",
            "rdl": "Push your hips back and keep a slight bend in your knees.",
            "lunge": "Step forward into a position where both knees form 90-degree angles.",
            "bulgarian lunge": "Keep most of your weight on your front foot and descend straight down.",
            "leg press": "Place your feet shoulder-width apart and press through your heels.",
            "leg extension": "Control the weight and squeeze your quads at the top.",
            "leg curl": "Keep your hips pressed against the pad and curl with control.",

            # Arm exercises
            "bicep curl": "Keep your elbows stationary and focus on squeezing your biceps at the top.",
            "hammer curl": "Maintain a neutral grip and control the weight on both the up and down phases.",
            "preacher curl": "Don't let your elbows flare out and control the negative portion.",
            "tricep extension": "Keep your elbows close to your head and extend only at the elbow joint.",
            "skull crusher": "Keep your upper arms stationary and lower the weight to your forehead.",
            "tricep pushdown": "Keep your elbows at your sides and focus on squeezing your triceps.",
            "close grip bench": "Keep your elbows close to your body and press with your triceps.",

            # Core exercises
            "plank": "Keep your body in a straight line from head to heels, engaging your core.",
            "crunches": "Focus on bringing your ribs to your hips, not your head to your knees.",
            "russian twist": "Keep your feet off the ground and rotate from your core, not your arms.",
            "hanging knee raise": "Use your abs to pull your knees up, not momentum.",
            "cable crunch": "Focus on crunching your abs, not pulling with your arms.",
            "ab wheel": "Keep your core tight and roll out only as far as you can control."
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


def process_client_data(client_data_file, video_path, output_dir):
    """Process a single client data file and create a video for that client with optimized flow"""
    print(f"\n{'='*80}")
    print(f"Processing client data from: {client_data_file}")
    print(f"{'='*80}")

    try:
        # Load client data
        with open(client_data_file, 'r') as f:
            client_data = json.load(f)

        print(f"Loaded client data for: {client_data['name']}\n")

        # 🔥 Progressive Overload AI Analysis Integration
        if PROGRESSIVE_OVERLOAD_AVAILABLE:
            print("🧠 Running Progressive Overload AI Analysis...")
            try:
                enhanced_client_data = enhance_video_data_with_progressions(
                    client_data)
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
                "text": f"At {client_data['business_name']}",
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

        # 5-8. Progressive Overload slides
        if PROGRESSIVE_OVERLOAD_AVAILABLE:
            print("🎯 Adding Progressive Overload slides...")
            try:
                progression_slides = create_progression_slides(
                    video_path, client_data, width, height)
                if progression_slides:
                    slides.extend(progression_slides)
                    print(
                        f"✓ Added {len(progression_slides)} progression slides")
                else:
                    print(
                        "  ℹ️  No progression slides added (no workout data available)")
            except Exception as e:
                print(f"  ⚠️  Error creating progression slides: {e}")

        # 9. Most Improved Exercise slide
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
                # Wrap long tips to fit on screen
                max_chars_per_line = 45
                if len(technique_tip) > max_chars_per_line:
                    words = technique_tip.split()
                    lines = []
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) <= max_chars_per_line:
                            current_line += (" " if current_line else "") + word
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    if current_line:
                        lines.append(current_line)

                    # Limit to 3 lines max
                    if len(lines) > 3:
                        lines = lines[:3]
                        lines[-1] += "..."

                    technique_tip = "\n".join(lines)

                tip_text = [
                    {
                        "text": "Technique Tip",
                        "position": (None, center_y - line_height * 1.8),
                        "font_size": 70,
                        "animation": "fade_in",
                        "delay": 0.0
                    },
                    {
                        "text": f"For {display_exercise_name}:",
                        "position": (None, center_y - line_height * 0.8),
                        "font_size": 50,
                        "animation": "fade_in",
                        "delay": 0.5
                    },
                    {
                        "text": technique_tip,
                        "position": (None, center_y + line_height * 0.3),
                        "font_size": 42,
                        "animation": "fade_in",
                        "delay": 1.0
                    }
                ]
                tip_slide = create_slide_with_text(
                    video_path, tip_text, duration=5.0)  # Longer duration for reading
                if tip_slide:
                    slides.append(tip_slide)
                    print(
                        f"✓ Added Technique Tip slide for {display_exercise_name}")

        # 11. Weight analysis slide
        if has_weight_data:
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
        if has_steps_data:
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
        if has_nutrition_data:
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
        if has_sleep_data:
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
        output_filename = f"{client_name_clean}_week_summary_enhanced_{timestamp}.mp4"
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
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function to process client data files and create videos"""
    parser = argparse.ArgumentParser(
        description='Create personalized weekly fitness videos')
    parser.add_argument('client_data_path',
                        help='Path to client data file or directory')
    parser.add_argument('--video_path', default='templates/simple_blue_background.mp4',
                        help='Path to background video template')
    parser.add_argument('--output_dir', default='output',
                        help='Output directory for generated videos')

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Check if background video exists
    if not os.path.exists(args.video_path):
        print(f"❌ Background video not found: {args.video_path}")
        return

    # Process files
    if os.path.isfile(args.client_data_path):
        # Single file
        print("Processing single client data file...")
        result = process_client_data(
            args.client_data_path, args.video_path, args.output_dir)
        if result:
            print(f"✅ Successfully created video: {result}")
        else:
            print("❌ Failed to create video")
    elif os.path.isdir(args.client_data_path):
        # Directory of files
        print("Processing directory of client data files...")
        json_files = [f for f in os.listdir(
            args.client_data_path) if f.endswith('.json')]

        if not json_files:
            print(f"❌ No JSON files found in {args.client_data_path}")
            return

        print(f"Found {len(json_files)} client data files")

        successful = 0
        failed = 0

        for json_file in json_files:
            file_path = os.path.join(args.client_data_path, json_file)
            print(f"\n🔄 Processing {json_file}...")

            result = process_client_data(
                file_path, args.video_path, args.output_dir)
            if result:
                successful += 1
                print(f"✅ Success: {json_file}")
            else:
                failed += 1
                print(f"❌ Failed: {json_file}")

        print(f"\n📊 Final Results:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Output directory: {args.output_dir}")
    else:
        print(f"❌ Invalid path: {args.client_data_path}")


if __name__ == "__main__":
    main()
