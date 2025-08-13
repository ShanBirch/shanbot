#!/usr/bin/env python3
"""
Start Auto Response Sender
"""

import subprocess
import sys
import os
import time


def start_auto_sender():
    print("🤖 Starting Auto Response Sender...")

    # Get the path to auto_response_sender.py
    script_path = os.path.join(os.path.dirname(
        __file__), "auto_response_sender.py")

    try:
        # Start the auto response sender
        process = subprocess.Popen([
            sys.executable,
            script_path
        ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(f"✅ Auto Response Sender started with PID: {process.pid}")
        print("📝 Check the logs in app/dashboard_modules/auto_sender.log")
        print("🔄 The sender will check for responses every 60 seconds")

        # Wait a moment to see if it starts successfully
        time.sleep(3)

        if process.poll() is None:
            print("✅ Process is running successfully")
        else:
            print("❌ Process exited unexpectedly")
            stdout, stderr = process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")

    except Exception as e:
        print(f"❌ Error starting auto response sender: {e}")


if __name__ == "__main__":
    start_auto_sender()
