"""
Shared Utilities Module - Simplified for Render
"""


def get_user_topics():
    """Return default topics"""
    return ["General Check-in", "Nutrition Help", "Workout Questions", "Goal Setting"]


def call_gemini_with_retry_sync(model_name: str, prompt: str, retry_count: int = 0) -> str:
    """Stub function for Gemini calls"""
    return "AI response placeholder - configure Gemini API key"


def queue_message_for_followup(username, message, topic):
    """Queue a message for follow-up sending"""
    pass
