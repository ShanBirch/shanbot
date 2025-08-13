#!/usr/bin/env python3
"""
Test script to show examples of DMs that would be generated for Shannon
"""

import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')


def generate_sample_dm(username, account_mode):
    """Generate a sample DM using the exact prompt from the follow-back checker"""
    if account_mode == 'local':
        prompt = f"""
You are Shannon, a 32-year-old casual Australian fitness coach who runs Coco's PT studio in Hampton, Melbourne. You're DMing @{username} who just followed you back on Instagram.

Generate a short, authentic DM in Shannon's voice based on these real examples from his conversations:

REAL SHANNON EXAMPLES:
- "Heya! How's your week been?" 
- "Hey! Thanks for the follow back!"
- "Hey there! Thanks for connecting, how's your week going?"
- "oh nice as dude! Where abouts are you?"
- "Haha yeah! How things?"

SHANNON'S STYLE:
- Very casual Australian ("heya", "hey", "yeah", "cheers mate", "no worries")
- Keeps it SHORT (5-15 words max)
- Natural and conversational, not salesy
- Often asks simple follow-up questions
- Shows genuine interest without being pushy
- Sometimes makes connections like "oh I saw you liked..." 

TARGET AUDIENCE: Bayside Melbourne mums and locals

RULES:
- Maximum 15 words
- Use Shannon's exact casual language style
- Be friendly but chill, not overly excited
- Don't mention fitness/training immediately
- NO emojis
- Sound like you're just genuinely connecting

Generate ONE short DM that sounds exactly like Shannon:
"""
    else:  # online mode
        prompt = f"""
You are Shannon, a 32-year-old casual Australian fitness coach who runs Coco's Connected online coaching. You're DMing @{username} who just followed you back on Instagram.

Generate a short, authentic DM in Shannon's voice based on these real examples from his conversations:

REAL SHANNON EXAMPLES:
- "Heya! How's your week been?"
- "Hey! Thanks for the follow back!"
- "Hey there! Thanks for connecting, how's your week going?"
- "oh nice as dude! Where abouts are you?"
- "Haha yeah! How things?"

SHANNON'S STYLE:
- Very casual Australian ("heya", "hey", "yeah", "cheers mate", "no worries")
- Keeps it SHORT (5-15 words max)
- Natural and conversational, not salesy
- Often asks simple follow-up questions
- Shows genuine interest without being pushy
- Sometimes makes connections like "oh I saw you liked..."

TARGET AUDIENCE: Vegan/plant-based people interested in fitness

RULES:
- Maximum 15 words
- Use Shannon's exact casual language style
- Be friendly but chill, not overly excited
- Don't mention fitness/training immediately
- NO emojis
- Sound like you're just genuinely connecting
- Can casually reference plant-based lifestyle if it fits naturally

Generate ONE short DM that sounds exactly like Shannon:
"""

    try:
        response = model.generate_content(prompt)
        if response and response.text:
            # Clean up the response
            message = response.text.strip()
            # Remove quotes if the AI wrapped the message in them
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            if message.startswith("'") and message.endswith("'"):
                message = message[1:-1]
            return message
    except Exception as e:
        print(f"Error generating message: {e}")
        return "Heya! Thanks for the follow back!"


def main():
    print("🎯 SHANNON'S AUTOMATED DM EXAMPLES")
    print("=" * 50)
    print()

    # Local mode examples (Bayside gym clients)
    print("🏠 LOCAL MODE (@cocos_pt_studio)")
    print("Target: Bayside Melbourne mums & locals")
    print("-" * 30)

    local_usernames = ["sarah_brighton", "melissa_hampton",
                       "kate_bayside", "jenny_sandringham", "lisa_melbourne"]

    for i, username in enumerate(local_usernames, 1):
        dm = generate_sample_dm(username, 'local')
        print(f"{i}. To @{username}: \"{dm}\"")

    print()
    print("🌱 ONLINE MODE (@cocos_connected)")
    print("Target: Vegan/plant-based fitness enthusiasts")
    print("-" * 30)

    online_usernames = ["vegan_sarah", "plantbased_mike",
                        "green_goddess", "veganfitness", "plant_warrior"]

    for i, username in enumerate(online_usernames, 1):
        dm = generate_sample_dm(username, 'online')
        print(f"{i}. To @{username}: \"{dm}\"")

    print()
    print("🔥 KEY FEATURES OF SHANNON'S DM STYLE:")
    print("✅ Very short (5-15 words)")
    print("✅ Casual Australian voice ('heya', 'hey', 'yeah')")
    print("✅ Genuine connection, not salesy")
    print("✅ Often includes a simple question")
    print("✅ No emojis or excessive enthusiasm")
    print("✅ Sounds like a real person, not a bot")
    print()
    print("💬 These DMs are automatically sent to EVERYONE who follows back")
    print("⏰ With 45-75 second delays between each DM to avoid spam detection")


if __name__ == "__main__":
    main()
