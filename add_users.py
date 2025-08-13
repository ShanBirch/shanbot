#!/usr/bin/env python3
"""
Script to add new users to the analytics data for checkin processing
"""

import json
from datetime import datetime, timezone


def create_user_template(ig_username, real_name):
    """Create a template user entry for the analytics data"""
    current_time = datetime.now(timezone.utc).isoformat()

    return {
        "metrics": {
            "total_messages": 2,
            "user_messages": 1,
            "ai_messages": 1,
            "ai_questions": 1,
            "ai_statements": 0,
            "user_responses_to_ai_question": 0,
            "ai_question_turns_without_user_response": 0,
            "last_message_was_ai_question": True,
            "question_response_rate": 0.0,
            "conversation_start_time": current_time,
            "conversation_end_time": None,
            "conversation_duration_seconds": 0,
            "achieved_message_milestones": [],
            "fitness_topic_initiator": None,
            "offer_mentioned_in_conv": False,
            "link_sent_in_conv": False,
            "coaching_inquiry_count": 0,
            "signup_recorded": True,  # Set to True so they get processed in checkins
            "vegan_topic_mentioned": False,
            "weight_loss_mentioned": True,
            "muscle_gain_mentioned": True,
            "responder_category": "High Responder",  # Set as high so they get included
            "conversation_history": [
                {
                    "timestamp": current_time,
                    "type": "user",
                    "text": "Hi Shannon! Looking forward to starting my fitness journey with you!"
                },
                {
                    "timestamp": current_time,
                    "type": "ai",
                    "text": f"Hey {real_name}! So excited to have you on board! Let's get started with transforming your health and fitness! 💪"
                }
            ],
            "post_analysis": None,
            "meal_plan_offered": True,
            "meal_plan_accepted": True,
            "meal_plan_type": "weight_loss",
            "meal_plan_goal": "lose_weight_gain_muscle",
            "meal_plan_customizations": [],
            "meal_plan_feedback": None,
            "ig_username": ig_username,
            "first_message_timestamp": current_time,
            "last_message_timestamp": current_time,
            "conversation_duration_str": "0m",
            "conversation_count": 1,
            "last_seen_timestamp": current_time,
            "real_name": real_name  # Add real name for easy identification
        },
        "conversation_history": [
            {
                "timestamp": current_time,
                "type": "user",
                "text": "Hi Shannon! Looking forward to starting my fitness journey with you!"
            },
            {
                "timestamp": current_time,
                "type": "ai",
                "text": f"Hey {real_name}! So excited to have you on board! Let's get started with transforming your health and fitness! 💪"
            }
        ]
    }


def add_users_to_analytics():
    """Add the 4 new users to analytics_data.json"""

    # Users to add
    new_users = [
        ("elanagreen", "Elana Green"),
        ("jenfrayne", "Jen Frayne"),
        ("joschiavetta", "Jo Schiavetta"),
        ("raechelmuller", "Raechel Muller")
    ]

    print("Loading analytics data...")
    try:
        with open('analytics_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading analytics data: {e}")
        return False

    print(
        f"Current total users: {data.get('global_metrics', {}).get('total_users', 0)}")

    # Add each new user
    added_count = 0
    for ig_username, real_name in new_users:
        if ig_username not in data.get('conversation_metrics', {}):
            print(f"Adding {real_name} ({ig_username})...")
            data['conversation_metrics'][ig_username] = create_user_template(
                ig_username, real_name)
            added_count += 1
        else:
            print(f"{real_name} ({ig_username}) already exists")

    # Update global metrics
    if added_count > 0:
        if 'global_metrics' in data:
            data['global_metrics']['total_users'] = data['global_metrics'].get(
                'total_users', 0) + added_count
            data['global_metrics']['users_with_ig'] = data['global_metrics'].get(
                'users_with_ig', 0) + added_count
            data['global_metrics']['signups'] = data['global_metrics'].get(
                'signups', 0) + added_count

        # Save updated data
        print(f"Saving updated analytics data with {added_count} new users...")
        try:
            with open('analytics_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Successfully added {added_count} users!")
            print(f"New total users: {data['global_metrics']['total_users']}")
            return True
        except Exception as e:
            print(f"Error saving analytics data: {e}")
            return False
    else:
        print("No new users to add")
        return True


if __name__ == "__main__":
    print("Adding new users to analytics data for checkin processing...")
    success = add_users_to_analytics()
    if success:
        print("\n🎉 Users added successfully!")
        print("They will now be included in the next checkin run.")
    else:
        print("\n❌ Failed to add users.")
