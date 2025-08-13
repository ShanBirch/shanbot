#!/usr/bin/env python3
import sqlite3


def reset_unfollow_queue():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    # Count users marked as limit reached
    c.execute("""
        SELECT COUNT(*) FROM processing_queue 
        WHERE follow_back_status = 'no_unfollow_limit_reached'
    """)

    count = c.fetchone()[0]
    print(f"Found {count} users marked as 'no_unfollow_limit_reached'")

    if count > 0:
        # Reset their status to 'no' so they'll be processed again
        c.execute("""
            UPDATE processing_queue 
            SET follow_back_status = 'no'
            WHERE follow_back_status = 'no_unfollow_limit_reached'
        """)

        conn.commit()
        print(f"✅ Reset {count} users back to 'no' status")
        print("They will be unfollowed the next time you run check_daily_follow_backs.py")

        # Show first 10 users that were reset
        c.execute("""
            SELECT username, followed_at 
            FROM processing_queue 
            WHERE follow_back_status = 'no'
            ORDER BY followed_at DESC 
            LIMIT 10
        """)

        print("\nSample of users now ready to be unfollowed:")
        for row in c.fetchall():
            print(f"  {row[0]} | {row[1]}")
    else:
        print("No users need to be reset")

    conn.close()


if __name__ == "__main__":
    reset_unfollow_queue()
