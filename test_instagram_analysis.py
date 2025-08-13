#!/usr/bin/env python3
"""
Test script to debug Instagram analysis issues from the dashboard.
This replicates exactly what the dashboard does when you click "Analyze Bio".
"""

import subprocess
import tempfile
import os
import sys


def test_instagram_analysis(ig_username: str):
    """Test the Instagram analysis exactly like the dashboard does it"""

    print(f"🔍 Testing Instagram analysis for: {ig_username}")
    print("=" * 60)

    try:
        # Step 1: Create temporary file (exactly like dashboard)
        print("Step 1: Creating temporary file...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(ig_username)
            temp_file_path = temp_file.name

        print(f"✅ Created temp file: {temp_file_path}")

        # Step 2: Check if analyzer script exists
        print("\nStep 2: Checking analyzer script...")
        analyzer_script_path = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\anaylize_followers.py"

        if not os.path.exists(analyzer_script_path):
            print(f"❌ Analyzer script not found at: {analyzer_script_path}")
            return False

        print(f"✅ Found analyzer script at: {analyzer_script_path}")

        # Step 3: Prepare command (exactly like dashboard)
        print("\nStep 3: Preparing command...")
        cmd = ["python", analyzer_script_path,
               "--followers-list", temp_file_path, "--force"]
        print(f"Command: {' '.join(cmd)}")
        print(f"Working directory: {os.path.dirname(analyzer_script_path)}")

        # Step 4: Execute command with full output capture
        print("\nStep 4: Executing command...")
        print("=" * 40)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=os.path.dirname(analyzer_script_path)
        )

        print(f"Return code: {result.returncode}")
        print("\n--- STDOUT ---")
        print(result.stdout)
        print("\n--- STDERR ---")
        print(result.stderr)
        print("=" * 40)

        # Step 5: Clean up
        print("\nStep 5: Cleaning up...")
        try:
            os.unlink(temp_file_path)
            print(f"✅ Deleted temp file: {temp_file_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Could not delete temp file: {cleanup_error}")

        # Step 6: Analyze results
        print("\nStep 6: Results Analysis...")
        if result.returncode == 0:
            print("✅ SUCCESS: Instagram analysis completed successfully!")
            return True
        else:
            print("❌ FAILED: Instagram analysis failed")
            print(
                f"Error details: {result.stderr if result.stderr else result.stdout}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Analysis took longer than 5 minutes")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test with a real account that we know works
    test_username = "cocos_pt_studio"

    if len(sys.argv) > 1:
        test_username = sys.argv[1]

    print(f"Testing Instagram analysis with username: {test_username}")
    print("This replicates exactly what the dashboard does when you click 'Analyze Bio'")
    print()

    success = test_instagram_analysis(test_username)

    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED: The Instagram analysis should work from the dashboard!")
    else:
        print("💥 TEST FAILED: This shows why the dashboard analysis is failing!")
    print("=" * 60)
