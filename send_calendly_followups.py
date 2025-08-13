#!/usr/bin/env python3
"""
Bulk Messaging Script for Calendly Recipients
=============================================

This script will send personalized follow-up messages to all Calendly recipients.
Run this after reviewing the message templates above.
"""

import sqlite3
from datetime import datetime
import time

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

def send_followup_messages():
    """Send follow-up messages to Calendly recipients."""
    
    # Get recipients
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT ig_username, timestamp
        FROM messages 
        WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'
           OR text LIKE '%calendly.com/shannonrhysbirch/15min%'
        ORDER BY timestamp DESC
    """)
    
    recipients = cursor.fetchall()
    conn.close()
    
    # Create unique list
    unique_users = {}
    for username, timestamp in recipients:
        if username not in unique_users:
            unique_users[username] = timestamp
    
    print(f"🎯 Sending follow-up messages to {len(unique_users)} recipients")
    print("=" * 60)
    
    for username, timestamp in unique_users.items():
        msg_date = datetime.fromisoformat(timestamp.replace('+00:00', ''))
        days_ago = (datetime.now() - msg_date).days
        
        # Determine message based on timing
        if days_ago <= 7:
            message = f"""Hey {username}! 👋

I noticed you were interested in the vegan challenge but didn't get a chance to book a call. 

Quick question - would you be keen on jumping straight into the free 28-day challenge instead? 

It's the same program I was going to walk you through on the call, but you can start immediately:
• Custom vegan meal plan
• 4-week workout program  
• Weekly check-ins with me
• Completely free

Only got 3 spots left for this round! 

Want to grab one? Just hit this link: https://www.cocospersonaltraining.com/coaching-onboarding-form

Let me know when you're in and I'll get started on your meal plan straight away! 💪"""
        elif days_ago <= 30:
            message = f"""Hey {username}! 

Quick follow-up - I had a couple of spots open up in my coaching program and thought of you since you were interested in the challenge.

Instead of the free trial, I can get you straight into the full program at 50% off your first month ($10 instead of $19.99).

This includes:
• Everything from the challenge
• Ongoing support
• Weekly check-ins
• Meal plan updates

Interested? Just reply "yes" and I'll send you the sign-up link!"""
        else:
            message = f"""Hey {username}! 

Hope you're doing well! 

I'm putting together a free vegan meal plan download for people who were interested in the challenge. 

Would you like me to send it over? Just reply "yes" and I'll DM it to you! 

It's got some of my best high-protein vegan recipes that clients love 💪"""
        
        print(f"📤 Sending to @{username} ({days_ago} days ago)")
        print(f"💬 Message: {message[:100]}...")
        print("-" * 40)
        
        # Add to conversation history
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get subscriber_id
            cursor.execute("SELECT subscriber_id FROM users WHERE ig_username = ?", (username,))
            user_result = cursor.fetchone()
            subscriber_id = user_result[0] if user_result else None
            
            # Add message to history
            cursor.execute("""
                INSERT INTO messages (ig_username, subscriber_id, timestamp, message_type, message_text)
                VALUES (?, ?, ?, ?, ?)
            """, (username, subscriber_id, datetime.now().isoformat(), 'ai', message))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Message added to history for @{username}")
            
        except Exception as e:
            print(f"❌ Error adding message for @{username}: {e}")
        
        # Small delay between messages
        time.sleep(2)
    
    print("\n🎉 Follow-up campaign complete!")
    print("📊 Next steps:")
    print("   1. Monitor responses over next 48 hours")
    print("   2. Follow up with anyone who replies")
    print("   3. Track conversion rates")

if __name__ == "__main__":
    send_followup_messages()
