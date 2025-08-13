#!/usr/bin/env python3
"""
Search specifically for Hannah in paying clients
"""

import sqlite3


def find_hannah():
    """Find Hannah in paying clients"""

    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    print("=== Searching for Hannah in paying clients ===\n")

    # Search for Hannah by first name
    cursor.execute("""
        SELECT ig_username, subscriber_id, first_name, last_name, client_status, journey_stage
        FROM users 
        WHERE (client_status LIKE '%paying%' OR client_status LIKE '%trial%')
        AND (LOWER(first_name) LIKE '%hannah%' OR LOWER(ig_username) LIKE '%hannah%')
        ORDER BY ig_username
    """)

    hannah_results = cursor.fetchall()

    if hannah_results:
        print(f"Found {len(hannah_results)} Hannah(s) in paying clients:\n")
        for i, row in enumerate(hannah_results, 1):
            print(
                f"{i}. {row[0]} (ID: {row[1]}, Name: {row[2]} {row[3]}, Status: {row[4]})")
    else:
        print("❌ No Hannah found in paying clients")

        # Let's also check all paying clients to see if we missed her
        print("\n=== All paying clients for reference ===")
        cursor.execute("""
            SELECT ig_username, subscriber_id, first_name, last_name, client_status
            FROM users 
            WHERE client_status LIKE '%paying%' OR client_status LIKE '%trial%'
            ORDER BY ig_username
        """)

        all_paying = cursor.fetchall()
        for i, row in enumerate(all_paying, 1):
            print(f"{i}. {row[0]} (Name: {row[2]} {row[3]}, Status: {row[4]})")

    conn.close()
    return hannah_results


if __name__ == "__main__":
    find_hannah()
