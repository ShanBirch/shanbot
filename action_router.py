"""
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
