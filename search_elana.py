import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
c = conn.cursor()

print("=== Searching for elana/green related accounts ===")

# Search for usernames containing elana
c.execute("SELECT ig_username, subscriber_id, client_status FROM users WHERE ig_username LIKE '%elana%'")
elana_rows = c.fetchall()

print("Accounts containing 'elana':")
if elana_rows:
    for row in elana_rows:
        print(
            f"  Username: {row[0]}, Subscriber ID: {row[1]}, Status: {row[2]}")
else:
    print("  No accounts found")

# Search for usernames containing green
c.execute("SELECT ig_username, subscriber_id, client_status FROM users WHERE ig_username LIKE '%green%'")
green_rows = c.fetchall()

print("\nAccounts containing 'green':")
if green_rows:
    for row in green_rows:
        print(
            f"  Username: {row[0]}, Subscriber ID: {row[1]}, Status: {row[2]}")
else:
    print("  No accounts found")

# Search for le_greenies specifically
c.execute("SELECT ig_username, subscriber_id, client_status FROM users WHERE ig_username = 'le_greenies'")
le_greenies_row = c.fetchone()

print(f"\nle_greenies account:")
if le_greenies_row:
    print(
        f"  Username: {le_greenies_row[0]}, Subscriber ID: {le_greenies_row[1]}, Status: {le_greenies_row[2]}")

    # Check message count for le_greenies
    c.execute("SELECT COUNT(*) FROM messages WHERE ig_username = 'le_greenies'")
    msg_count = c.fetchone()[0]
    print(f"  Messages: {msg_count}")
else:
    print("  Not found")

# Search for any account that might be related (case insensitive)
print(f"\nSearching for similar usernames...")
search_terms = ['elena', 'greenie', 'green_', '_green']

for term in search_terms:
    c.execute(
        "SELECT ig_username, subscriber_id, client_status FROM users WHERE ig_username LIKE ?", (f'%{term}%',))
    rows = c.fetchall()
    if rows:
        print(f"\nAccounts containing '{term}':")
        for row in rows:
            print(
                f"  Username: {row[0]}, Subscriber ID: {row[1]}, Status: {row[2]}")

conn.close()
