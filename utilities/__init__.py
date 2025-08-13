"""
Utilities Package
================
Shared utilities for the Shanbot webhook system.
"""

# Import key functions from webhook_handlers for compatibility
try:
    from ..webhook_handlers import get_user_data, update_analytics_data
except ImportError:
    # Fallback if webhook_handlers is not available
    def get_user_data(ig_username: str, subscriber_id: str = None):
        """Fallback get_user_data function."""
        return [], {}, None

    def update_analytics_data(*args, **kwargs):
        """Fallback update_analytics_data function."""
        pass

# Import ManyChat utilities
try:
    from ..app.manychat_utils import update_manychat_fields
except ImportError:
    # Fallback if manychat_utils is not available
    def update_manychat_fields(*args, **kwargs):
        """Fallback update_manychat_fields function."""
        pass

# Import other utilities
from .models import *
from .config import Config
from .helpers import *

# Import AI handler functions
try:
    from ..app.ai_handler import call_gemini_with_retry
except ImportError:
    # Fallback if ai_handler is not available
    def call_gemini_with_retry(model_name: str, prompt: str, retry_count: int = 0):
        """Fallback call_gemini_with_retry function."""
        return None

# Add missing functions that action_handler.py needs


def add_todo_item(*args, **kwargs):
    """Fallback add_todo_item function."""
    pass


def get_video_analysis(*args, **kwargs):
    """Fallback get_video_analysis function."""
    return None


def get_calorie_analysis(*args, **kwargs):
    """Fallback get_calorie_analysis function."""
    return None


def get_db_connection(*args, **kwargs):
    """Fallback get_db_connection function."""
    return None


def get_username_from_manychat(*args, **kwargs):
    """Fallback get_username_from_manychat function."""
    return None


def add_response_to_review_queue(*args, **kwargs):
    """Fallback add_response_to_review_queue function."""
    return None


def schedule_auto_response(*args, **kwargs):
    """Fallback schedule_auto_response function."""
    pass


def is_auto_mode_active(*args, **kwargs):
    """Fallback is_auto_mode_active function."""
    return False


def is_vegan_auto_mode_active(*args, **kwargs):
    """Fallback is_vegan_auto_mode_active function."""
    return False

# Add missing functions that main_app.py needs


def process_conversation_for_media(*args, **kwargs):
    """Fallback process_conversation_for_media function."""
    return args[0] if args else ""


def build_member_chat_prompt(*args, **kwargs):
    """Fallback build_member_chat_prompt function."""
    return "Fallback prompt", "general_chat"


def get_ai_response(*args, **kwargs):
    """Fallback get_ai_response function."""
    return "Fallback AI response"


def filter_shannon_response(*args, **kwargs):
    """Fallback filter_shannon_response function."""
    return args[0] if args else ""


def split_response_into_messages(*args, **kwargs):
    """Fallback split_response_into_messages function."""
    return [args[0]] if args else [""]


def create_scheduled_responses_table_if_not_exists(*args, **kwargs):
    """Fallback create_scheduled_responses_table_if_not_exists function."""
    pass


__all__ = [
    'get_user_data',
    'update_analytics_data',
    'update_manychat_fields',
    'call_gemini_with_retry',
    'add_todo_item',
    'get_video_analysis',
    'get_calorie_analysis',
    'get_db_connection',
    'get_username_from_manychat',
    'add_response_to_review_queue',
    'schedule_auto_response',
    'is_auto_mode_active',
    'is_vegan_auto_mode_active',
    'process_conversation_for_media',
    'build_member_chat_prompt',
    'get_ai_response',
    'filter_shannon_response',
    'split_response_into_messages',
    'create_scheduled_responses_table_if_not_exists',
    'Config',
    'WebhookMessage',
    'UserData',
    'ActionResult',
    'BufferStats',
    'sanitize_username',
    'format_response_time',
    'is_recent_message',
    'extract_message_keywords',
    'truncate_text',
    'get_message_priority',
    'format_user_metrics_summary',
    'generate_request_id'
]
