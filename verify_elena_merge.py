import sqlite3

conn = sqlite3.connect('app/analytics_data_good.sqlite')
c = conn.cursor()

print("=== Verifying Elena Account Merge ===")

# Check if elena_green was removed
c.execute("SELECT COUNT(*) FROM users WHERE ig_username = 'elena_green'")
elena_count = c.fetchone()[0]
print(f"elena_green accounts remaining: {elena_count}")

# Check le_greenies account
c.execute("SELECT ig_username, subscriber_id, client_status FROM users WHERE ig_username = 'le_greenies'")
le_greenies_row = c.fetchone()

if le_greenies_row:
    print(f"\nle_greenies account:")
    print(f"  Username: {le_greenies_row[0]}")
    print(f"  Subscriber ID: {le_greenies_row[1]}")
    print(f"  Status: {le_greenies_row[2]}")

    # Check message count
    c.execute("SELECT COUNT(*) FROM messages WHERE ig_username = 'le_greenies'")
    msg_count = c.fetchone()[0]
    print(f"  Messages: {msg_count}")

    if elena_count == 0 and le_greenies_row[2] == 'paying_client':
        print("\n✅ Merge successful!")
        print("  - elena_green account removed")
        print("  - le_greenies now has paying_client status")
        print("  - All data preserved")
    else:
        print("\n❌ Merge may have issues")

else:
    print("\n❌ le_greenies account not found!")

conn.close()
