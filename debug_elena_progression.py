#!/usr/bin/env python3
"""
Debug Elena's Progressive Overload analysis to see why goal completion isn't working
"""

from progressive_overload_video_integration import enhance_video_data_with_progressions
import json
import sys
import os

# Add app directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))


def main():
    print("🔍 DEBUGGING ELENA'S PROGRESSIVE OVERLOAD ANALYSIS")
    print("=" * 60)

    # Load Elena's original data
    with open('output/checkin_reviews/Elena_Green_2025-06-08_fitness_wrapped_data.json', 'r') as f:
        original_data = json.load(f)

    print(f"📁 Loaded original data for: {original_data['name']}")
    print(
        f"Has exercise data: {original_data.get('has_exercise_data', False)}")
    print(f"Workouts this week: {original_data.get('workouts_this_week', 0)}")

    # Run the Progressive Overload enhancement
    print("\n🧠 Running Progressive Overload enhancement...")
    enhanced_data = enhance_video_data_with_progressions(
        original_data, "Elena Green")

    # Check what was added
    progression_analysis = enhanced_data.get('progression_analysis', {})

    print(f"\n📊 PROGRESSION ANALYSIS RESULTS:")
    print(
        f"Goal completion rate: {progression_analysis.get('goal_completion_rate', 'N/A')}")
    print(
        f"Has progression data: {progression_analysis.get('has_progression_data', False)}")
    print(
        f"Has progressions: {progression_analysis.get('has_progressions', False)}")
    print(
        f"Exercises improved: {len(progression_analysis.get('exercises_improved', []))}")
    print(
        f"Exercises maintained: {len(progression_analysis.get('exercises_maintained', []))}")
    print(
        f"Exercises declined: {len(progression_analysis.get('exercises_declined', []))}")

    # Show the actual exercise data
    if progression_analysis.get('exercises_improved'):
        print(f"\n✅ IMPROVED EXERCISES:")
        for ex in progression_analysis['exercises_improved']:
            print(f"  - {ex}")

    if progression_analysis.get('exercises_maintained'):
        print(f"\n🔄 MAINTAINED EXERCISES:")
        for ex in progression_analysis['exercises_maintained']:
            print(f"  - {ex}")

    if progression_analysis.get('exercises_declined'):
        print(f"\n📉 DECLINED EXERCISES:")
        for ex in progression_analysis['exercises_declined']:
            print(f"  - {ex}")

    # Check if this would trigger the goal completion slide
    will_show_goal_slide = (progression_analysis.get('has_progressions', False) and
                            progression_analysis.get('goal_completion_rate', 0) > 0)

    print(f"\n🎬 WILL SHOW GOAL COMPLETION SLIDE: {will_show_goal_slide}")

    if not will_show_goal_slide:
        print("❌ This is why Elena's video doesn't show goal completion!")


if __name__ == "__main__":
    main()
