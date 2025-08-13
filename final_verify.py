import sqlite3
import json

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

# Check both kristyleecoop entries
cursor.execute("SELECT ig_username, subscriber_id, client_status, journey_stage FROM users WHERE ig_username IN ('kristyleecoop', 'Kristyleecoop')")
results = cursor.fetchall()

print("Final verification of kristyleecoop status:")
for row in results:
    username, subscriber_id, status, journey = row
    print(f"\nUsername: {username}")
    print(f"Subscriber ID: {subscriber_id}")
    print(f"Client Status: {status}")
    
    if journey:
        try:
            data = json.loads(journey)
            is_paying = data.get('is_paying_client', False)
            current_stage = data.get('current_stage', 'Unknown')
            print(f"Is Paying Client: {is_paying}")
            print(f"Current Stage: {current_stage}")
            
            if is_paying and current_stage == "Paying Client":
                print("✅ CONFIRMED: User is properly marked as paid member!")
            else:
                print("❌ User is not properly marked as paid member")
        except json.JSONDecodeError:
            print(f"Raw journey_stage: {journey}")
    else:
        print("❌ No journey_stage data found")

conn.close() 