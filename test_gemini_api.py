#!/usr/bin/env python3
"""
Test script to verify Gemini API key and scopes
"""

import os
import google.generativeai as genai


def test_gemini_api():
    """Test the Gemini API key"""
    api_key = os.getenv(
        'GEMINI_API_KEY', 'AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y')

    if not api_key:
        print("❌ No API key available")
        return False

    if api_key == 'AIzaSyCGawrpt6EFWeaGDQ3rgf2yMS8-DMcXw0Y':
        print("🔧 Using fallback API key from webhook files")
    else:
        print("✅ Using environment variable API key")

    print(f"✅ API key found: {api_key[:10]}...")

    try:
        # Configure Gemini
        genai.configure(api_key=api_key)

        # Try to create a model instance
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Model instance created successfully")

        # Try a simple test generation
        response = model.generate_content(
            "Hello, this is a test. Please respond with 'API working'")

        if response and response.text:
            print(f"✅ API test successful: {response.text}")
            return True
        else:
            print("❌ API test failed: No response")
            return False

    except Exception as e:
        print(f"❌ API test failed: {e}")

        # Check if it's a scope issue
        if "insufficient authentication scopes" in str(e).lower():
            print("\n🔧 SOLUTION: Your API key needs broader scopes.")
            print("Go to https://makersuite.google.com/app/apikey")
            print("Create a new API key or regenerate the existing one")
            print("Make sure to enable all available scopes")

        return False


if __name__ == "__main__":
    print("🧪 Testing Gemini API...")
    success = test_gemini_api()
    if success:
        print("\n🎉 Gemini API is working correctly!")
    else:
        print("\n💡 Please fix the API key issue and try again")
