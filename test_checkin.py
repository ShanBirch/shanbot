#!/usr/bin/env python3
"""
Test script to verify the check-in flow works end-to-end
"""
import json
import time
import os
from datetime import datetime


def create_test_queue():
    """Create a test message queue for the followup manager to process"""
    test_queue = {
        "messages": [
            {
                "username": "test_monday_checkin",
                "message": "Good morning! Ready for the week? 💪",
                "topic": "Monday Morning Check-in",
                "checkin_type": "monday",
                "queued_time": datetime.now().isoformat()
            }
        ],
        "created_at": datetime.now().isoformat()
    }

    queue_file = "followup_queue.json"
    with open(queue_file, 'w') as f:
        json.dump(test_queue, f, indent=2)

    print(f"✅ Test queue created: {queue_file}")
    print(f"📄 Message queued for: test_monday_checkin")
    return queue_file


def monitor_queue_processing():
    """Monitor the queue file to see if messages are being processed"""
    queue_file = "followup_queue.json"

    print("🔍 Monitoring queue processing...")
    for i in range(30):  # Monitor for 30 seconds
        if os.path.exists(queue_file):
            try:
                with open(queue_file, 'r') as f:
                    queue_data = json.load(f)
                messages = queue_data.get("messages", [])
                print(f"📊 Queue status: {len(messages)} messages remaining")

                if len(messages) == 0:
                    print("✅ Queue processed successfully!")
                    return True

            except Exception as e:
                print(f"❌ Error reading queue: {e}")
        else:
            print("✅ Queue file removed - processing complete!")
            return True

        time.sleep(1)

    print("⏰ Timeout waiting for queue processing")
    return False


def main():
    print("🚀 Testing Check-in Flow")
    print("=" * 50)

    # Step 1: Create test queue
    queue_file = create_test_queue()

    # Step 2: Monitor processing
    print("\n⏳ Waiting for followup manager to process the queue...")
    success = monitor_queue_processing()

    if success:
        print("\n✅ Check-in flow test PASSED!")
        print("Your Monday morning check-ins should work correctly.")
    else:
        print("\n❌ Check-in flow test FAILED!")
        print("The followup manager may not be running or there's an issue.")

        # Check if followup manager is running
        try:
            import psutil
            python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline'])
                                if p.info['name'] == 'python.exe']

            followup_running = any('followup_manager.py' in ' '.join(p.info['cmdline'] or [])
                                   for p in python_processes)

            if followup_running:
                print("✅ Followup manager is running")
            else:
                print("❌ Followup manager is NOT running")
                print("💡 Try running: python followup_manager.py")

        except ImportError:
            print("🔍 Install psutil to check process status: pip install psutil")


if __name__ == "__main__":
    main()
