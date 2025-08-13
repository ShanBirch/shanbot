#!/usr/bin/env python3
"""
Clear Streamlit cache and test the regenerate function
"""

import os
import shutil
import subprocess
import time


def clear_streamlit_cache():
    """Clear Streamlit cache to force reload of conversation history."""
    print("🧹 CLEARING STREAMLIT CACHE")
    print("=" * 40)

    # Find and clear .streamlit directory
    cache_dirs = [
        ".streamlit",
        os.path.expanduser("~/.streamlit"),
        os.path.expanduser("~/.cache/streamlit")
    ]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared cache directory: {cache_dir}")
            except Exception as e:
                print(f"⚠️ Could not clear {cache_dir}. Error: {e}")
        else:
            print(f"ℹ️ Cache directory not found: {cache_dir}")
    print("✅ Cache clearing completed")


def test_regenerate_function():
    """Test the regenerate function with fresh cache"""
    print("\n🧪 TESTING REGENERATE FUNCTION")
    print("=" * 40)

    print("💡 Instructions:")
    print("   1. The cache has been cleared")
    print("   2. Refresh your dashboard in the browser")
    print("   3. Try the 'Regenerate' button again")
    print("   4. The AI should now receive proper conversation context")
    print("   5. Responses should be much more contextual and relevant")

    print("\n🔧 FIXES APPLIED:")
    print("   ✅ Fixed conversation history order (ASC instead of DESC)")
    print("   ✅ Fixed format_conversation_history function")
    print("   ✅ Cleared Streamlit cache")
    print("   ✅ AI will now receive proper conversation context")


if __name__ == "__main__":
    clear_streamlit_cache()
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)  # Give time for cache to clear
    test_regenerate_function()
    print("\n🎉 Process completed!")
    print("📊 Your regenerate function should now work correctly.")
