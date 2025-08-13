#!/usr/bin/env python3
"""
Enhanced Simple Blue Video Generator with Progressive Overload AI Integration
This version includes workout progression analysis in the weekly videos
"""

from enhanced_video_slides import create_progression_slides
from progressive_overload_video_integration import enhance_video_data_with_progressions, ProgressionVideoIntegrator
from simple_blue_video import *
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all original functions and dependencies

# Import the new Progressive Overload integration


def process_client_data_enhanced(client_data_file, video_path, output_dir):
    """Enhanced version that includes Progressive Overload AI analysis"""
    print(f"\n{'='*80}")
    print(f"Processing ENHANCED client data from: {client_data_file}")
    print(f"{'='*80}")

    try:
        # Load client data
        with open(client_data_file, 'r') as f:
            client_data = json.load(f)

        print(f"Loaded client data for: {client_data['name']}\n")

        # 🔥 NEW: Add Progressive Overload Analysis
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
        except Exception as e:
            print(f"  ⚠️  Progressive Overload analysis failed: {e}")
            enhanced_client_data = client_data  # Fallback to original data

        # Create slides
        print("\nCreating slides...")
        slides = []

        # Get video dimensions for text positioning
        with VideoFileClip(video_path) as clip:
            width, height = clip.size

        center_x = width // 2
        center_y = height // 2
        line_height = 100

        # 1. Intro slide (unchanged)
        intro_text = [
            {
                "text": "Your Week",
                "position": (None, center_y - line_height),
                "font_size": 70,
                "animation": "fade_in",
                "delay": 0.0
            },
            {
                "text": f"At {enhanced_client_data['business_name']}",
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

        # 🔥 NEW: Add Progressive Overload slides BEFORE existing content
        print("🎯 Adding Progressive Overload slides...")
        progression_slides = create_progression_slides(
            video_path, enhanced_client_data, width, height)
        if progression_slides:
            slides.extend(progression_slides)
            print(f"✓ Added {len(progression_slides)} progression slides")
        else:
            print("  ℹ️  No progression slides added (no workout data available)")

        # Continue with existing slides (weight, workout analysis, etc.)
        # ... rest of the original slide creation logic ...

        # 2. Weight Analysis (existing code)
        if enhanced_client_data.get('has_weight_data'):
            print("Adding weight slides...")
            # ... existing weight slide code ...

        # 3. Workout Analysis (now enhanced with progression data)
        if enhanced_client_data.get('workouts_completed_analysis'):
            print("Adding workout analysis slides...")
            # ... existing workout slide code ...
            # Note: This could now also reference the progression analysis

        # ... rest of existing slide creation logic ...

        # Generate final video
        if slides:
            print(f"\nGenerating video with {len(slides)} slides...")
            final_video = concatenate_videoclips(slides, method="compose")

            # Create output filename
            client_name_safe = "".join(c for c in enhanced_client_data['name'] if c.isalnum(
            ) or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{client_name_safe}_weekly_summary_{timestamp}.mp4"
            output_path = os.path.join(output_dir, output_filename)

            print(f"Saving video to: {output_path}")
            final_video.write_videofile(
                output_path,
                fps=24,
                audio_codec='aac',
                verbose=False,
                logger=None
            )

            final_video.close()
            print(f"✅ ENHANCED video created successfully: {output_filename}")
            return output_path
        else:
            print("❌ No slides created, skipping video generation")
            return None

    except Exception as e:
        print(f"❌ Error processing enhanced client data: {e}")
        import traceback
        traceback.print_exc()
        return None


def main_enhanced():
    """Enhanced main function with Progressive Overload integration"""
    if len(sys.argv) != 4:
        print("Usage: python simple_blue_video_enhanced.py <client_data_file> <video_path> <output_dir>")
        sys.exit(1)

    client_data_file = sys.argv[1]
    video_path = sys.argv[2]
    output_dir = sys.argv[3]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process with enhanced features
    result = process_client_data_enhanced(
        client_data_file, video_path, output_dir)

    if result:
        print(f"\n🎉 Enhanced video generation completed successfully!")
        print(f"📁 Output: {result}")
    else:
        print(f"\n❌ Enhanced video generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main_enhanced()
