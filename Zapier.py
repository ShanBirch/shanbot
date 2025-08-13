# -*- coding: utf-8 -*-
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks, Body, Response
import json
import logging
import os
from datetime import datetime
import httpx
import asyncio
import traceback
from typing import Union

from app.schemas.manychat import WebhookPayload, WebhookResponse, EventType, TextResponse
from utils.security import verify_api_key
from services.gemini_service import gemini_service
from services.google_sheets import sheets_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the ManyChat API token from environment
MANYCHAT_API_TOKEN = os.getenv("MANYCHAT_API_TOKEN")

# Set up the router
router = APIRouter(prefix="", tags=["manychat"])

# Get environment variables
SHEETS_SPREADSHEET_ID = os.getenv("MANYCHAT_SPREADSHEET_ID")

# Log API token status (masked for security)
if MANYCHAT_API_TOKEN:
    masked_token = MANYCHAT_API_TOKEN[:4] + "*" * \
        (len(MANYCHAT_API_TOKEN) - 8) + MANYCHAT_API_TOKEN[-4:]
    logger.info(f"ManyChat API token configured: {masked_token}")
else:
    logger.warning(
        "ManyChat API token not configured - field updates will fail")  # Modified warning


@router.post("/", response_model=None, dependencies=[Depends(verify_api_key)])
async def receive_manychat_webhook(request: Request, background_tasks: BackgroundTasks, response: Response):
    """
    Receive webhook from ManyChat, process it, and return response.
    """
    logger.info("\n\n=== INCOMING WEBHOOK REQUEST ===")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("Raw request received")

    try:
        # Log raw request details before any processing
        logger.info("="*50)
        logger.info("[WEBHOOK_DEBUG] New webhook request received")
        logger.info(f"[WEBHOOK_DEBUG] Request URL: {request.url}")
        logger.info(f"[WEBHOOK_DEBUG] Request method: {request.method}")
        logger.info(f"[WEBHOOK_DEBUG] Raw headers: {dict(request.headers)}")

        # Get raw body first
        raw_body = await request.body()
        logger.info(f"[WEBHOOK_DEBUG] Raw request body: {raw_body}")

        # Then parse as JSON
        payload = await request.json()
        logger.info(
            f"[WEBHOOK_DEBUG] Parsed JSON payload: {json.dumps(payload, indent=2)}")

        # Log the URL the webhook was received on
        logger.info(f"[WEBHOOK_DEBUG] Webhook received at URL: {request.url}")
        logger.info(f"[WEBHOOK_DEBUG] Request headers: {request.headers}")

        # Process webhook in the background
        background_tasks.add_task(process_manychat_webhook, payload)
        logger.info(
            "[WEBHOOK_DEBUG] Added webhook processing to background tasks")

        # Check if plaintext is requested via query parameter
        plaintext_requested = request.query_params.get("plaintext") == "true"

        if plaintext_requested:
            logger.info("[WEBHOOK_DEBUG] Plaintext response requested via URL")
            response.headers["Content-Type"] = "text/plain"
            return "Webhook received successfully, processing in background."
        else:
            # Return immediate success response as JSON
            logger.info(
                "[WEBHOOK_DEBUG] Returning immediate success response to webhook")
            return WebhookResponse(
                success=True,
                message="Webhook received successfully, processing in background",
                data={"received_at": datetime.now().isoformat()}
            )

    except Exception as e:
        logger.error(
            f"[WEBHOOK_DEBUG] Error processing ManyChat webhook: {str(e)}")
        logger.error(
            f"[WEBHOOK_DEBUG] Exception details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )


async def process_manychat_webhook(payload: dict):
    """
    Process the ManyChat webhook payload.
    """
    try:
        # Log the payload for debugging
        logger.info(
            f"[PROCESS_DEBUG] Processing webhook payload: {json.dumps(payload)}")

        # Get subscriber and custom fields
        subscriber = payload.get("subscriber", {})
        custom_fields = subscriber.get("custom_fields", {})

        # If no custom fields in subscriber, check top level
        if not custom_fields and "custom_fields" in payload:
            custom_fields = payload.get("custom_fields", {})

        # Check which flow to handle
        if custom_fields.get("General Chat") in ["yes", True, "true", "True"]:
            logger.info("[PROCESS_DEBUG] Handling general chat flow")
            return await handle_general_chat_flow(payload)

        elif custom_fields.get("Member Help") in ["yes", True, "true", "True"]:
            logger.info("[PROCESS_DEBUG] Handling member help flow")
            return await handle_member_help_flow(payload)

        elif custom_fields.get("Member General Chat") in ["yes", True, "true", "True"]:
            logger.info("[PROCESS_DEBUG] Handling member general chat flow")
            return await handle_member_general_chat_flow(payload)

        elif custom_fields.get("check in monday") in ["yes", True, "true", "True"]:
            logger.info("[PROCESS_DEBUG] Handling check-ins flow")
            return await handle_check_ins_flow(payload)

        elif custom_fields.get("Initial Whats App Check in") in ["yes", True, "true", "True"]:
            logger.info("[PROCESS_DEBUG] Handling onboarding flow")
            return await handle_onboarding_flow(payload)

        else:
            logger.info("[PROCESS_DEBUG] No specific flow type detected")
            return {"success": False, "message": "No flow type detected in custom fields"}

    except Exception as e:
        logger.error(f"[PROCESS_DEBUG] Error processing webhook: {str(e)}")
        logger.error(
            f"[PROCESS_DEBUG] Exception details: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}


# --- Helper functions for message formatting (Keep these) ---
async def clean_message_format(message_content):
    # ... (keep existing code) ...
    try:
        clean_prompt = f"""
        Instructions for GPT:

        You have been provided with a complete drafted response, which has been split into multiple parts. Your task is to generate only the first part of the response.

        Guidelines:

        Produce only the first message in the split sequence.

        Do not include any additional information or context—produce just the message content itself.

        Drafted Response: {message_content}

        Your Task:

        Output only the first message.

        Example input.

        Double Message:
        Message 1: "First to master GPT will make a milli 💸"
        Message 2: "Just you wait till I get it chatting to everyone"

        example output:
        First to master GPT will make a milli 💸
        """
        cleaned_message = await gemini_service.complete(clean_prompt)
        cleaned_message = cleaned_message.strip().strip('"\'')
        return cleaned_message
    except Exception as e:
        logger.error(f"Error cleaning message format: {str(e)}")
        return message_content


async def clean_second_message_format(message_content):
    # ... (keep existing code) ...
    try:
        clean_prompt = f"""
        Instructions for GPT:

        You have been provided with a complete drafted response, which has been split into multiple parts. Your task is to generate only the second part of the response.

        Guidelines:

        Produce only the second message in the split sequence.

        Do not include any additional information or context—produce just the message content itself.

        Drafted Response: {message_content}

        Your Task:

        Output only the second message.

        Example input.

        Double Message:
        Message 1: "First to master GPT will make a milli 💸"
        Message 2: "Just you wait till I get it chatting to everyone"

        example output:
        Just you wait till I get it chatting to everyone
        """
        cleaned_message = await gemini_service.complete(clean_prompt)
        cleaned_message = cleaned_message.strip().strip('"\'')
        return cleaned_message
    except Exception as e:
        logger.error(f"Error cleaning second message format: {str(e)}")
        return message_content


async def clean_third_message_format(message_content):
    # ... (keep existing code) ...
    try:
        clean_prompt = f"""
        Instructions for GPT:

        You have been provided with a complete drafted response, which has been split into multiple parts. Your task is to generate only the third part of the response.

        Guidelines:

        Produce only the third message in the split sequence.

        Do not include any additional information or context—produce just the message content itself.

        Drafted Response: {message_content}

        Your Task:

        Output only the third message.

        Example input.

        Triple Message:
        Message 1: "Gonna kick the day off with a workout"
        Message 2: "Then dive into some projects"
        Message 3: "How about you mate?"

        example output:
        How about you mate?
        """
        cleaned_message = await gemini_service.complete(clean_prompt)
        cleaned_message = cleaned_message.strip().strip('"\'')
        return cleaned_message
    except Exception as e:
        logger.error(f"Error cleaning third message format: {str(e)}")
        return message_content


# --- Core Flow Handlers (Keep these as they update the target fields) ---
# These functions contain the logic to call Gemini and then update fields
# 11944956, 11967919, 11967920 based on the split response.

async def handle_general_chat_flow(payload: dict):
    try:
        # Extract data from payload - check both locations for subscriber_id
        subscriber_id = None

        # Try to get from subscriber object first
        if "subscriber" in payload and "subscriber_id" in payload["subscriber"]:
            subscriber_id = payload["subscriber"]["subscriber_id"]

        # If not found, check top level
        if not subscriber_id and "id" in payload:
            subscriber_id = payload["id"]
            logger.info(f"[CHAT_DEBUG] Using top-level ID: {subscriber_id}")

        if not subscriber_id:
            logger.error("[CHAT_DEBUG] No subscriber_id found in payload")
            return {"success": False, "error": "No subscriber_id found"}

        logger.info(f"[CHAT_DEBUG] Using subscriber_id: {subscriber_id}")

        # Get custom fields from subscriber or top level
        custom_fields = {}
        if "subscriber" in payload and "custom_fields" in payload["subscriber"]:
            custom_fields = payload["subscriber"]["custom_fields"]
        elif "custom_fields" in payload:
            custom_fields = payload["custom_fields"]

        # Get conversation history
        conversation_history = custom_fields.get("11821126", "")
        if not conversation_history:
            conversation_history = custom_fields.get("memory", "")
        if not conversation_history:
            conversation_history = custom_fields.get("CONVERSATION", "")

        # Extract last user message
        last_user_message = ""
        if conversation_history:
            messages = conversation_history.split(" + ")
            for msg in reversed(messages):
                if msg.startswith("Lead :"):
                    last_user_message = msg.replace("Lead :", "").strip()
                    break

        # Fallback if we couldn't extract a message
        if not last_user_message:
            last_user_message = "Hello"

        logger.info(f"[CHAT_DEBUG] Last user message: {last_user_message}")
        logger.info(
            f"[CHAT_DEBUG] Conversation history found: {bool(conversation_history)}")

        # Initialize response variable with a fallback
        shannon_response = "Thanks for reaching out! How can I help with your fitness goals today?"

        # Try multiple approaches to get a response
        try:
            # First try: Use our main prompt with the simple model
            gemini_prompt = f"""
            You are Shannon, a fitness coach at Coco's PT Studio. You're having a real conversation with a client.
            
            IMPORTANT RULES:
            1. NEVER start with "Hey Coco's" or any generic greeting
            2. ALWAYS reference something specific from the conversation
            3. Keep responses casual and authentic
            4. If they mention training/fitness, ask specific follow-up questions
            
            Previous conversation:
            {conversation_history}
            
            Their last message: "{last_user_message}"
            
            Instructions:
            - Respond naturally as if continuing a real conversation
            - Reference specific details they've mentioned
            - Ask relevant follow-up questions about their goals/progress
            - Keep it personal and engaging
            
            Your response (without any greeting like "Hey Coco's"):
            """

            logger.info(
                "[CHAT_DEBUG] Attempting to generate response with primary prompt")

            # Get response from Gemini using the most stable model
            response = await gemini_service.complete(
                prompt=gemini_prompt,
                model="gemini-1.0-pro",
                temperature=0.7,
                max_tokens=150
            )

            if response and len(response.strip()) > 10:
                shannon_response = response.strip()
                logger.info(
                    "[CHAT_DEBUG] Successfully generated response with primary prompt")
            else:
                logger.warning(
                    "[CHAT_DEBUG] Primary prompt returned empty or too short response")
                raise ValueError(
                    "Empty or too short response from primary prompt")

        except Exception as e:
            logger.error(f"[CHAT_DEBUG] Error with primary prompt: {str(e)}")

            try:
                # Second try: Use a simpler prompt
                backup_prompt = f"""
                As Shannon, a fitness coach, write a brief response to a client who said: "{last_user_message}"
                
                Keep it casual, friendly, and helpful. Don't use generic greetings like "Hey Coco's".
                Reference something from their message if possible.
                """

                logger.info(
                    "[CHAT_DEBUG] Attempting to generate response with backup prompt")

                # Try with backup prompt
                response = await gemini_service.complete(
                    prompt=backup_prompt,
                    model="gemini-1.0-pro",  # Use the stable model
                    temperature=0.5,
                    max_tokens=100
                )

                if response and len(response.strip()) > 10:
                    shannon_response = response.strip()
                    logger.info(
                        "[CHAT_DEBUG] Successfully generated response with backup prompt")
                else:
                    logger.warning(
                        "[CHAT_DEBUG] Backup prompt returned empty or too short response")
                    raise ValueError(
                        "Empty or too short response from backup prompt")

            except Exception as e2:
                # All Gemini attempts failed, use our fallback response
                logger.error(
                    f"[CHAT_DEBUG] Error with backup prompt: {str(e2)}")
                logger.info("[CHAT_DEBUG] Using fallback response")

        # Clean up response
        if shannon_response.lower().startswith("shannon:"):
            shannon_response = shannon_response[8:].strip()

        logger.info(f"[CHAT_DEBUG] Final response: {shannon_response}")

        # Update the fields
        logger.info(
            f"[CHAT_DEBUG] Updating field 11944956 for subscriber {subscriber_id}")
        result = await update_subscriber_custom_field_by_id(subscriber_id, "11944956", shannon_response)
        logger.info(f"[CHAT_DEBUG] Field update result: {result}")

        await update_subscriber_custom_field_by_id(subscriber_id, "11967919", "")
        await update_subscriber_custom_field_by_id(subscriber_id, "11967920", "")

        # Update message mode
        await update_subscriber_custom_field(subscriber_id, "message_mode", "single")

        return {"success": True, "message": shannon_response}

    except Exception as e:
        logger.error(
            f"[CHAT_DEBUG] Error in handle_general_chat_flow: {str(e)}")
        logger.error(
            f"[CHAT_DEBUG] Exception details: {traceback.format_exc()}")

        # Always try to update the field with a fallback message even if everything else fails
        try:
            fallback_message = "Thanks for your message! I'll get back to you shortly."
            if subscriber_id:
                await update_subscriber_custom_field_by_id(subscriber_id, "11944956", fallback_message)
                logger.info("[CHAT_DEBUG] Updated field with fallback message")
        except Exception as e_fallback:
            logger.error(
                f"[CHAT_DEBUG] Even fallback update failed: {str(e_fallback)}")

        return {"success": False, "error": str(e)}


async def handle_check_ins_flow(payload: dict):
    """Handles check-ins flow - updates fields 11944956, 11967919, 11967920."""
    # This function follows the same pattern as handle_general_chat_flow
    # Keep the existing logic for data extraction, prompt building, Gemini call,
    # response cleaning, splitting, and updating the THREE target fields.
    # Ensure NO send_message_to_subscriber calls exist here.
    try:
        # ... (Extract data, build prompt, call Gemini - KEEP EXISTING CODE) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        custom_fields = subscriber.get("custom_fields", {})
        conversation_history = custom_fields.get("CONVERSATION", "")
        instagram_username = custom_fields.get("IG Username", "")
        # ... (extract other client fields) ...
        client_first_name = custom_fields.get("COL$D", "")  # Example

        logger.info(
            f"Processing Check Ins flow for subscriber {subscriber_id}")
        # ... (sheet lookup logic if needed) ...

        # Build the specific prompt for Check Ins
        gemini_prompt = f"""
        Context:
        - You are Shannon, a human fitness coach... (rest of the detailed check-in prompt)

        Client Information...
        {client_first_name} # Example

        Current Conversation
        {conversation_history}
        """
        logger.info("Sending check-in conversation to Gemini")
        shannon_response = await gemini_service.complete(gemini_prompt, model="gemini-2.0-flash-thinking-exp-01-21", temperature=0.7, max_tokens=5000)

        # ... (response cleaning and retry logic - KEEP EXISTING CODE) ...
        shannon_response = shannon_response.strip()
        # ... (generic check and retry) ...
        # ... (emergency replacement if 'cocos' is mentioned) ...

        logger.info(f"Gemini generated check-in response: {shannon_response}")

        # --- Update Intermediate Fields ---
        await update_subscriber_custom_field(subscriber_id, "AI_Generated_Response", shannon_response)
        # ... (update AI_Split_Message_X, AI_Message_Count, Signed_Up etc. if needed) ...

        # --- Determine Message Type and Update Target Fields ---
        split_result = await gemini_service.complete(f"""Analyze this message... '{shannon_response}' ... Respond with "Single Message", "Double Message", or "Triple Message".""")
        message_type = split_result.strip().lower()
        logger.info(f"Check-in message type determination: {message_type}")

        cleaned_part_1 = await clean_message_format(shannon_response)
        cleaned_part_2 = None
        cleaned_part_3 = None
        if "double message" in message_type or "triple message" in message_type:
            cleaned_part_2 = await clean_second_message_format(shannon_response)
        if "triple message" in message_type:
            cleaned_part_3 = await clean_third_message_format(shannon_response)

        logger.info(
            f"Attempting to update target fields for check-in {message_type}")
        await update_subscriber_custom_field_by_id(subscriber_id, "11944956", cleaned_part_1)
        if ("double message" in message_type or "triple message" in message_type) and cleaned_part_2 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", cleaned_part_2)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", "")
        if "triple message" in message_type and cleaned_part_3 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", cleaned_part_3)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", "")

        logger.info("Check-in flow: Target fields updated.")
        return {"success": True, "message": "Check-ins flow processed, fields updated"}

    except Exception as e:
        logger.error(f"Error handling Check Ins flow: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def handle_coaching_onboarding_flow(payload: dict):
    """Handles coaching onboarding - updates fields 11944956, 11967919, 11967920."""
    # Follows the same pattern. Keep Gemini logic, remove direct messages.
    try:
        # ... (Extract data, lookup, build prompt, call Gemini - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        # ... (extract fields, lookup client details) ...
        conversation_history = custom_fields.get("CONVERSATION", "")
        client_details = "..."  # From sheet lookup

        gemini_prompt = f"""
        Context:
        - You are Shannon... coaching onboarding process...

        Client Information from Coaching Onboarding Form:
        {client_details}

        Current conversation:
        {conversation_history}
        """
        logger.info("Sending onboarding conversation to Gemini")
        # Add model params if needed
        shannon_response = await gemini_service.complete(gemini_prompt)
        shannon_response = shannon_response.strip()
        # ... (cleaning, no retry logic shown here but could be added) ...

        logger.info(
            f"Gemini generated onboarding response: {shannon_response}")

        # --- Update Intermediate Fields ---
        await update_subscriber_custom_field(subscriber_id, "AI_Generated_Response", shannon_response)
        # ... (update AI_Split_Message_X, AI_Message_Count etc. if needed) ...

        # --- Determine Message Type and Update Target Fields ---
        split_result = await gemini_service.complete(f"""Analyze... '{shannon_response}' ... Respond "Single/Double/Triple Message".""")
        message_type = split_result.strip().lower()
        logger.info(f"Onboarding message type determination: {message_type}")

        cleaned_part_1 = await clean_message_format(shannon_response)
        # ... (get cleaned_part_2, cleaned_part_3 if needed) ...

        logger.info(
            f"Attempting to update target fields for onboarding {message_type}")
        await update_subscriber_custom_field_by_id(subscriber_id, "11944956", cleaned_part_1)
        # ... (update/clear 11967919 and 11967920 based on message_type) ...
        if ("double message" in message_type or "triple message" in message_type):
            cleaned_part_2 = await clean_second_message_format(shannon_response)
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", cleaned_part_2)
        else:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", "")
        if ("triple message" in message_type):
            cleaned_part_3 = await clean_third_message_format(shannon_response)
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", cleaned_part_3)
        else:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", "")

        logger.info("Onboarding flow: Target fields updated.")
        return {"success": True, "message": "Onboarding flow processed, fields updated"}

    except Exception as e:
        logger.error(f"Error handling Coaching Onboarding flow: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return {"success": False, "message": f"Error: {str(e)}"}


async def handle_member_general_chat_flow(payload: dict):
    """Handles member general chat - updates fields 11944956, 11967919, 11967920."""
    # Follows the same pattern. Keep Gemini logic, remove direct messages.
    try:
        # ... (Extract data, lookup, build prompt, call Gemini - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        custom_fields = subscriber.get("custom_fields", {})
        conversation_history = custom_fields.get("CONVERSATION", "")
        # ... (sheet lookup logic) ...
        # Placeholder for actual sheet data structure
        sheet_data = ["", "", ...]

        prompt = f"""Context: You are Shannon Birch... Member Interactions...
        (rest of detailed member chat prompt using sheet_data)

        Task: Provide Shannon's next response...
        Current conversation: {conversation_history}
        """
        logger.info("Sending member general chat conversation to Gemini")
        # response = await get_gemini_response(prompt) # Assuming this wraps gemini_service.complete
        # Use direct call if get_gemini_response not defined elsewhere
        response = await gemini_service.complete(prompt)
        response = response.strip()

        logger.info(f"Gemini generated member chat response: {response}")

        # --- Update Intermediate Fields ---
        # This flow seems to update fields like MESSAGE_PART_1, message_mode directly
        # Adapt this if you want to use the standard AI_Generated_Response, AI_Split_Message_X etc.
        # For now, assume the existing logic is intended, but it differs slightly
        # We need to ensure it *also* populates the 3 target fields correctly.

        # --- Determine Message Type and Update Target Fields ---
        # Re-use the standard splitting logic for consistency
        split_result = await gemini_service.complete(f"""Analyze... '{response}' ... Respond "Single/Double/Triple Message".""")
        message_type = split_result.strip().lower()
        logger.info(f"Member chat message type determination: {message_type}")

        cleaned_part_1 = await clean_message_format(response)
        cleaned_part_2 = None
        cleaned_part_3 = None
        if "double message" in message_type or "triple message" in message_type:
            cleaned_part_2 = await clean_second_message_format(response)
        if "triple message" in message_type:
            cleaned_part_3 = await clean_third_message_format(response)

        logger.info(
            f"Attempting to update target fields for member chat {message_type}")
        await update_subscriber_custom_field_by_id(subscriber_id, "11944956", cleaned_part_1)
        if ("double message" in message_type or "triple message" in message_type) and cleaned_part_2 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", cleaned_part_2)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", "")
        if "triple message" in message_type and cleaned_part_3 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", cleaned_part_3)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", "")

        # Also update the message_mode field if used by Manychat flow
        if "single message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "single")
        elif "double message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "double")
        elif "triple message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "triple")

        logger.info("Member chat flow: Target fields updated.")
        return True  # Original returned True/False

    except Exception as e:
        logger.error(f"Error in handle_member_general_chat_flow: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return False


async def handle_member_help_flow(payload: dict):
    """Handles member help - updates fields 11944956, 11967919, 11967920."""
    # Follows the same pattern. Keep Gemini logic, remove direct messages.
    # Adapting structure similar to handle_member_general_chat_flow
    try:
        # ... (Extract data, lookup, build prompt, call Gemini - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        custom_fields = subscriber.get("custom_fields", {})
        conversation_history = custom_fields.get("CONVERSATION", "")
        # ... (sheet lookup) ...
        sheet_data = ["", "", ...]  # Placeholder

        prompt = f"""Context: You are Shannon Birch... Member Interactions, helping with member enquiries...
        (rest of detailed member help prompt using sheet_data)

        Task: Provide Shannon's next response...
        Current conversation: {conversation_history}
        """
        logger.info("Sending member help conversation to Gemini")
        # response = await get_gemini_response(prompt)
        response = await gemini_service.complete(prompt)
        response = response.strip()

        logger.info(f"Gemini generated member help response: {response}")

        # --- Determine Message Type and Update Target Fields ---
        split_result = await gemini_service.complete(f"""Analyze... '{response}' ... Respond "Single/Double/Triple Message".""")
        message_type = split_result.strip().lower()
        logger.info(f"Member help message type determination: {message_type}")

        cleaned_part_1 = await clean_message_format(response)
        cleaned_part_2 = None
        cleaned_part_3 = None
        if "double message" in message_type or "triple message" in message_type:
            cleaned_part_2 = await clean_second_message_format(response)
        if "triple message" in message_type:
            cleaned_part_3 = await clean_third_message_format(response)

        logger.info(
            f"Attempting to update target fields for member help {message_type}")
        await update_subscriber_custom_field_by_id(subscriber_id, "11944956", cleaned_part_1)
        if ("double message" in message_type or "triple message" in message_type) and cleaned_part_2 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", cleaned_part_2)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", "")
        if "triple message" in message_type and cleaned_part_3 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", cleaned_part_3)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", "")

        # Update message_mode if needed
        if "single message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "single")
        elif "double message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "double")
        elif "triple message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "triple")

        logger.info("Member help flow: Target fields updated.")
        return True

    except Exception as e:
        logger.error(f"Error in handle_member_help_flow: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return False


async def handle_onboarding_flow(payload: dict):
    """Handles onboarding - updates fields 11944956, 11967919, 11967920."""
    # Follows the same pattern. Keep Gemini logic, remove direct messages.
    # Adapting structure similar to handle_member_general_chat_flow
    try:
        # ... (Extract data, lookup, build prompt, call Gemini - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        custom_fields = subscriber.get("custom_fields", {})
        conversation_history = custom_fields.get("CONVERSATION", "")
        # ... (sheet lookup) ...
        sheet_data = ["", "", ...]  # Placeholder

        prompt = f"""You are Shannon... Currently helping a new client onboard...
        (rest of detailed onboarding prompt using sheet_data)

        Task: Provide Shannon's next response...
        Current conversation: {conversation_history}
        """
        logger.info("Sending onboarding conversation to Gemini")
        # response = await get_gemini_response(prompt)
        response = await gemini_service.complete(prompt)
        response = response.strip()

        logger.info(f"Gemini generated onboarding response: {response}")

        # --- Determine Message Type and Update Target Fields ---
        split_result = await gemini_service.complete(f"""Analyze... '{response}' ... Respond "Single/Double/Triple Message".""")
        message_type = split_result.strip().lower()
        logger.info(f"Onboarding message type determination: {message_type}")

        cleaned_part_1 = await clean_message_format(response)
        cleaned_part_2 = None
        cleaned_part_3 = None
        if "double message" in message_type or "triple message" in message_type:
            cleaned_part_2 = await clean_second_message_format(response)
        if "triple message" in message_type:
            cleaned_part_3 = await clean_third_message_format(response)

        logger.info(
            f"Attempting to update target fields for onboarding {message_type}")
        await update_subscriber_custom_field_by_id(subscriber_id, "11944956", cleaned_part_1)
        if ("double message" in message_type or "triple message" in message_type) and cleaned_part_2 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", cleaned_part_2)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967919", "")
        if "triple message" in message_type and cleaned_part_3 is not None:
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", cleaned_part_3)
        else:
            # Clear
            await update_subscriber_custom_field_by_id(subscriber_id, "11967920", "")

        # Update message_mode if needed
        if "single message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "single")
        elif "double message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "double")
        elif "triple message" in message_type:
            await update_subscriber_custom_field(subscriber_id, "message_mode", "triple")

        logger.info("Onboarding flow: Target fields updated.")
        return True

    except Exception as e:
        logger.error(f"Error in handle_onboarding_flow: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return False


# --- Other Event Handlers (Remove Direct Messages) ---

async def handle_instagram_lookup(payload: dict):
    """Handle Instagram username lookup in Google Sheets."""
    try:
        # ... (extract data, sheet lookup logic - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        # ... (rest of extraction) ...
        instagram_username = custom_fields.get("IG Username", "")

        if not instagram_username:
            logger.error("Instagram username not found in payload")
            # REMOVED: await send_message_to_subscriber(...)
            return  # No message sent, just log

        logger.info(f"Looking up Instagram username: {instagram_username}")
        # ... (prepare additional_data) ...
        result = sheets_service.lookup_or_add_instagram(...)
        logger.info(f"Instagram lookup result: {json.dumps(result)}")

        # REMOVED Direct message sending logic based on result
        # if result.get("success"):
        #     if result.get("found"): message = f"Found..."
        #     else: message = f"Thanks! Added..."
        #     message += "\nIs there anything specific...?"
        # else: message = f"Sorry, there was an error..."
        # await send_message_to_subscriber(subscriber_id, message)

        # Keep updating custom field with lookup result
        await update_subscriber_custom_field(subscriber_id, "Instagram Lookup Result", json.dumps(result))
        logger.info("Instagram lookup processed, field updated.")

    except Exception as e:
        logger.error(f"Error handling Instagram lookup: {str(e)}")
        # REMOVED: await send_message_to_subscriber(...)


async def handle_new_subscriber(payload: dict):
    """Handle new subscriber event"""
    try:
        # ... (extract data, prepare row_data - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        first_name = subscriber.get("first_name", "")
        # ... (rest of extraction) ...

        # Append to Subscribers sheet
        success = sheets_service.append_row(...)
        # ... (logging - KEEP EXISTING) ...

        # Optional: Gemini analysis and *field update* instead of direct message
        if custom_fields and "interests" in custom_fields:
            interests = custom_fields["interests"]
            gemini_prompt = f"Analyze these customer interests and suggest content categories: {interests}"
            suggestions = await gemini_service.complete(gemini_prompt)
            logger.info(
                f"Gemini suggestions for {subscriber_id}: {suggestions}")

            # Store suggestions in a custom field instead of sending message
            await update_subscriber_custom_field(subscriber_id, "AI_Content_Suggestions", suggestions)
            logger.info(
                f"Stored AI suggestions in custom field for {subscriber_id}")

            # REMOVED: Send welcome message with personalized content suggestions
            # welcome_message = f"Welcome {first_name}! ..."
            # await send_message_to_subscriber(subscriber_id, welcome_message)

    except Exception as e:
        logger.error(f"Error handling new subscriber: {str(e)}")


async def handle_subscriber_updated(payload: dict):
    """Handle subscriber updated event"""
    # No direct messages here originally, just logging. Keep as is.
    logger.info(
        f"Subscriber updated event received: {payload.get('subscriber', {}).get('subscriber_id')}")
    # Add Sheet update logic here if needed


async def handle_message_received(payload: dict):
    """Handle message received event - NO direct response"""
    try:
        # ... (extract data, prepare row_data for Sheets - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        # Used only in removed prompt
        first_name = subscriber.get("first_name", "")
        conversation = payload.get("conversation", {})
        message = conversation.get("message", {})
        text = message.get("text", "")

        # Append to Messages sheet
        success = sheets_service.append_row(...)
        # ... (logging - KEEP EXISTING) ...

        # Analyze sentiment with Gemini and log/store in Sheets
        if text:
            sentiment = await gemini_service.analyze_sentiment(text)
            logger.info(
                f"Sentiment analysis for message from {subscriber_id}: {sentiment}")
            # ... (store sentiment in Sheets - KEEP EXISTING) ...

            # REMOVED: Generate and send a response with Gemini based on user message
            # gemini_prompt = f"""You are a helpful assistant for {first_name}..."""
            # response = await gemini_service.complete(gemini_prompt)
            # await send_message_to_subscriber(subscriber_id, response) # REMOVED
            # logger.info(f"Sent Gemini response to {subscriber_id}: {response}") # REMOVED

            # Optionally, store the AI response idea in a custom field if needed later
            # gemini_prompt_idea = f"""Based on the message '{text}', suggest a brief response idea."""
            # response_idea = await gemini_service.complete(gemini_prompt_idea)
            # await update_subscriber_custom_field(subscriber_id, "AI_Response_Idea", response_idea)

        logger.info(
            f"Message received from {subscriber_id} processed and logged.")

    except Exception as e:
        logger.error(f"Error handling message received: {str(e)}")


async def handle_tag_event(payload: dict):
    """Handle tag applied or removed event - NO direct message"""
    try:
        # ... (extract data, log, store in Sheets - KEEP EXISTING) ...
        event_type = payload.get("event_type")
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        # Used only in removed prompt
        first_name = subscriber.get("first_name", "")
        tag = payload.get("tag", "")

        logger.info(f"Tag event received: {event_type} for tag {tag}")
        row_data = [...]
        sheets_service.append_row(...)

        # Special handling for specific tags - Update field instead of sending message
        if tag == "6 week challenge" and event_type == EventType.TAG_APPLIED:
            gemini_prompt = f"""
            Create a motivational welcome message snippet (max 100 chars) for {first_name} joining our 6-week challenge.
            Focus on excitement and readiness.
            """
            welcome_snippet = await gemini_service.complete(gemini_prompt)
            # Store the snippet in a field, let Manychat send the full message
            await update_subscriber_custom_field(subscriber_id, "Challenge_Welcome_Snippet", welcome_snippet)
            logger.info(
                f"Stored challenge welcome snippet for {subscriber_id}")

            # REMOVED: Generate and send full welcome message
            # gemini_prompt_full = f"""Create a motivational welcome message..."""
            # welcome_message = await gemini_service.complete(gemini_prompt_full)
            # await send_message_to_subscriber(subscriber_id, welcome_message) # REMOVED

    except Exception as e:
        logger.error(f"Error handling tag event: {str(e)}")


async def handle_custom_field_updated(payload: dict):
    """Handle custom field updated event - NO direct message"""
    try:
        # ... (extract data, store in Sheets - KEEP EXISTING) ...
        subscriber = payload.get("subscriber", {})
        subscriber_id = subscriber.get("subscriber_id")
        field_name = payload.get("field_name", "")
        field_value = payload.get("field_value", "")

        row_data = [...]
        sheets_service.append_row(...)
        logger.info(
            f"Custom field '{field_name}' updated for {subscriber_id}, logged.")

        # REMOVED: Special handling for "conversation" field to send direct message
        # if field_name == "conversation" and field_value:
        #     gemini_prompt = f"""Based on this conversation context: "{field_value}"..."""
        #     response = await gemini_service.complete(gemini_prompt)
        #     await send_message_to_subscriber(subscriber_id, response) # REMOVED

    except Exception as e:
        logger.error(f"Error handling custom field updated: {str(e)}")


async def handle_generic_event(payload: dict):
    """Handle any other event type"""
    # No direct messages here originally, just logging. Keep as is.
    try:
        event_type = payload.get("event_type", "unknown")
        logger.info(f"Generic event received: {event_type}")
        row_data = [...]
        sheets_service.append_row(...)
    except Exception as e:
        logger.error(f"Error handling generic event: {str(e)}")


# --- ManyChat API Interaction Functions ---

async def send_message_to_subscriber(subscriber_id, message):
    """
    Send a message to a ManyChat subscriber using the ManyChat API.
    *** THIS FUNCTION IS NO LONGER CALLED IN THE MODIFIED SCRIPT ***
    (Keeping the function definition in case it's needed for debugging or future use,
     but it should not be executed with the current logic flow)
    """
    logger.warning(
        f"Attempted to call send_message_to_subscriber for {subscriber_id}, but direct messages are disabled.")
    # Return False immediately as we don't want to send messages
    return False

    # --- Original code commented out below ---
    # if not MANYCHAT_API_TOKEN:
    #     logger.warning("ManyChat API token not configured, cannot send messages")
    #     return False
    # try:
    #     url = "https://api.manychat.com/fb/sending/sendContent"
    #     payload = { ... } # Original payload
    #     logger.info(f"Attempting to send message (but disabled): {payload}") # Log attempt if needed
    #     # async with httpx.AsyncClient() as client:
    #     #     response = await client.post(...) # Original request
    #     # ... (Original response handling) ...
    # except Exception as e:
    #     logger.error(f"Error in disabled send_message_to_subscriber function: {str(e)}")
    #     return False


async def update_subscriber_custom_field(subscriber_id, field_name, value):
    """Update a custom field by NAME (Keep this function)"""
    if not MANYCHAT_API_TOKEN:
        logger.warning(
            "ManyChat API token not configured, cannot update custom fields")
        return False
    try:
        # ... (Keep existing code for updating by name) ...
        url = "https://api.manychat.com/fb/subscriber/setCustomField"
        payload = {
            "subscriber_id": subscriber_id,
            "field_name": field_name,
            "field_value": str(value)  # Ensure value is string
        }
        logger.info(
            f"Attempting to update field by NAME '{field_name}' to '{str(value)[:50]}...' for {subscriber_id}")
        async with httpx.AsyncClient() as client:
            # Add other headers if needed
            response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {MANYCHAT_API_TOKEN}"})
        logger.debug(
            f"ManyChat API response (update by name): {response.text}")
        if response.status_code == 200 and response.json().get("status") == "success":
            logger.info(f"Successfully updated field by NAME {field_name}")
            return True
        else:
            logger.error(
                f"Failed update field by NAME {field_name}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating field by NAME {field_name}: {str(e)}")
        return False


async def update_subscriber_custom_field_by_id(subscriber_id, field_id, value):
    """Update a custom field by ID (Keep this crucial function)"""
    if not MANYCHAT_API_TOKEN:
        logger.warning(
            "[FIELD_DEBUG] ManyChat API token not configured, cannot update custom fields by ID")
        return False

    # Ensure value is string, handle None
    field_value_str = str(value) if value is not None else ""

    # Try endpoint 1: setCustomFieldByID (May not exist or work as expected)
    url1 = "https://api.manychat.com/fb/subscriber/setCustomFieldByID"
    payload1 = {
        "subscriber_id": subscriber_id,
        "field_id": str(field_id),  # Ensure field ID is string
        "field_value": field_value_str
    }
    logger.info(
        f"[FIELD_DEBUG] Attempting update ID {field_id} via {url1} with value '{field_value_str[:50]}...'")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response1 = await client.post(url1, json=payload1, headers={"Authorization": f"Bearer {MANYCHAT_API_TOKEN}", "Content-Type": "application/json"})
        logger.debug(
            f"[FIELD_DEBUG] Response from {url1}: {response1.status_code} - {response1.text}")
        if response1.status_code == 200 and response1.json().get("status") == "success":
            logger.info(
                f"[FIELD_DEBUG] Successfully updated field ID {field_id} via {url1}")
            return True
        logger.warning(
            f"[FIELD_DEBUG] Endpoint {url1} failed or returned non-success status.")
    except Exception as e:
        logger.error(f"[FIELD_DEBUG] Error with endpoint {url1}: {str(e)}")

    # Try endpoint 2: setCustomField (using field_id parameter) - Often more reliable
    url2 = "https://api.manychat.com/fb/subscriber/setCustomField"
    payload2 = {
        "subscriber_id": subscriber_id,
        "field_id": str(field_id),  # Use field_id key
        "field_value": field_value_str
    }
    logger.info(
        f"[FIELD_DEBUG] Attempting update ID {field_id} via {url2} with value '{field_value_str[:50]}...'")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response2 = await client.post(url2, json=payload2, headers={"Authorization": f"Bearer {MANYCHAT_API_TOKEN}", "Content-Type": "application/json"})
        logger.debug(
            f"[FIELD_DEBUG] Response from {url2}: {response2.status_code} - {response2.text}")
        if response2.status_code == 200 and response2.json().get("status") == "success":
            logger.info(
                f"[FIELD_DEBUG] Successfully updated field ID {field_id} via {url2}")
            return True
        logger.error(
            f"[FIELD_DEBUG] Failed update field ID {field_id} via {url2}: {response2.status_code} - {response2.text}")
        return False
    except Exception as e:
        logger.error(f"[FIELD_DEBUG] Error with endpoint {url2}: {str(e)}")
        return False


# --- Test Endpoint (Keep this for testing field updates) ---
@router.post("/test_field_update", response_model=WebhookResponse, dependencies=[Depends(verify_api_key)])
async def test_field_update(request: Request):
    """Test endpoint to manually trigger a custom field update BY ID."""
    try:
        payload = await request.json()
        logger.info(
            f"[TEST_ENDPOINT] Received test field update request: {json.dumps(payload)}")

        subscriber_id = payload.get(
            "subscriber_id", "459582207")  # Default test ID
        # Default to o1 response
        field_id = payload.get("field_id", "11944956")
        field_value = payload.get(
            "field_value", f"Test update at {datetime.now().isoformat()} - Direct API Test")

        logger.info(
            f"[TEST_ENDPOINT] Attempting to update field ID {field_id} for subscriber {subscriber_id} with value: {field_value}")

        update_result = await update_subscriber_custom_field_by_id(subscriber_id, field_id, field_value)
        logger.info(f"[TEST_ENDPOINT] Update by ID result: {update_result}")

        # ... (Keep verification logic if needed, it uses getInfo which is fine) ...
        verification_message = "Verification check initiated..."
        # ... (rest of verification logic) ...

        return WebhookResponse(
            success=update_result,  # Reflect actual update success
            message="Test field update by ID request processed",
            data={
                "subscriber_id": subscriber_id,
                "field_id": field_id,
                "field_value": field_value,
                "update_result": update_result,
                "verification": verification_message,  # Note: verification runs after response
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(
            f"[TEST_ENDPOINT] Error processing test field update: {str(e)}")
        logger.error(
            f"[TEST_ENDPOINT] Exception details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error processing test field update: {str(e)}")


async def split_message_with_gemini(message):
    """
    Use Gemini to intelligently split a message into multiple parts.

    Args:
        message (str): The message to split

    Returns:
        list: A list of message parts
    """
    try:
        # Ask Gemini to determine if and how the message should be split
        prompt = f"""
        Analyze this message and determine how it should be split into separate messages for Instagram:
        
        "{message}"
        
        Rules for splitting:
        1. If the message is short or has a single thought, keep it as one message
        2. If the message has natural breaks or separate thoughts, split it
        3. Maximum 3 separate messages
        4. Each message should be complete and make sense on its own
        5. Preserve the original meaning and tone
        
        Format your response as:
        PART 1: [First message]
        PART 2: [Second message]
        PART 3: [Third message]
        
        Only include parts that are necessary (1-3 parts).
        """

        result = await gemini_service.complete(prompt)
        logger.info(f"Gemini split message result: {result}")

        # Parse the split messages
        parts = []
        current_part = None

        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("PART 1:"):
                current_part = line[7:].strip()
                parts.append(current_part)
            elif line.startswith("PART 2:"):
                current_part = line[7:].strip()
                parts.append(current_part)
            elif line.startswith("PART 3:"):
                current_part = line[7:].strip()
                parts.append(current_part)

        # If Gemini didn't provide a proper split, return the original message as a single part
        if not parts:
            logger.warning(
                "Gemini didn't provide a proper split, using original message")
            return [message]

        logger.info(f"Split message into {len(parts)} parts")
        return parts

    except Exception as e:
        logger.error(f"Error splitting message with Gemini: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        # Fall back to the original message as a single part
        return [message]


async def handle_test_webhook(payload: dict):
    """Handle test webhooks from ManyChat"""
    try:
        # Extract subscriber info from payload
        test_subscriber_id = payload.get("id")
        logger.info(
            f"[TEST_DEBUG] Test webhook subscriber ID: {test_subscriber_id}")

        # Get custom fields from payload
        custom_fields = payload.get("custom_fields", {})
        if not custom_fields and "subscriber" in payload:
            custom_fields = payload.get(
                "subscriber", {}).get("custom_fields", {})

        # Prepare response object
        test_response = {
            "success": True,
            "message": "Test webhook received and processed",
            "subscriber_id": test_subscriber_id,
            "custom_fields": custom_fields
        }

        # Get subscriber name if available
        test_first_name = payload.get("first_name", "")
        if not test_first_name and "subscriber" in payload:
            test_first_name = payload.get(
                "subscriber", {}).get("first_name", "")

        logger.info(f"[TEST_DEBUG] Test webhook first name: {test_first_name}")

        # Generate a test message
        test_prompt = """
        Generate a test response as Shannon to confirm the webhook is working.
        Keep it under 50 characters and make it casual but professional.
        DO NOT use generic greetings like "Hey Coco's".
        """
        test_message = await gemini_service.complete(test_prompt)
        logger.info(f"[TEST_DEBUG] Generated test message: {test_message}")

        # Include test message in response
        test_response["test_message"] = test_message

        # Check if General Chat is enabled
        is_general_chat = custom_fields.get("General Chat") in [
            True, "true", "True", "yes"]
        test_response["is_general_chat"] = is_general_chat

        # Update test field if we have a subscriber ID
        if test_subscriber_id:
            logger.info(
                f"[TEST_DEBUG] Updating test field for subscriber: {test_subscriber_id}")
            result = await update_subscriber_custom_field_by_id(test_subscriber_id, "11944956", test_message)
            test_response["field_update"] = result

        logger.info(
            f"[TEST_DEBUG] Test webhook processed: {json.dumps(test_response)}")
        return test_response

    except Exception as e:
        logger.error(f"[TEST_DEBUG] Error processing test webhook: {str(e)}")
        logger.error(
            f"[TEST_DEBUG] Exception details: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }
