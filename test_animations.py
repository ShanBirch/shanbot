#!/usr/bin/env python
"""
Test script to demonstrate the new animation features in simple_blue_video.py
This creates a short demo video showing all available animation types.
"""

from moviepy.editor import concatenate_videoclips, VideoFileClip
from simple_blue_video import create_slide_with_text
import sys
import os
from pathlib import Path

# Add the current directory to the path so we can import from simple_blue_video
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def create_animation_demo():
    """Create a demo video showing all animation types"""

    # Path to the video template
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, "blue2.mp4")

    if not os.path.exists(video_path):
        video_path = os.path.join(script_dir, "blue.mp4")
        if not os.path.exists(video_path):
            print("Error: No video template found (blue2.mp4 or blue.mp4)")
            return False

    print("Creating animation demo video...")

    # Get actual video dimensions dynamically
    with VideoFileClip(video_path) as temp_clip:
        width, height = temp_clip.size

    center_x = width // 2
    center_y = height // 2
    print(
        f"Video dimensions: {width}x{height}, Center: ({center_x}, {center_y})")

    slides = []

    # Demo slides for each animation type
    animation_demos = [
        {
            "title": "Fade In Animation",
            "animation": "fade_in"
        },
        {
            "title": "Slide From Left",
            "animation": "slide_from_left"
        },
        {
            "title": "Slide From Right",
            "animation": "slide_from_right"
        },
        {
            "title": "Slide From Top",
            "animation": "slide_from_top"
        },
        {
            "title": "Slide From Bottom",
            "animation": "slide_from_bottom"
        },
        {
            "title": "Zoom In Effect",
            "animation": "zoom_in"
        },
        {
            "title": "Bounce In Effect",
            "animation": "bounce_in"
        },
        {
            "title": "Typewriter Effect",
            "animation": "typewriter"
        }
    ]

    # Create intro slide
    intro_text = [
        {
            "text": "Animation Demo",
            "position": (None, center_y - 50),
            "font_size": 80,
            "animation": "zoom_in",
            "delay": 0.0
        },
        {
            "text": "Enhanced Video Features",
            "position": (None, center_y + 50),
            "font_size": 50,
            "animation": "fade_in",
            "delay": 0.8
        }
    ]

    intro_slide = create_slide_with_text(video_path, intro_text, duration=3.0)
    if intro_slide:
        slides.append(intro_slide)
        print("✓ Added intro slide")

    # Create demo slides for each animation
    for demo in animation_demos:
        demo_text = [
            {
                "text": demo["title"],
                "position": (None, center_y),
                "font_size": 70,
                "animation": demo["animation"],
                "delay": 0.0
            }
        ]

        demo_slide = create_slide_with_text(
            video_path, demo_text, duration=4.0)
        if demo_slide:
            slides.append(demo_slide)
            print(f"✓ Added {demo['animation']} demo slide")

    # Create combined effects slide
    combined_text = [
        {
            "text": "Multiple Effects",
            "position": (None, center_y - 100),
            "font_size": 60,
            "animation": "slide_from_top",
            "delay": 0.0
        },
        {
            "text": "Can Work",
            "position": (None, center_y - 30),
            "font_size": 50,
            "animation": "slide_from_left",
            "delay": 0.5
        },
        {
            "text": "Together",
            "position": (None, center_y + 40),
            "font_size": 50,
            "animation": "slide_from_right",
            "delay": 1.0
        },
        {
            "text": "Seamlessly!",
            "position": (None, center_y + 110),
            "font_size": 60,
            "animation": "bounce_in",
            "delay": 1.5
        }
    ]

    combined_slide = create_slide_with_text(
        video_path, combined_text, duration=5.0)
    if combined_slide:
        slides.append(combined_slide)
        print("✓ Added combined effects slide")

    if not slides:
        print("Error: No slides were created!")
        return False

    # Combine all slides with transitions
    print(f"\nCombining {len(slides)} demo slides...")

    if len(slides) > 1:
        transition_duration = 0.5
        final_slides = [slides[0]]

        for i in range(1, len(slides)):
            prev_slide = final_slides[-1].crossfadeout(transition_duration)
            current_slide = slides[i].crossfadein(transition_duration)
            final_slides[-1] = prev_slide
            final_slides.append(current_slide)

        final_clip = concatenate_videoclips(final_slides, method="compose")
    else:
        final_clip = concatenate_videoclips(slides)

    # Save the demo video
    output_path = Path(script_dir) / "animation_demo.mp4"
    print(f"\nSaving animation demo to {output_path}...")

    final_clip.write_videofile(
        str(output_path),
        codec='libx264',
        audio_codec='aac',
        fps=30,
        preset='fast',
        threads=4,
        ffmpeg_params=['-pix_fmt', 'yuv420p']
    )

    print(f"\n✅ Animation demo created successfully: {output_path}")
    print(f"Video duration: {final_clip.duration:.1f} seconds")
    return True


if __name__ == "__main__":
    success = create_animation_demo()
    if success:
        print("\n🎬 Demo video ready! You can now see all the new animation effects.")
    else:
        print("\n❌ Failed to create demo video.")
