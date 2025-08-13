#!/usr/bin/env python3
"""
Search for Hannah more broadly across all clients
"""

import sqlite3


def find_hannah_broad():
    """Find Hannah across all clients"""

    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    print("=== Searching for Hannah across ALL clients ===\n")

    # Search for Hannah by first name across all clients
    cursor.execute("""
        SELECT ig_username, subscriber_id, first_name, last_name, client_status, journey_stage
        FROM users 
        WHERE LOWER(first_name) LIKE '%hannah%' OR LOWER(ig_username) LIKE '%hannah%' OR LOWER(last_name) LIKE '%hannah%'
        ORDER BY client_status, ig_username
    """)

    hannah_results = cursor.fetchall()

    if hannah_results:
        print(f"Found {len(hannah_results)} Hannah(s) across all clients:\n")
        for i, row in enumerate(hannah_results, 1):
            print(
                f"{i}. {row[0]} (ID: {row[1]}, Name: {row[2]} {row[3]}, Status: {row[4]})")
    else:
        print("❌ No Hannah found across all clients")

        # Let's also check for similar names
        print("\n=== Searching for similar names ===")
        similar_names = ["hanna", "hannah", "devlin", "dev"]
        for name in similar_names:
            cursor.execute("""
                SELECT ig_username, subscriber_id, first_name, last_name, client_status
                FROM users 
                WHERE LOWER(first_name) LIKE ? OR LOWER(last_name) LIKE ? OR LOWER(ig_username) LIKE ?
                ORDER BY ig_username
            """, (f"%{name}%", f"%{name}%", f"%{name}%"))

            results = cursor.fetchall()
            if results:
                print(f"\nFound {len(results)} with '{name}':")
                for row in results:
                    print(
                        f"  - {row[0]} (Name: {row[2]} {row[3]}, Status: {row[4]})")

    conn.close()
    return hannah_results


if __name__ == "__main__":
    find_hannah_broad()
