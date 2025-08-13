#!/usr/bin/env python3
"""
Calendly Follow-up Campaign Strategy
===================================

Target: People who received Calendly links but didn't book calls
Strategy: Re-engage with compelling offers to convert warm leads

CAMPAIGN APPROACH:
1. **Immediate Value Offer** - Free 28-day challenge (your existing offer)
2. **Urgency** - Limited spots, time-sensitive
3. **Social Proof** - Mention recent success stories
4. **Low Friction** - Direct link to sign up, no call required
5. **Personal Touch** - Reference their previous interest

MESSAGE TEMPLATES:
- **Primary Offer**: Free 28-day challenge with meal plan + workout
- **Secondary**: Direct coaching sign-up with special pricing
- **Fallback**: Free meal plan download

TARGET LIST (Cleaned - only non-signups):
1. @blissedlia (oldest - Jan 2025)
2. @burcherella (recent - July/Aug 2025)
3. @cocos_connected (recent - Aug 2025)
4. @cocos_pt_studio (multiple - July/Aug 2025)
5. @fi_perley (recent - July 2025)
6. @hannahjanedevlin (recent - July 2025)
7. @idivc2711 (recent - July 2025)
8. @kristyleecoop (recent - Aug 2025)
9. @linda.mhayes (recent - Aug 2025)
10. @mabel_fruta_murillo (recent - Aug 2025)
11. @melanieejane_ (recent - July 2025)
12. @reece_eykle (recent - July 2025)
13. @sanjanamunjal_ (recent - July 2025)
14. @sara_precious_lives (recent - July 2025)
15. @sentientpretzel (recent - Aug 2025)
16. @stabi (recent - Aug 2025)
17. @user_24341484705485852 (recent - July 2025)
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_calendly_recipients():
    """Get the list of Calendly recipients for follow-up."""
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

    return unique_users


def create_followup_messages():
    """Create personalized follow-up messages for each recipient."""

    recipients = get_calendly_recipients()

    print("🎯 CALENDLY FOLLOW-UP CAMPAIGN")
    print("=" * 60)
    print(f"Target: {len(recipients)} recipients who didn't book calls")
    print()

    # Message templates
    templates = {
        "primary": """Hey {username}! 👋

Quick follow-up - I had someone drop out of my coaching program and now I've got one last spot available at 50% off.

Since you were interested in the challenge, I thought I'd offer it to you first before opening it up to my waitlist.

This includes:
• Custom vegan meal plan
• 4-week workout program  
• Weekly check-ins with me
• Ongoing support
• Only $19.99/week instead of $39.99/week

Would you be keen for a quick 10-min call to see if it's a good fit? I can walk you through the program and answer any questions you've got.

Just reply "yes" and I'll send you the booking link! 💪""",

        "secondary": """Hey {username}! 

Quick follow-up - I had a couple of spots open up in my coaching program and thought of you since you were interested in the challenge.

Instead of the free trial, I can get you straight into the full program at 50% off your first month ($19.99/week instead of $39.99/week).

This includes:
• Everything from the challenge
• Ongoing support
• Weekly check-ins
• Meal plan updates

Interested? Just reply "yes" and I'll send you the sign-up link!""",

        "fallback": """Hey {username}! 

Hope you're doing well! 

I'm putting together a free vegan meal plan download for people who were interested in the challenge. 

Would you like me to send it over? Just reply "yes" and I'll DM it to you! 

It's got some of my best high-protein vegan recipes that clients love 💪"""
    }

    print("📝 MESSAGE TEMPLATES:")
    print("-" * 40)
    for template_name, template in templates.items():
        print(f"\n{template_name.upper()} TEMPLATE:")
        print(template)
        print()

    print("🎯 RECIPIENT LIST:")
    print("-" * 40)

    for i, (username, timestamp) in enumerate(recipients.items(), 1):
        # Determine message type based on timing
        msg_date = datetime.fromisoformat(timestamp.replace('+00:00', ''))
        days_ago = (datetime.now() - msg_date).days

        if days_ago <= 7:
            message_type = "primary"  # Recent - push the free challenge
        elif days_ago <= 30:
            message_type = "secondary"  # Medium - offer discount
        else:
            message_type = "fallback"  # Old - offer free meal plan

        print(f"{i:2d}. @{username}")
        print(f"    📅 Received: {days_ago} days ago")
        print(f"    💬 Message: {message_type}")
        print(f"    📋 Template: {templates[message_type][:50]}...")
        print()

    return recipients, templates


def create_bulk_messaging_script():
    """Create a script to send messages to all recipients."""

    script = '''#!/usr/bin/env python3
"""
Bulk Messaging Script for Calendly Recipients
=============================================

This script will send personalized follow-up messages to all Calendly recipients.
Run this after reviewing the message templates above.
"""

import sqlite3
from datetime import datetime
import time

DB_PATH = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.sqlite"

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
    
    print("\\n🎉 Follow-up campaign complete!")
    print("📊 Next steps:")
    print("   1. Monitor responses over next 48 hours")
    print("   2. Follow up with anyone who replies")
    print("   3. Track conversion rates")

if __name__ == "__main__":
    send_followup_messages()
'''

    with open("send_calendly_followups.py", "w", encoding='utf-8') as f:
        f.write(script)

    print("📝 Created send_calendly_followups.py")
    print("   Review the script and run it when ready!")


def main():
    """Create the follow-up campaign strategy."""
    recipients, templates = create_followup_messages()
    create_bulk_messaging_script()

    print("🎯 CAMPAIGN STRATEGY SUMMARY:")
    print("=" * 60)
    print(f"📊 Target: {len(recipients)} Calendly recipients")
    print(f"💬 Approach: Personalized follow-up based on timing")
    print(f"🎁 Primary Offer: Free 28-day challenge")
    print(f"💰 Secondary Offer: 50% off first month")
    print(f"📋 Fallback: Free meal plan download")
    print()
    print("📋 NEXT STEPS:")
    print("   1. Review message templates above")
    print("   2. Run send_calendly_followups.py when ready")
    print("   3. Monitor responses and follow up")
    print("   4. Track conversion rates")


if __name__ == "__main__":
    main()
