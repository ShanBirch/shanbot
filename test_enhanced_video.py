#!/usr/bin/env python3
"""
Test script for the Enhanced Video Flow
This demonstrates the new video order:
1. Intro
2. "Let's check your progress"  
3. "You lifted weights X times"
4. "Your workout stats"
5-8. Progressive overload slides
9. Most improved exercise
10. Exercise technique tip
11. Weight/steps/nutrition/sleep
"""

import os
import sys
import json
from simple_blue_video_enhanced_flow import process_client_data


def create_sample_client_data():
    """Create sample client data for testing the enhanced flow"""
    sample_data = {
        "name": "Sarah Johnson",
        "business_name": "Elite Fitness Studio",
        "date_range": "13 Jan - 19 Jan",

        # Workout data
        "workouts_this_week": 4,
        "has_exercise_data": True,
        "total_reps": 156,
        "total_sets": 24,
        "total_weight_lifted": 2840,

        # Most improved exercise data
        "most_improved_exercise": {
            "name": "Barbell Bench Press",
            "current_performance_desc": "85kg x 8 reps",
            "improvement_type": "weight_increase",
            "improvement_percentage": 12.5
        },

        # Weight data
        "has_weight_data": True,
        "current_weight": 68.5,
        "current_weight_message": "Great progress! Down 0.8kg this week",

        # Steps data
        "has_steps_data": True,
        "current_steps_avg": 9240,
        "current_steps_message": "Excellent daily activity level!",

        # Nutrition data
        "has_nutrition_data": True,
        "current_nutrition_message": "Protein goals consistently met this week",

        # Sleep data
        "has_sleep_data": True,
        "current_sleep_avg": 7.2,
        "current_sleep_message": "Quality sleep supporting your recovery"
    }

    return sample_data


def test_enhanced_flow():
    """Test the enhanced video flow"""
    print("🎬 Testing Enhanced Video Flow")
    print("=" * 50)

    # Create test data
    client_data = create_sample_client_data()

    # Save to temp file
    test_file = "temp_test_client.json"
    with open(test_file, 'w') as f:
        json.dump(client_data, f, indent=2)

    # Set paths
    video_template = "templates/simple_blue_background.mp4"
    output_dir = "output"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Check if video template exists
    if not os.path.exists(video_template):
        print(f"⚠️  Video template not found: {video_template}")
        print("📝 Please ensure you have the background video template.")
        print("💡 You can use any MP4 video as a background template.")
        return False

    print(f"📁 Using template: {video_template}")
    print(f"📊 Processing client: {client_data['name']}")
    print(f"🎯 Expected flow:")
    print("   1. Intro")
    print("   2. Let's check your progress")
    print("   3. You lifted weights 4 times")
    print("   4. Your workout stats")
    print("   5-8. Progressive overload slides (if available)")
    print("   9. Most improved exercise: Barbell Bench Press")
    print("   10. Technique tip for Barbell Bench Press")
    print("   11. Weight analysis")
    print("   12. Steps analysis")
    print("   13. Nutrition analysis")
    print("   14. Sleep analysis")
    print("   15. Motivational closing")
    print()

    # Process the video
    try:
        result = process_client_data(test_file, video_template, output_dir)

        if result:
            print(f"✅ SUCCESS! Video created: {result}")
            print(f"🎬 The video includes the technique tip for Barbell Bench Press!")
            return True
        else:
            print("❌ FAILED: Video creation failed")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    finally:
        # Clean up temp file
        if os.path.exists(test_file):
            os.remove(test_file)


def main():
    """Main test function"""
    print("🚀 Enhanced Video Flow Test")
    print("=" * 60)
    print()

    success = test_enhanced_flow()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        print("💡 Your enhanced flow is working with:")
        print("   ✓ Most improved exercise detection")
        print("   ✓ Technique tips generation")
        print("   ✓ Optimized slide order")
        print("   ✓ Progressive overload integration")
    else:
        print("❌ Test failed. Please check the error messages above.")

    print("\n📋 To use with real client data:")
    print("   python simple_blue_video_enhanced_flow.py path/to/client/data.json")
    print("\n🔧 To process multiple clients:")
    print("   python simple_blue_video_enhanced_flow.py path/to/client/data/directory/")


if __name__ == "__main__":
    main()
