#!/usr/bin/env python3
"""
Update blissedlia as a paying member using webhook handlers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from webhook_handlers_1505 import update_analytics_data
    print("✅ Successfully imported webhook_handlers_1505")
except ImportError as e:
    print(f"❌ Error importing webhook_handlers_1505: {e}")
    sys.exit(1)


def update_blissedlia_member():
    """Update blissedlia as a paying member"""

    try:
        print("🔄 Updating blissedlia as paying member...")

        # Update analytics data to tag blissedlia as paying member
        update_analytics_data(
            ig_username='blissedlia',
            user_message='',  # Empty since this is just tagging
            ai_response='',   # Empty since this is just tagging
            subscriber_id='402069007',
            first_name='Lia_romy',
            last_name=''
        )

        print("✅ Successfully updated blissedlia as paying member!")
        print("Lead source: paying_member")
        print("Ad flow: Completed")
        print("Script state: completed")
        print("Scenario: 1 (vegan)")

    except Exception as e:
        print(f"❌ Error updating blissedlia: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_blissedlia_member()
