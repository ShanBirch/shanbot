#!/usr/bin/env python3
import sqlite3
from datetime import datetime

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

print('=== FOLLOW STATUS REPORT ===')

# Check users already followed
cursor.execute('''
    SELECT username, followed_at, follow_status, hashtag_found 
    FROM new_leads 
    WHERE followed_at IS NOT NULL 
    ORDER BY followed_at DESC
''')
followed_users = cursor.fetchall()

print(f'✅ Users already followed: {len(followed_users)}')
for user in followed_users[:10]:  # Show last 10
    username, followed_at, status, hashtag = user
    print(f'  @{username} - {followed_at[:10]} via #{hashtag}')

if len(followed_users) > 10:
    print(f'  ... and {len(followed_users) - 10} more')

print()

# Check users ready to follow
cursor.execute('''
    SELECT COUNT(*) FROM new_leads 
    WHERE followed_at IS NULL 
    AND status = 'new'
''')
ready_to_follow = cursor.fetchone()[0]

print(f'🎯 Users ready to follow: {ready_to_follow}')

# Check follows today
today = datetime.now().strftime('%Y-%m-%d')
cursor.execute('''
    SELECT COUNT(*) FROM new_leads 
    WHERE DATE(followed_at) = ?
''', (today,))
follows_today = cursor.fetchone()[0]

print(f'📅 Follows today: {follows_today}/25')
print(f'📊 Can follow {25 - follows_today} more today')

conn.close()
