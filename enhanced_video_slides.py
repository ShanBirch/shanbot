# Import necessary functions from the main video script
# Removed imports to avoid circular dependency
import math
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def get_text_dimensions(text, font):
    """Get the width and height of text with a given font"""
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

    try:
        font = ImageFont.truetype("arial.ttf", min_font_size)
    except:
        font = ImageFont.load_default()
    return min_font_size, font


def create_slide_with_text(title, text_lines, width, height, title_color=(255, 255, 255),
                           text_color=(240, 240, 240), bg_color=(47, 72, 115), center_text=False, video_path=None):
    """Create a slide with properly formatted text using video background"""

    # Always use the image-based approach to avoid ImageMagick issues
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", min(72, width//15))
        text_font = ImageFont.truetype("arial.ttf", min(48, width//20))
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    # Title positioning - ensure it fits
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = max(10, (width - title_width) // 2)
    title_y = height // 8

    draw.text((title_x, title_y), title, fill=title_color, font=title_font)

    # Body text positioning
    text_start_y = title_y + 120
    line_height = min(65, height//12)

    for i, line in enumerate(text_lines[:6]):
        clean_line = line.replace('□', '').replace(
            '☑', '').replace('✓', '').strip()

        if clean_line.startswith('  '):
            text_x = width // 4
            clean_line = clean_line[2:]
            current_font = text_font
        else:
            text_x = width // 6
            current_font = title_font if len(clean_line) < 30 else text_font

        line_y = text_start_y + (i * line_height)

        if line_y + line_height < height - 50:
            draw.text((text_x, line_y), clean_line,
                      fill=text_color, font=current_font)

    img_array = np.array(img)
    from moviepy.editor import ImageClip
    clip = ImageClip(img_array, duration=3.0)
    return clip


def create_progression_slides(video_path, client_data, width, height):
    """Create enhanced progression slides with AI-powered recommendations"""
    slides = []

    # Get progression analysis
    progression_data = client_data.get('progression_analysis', {})

    if not progression_data or not progression_data.get('has_progressions', False):
        print("  ℹ️  Creating introduction + basic goals slides with video background")

        # Import the main create_slide_with_text function
        import sys
        import os
        sys.path.append(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        from simple_blue_video import create_slide_with_text as main_create_slide

        # Slide 1: Introducing
        intro_text = [
            {
                "text": "Introducing",
                "position": (None, height//2),
                "font_size": 80,
                "animation": "fade_in",
                "delay": 0.0
            }
        ]

        slide1 = main_create_slide(video_path, intro_text, duration=3.0)
        if slide1:
            slides.append(slide1)

        # Slide 2: Goal Setting
        goal_setting_text = [
            {
                "text": "Goal Setting",
                "position": (None, height//2),
                "font_size": 80,
                "animation": "fade_in",
                "delay": 0.0
            }
        ]

        slide2 = main_create_slide(video_path, goal_setting_text, duration=3.0)
        if slide2:
            slides.append(slide2)

        # Slide 3: Brief intro to the idea
        idea_intro_text = [
            {
                "text": "Every week we analyze your data",
                "position": (None, height//2 - 60),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": "and set personalized goals for you",
                "position": (None, height//2 + 20),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.8
            },
            {
                "text": "Challenge: Can you hit 100%?",
                "position": (None, height//2 + 100),
                "font_size": 45,
                "animation": "fade_in",
                "delay": 1.6
            }
        ]

        slide3 = main_create_slide(video_path, idea_intro_text, duration=4.0)
        if slide3:
            slides.append(slide3)

        # Slide 4: Your goals have been set
        goals_set_text = [
            {
                "text": "Your goals have been set",
                "position": (None, height//2 - 60),
                "font_size": 65,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": "Look for goals when you start your workout",
                "position": (None, height//2 + 40),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.8
            }
        ]

        slide4 = main_create_slide(video_path, goals_set_text, duration=3.5)
        if slide4:
            slides.append(slide4)

        return slides

    # Extract progression recommendations
    recommendations = progression_data.get('recommendations', {})

    if recommendations:
        # Import the main create_slide_with_text function
        import sys
        import os
        sys.path.append(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        from simple_blue_video import create_slide_with_text as main_create_slide

        # Slide 1: Introducing
        intro_text = [
            {
                "text": "Introducing",
                "position": (None, height//2),
                "font_size": 80,
                "animation": "fade_in",
                "delay": 0.0
            }
        ]

        slide1 = main_create_slide(video_path, intro_text, duration=3.0)
        if slide1:
            slides.append(slide1)

        # Slide 2: Goal Completion Results (NEW!)
        goal_completion_rate = progression_data.get('goal_completion_rate', 0)
        exercises_improved = progression_data.get('exercises_improved', [])

        # Format completion rate display
        if goal_completion_rate >= 80:
            completion_msg = f"{goal_completion_rate:.0f}% - EXCELLENT! 🔥"
            encouragement = "You crushed most of your goals!"
        elif goal_completion_rate >= 60:
            completion_msg = f"{goal_completion_rate:.0f}% - GREAT JOB! 💪"
            encouragement = "Solid progress on most exercises!"
        elif goal_completion_rate >= 40:
            completion_msg = f"{goal_completion_rate:.0f}% - BUILDING MOMENTUM! 📈"
            encouragement = "Good effort! Progress week by week!"
        else:
            completion_msg = f"{goal_completion_rate:.0f}% - FOUNDATION WEEK 💪"
            encouragement = "Setting up for future success!"

        goal_results_text = [
            {
                "text": "Last Week's Goal Results",
                "position": (None, height//2 - 80),
                "font_size": 60,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": completion_msg,
                "position": (None, height//2 - 10),
                "font_size": 65,
                "animation": "slide_from_left",
                "delay": 0.8
            },
            {
                "text": encouragement,
                "position": (None, height//2 + 60),
                "font_size": 45,
                "animation": "fade_in",
                "delay": 1.6
            }
        ]

        slide2 = main_create_slide(video_path, goal_results_text, duration=4.0)
        if slide2:
            slides.append(slide2)

        # Slide 3: Goal Setting
        goal_setting_text = [
            {
                "text": "Goal Setting",
                "position": (None, height//2),
                "font_size": 80,
                "animation": "fade_in",
                "delay": 0.0
            }
        ]

        slide3 = main_create_slide(video_path, goal_setting_text, duration=3.0)
        if slide3:
            slides.append(slide3)

        # Slide 3: Brief intro to the idea
        idea_intro_text = [
            {
                "text": "Every week we analyze your data",
                "position": (None, height//2 - 60),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": "and set personalized goals for you",
                "position": (None, height//2 + 20),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.8
            },
            {
                "text": "Challenge: Can you hit 100%?",
                "position": (None, height//2 + 100),
                "font_size": 45,
                "animation": "fade_in",
                "delay": 1.6
            }
        ]

        slide3 = main_create_slide(video_path, idea_intro_text, duration=4.0)
        if slide3:
            slides.append(slide3)

        # Slide 4: Your goals have been set
        goals_set_text = [
            {
                "text": "Your goals have been set",
                "position": (None, height//2 - 60),
                "font_size": 65,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": "Look for goals when you start your workout",
                "position": (None, height//2 + 40),
                "font_size": 50,
                "animation": "fade_in",
                "delay": 0.8
            }
        ]

        slide4 = main_create_slide(video_path, goals_set_text, duration=3.5)
        if slide4:
            slides.append(slide4)
            print("✓ Added weekly goal targets slide with proper video background")

    return slides


def shorten_exercise_name(exercise_name, max_length=25):
    """Shorten exercise names for better video display"""
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
        'Lateral': 'Lat',
        'Overhead': 'OH',
        'Romanian': 'RDL',
        'Bulgarian': 'Bulg'
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
