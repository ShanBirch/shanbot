#!/usr/bin/env python3
"""
Run Smart Lead Finder in Local Mode
For finding Bayside gym prospects using cocos_pt_studio account
"""

import subprocess
import sys
import os


def main():
    """Run Smart Lead Finder in local mode."""
    print("🏠 STARTING SMART LEAD FINDER - LOCAL MODE")
    print("="*50)
    print("🎯 Target: Women 30+ (especially mums) in Bayside area")
    print("📍 Location: Hampton/Brighton/Sandringham/Mentone")
    print("👤 Account: cocos_pt_studio")
    print("📊 Daily Limit: 75 follows")
    print("="*50)

    # Path to smart lead finder
    script_path = os.path.join(os.path.dirname(
        __file__), "smart_lead_finder.py")

    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return

    try:
        # Run with local mode
        subprocess.run([
            sys.executable,
            script_path,
            "--mode", "local"
        ], check=True)

    except KeyboardInterrupt:
        print("\n🛑 Script stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with error code: {e.returncode}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
