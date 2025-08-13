import sqlite3
import json

conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

# List of Instagram accounts likely conversing with Cocos
target_users = ['rawadrh', 'sellawindi']

# Search for these users and look for coaching inquiries in their conversation history
user_placeholders = ', '.join('?' for _ in target_users)
query = f"SELECT ig_username, metrics_json FROM users WHERE ig_username IN ({user_placeholders});"
cursor.execute(query, target_users)

results = cursor.fetchall()

print("Users likely inquiring about Cocos' coaching services:")
if results:
    found_inquiries = False
    for row in results:
        ig_username = row[0]
        metrics_json = row[1]

        try:
            metrics = json.loads(metrics_json)
            conversation_history = metrics.get('conversation_history', [])

            coaching_inquiry_messages = []
            inquiry_keywords = ['interested', 'cost', 'price',
                                'how much', 'tell me about', 'help with', 'sign up', 'join']

            for message in conversation_history:
                if isinstance(message, dict) and 'text' in message and isinstance(message['text'], str):
                    message_text = message['text'].lower()
                    if 'coaching' in message_text and any(keyword in message_text for keyword in inquiry_keywords):
                        coaching_inquiry_messages.append(
                            message['text'][:200] + "...")  # Append snippet

            if coaching_inquiry_messages:
                found_inquiries = True
                print(f"\nInstagram Account: @{ig_username}")
                for message_snippet in coaching_inquiry_messages:
                    print(f"  - {message_snippet}")

        except json.JSONDecodeError:
            # Handle cases where metrics_json is not valid JSON
            print(f"\nInstagram Account: @{ig_username}")
            print(
                f"  Error processing metrics_json for @{ig_username} (not valid JSON): {metrics_json[:300]}...")
        except Exception as e:
            # Catch other potential errors during processing
            print(f"\nInstagram Account: @{ig_username}")
            print(
                f"  Error processing conversation history for @{ig_username}: {e}")

    if not found_inquiries:
        print("No specific coaching inquiries found among the selected users.")

else:
    print("No data found for the specified Instagram accounts.")

# Specify the user whose conversation history you want to examine
user_to_examine = 'rawadrh'  # Or choose another user from the previous list

cursor.execute(
    'SELECT metrics_json FROM users WHERE ig_username = ?;', (user_to_examine,))

result = cursor.fetchone()

if result:
    metrics_json = result[0]
    print(f"Conversation history for @{user_to_examine}:\n")
    try:
        metrics = json.loads(metrics_json)
        conversation_history = metrics.get('conversation_history', [])

        if conversation_history:
            # Print the full conversation history for inspection
            print(json.dumps(conversation_history, indent=4))
        else:
            print(f"No conversation history found for @{user_to_examine}.")

    except json.JSONDecodeError:
        print(
            f"Error decoding metrics_json for @{user_to_examine}: {metrics_json[:300]}...")
    except Exception as e:
        print(f"Error processing metrics_json for @{user_to_examine}: {e}")

else:
    print(f"User @{user_to_examine} not found or has no metrics_json.")

# Search for users with 'coaching' in their metrics_json (as a broad initial filter)
cursor.execute(
    "SELECT ig_username, metrics_json FROM users WHERE metrics_json LIKE '%coaching%';")

results = cursor.fetchall()

print("Users who likely enquired about coaching services (based on conversation keywords):")
if results:
    found_inquiries = False
    inquiry_keywords = ['interested', 'cost', 'price',
                        'how much', 'tell me about', 'help with', 'sign up', 'join']

    for row in results:
        ig_username = row[0]
        metrics_json = row[1]

        try:
            metrics = json.loads(metrics_json)
            conversation_history = metrics.get('conversation_history', [])

            user_coaching_inquiry_messages = []

            # Iterate through messages and check if from user and contain inquiry keywords
            for message in conversation_history:
                if isinstance(message, dict) and message.get('type') == 'user' and 'text' in message and isinstance(message['text'], str):
                    message_text = message['text'].lower()
                    if 'coaching' in message_text and any(keyword in message_text for keyword in inquiry_keywords):
                        user_coaching_inquiry_messages.append(
                            message['text'][:200] + "...")  # Append snippet

            if user_coaching_inquiry_messages:
                found_inquiries = True
                print(f"\nInstagram Account: @{ig_username}")
                for message_snippet in user_coaching_inquiry_messages:
                    print(f"  - {message_snippet}")

        except json.JSONDecodeError:
            # Handle cases where metrics_json is not valid JSON
            print(f"\nInstagram Account: @{ig_username}")
            print(
                f"  Error processing metrics_json for @{ig_username} (not valid JSON): {metrics_json[:300]}...")
        except Exception as e:
            # Catch other potential errors during processing
            print(f"\nInstagram Account: @{ig_username}")
            print(
                f"  Error processing conversation history for @{ig_username}: {e}")

    if not found_inquiries:
        print(
            "No specific coaching inquiries found in user messages with inquiry keywords.")

else:
    print("No users found with 'coaching' in their metrics_json.")

conn.close()
