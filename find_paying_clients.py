#!/usr/bin/env python3
"""
Search through paying clients to find specific ones
"""

import sqlite3


def find_paying_clients():
    """Find all paying clients and search for specific ones"""

    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    print("=== All Paying Clients ===")

    # Get all paying clients
    cursor.execute("""
        SELECT ig_username, subscriber_id, first_name, last_name, client_status, journey_stage
        FROM users 
        WHERE client_status LIKE '%paying%' OR client_status LIKE '%trial%'
        ORDER BY ig_username
    """)

    paying_clients = cursor.fetchall()

    print(f"Found {len(paying_clients)} paying/trial clients:\n")

    for i, row in enumerate(paying_clients, 1):
        print(
            f"{i}. {row[0]} (ID: {row[1]}, Name: {row[2]} {row[3]}, Status: {row[4]})")

    print("\n=== Looking for specific clients ===")

    # Search terms to look for
    search_terms = [
        "marc", "potter", "hannah", "devlin", "romy", "blisseda",
        "amy", "burchella", "kirsty", "coop", "shane", "minahan"
    ]

    found_matches = []

    for client in paying_clients:
        ig_username = client[0].lower()
        first_name = (client[2] or "").lower()
        last_name = (client[3] or "").lower()

        for term in search_terms:
            if term in ig_username or term in first_name or term in last_name:
                found_matches.append(client)
                print(
                    f"✅ MATCH: {client[0]} (Name: {client[2]} {client[3]}, Status: {client[4]})")
                break

    if not found_matches:
        print("❌ No exact matches found. Here are the closest possibilities:")
        for client in paying_clients:
            print(f"  - {client[0]} ({client[2]} {client[3]})")

    conn.close()
    return paying_clients


if __name__ == "__main__":
    find_paying_clients()
