import sqlite3
import json
from datetime import datetime, timedelta
import re

try:
    # Connect to the database
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    # Get cutoff date (4 days ago)
    four_days_ago = datetime.now() - timedelta(days=4)
    cutoff_date = four_days_ago.strftime('%Y-%m-%d')
    print(f'Looking for emails submitted since: {cutoff_date}')

    # Method 1: Check users table for recent challenge_email entries
    print('\n=== CHECKING USERS TABLE FOR RECENT CHALLENGE EMAILS ===')
    cursor.execute("""
        SELECT ig_username, first_name, last_name, challenge_email, challenge_type, challenge_signup_date
        FROM users 
        WHERE challenge_email IS NOT NULL 
        AND challenge_email != ''
        AND challenge_signup_date > ?
        ORDER BY challenge_signup_date DESC
    """, (cutoff_date,))

    recent_challenge_users = cursor.fetchall()
    print(
        f'Found {len(recent_challenge_users)} users with recent challenge emails:')

    for user in recent_challenge_users:
        ig_username, first_name, last_name, email, challenge_type, signup_date = user
        print(
            f'  ✅ {ig_username} - {first_name} {last_name} - {email} ({challenge_type}) - {signup_date}')

    # Method 2: Check conversation_history table for email mentions
    print('\n=== CHECKING CONVERSATION HISTORY FOR EMAIL MENTIONS ===')
    cursor.execute("""
        SELECT DISTINCT ch.ig_username, u.first_name, u.last_name, ch.message_text, ch.timestamp
        FROM conversation_history ch
        JOIN users u ON ch.ig_username = u.ig_username
        WHERE ch.message_text LIKE '%@%'
        AND (ch.message_text LIKE '%.com%' OR ch.message_text LIKE '%.au%' OR ch.message_text LIKE '%.org%' 
             OR ch.message_text LIKE '%.net%' OR ch.message_text LIKE '%.gmail%')
        AND ch.timestamp > ?
        ORDER BY ch.timestamp DESC
        LIMIT 20
    """, (cutoff_date,))

    conversation_emails = cursor.fetchall()
    print(
        f'Found {len(conversation_emails)} conversation messages with email patterns:')

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    conversation_email_users = []

    for conv in conversation_emails:
        ig_username, first_name, last_name, message_text, timestamp = conv
        emails = re.findall(email_pattern, message_text, re.IGNORECASE)

        if emails:
            conversation_email_users.append({
                'ig_username': ig_username,
                'first_name': first_name or 'Unknown',
                'last_name': last_name or '',
                'email': emails[0],
                'timestamp': timestamp,
                'message_snippet': message_text[:100] + '...' if len(message_text) > 100 else message_text
            })

            print(
                f'  📧 {ig_username} - {first_name} {last_name} - {emails[0]} - {timestamp}')
            print(f'     Message: {message_text[:80]}...')

    # Method 3: Check if challenge_entries table exists, if not create it
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='challenge_entries';")
    challenge_table_exists = cursor.fetchone() is not None

    if not challenge_table_exists:
        print('\n=== CREATING CHALLENGE ENTRIES TABLE ===')
        cursor.execute("""
            CREATE TABLE challenge_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ig_username TEXT NOT NULL UNIQUE,
                name TEXT,
                email TEXT,
                challenge_type TEXT DEFAULT 'Plant-Based',
                entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                source TEXT DEFAULT 'auto_detected'
            )
        """)
        conn.commit()
        print('✅ Challenge entries table created!')
    else:
        cursor.execute("SELECT COUNT(*) FROM challenge_entries")
        existing_count = cursor.fetchone()[0]
        print(f'\n=== CHALLENGE ENTRIES TABLE EXISTS ===')
        print(f'Current entries: {existing_count}')

    # Add users to challenge entries
    print('\n=== ADDING USERS TO CHALLENGE ENTRIES ===')
    added_count = 0

    # Add users who already have challenge_email in users table
    for user in recent_challenge_users:
        ig_username, first_name, last_name, email, challenge_type, signup_date = user
        full_name = f"{first_name or ''} {last_name or ''}".strip() or 'Unknown'

        cursor.execute(
            "SELECT COUNT(*) FROM challenge_entries WHERE ig_username = ?", (ig_username,))
        exists = cursor.fetchone()[0] > 0

        if not exists:
            cursor.execute("""
                INSERT OR IGNORE INTO challenge_entries (ig_username, name, email, challenge_type, source)
                VALUES (?, ?, ?, ?, ?)
            """, (ig_username, full_name, email, challenge_type or 'Plant-Based', 'users_table'))
            added_count += 1
            print(
                f'✅ Added from users table: {ig_username} ({full_name}) - {email}')

    # Add users from conversation history
    for user in conversation_email_users:
        # Check if this user doesn't already have challenge_email set
        cursor.execute(
            "SELECT challenge_email FROM users WHERE ig_username = ?", (user['ig_username'],))
        existing_email = cursor.fetchone()

        if not existing_email or not existing_email[0]:
            cursor.execute(
                "SELECT COUNT(*) FROM challenge_entries WHERE ig_username = ?", (user['ig_username'],))
            exists = cursor.fetchone()[0] > 0

            if not exists:
                full_name = f"{user['first_name']} {user['last_name']}".strip(
                ) or 'Unknown'
                cursor.execute("""
                    INSERT OR IGNORE INTO challenge_entries (ig_username, name, email, challenge_type, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (user['ig_username'], full_name, user['email'], 'Plant-Based', 'conversation'))
                added_count += 1
                print(
                    f'✅ Added from conversation: {user["ig_username"]} ({full_name}) - {user["email"]}')

    conn.commit()

    # Final summary
    cursor.execute("SELECT COUNT(*) FROM challenge_entries")
    total_entries = cursor.fetchone()[0]

    print(f'\n=== SUMMARY ===')
    print(f'Users added to challenge entries: {added_count}')
    print(f'Total challenge entries now: {total_entries}')

    # Show recent entries
    cursor.execute("""
        SELECT ig_username, name, email, challenge_type, entry_date, source
        FROM challenge_entries 
        ORDER BY entry_date DESC 
        LIMIT 10
    """)
    recent_entries = cursor.fetchall()

    print(f'\nMost recent challenge entries:')
    for entry in recent_entries:
        ig_username, name, email, challenge_type, entry_date, source = entry
        print(
            f'  {ig_username} - {name} - {email} - {challenge_type} - {entry_date} ({source})')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    if 'conn' in locals():
        conn.close()

print('\n✅ Process completed!')
