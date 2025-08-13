# Test Smart Lead Finder Local Mode - Debug single profile analysis
# Tests if the AI can correctly identify local Bayside gym prospects

from smart_lead_finder import SmartLeadFinder
import sys
import os

# Add the parent directory to sys.path so we can import from smart_lead_finder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_local_profile(username):
    """Test a single profile in local mode."""
    print(f"🧪 TESTING LOCAL MODE: Analyzing @{username}")
    print(f"🎯 Target: Women 30+ (especially mums) in Bayside Melbourne area")
    print("="*60)

    # Create finder in local mode
    finder = SmartLeadFinder(mode='local')

    try:
        # Setup browser and login
        if not finder.setup_driver():
            print("❌ Failed to setup browser")
            return

        if not finder.login_to_instagram():
            print("❌ Failed to login")
            return

        print("✅ Browser setup and login successful")
        print(f"🔍 Now analyzing @{username} for local Bayside criteria...")
        print("-"*60)

        # Test the analysis
        result = finder.analyze_profile(username)

        print("-"*60)
        print(
            f"📊 FINAL RESULT: {'✅ POTENTIAL LOCAL CLIENT' if result else '❌ NOT A MATCH'}")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if finder.driver:
            try:
                finder.driver.quit()
                print("✅ Browser closed")
            except:
                pass


if __name__ == "__main__":
    # Test with known local profiles
    test_profiles = [
        'payneinthenix',  # Shannon's existing gym client - should be perfect match
        'simonetindallrealestate',  # Another gym client
        'baysidecouncil',  # Local council (should be rejected as business)
    ]

    print("🏠 LOCAL MODE TESTING - Bayside Gym Client Finder")
    print("="*60)

    if len(sys.argv) > 1:
        # Test specific username from command line
        username = sys.argv[1]
        test_local_profile(username)
    else:
        # Test default profiles
        for username in test_profiles:
            test_local_profile(username)
            print("\n" + "="*60 + "\n")
