#!/usr/bin/env python3
"""
Wednesday afternoon check-in message for first-time clients
"""


def create_wednesday_checkin_message():
    """Create the Wednesday afternoon check-in message"""

    message = """Heya! 👋

Hope your week's been going well! It's Wednesday afternoon which means it's time for our first check-in! 

So here's what we do in these check-ins - we go over how you're going for the week, I get you to prepare meals for me and show me the macro content, and also get you to film exercises for me so we can perfect your technique.

The conversation can last anywhere from 20 minutes to 2 days depending on how much we have to cover and how much support you need.

How have you gone over the first 3 days of the challenge so far? What's been working well and what's been a bit tricky?"""

    return message


def send_wednesday_checkin():
    """Send the Wednesday check-in message to clients"""

    message = create_wednesday_checkin_message()

    print("📝 WEDNESDAY CHECK-IN MESSAGE")
    print("=" * 50)
    print(message)
    print("=" * 50)
    print()
    print("💡 This message:")
    print("   ✅ Sets expectations for check-in process")
    print("   ✅ Explains meal prep and macro tracking")
    print("   ✅ Mentions exercise filming for technique")
    print("   ✅ Clarifies conversation duration (20 mins to 2 days)")
    print("   ✅ Asks about first 3 days progress")
    print("   ✅ Uses Shannon's casual Australian tone")

    return message


if __name__ == "__main__":
    send_wednesday_checkin()
