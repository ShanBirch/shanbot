#!/usr/bin/env python3
"""
Simple test to debug the Trainerize login issue.
This uses the improved pb.py login function.
"""

from pb import TrainerizeAutomation
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_pb_login():
    """Test the improved pb.py login function."""

    print("🔧 Testing improved pb.py login...")

    try:
        print("🚀 Initializing TrainerizeAutomation...")
        trainerize = TrainerizeAutomation()

        print("✅ TrainerizeAutomation initialized!")

        print("🔑 Attempting login...")
        username = "Shannonbirch@cocospersonaltraining.com"
        password = "cyywp7nyk2"

        success = trainerize.login(username, password)

        if success:
            print("🎉 LOGIN SUCCESSFUL!")
            print("✅ The pb.py login function is working correctly!")

            # Test navigation to make sure we're really logged in
            print("🧪 Testing navigation to verify login...")
            try:
                current_url = trainerize.driver.current_url
                print(f"📍 Current URL: {current_url}")

                if "trainerize.com" in current_url and "login" not in current_url.lower():
                    print("✅ Successfully logged into Trainerize dashboard!")
                else:
                    print("⚠️ URL suggests we might still be on login page")

            except Exception as nav_e:
                print(f"⚠️ Error testing navigation: {nav_e}")

        else:
            print("❌ LOGIN FAILED!")
            print("Check the logs above for details on what went wrong")

        input("\nPress Enter to close browser and continue...")

    except Exception as e:
        print(f"❌ Error during test: {e}")

    finally:
        if 'trainerize' in locals():
            print("🧹 Cleaning up...")
            trainerize.cleanup()
            print("✅ Cleanup complete!")


def test_progression_system():
    """Test the full progression system if login works."""

    print("\n" + "="*60)
    print("🏋️ TESTING FULL PROGRESSION SYSTEM")
    print("="*60)

    try:
        from progressive_overload_ai import ProgressiveOverloadAI

        ai = ProgressiveOverloadAI()
        client_name = "Alice Forster"  # Known good test client

        print(f"📊 Loading workout data for {client_name}...")
        workout_data = ai.load_client_workout_data(client_name, weeks_back=4)

        if workout_data:
            print(f"✅ Loaded {len(workout_data)} exercise performances")

            print("🧠 Analyzing progressions...")
            progressions = ai.analyze_progression_patterns_rep_based(
                workout_data)

            if progressions:
                print(f"✅ Generated {len(progressions)} progressions")
                print("\n📋 Sample progressions:")

                count = 0
                for exercise_name, decisions in progressions.items():
                    if count >= 3:  # Show only first 3
                        break
                    decision = decisions[0]
                    print(
                        f"   • {exercise_name}: W({decision.recommended_weight}) R({decision.recommended_reps})")
                    count += 1

                if len(progressions) > 3:
                    print(f"   ... and {len(progressions) - 3} more")

                print("\n🚀 Progression system is ready!")
                print("💡 Run: python test_rep_based_progressions.py")
                print("   Then choose option 1 for full automation!")

            else:
                print("❌ No progressions generated")
        else:
            print("❌ No workout data found")
            print("💡 Make sure Alice Forster has workout data in the system")

    except Exception as e:
        print(f"❌ Error testing progression system: {e}")


def main():
    """Main function to run all tests."""

    print("🏋️ TRAINERIZE AUTOMATION TEST SUITE")
    print("="*50)

    print("\n1️⃣ Testing pb.py login function...")
    test_pb_login()

    print("\n2️⃣ Testing progression system...")
    test_progression_system()

    print("\n" + "="*50)
    print("🎯 TEST SUMMARY")
    print("="*50)
    print("✅ If login worked: pb.py is fixed!")
    print("✅ If progressions loaded: Data integration works!")
    print("🚀 Next: Run full system with test_rep_based_progressions.py")


if __name__ == "__main__":
    main()
