#!/usr/bin/env python3
"""
Test script to verify calendar integration with checkin system
"""

from checkin_good_110525 import TrainerizeAutomation
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_calendar_integration():
    """Test the calendar integration functionality"""

    # Test credentials
    username = "shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    gemini_api_key = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
    test_client = "Alice Forster"

    print("🧪 Testing Calendar Integration with Checkin System")
    print("=" * 60)

    try:
        # Initialize automation
        automation = TrainerizeAutomation(gemini_api_key)

        # Test login
        print("🔐 Testing login...")
        if not automation.login(username, password):
            print("❌ Login failed!")
            return False
        print("✅ Login successful!")

        # Test navigation to client
        print(f"🎯 Testing navigation to {test_client}...")
        if not automation.navigate_to_client(test_client):
            print(f"❌ Could not navigate to {test_client}!")
            automation.cleanup()
            return False
        print(f"✅ Successfully navigated to {test_client}!")

        # Test comprehensive calendar analysis
        print("📅 Testing comprehensive calendar analysis...")
        calendar_results = automation.analyze_comprehensive_calendar_data(
            test_client, username, password, gemini_api_key)

        if calendar_results:
            print("✅ Calendar analysis completed successfully!")
            print("\n📊 Results Summary:")

            # Check nutrition results
            nutrition_results = calendar_results.get(
                'nutrition_analysis_results', {})
            cal_prot = nutrition_results.get('calories_protein', {})
            print(
                f"  🍎 Nutrition (Calories/Protein): {cal_prot.get('availability', 'unknown')}")

            # Check bodyweight results
            bodyweight_availability = calendar_results.get(
                'bodyweight_availability', 'unknown')
            print(f"  ⚖️ Bodyweight: {bodyweight_availability}")

            # Check steps/walking results
            steps_availability = calendar_results.get(
                'steps_availability', 'unknown')
            print(f"  🚶 Walking/Steps: {steps_availability}")

            print("\n✅ Calendar integration test PASSED!")

        else:
            print("❌ Calendar analysis failed!")
            automation.cleanup()
            return False

        # Test workout data collection (keep this from original system)
        print("\n💪 Testing workout data collection...")
        if automation.click_progress_tab():
            if automation.click_review_by_workout().startswith("Successfully"):
                workout_data_list = automation.process_workouts()
                print(f"✅ Retrieved {len(workout_data_list)} workout records")
            else:
                print("⚠️ Could not access workout review")
        else:
            print("⚠️ Could not navigate to progress tab")

        # Cleanup
        automation.cleanup()
        print("\n🎉 All tests completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        try:
            automation.cleanup()
        except:
            pass
        return False


if __name__ == "__main__":
    success = test_calendar_integration()
    if success:
        print("\n✅ Calendar integration is working correctly!")
        print("🚀 You can now run the full checkin script with calendar analysis.")
    else:
        print("\n❌ Calendar integration test failed!")
        print("🔧 Please check the configuration and try again.")

    sys.exit(0 if success else 1)
