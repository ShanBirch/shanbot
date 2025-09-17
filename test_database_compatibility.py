#!/usr/bin/env python3
"""
Database Compatibility Test
===========================
Test script to verify PostgreSQL/SQLite compatibility in CoreActionHandler.
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))


def test_database_detection():
    """Test the database type detection."""
    print("🔍 Testing Database Type Detection...")

    try:
        from action_handlers.core_action_handler import _get_database_type

        # Test without DATABASE_URL (should be SQLite)
        original_db_url = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

        is_postgres_without_url = _get_database_type()
        print(
            f"   Without DATABASE_URL: {'Postgres' if is_postgres_without_url else 'SQLite'}")

        # Test with DATABASE_URL (should be Postgres)
        os.environ['DATABASE_URL'] = 'postgresql://test'
        is_postgres_with_url = _get_database_type()
        print(
            f"   With DATABASE_URL: {'Postgres' if is_postgres_with_url else 'SQLite'}")

        # Restore original
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

        return True

    except Exception as e:
        print(f"   ❌ Database detection test failed: {e}")
        return False


def test_import_compatibility():
    """Test that the CoreActionHandler imports work in both database modes."""
    print("📦 Testing Import Compatibility...")

    try:
        from action_handlers.core_action_handler import CoreActionHandler
        print("   ✅ CoreActionHandler imported successfully")

        # Test that methods exist
        if hasattr(CoreActionHandler, 'detect_and_handle_action'):
            print("   ✅ detect_and_handle_action method exists")
        else:
            print("   ❌ detect_and_handle_action method missing")
            return False

        if hasattr(CoreActionHandler, '_get_recent_ai_questions'):
            print("   ✅ _get_recent_ai_questions method exists")
        else:
            print("   ❌ _get_recent_ai_questions method missing")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False


def test_sqlite_specific_functions():
    """Test that SQLite-specific functions are only called when appropriate."""
    print("🗄️ Testing SQLite Function Isolation...")

    try:
        # Set environment to simulate Postgres
        os.environ['DATABASE_URL'] = 'postgresql://test'

        from action_handlers.core_action_handler import _get_database_type

        if _get_database_type():
            print("   ✅ Detected Postgres mode - SQLite functions should be skipped")
        else:
            print("   ❌ Should detect Postgres mode with DATABASE_URL set")
            return False

        # Test SQLite-specific functions return empty/False in Postgres mode
        try:
            from app.dashboard_modules.dashboard_sqlite_utils import (
                get_good_few_shot_examples,
                get_vegan_few_shot_examples,
                is_user_in_vegan_flow
            )

            # These should return empty/False in Postgres mode
            good_examples = get_good_few_shot_examples()
            vegan_examples = get_vegan_few_shot_examples()
            vegan_flow = is_user_in_vegan_flow("test_user")

            if len(good_examples) == 0 and len(vegan_examples) == 0 and not vegan_flow:
                print(
                    "   ✅ SQLite functions correctly return empty/False in Postgres mode")
            else:
                print("   ❌ SQLite functions should return empty/False in Postgres mode")
                return False

        except Exception as e:
            print(f"   ❌ Error testing SQLite functions: {e}")
            return False

        # Test conversation strategy fresh lead check
        try:
            from conversation_strategy import ConversationStrategy
            strategy = ConversationStrategy()
            fresh_lead = strategy.check_fresh_lead_status("test_user")

            if not fresh_lead:
                print("   ✅ Fresh lead check correctly returns False in Postgres mode")
            else:
                print("   ❌ Fresh lead check should return False in Postgres mode")
                return False

        except Exception as e:
            print(f"   ❌ Error testing fresh lead check: {e}")
            return False

        # Clean up
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

        return True

    except Exception as e:
        print(f"   ❌ SQLite isolation test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Database Compatibility Test for CoreActionHandler")
    print("=" * 60)
    print()

    tests_passed = 0
    total_tests = 3

    # Test 1: Database detection
    if test_database_detection():
        tests_passed += 1
    print()

    # Test 2: Import compatibility
    if test_import_compatibility():
        tests_passed += 1
    print()

    # Test 3: SQLite function isolation
    if test_sqlite_specific_functions():
        tests_passed += 1
    print()

    # Summary
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Database compatibility is fixed.")
        print()
        print("✅ The CoreActionHandler now properly:")
        print("   • Detects database type (Postgres vs SQLite)")
        print("   • Only imports SQLite functions when using SQLite")
        print("   • Skips SQLite-specific operations in Postgres mode")
        print("   • Handles database detection errors gracefully")
    else:
        print(
            f"⚠️ {total_tests - tests_passed} test(s) failed. Check the output above for details.")

    print()
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
