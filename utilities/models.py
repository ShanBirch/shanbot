"""
Pydantic Models
==============
Data models for the Shanbot webhook system.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class WebhookMessage(BaseModel):
    """Model for incoming webhook messages."""
    subscriber_id: str = Field(..., description="ManyChat subscriber ID")
    ig_username: str = Field(..., description="Instagram username")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    text: str = Field(..., description="Message text")
    user_message_timestamp_iso: str = Field(...,
                                            description="Message timestamp")


class UserData(BaseModel):
    """Model for user data and metrics."""
    ig_username: str
    subscriber_id: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    use_message_buffering: bool = True
    response_level: str = "friendly"
    contact_timing: str = "normal"


class ActionResult(BaseModel):
    """Model for action processing results."""
    status: str = Field(..., description="Processing status")
    success: bool = Field(default=True, description="Whether action succeeded")
    message: str = Field(default="", description="Result message")
    processing_time: Optional[float] = Field(
        None, description="Time taken to process")
    action_type: Optional[str] = Field(
        None, description="Type of action performed")


class BufferStats(BaseModel):
    """Model for message buffer statistics."""
    total_buffered_messages: int = 0
    active_buffers: int = 0
    total_users_with_buffers: int = 0
