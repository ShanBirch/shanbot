#!/usr/bin/env python3
"""
Search for specific clients in the database
"""

import sqlite3
import json


def find_clients():
    """Find the specific clients mentioned"""

    # Connect to database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # List of clients to find
    clients_to_find = [
        # New challenge clients
        "marc potter",
        "hannah devlin",
        "romy",
        "blisseda",
        "amy",
        "burchella",
        # Existing clients
        "kirstyleecoop",
        "shaneminehan"
    ]

    print("=== Searching for specific clients ===\n")

    found_clients = []

    for search_term in clients_to_find:
        print(f"Searching for: {search_term}")

        # Search by ig_username
        cursor.execute("""
            SELECT ig_username, subscriber_id, first_name, last_name, client_status, journey_stage
            FROM users 
            WHERE LOWER(ig_username) LIKE ? OR LOWER(first_name) LIKE ? OR LOWER(last_name) LIKE ?
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))

        results = cursor.fetchall()

        if results:
            for row in results:
                print(
                    f"  ✅ Found: {row[0]} (ID: {row[1]}, Name: {row[2]} {row[3]}, Status: {row[4]})")
                found_clients.append({
                    'ig_username': row[0],
                    'subscriber_id': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'client_status': row[4],
                    'journey_stage': row[5]
                })
        else:
            print(f"  ❌ Not found: {search_term}")

    print(f"\n=== Summary ===")
    print(f"Found {len(found_clients)} clients")

    # Group by status
    new_clients = [c for c in found_clients if 'trial' in c['client_status'].lower(
    ) or 'challenge' in c['client_status'].lower()]
    existing_clients = [
        c for c in found_clients if 'paying' in c['client_status'].lower()]

    print(f"\nNew Challenge Clients ({len(new_clients)}):")
    for client in new_clients:
        print(
            f"  - {client['ig_username']} ({client['first_name']} {client['last_name']})")

    print(f"\nExisting Paying Clients ({len(existing_clients)}):")
    for client in existing_clients:
        print(
            f"  - {client['ig_username']} ({client['first_name']} {client['last_name']})")

    conn.close()
    return found_clients


if __name__ == "__main__":
    find_clients()
