#!/usr/bin/env python3
"""
Test script for the new Prospects tab functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))


def test_prospects_import():
    """Test if we can import the prospects module"""
    try:
        # Add the app/dashboard_modules directory to the path
        import sys
        import os
        dashboard_modules_path = os.path.join(
            os.path.dirname(__file__), 'app', 'dashboard_modules')
        if dashboard_modules_path not in sys.path:
            sys.path.insert(0, dashboard_modules_path)

        from prospects import display_prospects_tab, get_prospects_data
        print("✅ Successfully imported prospects module")
        return True
    except ImportError as e:
        print(f"❌ Failed to import prospects module: {e}")
        return False


def test_coaching_analysis_import():
    """Test if we can import the coaching analysis functions"""
    try:
        from identify_potential_clients_sqlite import get_high_potential_clients_sqlite, generate_coaching_outreach_message
        print("✅ Successfully imported coaching analysis functions")
        return True
    except ImportError as e:
        print(f"❌ Failed to import coaching analysis functions: {e}")
        return False


def test_database_connection():
    """Test if we can connect to the database"""
    try:
        from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        print(
            f"✅ Successfully connected to database. Found {user_count} users.")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False


def test_prospects_data():
    """Test if we can get prospects data"""
    try:
        from identify_potential_clients_sqlite import get_high_potential_clients_sqlite

        # Add the app/dashboard_modules directory to the path
        import sys
        import os
        dashboard_modules_path = os.path.join(
            os.path.dirname(__file__), 'app', 'dashboard_modules')
        if dashboard_modules_path not in sys.path:
            sys.path.insert(0, dashboard_modules_path)

        from prospects import get_existing_users, get_prospects_data

        # Get existing users
        existing_users = get_existing_users()
        print(f"✅ Found {len(existing_users)} existing users")

        # Get prospects data
        prospects = get_prospects_data(min_score=50)
        print(f"✅ Found {len(prospects)} prospects with score >= 50")

        if prospects:
            sample_prospect = prospects[0]
            print(
                f"✅ Sample prospect: @{sample_prospect.get('ig_username')} (Score: {sample_prospect.get('coaching_potential_score')})")

        return True
    except Exception as e:
        print(f"❌ Failed to get prospects data: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Prospects Tab Functionality")
    print("=" * 50)

    tests = [
        ("Import prospects module", test_prospects_import),
        ("Import coaching analysis", test_coaching_analysis_import),
        ("Database connection", test_database_connection),
        ("Get prospects data", test_prospects_data),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️  This test failed - check the error above")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The Prospects tab should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("💡 Make sure you've run the coaching analysis on some followers first.")


if __name__ == "__main__":
    main()
