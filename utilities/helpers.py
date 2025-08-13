"""
Helper Functions
===============
Utility functions for the Shanbot webhook system.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
import dateutil.parser
import pytz  # Import pytz for timezone operations

logger = logging.getLogger("shanbot_helpers")


def sanitize_username(username: str) -> str:
    """Sanitize Instagram username for safe processing."""
    if not username:
        return ""

    # Remove @ symbol if present
    clean_username = username.lstrip('@')

    # Remove any whitespace
    clean_username = clean_username.strip()

    return clean_username


def format_response_time(seconds: float) -> str:
    """Format processing time in a human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"


def is_recent_message(timestamp_iso: str, window_minutes: int = 5) -> bool:
    """Check if a message timestamp is within the recent window."""
    try:
        message_time = dateutil.parser.parse(timestamp_iso)
        now = datetime.now(message_time.tzinfo)
        time_diff = now - message_time

        return time_diff < timedelta(minutes=window_minutes)
    except Exception as e:
        logger.warning(f"Error parsing timestamp {timestamp_iso}: {e}")
        return True  # Default to treating as recent if we can't parse


def extract_message_keywords(text: str) -> List[str]:
    """Extract important keywords from message text."""
    # Simple keyword extraction - can be enhanced with NLP
    import re

    # Remove punctuation and convert to lowercase
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())

    # Split into words
    words = clean_text.split()

    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may'
    }

    keywords = [
        word for word in words if word not in stop_words and len(word) > 2]

    return keywords[:10]  # Return top 10 keywords


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix."""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def get_message_priority(text: str, user_metrics: Dict[str, Any]) -> str:
    """Determine message priority based on content and user metrics."""
    text_lower = text.lower()

    # High priority keywords
    high_priority_keywords = [
        'urgent', 'emergency', 'help', 'problem', 'issue', 'error',
        'not working', 'broken', 'can\'t', 'unable', 'stuck'
    ]

    # Check for high priority content
    if any(keyword in text_lower for keyword in high_priority_keywords):
        return "high"

    # Check if user is new (based on conversation history)
    conversation_history = user_metrics.get('conversation_history', [])
    if len(conversation_history) <= 3:
        return "medium"

    # Default priority
    return "low"


def format_user_metrics_summary(metrics: Dict[str, Any]) -> str:
    """Format user metrics into a readable summary."""
    summary_parts = []

    # Response level
    response_level = metrics.get('response_level', 'unknown')
    summary_parts.append(f"Response Level: {response_level}")

    # Contact timing
    contact_timing = metrics.get('contact_timing', 'unknown')
    summary_parts.append(f"Contact Timing: {contact_timing}")

    # Conversation count
    conversation_history = metrics.get('conversation_history', [])
    summary_parts.append(f"Messages: {len(conversation_history)}")

    # Buffering preference
    use_buffering = metrics.get('use_message_buffering', True)
    summary_parts.append(
        f"Buffering: {'Enabled' if use_buffering else 'Disabled'}")

    return " | ".join(summary_parts)


def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    import uuid
    return str(uuid.uuid4())[:8]


def get_melbourne_time_str() -> str:
    """Get the current time in Melbourne, Australia, as a formatted string."""
    try:
        melbourne_tz = pytz.timezone('Australia/Melbourne')
        now_melbourne = datetime.now(melbourne_tz)
        return now_melbourne.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    except Exception as e:
        logging.error(f"Error getting Melbourne time: {e}")
        return datetime.now().isoformat()  # Fallback to UTC if timezone fails
