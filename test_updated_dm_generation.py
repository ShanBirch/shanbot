#!/usr/bin/env python3
"""
Test script to show examples of updated DMs in Shannon's exact style
"""

import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = "AIzaSyCrYZwENVEhfo0IF6puWyQaYlFW1VRWY-k"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')


def generate_sample_dm(username, account_mode):
    """Generate a sample DM using the updated prompt style"""
    if account_mode == 'local':
        prompt = f"""
You are Shannon, a 32-year-old casual Australian fitness coach who runs Coco's PT studio in Hampton, Melbourne. You're DMing @{username} who just followed you back on Instagram.

Generate a short, authentic DM in Shannon's voice based on these EXACT examples:

SHANNON'S ACTUAL STYLE EXAMPLES:
- "Heya! appreciate the follow! i saw that you were local to bayside? Been Around here for long?"
- "Hey! Thanks for the follow back! Noticed you're around Bayside too?"
- "Heya! Cheers for following back! Saw you're local to the area?"

SHANNON'S VOICE:
- Very casual and conversational
- Uses "Heya!" or "Hey!" to start
- Says "appreciate the follow" or "thanks for the follow back" 
- Mentions what he "saw" or "noticed" about them
- References being "local to bayside" or "around the area"
- Asks simple follow-up questions like "Been around here for long?"
- Uses lowercase for casual words like "i" instead of "I"
- Australian but not overly so

TARGET AUDIENCE: Bayside Melbourne mums and locals

CRITICAL RULES:
- Must be 8-15 words total
- Reference that they're "local to bayside" or "around the area" 
- Ask a simple question like "Been around here for long?" or "How long you been in the area?"
- Sound natural and conversational, not scripted
- Use Shannon's exact casual language patterns

Generate ONE casual DM message exactly like Shannon's style:
"""
    else:  # online mode
        prompt = f"""
You are Shannon, a casual Australian fitness coach who runs Coco's Connected online coaching. You're DMing @{username} who just followed you back on Instagram.

Generate a short, authentic DM in Shannon's voice based on these EXACT examples:

SHANNON'S ACTUAL STYLE EXAMPLES:
- "Heya! Appreciate the follow! Saw your Plant Based? Awesome! How long for?"
- "Hey! Thanks for the follow back! Noticed you're vegan too? How long?"
- "Heya! Cheers for following back! Saw you're plant based, awesome!"

SHANNON'S VOICE:
- Very casual and conversational  
- Uses "Heya!" or "Hey!" to start
- Says "appreciate the follow" or "thanks for the follow back"
- Mentions what he "saw" or "noticed" about them  
- References being "plant based" or "vegan"
- Shows enthusiasm with "Awesome!" or "Nice!"
- Asks simple questions like "How long for?" or "How long?"
- Uses lowercase casually

TARGET AUDIENCE: Vegan/plant-based people interested in fitness

CRITICAL RULES:
- Must be 8-15 words total
- Reference that they're "plant based" or "vegan" 
- Ask a simple question like "How long for?" or "How long you been at it?"
- Sound natural and conversational, not scripted
- Use Shannon's exact casual language patterns
- Show enthusiasm but keep it chill

Generate ONE casual DM message exactly like Shannon's style:
"""

    try:
        response = model.generate_content(prompt)
        message = response.text.strip()

        # Clean up the message
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        if message.startswith("'") and message.endswith("'"):
            message = message[1:-1]

        return message
    except Exception as e:
        if account_mode == 'local':
            return "Heya! appreciate the follow! i saw you were local to bayside?"
        else:
            return "Heya! Appreciate the follow! Saw your Plant Based? Awesome!"


# Test with different usernames
local_usernames = ["sarah_brighton", "emma_hampton",
                   "jenny_bayside", "kate_sandringham", "melissa_local"]
online_usernames = ["vegan_sarah", "plantbased_mike",
                    "green_emma", "vegan_lifestyle", "healthy_plants"]

print("🎯 SHANNON'S UPDATED AUTOMATED DM EXAMPLES")
print("=" * 60)

print("\n🏠 LOCAL MODE (@cocos_pt_studio)")
print("Target: Bayside Melbourne mums & locals")
print("-" * 40)

for i, username in enumerate(local_usernames, 1):
    dm = generate_sample_dm(username, 'local')
    print(f"{i}. **\"{dm}\"**")

print("\n🌱 ONLINE MODE (@cocos_connected)")
print("Target: Vegan/plant-based fitness enthusiasts")
print("-" * 40)

for i, username in enumerate(online_usernames, 1):
    dm = generate_sample_dm(username, 'online')
    print(f"{i}. **\"{dm}\"**")

print("\n" + "=" * 60)
print("✅ These messages will be automatically sent to people")
print("   who follow back Shannon's accounts!")
