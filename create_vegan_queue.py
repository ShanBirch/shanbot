#!/usr/bin/env python3
"""
Create Vegan Outreach Queue - Generate a followup queue for users who need the vegan message
"""

import sqlite3
import json
from datetime import datetime


def create_vegan_queue():
    """Create a followup queue for vegan outreach messages"""

    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get users who followed back but haven't been messaged
    query = """
    SELECT DISTINCT username 
    FROM processing_queue 
    WHERE follow_back_status = 'yes'
    AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending')
    AND DATE(followed_at) >= DATE('now', '-14 days')
    ORDER BY follow_back_checked_at DESC 
    LIMIT 30
    """

    cursor.execute(query)
    users = [row[0] for row in cursor.fetchall()]

    # Create queue data
    message = "Heya :) Love your content! How long have you been vegan for?"

    queue_data = {
        'messages': [
            {
                'username': user,
                'message': message,
                'topic': 'Vegan outreach',
                'queued_time': datetime.now().isoformat()
            }
            for user in users
        ],
        'created_at': datetime.now().isoformat()
    }

    # Save to followup queue
    with open('followup_queue.json', 'w') as f:
        json.dump(queue_data, f, indent=2)

    print(f"📝 Created followup queue with {len(users)} messages")
    print(f"💬 Message: '{message}'")
    print()
    print("🎯 Users to message:")
    for i, user in enumerate(users[:15], 1):  # Show first 15
        print(f"  {i:2d}. @{user}")

    if len(users) > 15:
        print(f"   ... and {len(users) - 15} more")

    print()
    print("🚀 To send these messages:")
    print("   1. Run: python followup_manager.py")
    print("   2. The script will process all queued messages automatically")

    conn.close()


if __name__ == "__main__":
    create_vegan_queue()
