#!/usr/bin/env python3
"""
Test script for the outreach system components
"""

import sqlite3
import os
from datetime import datetime


def create_test_database():
    """Create a test database with sample data"""
    print("Creating test database...")

    # Ensure app directory exists
    os.makedirs('app', exist_ok=True)

    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Create potential_clients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS potential_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            source_account TEXT,
            bio TEXT,
            interests TEXT,
            created_at TEXT,
            followed_at TEXT,
            follow_status TEXT,
            dm_sent_at TEXT,
            dm_message TEXT,
            dm_status TEXT
        )
    ''')

    # Insert test data
    test_users = [
        ('test_user_1', 'kristyleecoop', 'Plant based fitness enthusiast',
         'fitness,vegan', datetime.now().isoformat()),
        ('test_user_2', 'nimai_delgado', 'Vegan bodybuilder and coach',
         'bodybuilding,plant-based', datetime.now().isoformat()),
        ('test_user_3', 'le_greenies', 'Sustainable living advocate',
         'sustainability,vegan', datetime.now().isoformat()),
    ]

    for user_data in test_users:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO potential_clients 
                (username, source_account, bio, interests, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', user_data)
        except sqlite3.IntegrityError:
            pass  # User already exists

    conn.commit()
    conn.close()
    print("Test database created successfully!")


def test_follow_script():
    """Test the follow script functionality"""
    print("\nTesting follow script...")

    try:
        from follow_users import UserFollower
        follower = UserFollower()

        # Test database connection
        users = follower.get_unfollowed_users()
        print(f"Found {len(users)} users ready to follow")

        # Test daily follow check
        follows_today = follower.check_daily_follows()
        print(f"Follows completed today: {follows_today}")

        print("Follow script test: PASSED")
        return True

    except Exception as e:
        print(f"Follow script test: FAILED - {str(e)}")
        return False


def test_dm_script():
    """Test the DM script functionality"""
    print("\nTesting DM script...")

    try:
        from send_delayed_dms import DMSender
        dm_sender = DMSender()

        # Test message generation
        test_message = dm_sender.generate_message(
            'test_user', 'kristyleecoop', 'Plant based fitness', 'fitness,vegan'
        )
        print(f"Generated message: {test_message}")

        # Test daily DM check
        dms_today = dm_sender.check_daily_dms()
        print(f"DMs sent today: {dms_today}")

        print("DM script test: PASSED")
        return True

    except Exception as e:
        print(f"DM script test: FAILED - {str(e)}")
        return False


def test_scheduler():
    """Test the scheduler functionality"""
    print("\nTesting scheduler...")

    try:
        from outreach_scheduler import OutreachScheduler
        scheduler = OutreachScheduler()

        print("Scheduler initialized successfully")
        print("Scheduler test: PASSED")
        return True

    except Exception as e:
        print(f"Scheduler test: FAILED - {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=== Outreach System Test Suite ===")

    # Create test database
    create_test_database()

    # Run tests
    tests = [
        test_follow_script,
        test_dm_script,
        test_scheduler
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed! The outreach system is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python find_potential_clients.py --search-mode online --num-clients 100' to get real leads")
        print("2. Run 'python follow_users.py' to start following users")
        print("3. Wait 3 hours, then run 'python send_delayed_dms.py' to send DMs")
        print("4. Or use 'python outreach_scheduler.py' for full automation")
    else:
        print("✗ Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
