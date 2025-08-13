#!/usr/bin/env python3
"""
Test script to simulate what the dashboard Enable Auto Mode button does
"""

import subprocess
import sys
from pathlib import Path


def test_auto_launch():
    """Test launching the auto responder like the dashboard button does"""
    try:
        print("🧪 Testing Auto Mode Launch...")

        # Get the script path (same as in the dashboard)
        script_path = str(Path(__file__).parent /
                          "run_simple_auto_responder.py")
        print(f"📍 Script path: {script_path}")

        # Check if script exists
        if not Path(script_path).exists():
            print(f"❌ Script not found at: {script_path}")
            return False

        print(f"✅ Script found at: {script_path}")

        # Launch it (same way as dashboard)
        print("🚀 Launching auto responder...")
        process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(
                subprocess, 'CREATE_NEW_CONSOLE') else 0
        )

        print(f"✅ Auto responder launched successfully!")
        print(f"📊 Process ID: {process.pid}")
        print("💡 Check the new console window that should have opened")

        return True

    except Exception as e:
        print(f"❌ Failed to launch auto responder: {e}")
        return False


if __name__ == "__main__":
    test_auto_launch()
