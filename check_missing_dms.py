#!/usr/bin/env python3
import sqlite3


def check_missing_dms():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    print("Users who followed back but never got DMed:")

    # Find users marked as "yes" (followed back) but no DM sent
    c.execute("""
        SELECT username, followed_at, follow_back_status, dm_status, follow_back_checked_at
        FROM processing_queue 
        WHERE follow_back_status = 'yes'
        AND (dm_status IS NULL OR dm_status = '' OR dm_status = 'pending')
        ORDER BY follow_back_checked_at DESC
    """)

    missing_dms = c.fetchall()

    print(
        f"Found {len(missing_dms)} users who followed back but never got DMed:")

    for i, row in enumerate(missing_dms[:15], 1):  # Show first 15
        username, followed_at, fb_status, dm_status, checked_at = row
        dm_display = dm_status if dm_status else "NULL"
        print(
            f"{i:2d}. {username} | followed: {followed_at[:10]} | checked: {checked_at[:10] if checked_at else 'N/A'} | dm: {dm_display}")

    if len(missing_dms) > 15:
        print(f"... and {len(missing_dms) - 15} more")

    # Also check users with failed DM attempts
    print("\nUsers with failed DM attempts:")
    c.execute("""
        SELECT username, followed_at, dm_status, follow_back_checked_at
        FROM processing_queue 
        WHERE follow_back_status = 'yes'
        AND dm_status LIKE '%failed%'
        ORDER BY follow_back_checked_at DESC
        LIMIT 10
    """)

    failed_dms = c.fetchall()
    for row in failed_dms:
        print(f"  {row[0]} | {row[1][:10]} | {row[2]}")

    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Users who followed back but need DMs: {len(missing_dms)}")
    print(f"   • Users with failed DM attempts: {len(failed_dms)}")
    print(
        f"   • Total people who should have gotten DMs: {len(missing_dms) + len(failed_dms)}")

    conn.close()
    return len(missing_dms)


if __name__ == "__main__":
    check_missing_dms()
