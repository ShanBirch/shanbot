#!/usr/bin/env python3
"""
Test script to verify coaching analysis integration with analyze_followers.py
"""

import os
import sys


def test_imports():
    """Test if all required modules can be imported"""
    try:
        from identify_potential_clients_sqlite import analyze_for_coaching_potential, add_follower_to_database
        print("✅ Successfully imported coaching analysis functions")
        return True
    except ImportError as e:
        print(f"❌ Failed to import coaching functions: {e}")
        return False


def test_database_setup():
    """Test if the database is set up correctly"""
    try:
        from identify_potential_clients_sqlite import get_all_followers_from_database
        followers = get_all_followers_from_database()
        print(
            f"✅ Database accessible. Found {len(followers)} followers with analysis")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_sample_analysis():
    """Test coaching analysis on sample data"""
    try:
        from identify_potential_clients_sqlite import analyze_for_coaching_potential

        # Sample Instagram analysis data (like what analyze_followers.py produces)
        sample_data = {
            'posts_analyzed': 3,
            'timestamp': '2024-01-01T12:00:00',
            'interests': ['fitness', 'healthy eating', 'plant-based nutrition'],
            'lifestyle_indicators': ['gym workouts', 'meal prep', 'vegan recipes'],
            'recent_activities': ['posted workout video', 'shared vegan meal'],
            'conversation_topics': ['fitness goals', 'nutrition advice', 'workout tips'],
            'profile_bio': {
                'bio_text': 'Fitness enthusiast 🌱 Plant-based lifestyle',
                'goals': 'Building muscle on a vegan diet',
                'fitness_level': 'Intermediate'
            }
        }

        coaching_result = analyze_for_coaching_potential(sample_data)
        if coaching_result:
            score = coaching_result.get('coaching_potential_score', 0)
            category = coaching_result.get('coaching_category', 'Unknown')
            print(f"✅ Sample analysis successful: {score}/100 ({category})")
            return True
        else:
            print("❌ Sample analysis returned no results")
            return False
    except Exception as e:
        print(f"❌ Sample analysis error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Coaching Analysis Integration")
    print("=" * 50)

    tests = [
        ("Import coaching functions", test_imports),
        ("Database setup", test_database_setup),
        ("Sample coaching analysis", test_sample_analysis),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️  This test failed")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your analyze_followers.py script is ready to find coaching prospects!")
        print("\n💡 Next steps:")
        print("1. Run: python anaylize_followers.py")
        print("2. Let it analyze some followers from your Instagram_followers.txt")
        print("3. Check the 'Prospects' tab in your dashboard to see results")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
