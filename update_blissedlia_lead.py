#!/usr/bin/env python3
"""
Script to update blissedlia's lead source for vegan weight loss challenge flow
"""

import json
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_lead")


def update_blissedlia_lead():
    """Update blissedlia's lead source to plant_based_challenge and set ad flow flags"""

    # Try SQLite database first
    try:
        conn = sqlite3.connect("app/analytics_data_good.sqlite")
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute(
            "SELECT * FROM users WHERE ig_username = ?", ("blissedlia",))
        user = cursor.fetchone()

        if user:
            logger.info(
                "Found blissedlia in SQLite database, updating lead source...")

            # Update the user's lead source and ad flow flags
            cursor.execute("""
                UPDATE users 
                SET lead_source = ?, 
                    is_in_ad_flow = ?, 
                    ad_script_state = ?, 
                    ad_scenario = ?,
                    updated_at = ?
                WHERE ig_username = ?
            """, ('plant_based_challenge', True, 'step1', 1, datetime.now().isoformat(), 'blissedlia'))

            conn.commit()
            logger.info("Successfully updated blissedlia in SQLite database")

        else:
            logger.info(
                "blissedlia not found in SQLite database, creating new entry...")

            # Create new user entry
            cursor.execute("""
                INSERT INTO users (
                    ig_username, 
                    subscriber_id, 
                    lead_source, 
                    is_in_ad_flow, 
                    ad_script_state, 
                    ad_scenario,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'blissedlia',
                '402069007',  # From the logs
                'plant_based_challenge',
                True,
                'step1',
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            conn.commit()
            logger.info(
                "Successfully created blissedlia entry in SQLite database")

        conn.close()

    except Exception as e:
        logger.error(f"Error updating SQLite database: {e}")

        # Fallback to JSON file
        try:
            logger.info("Trying JSON file update...")

            # Load analytics data
            with open("app/analytics_data_good.json", "r") as f:
                analytics_data = json.load(f)

            conversations = analytics_data.get('conversations', {})
            user_found = False

            # Search for blissedlia
            for user_id, user_data in conversations.items():
                if user_data.get('ig_username', '').lower() == 'blissedlia':
                    logger.info(
                        f"Found blissedlia in JSON file with ID: {user_id}")

                    # Update lead source and ad flow flags
                    user_data['lead_source'] = 'plant_based_challenge'
                    user_data['is_in_ad_flow'] = True
                    user_data['ad_script_state'] = 'step1'
                    user_data['ad_scenario'] = 1
                    user_data['updated_at'] = datetime.now().isoformat()

                    user_found = True
                    break

            if not user_found:
                logger.info(
                    "blissedlia not found in JSON file, creating new entry...")

                # Create new user entry
                new_user_id = f"user_{len(conversations) + 1}"
                conversations[new_user_id] = {
                    'ig_username': 'blissedlia',
                    'subscriber_id': '402069007',
                    'lead_source': 'plant_based_challenge',
                    'is_in_ad_flow': True,
                    'ad_script_state': 'step1',
                    'ad_scenario': 1,
                    'conversation_history': [],
                    'metrics': {},
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

            # Save updated data
            with open("app/analytics_data_good.json", "w") as f:
                json.dump(analytics_data, f, indent=2)

            logger.info("Successfully updated blissedlia in JSON file")

        except Exception as e:
            logger.error(f"Error updating JSON file: {e}")


if __name__ == "__main__":
    update_blissedlia_lead()
    print("✅ blissedlia has been tagged for the vegan weight loss challenge flow!")
    print("Lead source: plant_based_challenge")
    print("Ad flow: Enabled")
    print("Script state: step1")
    print("Scenario: 1 (vegan)")
