import sqlite3
import os
from datetime import datetime, timedelta


def check_missed_dms():
    # Connect to database
    db_path = r'C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find users who followed back but never got DMs
    cursor.execute('''
        SELECT username, follow_back_status, dm_status, follow_back_checked_at, followed_at
        FROM processing_queue 
        WHERE follow_back_status = 'yes' 
        AND (dm_status IS NULL OR dm_status != 'sent')
        AND follow_back_checked_at >= date('now', '-7 days')
        ORDER BY follow_back_checked_at DESC
    ''')

    results = cursor.fetchall()
    print(
        f'Found {len(results)} users who followed back but never received DMs:')
    print()

    if results:
        print("These users followed back but never received their DMs:")
        print("="*60)
        for i, (username, fb_status, dm_status, checked_at, followed_at) in enumerate(results, 1):
            print(f'{i}. @{username}')
            print(f'   - Followed back: {fb_status}')
            print(f'   - DM status: {dm_status or "None"}')
            print(f'   - Checked at: {checked_at}')
            print(f'   - Originally followed: {followed_at}')
            print()
    else:
        print("No users found who followed back but missed their DMs.")

    conn.close()
    return results


if __name__ == "__main__":
    check_missed_dms()
