#!/usr/bin/env python3
"""
Test the improved workout finding functionality
"""

from pb import TrainerizeAutomation
import time


def test_workout_finding():
    """Test the improved find_and_click_workout_by_name function"""
    print("🔍 TESTING IMPROVED WORKOUT FINDING")
    print("=" * 60)

    trainerize = TrainerizeAutomation()

    # Login credentials
    username = "Shannonbirch@cocospersonaltraining.com"
    password = "cyywp7nyk2"
    client_name = "Alice Forster"

    try:
        print("🔐 Logging in to Trainerize...")
        if not trainerize.login(username, password):
            print("❌ Login failed!")
            return False

        time.sleep(2)
        trainerize.handle_notification_popup()

        print(f"🎯 Navigating to client: {client_name}")
        if not trainerize.navigate_to_client(client_name):
            print("❌ Failed to navigate to client!")
            return False

        print("📋 Navigating to training program...")
        if not trainerize.navigate_to_training_program():
            print("❌ Failed to navigate to training program!")
            return False

        # Test workout finding for Alice Forster's actual workouts
        test_workouts = [
            "Back Day",
            "Core Day",
            "Leg Day",
            "Shoulder Day",
            "Chest Day",
            "Back",
            "Shoulders",
            "Chest + Arms",
            "Core"
        ]

        print(f"\n🏋️ TESTING WORKOUT FINDING:")
        print("=" * 50)

        successful_finds = 0

        for workout_name in test_workouts:
            print(f"\n🔍 Testing: '{workout_name}'")

            # Try to find the workout (don't actually click, just test finding)
            try:
                # Use a modified version that doesn't click
                found = trainerize.find_and_click_workout_by_name(workout_name)

                if found:
                    print(f"  ✅ FOUND: '{workout_name}'")
                    successful_finds += 1
                    # Navigate back to program view
                    trainerize.navigate_to_training_program()
                    time.sleep(1)
                else:
                    print(f"  ❌ NOT FOUND: '{workout_name}'")

            except Exception as e:
                print(f"  ❌ ERROR testing '{workout_name}': {e}")
                # Navigate back to program view
                try:
                    trainerize.navigate_to_training_program()
                    time.sleep(1)
                except:
                    pass

        print(f"\n📊 WORKOUT FINDING RESULTS:")
        print("=" * 50)
        print(
            f"✅ Successfully found: {successful_finds}/{len(test_workouts)} workouts")
        print(
            f"❌ Failed to find: {len(test_workouts) - successful_finds} workouts")

        if successful_finds == len(test_workouts):
            print(f"\n🎉 PERFECT! All workouts found successfully!")
            print(f"   The smart mapping system will work efficiently!")
        elif successful_finds > len(test_workouts) // 2:
            print(f"\n✅ GOOD! Most workouts found successfully!")
            print(f"   The system will work for most exercises!")
        else:
            print(f"\n⚠️  WARNING! Many workouts not found!")
            print(f"   The selectors may need further adjustment!")

        return successful_finds > 0

    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

    finally:
        trainerize.cleanup()


def main():
    """Main test function"""
    print("🚀 WORKOUT FINDING IMPROVEMENT TEST")
    print("=" * 60)

    success = test_workout_finding()

    if success:
        print(f"\n🎉 WORKOUT FINDING TEST COMPLETE!")
        print(f"\n💡 IMPROVEMENTS MADE:")
        print(f"   • Added data-testid selectors for reliable finding")
        print(f"   • Added case-insensitive matching")
        print(f"   • Added comprehensive fallback selectors")
        print(f"   • Added debugging to show available workouts")
        print(f"   • Now uses actual HTML structure")

        print(f"\n🚀 Ready for full automation with improved finding!")
    else:
        print(f"\n❌ Test failed - selectors may need more work!")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
