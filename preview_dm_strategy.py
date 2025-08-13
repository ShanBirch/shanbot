#!/usr/bin/env python3
"""
DM Strategy Preview - Shows what messages would be sent to each user
"""

import sqlite3
import random
from datetime import datetime

# Message templates (same as in dm_strategy.py) - Shannon's authentic voice
message_templates = {
    'vegan_fitness': [
        "Heya! Noticed you're into plant based fitness 🌱 How's your training going?",
        "Hey! Saw you're passionate about vegan fitness, that's solid! How long you been at it?",
        "Hey! Fellow plant based here 🌱 How do you find balancing nutrition and training?"
    ],
    'vegan_lifestyle': [
        "Heya! Love seeing another plant based person 🌱 How long you been vegan?",
        "Hey! Noticed you're passionate about plant based living, that's awesome! What got you into it?",
        "Hey! Fellow vegan here 🌱 Been vegetarian since birth myself, how's your journey been?"
    ],
    'fitness_general': [
        "Hey! Love your fitness content 💪 How's your training been going?",
        "Heya! Noticed you're into fitness, that's awesome! What's your current focus?",
        "Hey! Your fitness journey looks solid 💪 How long you been training?"
    ],
    'nutrition_focused': [
        "Hey! Love your approach to nutrition 🌱 What's your biggest focus right now?",
        "Heya! Noticed you're into clean eating, that's solid! How's it going for you?",
        "Hey! Your nutrition content is great 💚 What's been your biggest game changer?"
    ]
}


def get_hashtag_category(hashtag):
    """Categorize hashtags to select appropriate message template"""
    vegan_fitness_tags = ['follower_of_buff_vegans',
                          'follower_of_veganfitness', 'follower_of_strengthtraining']
    vegan_lifestyle_tags = ['follower_of_eatveganbabe', 'follower_of_vegan.daily.recipes', 'follower_of_therawadvantage',
                            'plantbasedlifestyle', 'follower_of_vancouverwithlove', 'follower_of_squeakybeanveg']
    nutrition_tags = ['follower_of_cleanfooddirtygirl',
                      'follower_of_elevatenutritionteam', 'follower_of_plantprotein', 'follower_of_tofoo']

    if hashtag in vegan_fitness_tags:
        return 'vegan_fitness'
    elif hashtag in vegan_lifestyle_tags:
        return 'vegan_lifestyle'
    elif hashtag in nutrition_tags:
        return 'nutrition_focused'
    else:
        return 'fitness_general'


def get_personalized_message(hashtag):
    """Get a personalized message based on hashtag source"""
    category = get_hashtag_category(hashtag)
    return random.choice(message_templates[category])


# Get today's followed users
conn = sqlite3.connect('app/analytics_data_good.sqlite')
cursor = conn.cursor()

today = datetime.now().strftime('%Y-%m-%d')
cursor.execute('''
    SELECT username, hashtag_found, followed_at
    FROM new_leads 
    WHERE DATE(followed_at) = ?
    AND (dm_sent_at IS NULL OR dm_sent_at = '')
    ORDER BY followed_at DESC
''', (today,))

dm_targets = cursor.fetchall()

print('=== DM STRATEGY PREVIEW ===')
print(f'📝 Messages for {len(dm_targets)} users followed today:')
print('(These will be sent 24 hours after following)\n')

# Group by category for easier review
categories = {}
for username, hashtag, followed_at in dm_targets:
    category = get_hashtag_category(hashtag)
    message = get_personalized_message(hashtag)

    if category not in categories:
        categories[category] = []

    categories[category].append({
        'username': username,
        'hashtag': hashtag,
        'message': message
    })

# Display by category
for category, users in categories.items():
    print(f"🎯 {category.upper().replace('_', ' ')} ({len(users)} users):")
    for user in users:
        print(f"  @{user['username']} (#{user['hashtag']})")
        print(f"  📄 Message: {user['message']}")
        print()

print(f"⏰ These DMs will be ready to send tomorrow at this time!")
print(f"📊 Run 'python dm_strategy.py' in 24 hours to send them automatically")

conn.close()
