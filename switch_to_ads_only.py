#!/usr/bin/env python3
"""
Switch to Ads-Only Mode
=======================
Simple script to switch the webhook system to ONLY handle ad responses.
Run this when you want to focus purely on ad response flow.
"""

import shutil
import os
from datetime import datetime


def backup_current_router():
    """Backup the current action_router.py"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"action_router_backup_{timestamp}.py"

    if os.path.exists("action_router.py"):
        shutil.copy2("action_router.py", backup_name)
        print(f"✅ Backed up current router to: {backup_name}")
        return backup_name
    else:
        print("⚠️  No existing action_router.py found")
        return None


def switch_to_ads_only():
    """Switch to the simplified ad-only router"""
    try:
        # Backup current router
        backup_file = backup_current_router()

        # Create the simplified router content
        ads_only_content = '''"""
Action Router - ADS ONLY MODE
============================
Simplified router that ONLY handles ad responses.
All other messages get a simple generic response.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from action_router_ads_only import AdOnlyRouter
import logging

logger = logging.getLogger("shanbot_router")

class ActionRouter:
    """Simplified router - ads only!"""

    @staticmethod
    async def route_webhook_message(ig_username: str, message_text: str, subscriber_id: str,
                                    first_name: str, last_name: str, user_message_timestamp_iso: str, fb_ad: bool = False):
        """Route to ads-only system."""
        logger.info(f"[ADS-ONLY-MODE] Processing {ig_username}")
        return await AdOnlyRouter.route_webhook_message(
            ig_username, message_text, subscriber_id, first_name, last_name, user_message_timestamp_iso, fb_ad
        )

    @staticmethod
    def get_routing_stats():
        """Simple stats for ad-only mode."""
        return {"mode": "ads_only", "status": "active"}

    @staticmethod
    def clear_user_routing_data(subscriber_id: str):
        """Clear routing data."""
        return True

    @staticmethod
    async def process_direct_message(ig_username: str, message_text: str, subscriber_id: str,
                                     first_name: str, last_name: str, user_message_timestamp_iso: str, fb_ad: bool = False):
        """Process direct message in ads-only mode."""
        return await AdOnlyRouter.route_webhook_message(
            ig_username, message_text, subscriber_id, first_name, last_name, user_message_timestamp_iso, fb_ad
        )
'''

        # Write the new simplified router
        with open("action_router.py", "w") as f:
            f.write(ads_only_content)

        print("🎯 SWITCHED TO ADS-ONLY MODE!")
        print("=" * 50)
        print("✅ System will now ONLY handle ad responses")
        print("✅ All other messages get simple generic replies")
        print("✅ No calorie tracking, no complex flows")
        print("✅ Perfect for running ads and booking calls!")
        print()
        if backup_file:
            print(f"📦 Your original router is backed up as: {backup_file}")
        print()
        print("🔄 Restart your webhook to activate ads-only mode:")
        print("   python webhook_main.py")

        return True

    except Exception as e:
        print(f"❌ Error switching to ads-only mode: {e}")
        return False


def restore_original_router():
    """Restore the most recent backup"""
    try:
        # Find the most recent backup
        backups = [f for f in os.listdir(
            ".") if f.startswith("action_router_backup_")]
        if not backups:
            print("❌ No backup files found!")
            return False

        # Get the most recent backup
        latest_backup = sorted(backups)[-1]

        # Restore it
        shutil.copy2(latest_backup, "action_router.py")
        print(f"✅ Restored router from: {latest_backup}")
        print("🔄 Restart your webhook to activate the restored router")
        return True

    except Exception as e:
        print(f"❌ Error restoring router: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_original_router()
    else:
        print("🎯 SWITCHING TO ADS-ONLY MODE")
        print("=" * 40)
        print("This will simplify your system to ONLY handle:")
        print("• Ad responses → guide to sign-up link")
        print("• Everything else → simple generic reply")
        print()

        response = input("Continue? (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            if switch_to_ads_only():
                print("\n🚀 Ready to run ads!")
            else:
                print("\n❌ Switch failed")
        else:
            print("❌ Cancelled")

        print()
        print("💡 To restore your original complex system later:")
        print("   python switch_to_ads_only.py restore")
