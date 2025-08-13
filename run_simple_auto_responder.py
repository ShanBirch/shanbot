#!/usr/bin/env python3
"""
Run the Simple Auto Responder
This script starts the improved auto responder that properly handles timing delays.
"""

import sys
import os


def main():
    try:
        print("🚀 Starting Simple Auto Responder...")
        print("This new system fixes the timing issues and works reliably.")
        print("=" * 60)

        # Add the correct paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dashboard_modules_path = os.path.join(
            current_dir, 'app', 'dashboard_modules')

        print(f"📍 Adding path: {dashboard_modules_path}")

        if not os.path.exists(dashboard_modules_path):
            raise FileNotFoundError(
                f"Dashboard modules directory not found: {dashboard_modules_path}")

        sys.path.insert(0, dashboard_modules_path)

        # Check if simple_auto_responder.py exists
        responder_file = os.path.join(
            dashboard_modules_path, 'simple_auto_responder.py')
        if not os.path.exists(responder_file):
            raise FileNotFoundError(
                f"simple_auto_responder.py not found: {responder_file}")

        print(f"✅ Found simple_auto_responder.py at: {responder_file}")

        # Import and run
        print("📦 Importing simple_auto_responder...")
        from simple_auto_responder import main as responder_main

        print("🎯 Starting auto responder...")
        responder_main()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n" + "="*60)
        print("DEBUG INFO:")
        print(f"Current directory: {os.getcwd()}")
        print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
        print(f"Python path: {sys.path}")
        print("="*60)

        # Keep console open so user can see the error
        input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
