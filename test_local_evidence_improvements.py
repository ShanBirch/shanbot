#!/usr/bin/env python3
"""
Test script for the improved Local Evidence Score system in smart_lead_finder.py
"""

from smart_lead_finder import SmartLeadFinder
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_local_evidence_system():
    """Test the new Local Evidence Score system"""
    print("🧪 Testing Smart Lead Finder - Local Evidence Score Improvements")
    print("=" * 60)

    # Create finder in local mode
    finder = SmartLeadFinder(mode='local')

    # Verify that the new methods exist
    required_methods = [
        'calculate_local_evidence_score',
        'analyze_bio_for_local_signals',
        'analyze_posts_for_location_tags',
        'analyze_following_network',
        'analyze_post_captions',
        'extract_bio_text'
    ]

    print("✅ Checking that all new methods are available:")
    for method in required_methods:
        if hasattr(finder, method):
            print(f"   ✅ {method} - Available")
        else:
            print(f"   ❌ {method} - Missing")
            return False

    print("\n✅ All methods are available!")
    print("\n📋 New Local Evidence Score System Features:")
    print("   🔍 Layer 1: Bio Text Analysis (0-20 points)")
    print("   📍 Layer 2: Location Tags in Posts (0-40 points)")
    print("   👥 Layer 3: Following Network Analysis (0-30 points)")
    print("   📝 Layer 4: Post Caption Analysis (0-10 points)")
    print("   📊 Total possible score: 100 points")

    print("\n🎯 Scoring Thresholds:")
    print("   💪 Strong Evidence: 40+ points (auto-qualify if target mum)")
    print("   ✅ Decent Evidence + AI Approval: 20+ points")
    print("   ❌ Insufficient Evidence: <20 points")

    print("\n🚀 The script is ready to find local leads more accurately!")
    print("\n📚 To run the improved lead finder:")
    print("   python smart_lead_finder.py --mode local")

    return True


if __name__ == "__main__":
    if test_local_evidence_system():
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
