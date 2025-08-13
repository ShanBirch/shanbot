"""
Test Bio Integration
Tests the background bio fetcher with real usernames and verifies the data is available in prompts.
"""

import json
import sqlite3
import time
from background_bio_fetcher import BackgroundBioFetcher
from webhook_handlers import build_member_chat_prompt, get_user_data


def test_bio_fetch_and_integration():
    """Test fetching bio data and integrating it into prompts"""

    # Test username with a real Instagram account
    test_username = "danielle_emily_ruth"  # From our database check

    print(f"=== TESTING BIO FETCH AND INTEGRATION FOR {test_username} ===")

    # 1. First, let's manually fetch bio for this user
    print("\n1. Manually fetching bio data...")
    bio_fetcher = BackgroundBioFetcher()

    try:
        # Setup browser and login
        if bio_fetcher.setup_browser():
            print("✅ Browser setup successful")
        else:
            print("❌ Browser setup failed")
            return

        if bio_fetcher.login_to_instagram():
            print("✅ Instagram login successful")
        else:
            print("❌ Instagram login failed")
            return

        # Process the bio for our test user
        success = bio_fetcher.process_user_bio(test_username)
        if success:
            print(f"✅ Successfully processed bio for {test_username}")
        else:
            print(f"❌ Failed to process bio for {test_username}")

    finally:
        bio_fetcher.stop()

    # 2. Check if the bio data is now in the database
    print("\n2. Checking if bio data is in database...")
    SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT metrics_json FROM users WHERE ig_username = ?", (test_username,))
    result = cursor.fetchone()

    if result and result[0]:
        try:
            metrics = json.loads(result[0])
            bio_text = metrics.get('bio_text', '')
            full_name = metrics.get('full_name', '')
            interests = metrics.get('interests', [])

            print(f"✅ Bio data found in database:")
            print(f"   Full Name: {full_name}")
            print(f"   Bio Text: {bio_text[:100]}...")
            print(f"   Interests: {interests}")

        except json.JSONDecodeError:
            print("❌ Error parsing metrics JSON")
    else:
        print("❌ No bio data found in database")

    conn.close()

    # 3. Test the prompt integration
    print("\n3. Testing prompt integration...")
    try:
        # Get user data (this should include bio data)
        conversation_history, client_data, user_id = get_user_data(
            test_username)

        # Build a prompt
        prompt, prompt_type = build_member_chat_prompt(
            client_data=client_data,
            current_message="Hey Shannon, what should I eat for lunch today?",
            current_stage="Topic 1",
            trial_status="Initial Contact",
            full_name=test_username
        )

        # Check if bio context is included
        if "PROFILE INSIGHTS" in prompt:
            print("✅ Bio context found in prompt!")
            # Find and print the bio section
            start = prompt.find("--- PROFILE INSIGHTS")
            end = prompt.find("--- END PROFILE INSIGHTS ---") + \
                len("--- END PROFILE INSIGHTS ---")
            if start != -1 and end != -1:
                bio_section = prompt[start:end]
                print(f"   Bio Section:\n{bio_section}")
        else:
            print("❌ No bio context found in prompt")
            print(f"   Prompt preview: {prompt[:500]}...")

    except Exception as e:
        print(f"❌ Error testing prompt integration: {e}")

    print("\n=== TEST COMPLETE ===")


def test_background_fetcher_cycle():
    """Test the background fetcher cycle"""
    print("\n=== TESTING BACKGROUND FETCHER CYCLE ===")

    bio_fetcher = BackgroundBioFetcher()

    # Check for users needing bios
    users_needing_bios = bio_fetcher.get_new_users_needing_bios()
    print(
        f"Found {len(users_needing_bios)} users needing bios: {list(users_needing_bios)}")

    if users_needing_bios:
        print("✅ Bio fetcher can identify users needing bios")
    else:
        print("⚠️ No users found needing bios")


if __name__ == "__main__":
    # Run the basic cycle test first
    test_background_fetcher_cycle()

    # Then run the full integration test
    test_bio_fetch_and_integration()
