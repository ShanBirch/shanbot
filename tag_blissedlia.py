#!/usr/bin/env python3
"""
Simple script to tag blissedlia for vegan weight loss challenge flow
"""

from datetime import datetime
from webhook_handlers import update_analytics_data
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def tag_blissedlia():
    """Tag blissedlia for vegan weight loss challenge flow"""

    try:
        # Update analytics data to tag blissedlia for vegan challenge
        update_analytics_data(
            ig_username='blissedlia',
            user_message='',  # Empty since this is just tagging
            ai_response='',   # Empty since this is just tagging
            subscriber_id='402069007',
            first_name='Lia_romy',
            last_name='',
            lead_source='plant_based_challenge',
            is_in_ad_flow=True,
            ad_script_state='step1',
            ad_scenario=1
        )

        print("✅ Successfully tagged blissedlia for vegan weight loss challenge flow!")
        print("Lead source: plant_based_challenge")
        print("Ad flow: Enabled")
        print("Script state: step1")
        print("Scenario: 1 (vegan)")

    except Exception as e:
        print(f"❌ Error tagging blissedlia: {e}")


if __name__ == "__main__":
    tag_blissedlia()
