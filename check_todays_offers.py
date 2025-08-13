import sqlite3
from datetime import datetime, date

# Connect to the conversation history database
conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

# Get today's date
today = date.today().strftime('%Y-%m-%d')
print(f'🔍 Checking for challenge offers on {today}...')

# Check for challenge offer phrases in today's messages
challenge_phrases = [
    '28-day', '28 day', 'challenge', 'transformation',
    'reckon you\'d be perfect', 'taking on', 'free coaching',
    'spots left', 'onboarded', 'free trial', 'program'
]

print('\n📊 Searching conversation_history table...')
cursor.execute('''
    SELECT ig_username, message_text, timestamp 
    FROM conversation_history 
    WHERE DATE(timestamp) = ? 
    AND message_type = 'ai'
    ORDER BY timestamp DESC
''', (today,))

todays_ai_messages = cursor.fetchall()
print(f'Found {len(todays_ai_messages)} AI messages today')

# Show first few messages to see what we have
if todays_ai_messages:
    print(f'\n📋 Sample of today\'s AI messages:')
    for i, (username, message, timestamp) in enumerate(todays_ai_messages[:5]):
        print(f'{i+1}. @{username} at {timestamp}: {message[:100]}...')

# Check each message for challenge phrases
offers_found = []
for username, message, timestamp in todays_ai_messages:
    message_lower = message.lower()
    for phrase in challenge_phrases:
        if phrase in message_lower:
            offers_found.append((username, message, timestamp, phrase))
            break

if offers_found:
    print(f'\n🎯 FOUND {len(offers_found)} CHALLENGE OFFERS TODAY:')
    for username, message, timestamp, matched_phrase in offers_found:
        print(f'\n👤 @{username} at {timestamp}')
        print(f'🔑 Matched phrase: "{matched_phrase}"')
        print(f'💬 Message: {message}')
        print('─' * 80)
else:
    print('\n❌ No challenge offers found in conversation_history today')

conn.close()
