@app.get("/debug")
async def debug_endpoint(request: Request):
    """Simple debug endpoint that returns all query parameters and headers"""
    query_params = dict(request.query_params)
    headers = dict(request.headers)

    # Log everything for debugging
    logger.info(f"DEBUG ENDPOINT ACCESSED - Query params: {query_params}")

    # If this is a Facebook verification attempt, handle it specially
    if "hub.mode" in query_params and "hub.verify_token" in query_params and "hub.challenge" in query_params:
        mode = query_params.get("hub.mode")
        token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        logger.info(
            f"DEBUG: Facebook verification detected! Mode: {mode}, Token: {token}, Challenge: {challenge}")

        # Verify the token for proper logging (but always return challenge in debug mode)
        verify_token = "Shanbotcyywp7nyk"
        if mode == "subscribe" and token == verify_token:
            logger.info("DEBUG: Token verification successful")
        else:
            logger.warning(
                f"DEBUG: Token verification failed. Expected: {verify_token}, Got: {token}")

        # Always return the challenge as plain text without verification for debugging
        return PlainTextResponse(content=challenge)

    return {
        "status": "debug",
        "query_params": query_params,
        "headers": {k: v for k, v in headers.items()},
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint that redirects to health check"""
    logger.info("Root endpoint accessed")
    return {"status": "Shanbot API running", "message": "Use /webhook endpoints for functionality"}


async def schedule_response(sender_id: str, initial_delay_to_use: int):
    try:
        # --- NEW DELAY LOGIC --- START ---
        # Start with the base delay (20s or 600s)
        target_total_wait = initial_delay_to_use
        user_response_time_seconds = 0  # Default

        # Get user message arrival time and bot last reply time
        user_message_arrival_ts = last_message_timestamps.get(sender_id)
        last_bot_reply_ts = last_bot_reply_timestamps.get(sender_id)

        if user_message_arrival_ts and last_bot_reply_ts:
            user_response_time_seconds = user_message_arrival_ts - last_bot_reply_ts
            # Ensure response time isn't negative (e.g., clock sync issues)
            user_response_time_seconds = max(0, user_response_time_seconds)
            target_total_wait = max(
                initial_delay_to_use, user_response_time_seconds)
            logger.info(
                f"[schedule_response] User response time: {user_response_time_seconds:.1f}s.")
        elif user_message_arrival_ts:
            logger.info(
                f"[schedule_response] User message timestamp found, but no previous bot reply timestamp. Using initial delay.")
        else:
            logger.info(
                f"[schedule_response] No user message arrival timestamp found. Using initial delay.")

        logger.info(
            f"[schedule_response] Base Delay: {initial_delay_to_use}s, User Response Time: {user_response_time_seconds:.1f}s. Target Total Wait: {target_total_wait:.1f}s")

        # Perform the calculated total wait
        await asyncio.sleep(target_total_wait)
        logger.info(
            f"[schedule_response] Woke up after {target_total_wait:.1f}s total wait for {sender_id}.")
        # --- NEW DELAY LOGIC --- END ---

        # --- Rest of the message processing ---
        messages = message_buffer.pop(sender_id, [])
        if not messages:
            logger.info(
                f"No messages left in buffer for {sender_id} after delay.")
            return  # Exit if buffer was cleared by another message

        full_message = ' '.join(messages)
        logger.info(
            f"Processing combined message for {sender_id}: '{full_message}'")

        # Get or create user data and conversation history
        full_conversation_history, metrics_dict, user_id = get_user_data(
            ig_username=ig_username,
            subscriber_id=subscriber_id  # Pass subscriber_id here
        )

        # Append new message to history
        if message_text or media_url:  # Only add if there's content
            new_message_entry = {
                "type": "user", "text": message_text or f"[{message_type.upper()} received]", "timestamp": get_melbourne_time_str()}
            if media_url:
                new_message_entry["media_url"] = media_url
                new_message_entry["media_type"] = message_type
            if not isinstance(full_conversation_history, list):
                full_conversation_history = []  # Ensure it's a list if not already

            # Check for duplicate consecutive messages from the same sender to prevent webhook retries from cluttering history
            if full_conversation_history and new_message_entry['message_text'] == full_conversation_history[-1].get('message_text') and new_message_entry['message_type'] == full_conversation_history[-1].get('message_type'):
                logger.info(
                    f"Skipping duplicate message from {new_message_entry['message_type']}: {new_message_entry['message_text'][:50]}...")
            else:
                full_conversation_history.append(new_message_entry)

        # ---- ONBOARDING DETECTION AND HANDLING ----
        # Remove or comment out the direct user message trigger for onboarding
        # onboarding_trigger_phrase = "initiate_onboarding_sequence"
        # if message_text.lower() == onboarding_trigger_phrase.lower():
        #    logger.info(f"Onboarding sequence triggered for {ig_username}.")
        #    post_onboarding_handler = PostOnboardingHandler(gemini_api_key=GEMINI_API_KEY)
        #    background_tasks.add_task(
        #        post_onboarding_handler.process_onboarding_completion,
        #        ig_username=ig_username,
        #        conversation_history=full_conversation_history
        #    )
        #    logger.info(f"Onboarding for {ig_username} scheduled in background. Returning 200 OK to ManyChat.")
        #    return PlainTextResponse("Onboarding process started.", status_code=200)
        # ---- END (REMOVED) USER-TRIGGERED ONBOARDING HANDLING ----

        # Existing logic for non-onboarding messages (ensure this is still called if not onboarding)
        logger.info(f"Passing to regular message handler for {ig_username}")
        action_handled = await detect_and_handle_action(ig_username, message_text, data if isinstance(data, dict) else {}, batch_start_time_s)

        ai_response_for_analytics = ""

        if not action_handled:
            logger.info(
                f"No specific action detected for {ig_username}, proceeding to general AI response.")
            current_stage = metrics_dict.get(
                'journey_stage', {}).get('current_stage', "Topic 1")
            trial_status = metrics_dict.get('trial_status', "Initial Contact")

            first_name_from_data = data.get("first_name", "")
            last_name_from_data = data.get("last_name", "")
            calculated_full_name = f"{first_name_from_data} {last_name_from_data}".strip(
            )
            if not calculated_full_name:
                full_name_from_metrics_fn = metrics_dict.get('first_name', '')
                full_name_from_metrics_ln = metrics_dict.get('last_name', '')
                calculated_full_name = f"{full_name_from_metrics_fn} {full_name_from_metrics_ln}".strip(
                )
            if not calculated_full_name:
                calculated_full_name = ig_username

            current_message_for_prompt_builder = message_text
            if not current_message_for_prompt_builder and media_url:
                analyzed_media_type, analyzed_media_text = analyze_media_url(
                    media_url)
                if analyzed_media_text:
                    current_message_for_prompt_builder = f"[{analyzed_media_type.upper() if analyzed_media_type else 'MEDIA'} Content: {analyzed_media_text}]"
                else:
                    current_message_for_prompt_builder = f"[{message_type.upper() if message_type else 'MEDIA'} received, analysis failed or not applicable]"
            elif media_url and current_message_for_prompt_builder:
                analyzed_media_type, analyzed_media_text = analyze_media_url(
                    media_url)
                if analyzed_media_text:
                    current_message_for_prompt_builder = f"{message_text} [{analyzed_media_type.upper() if analyzed_media_type else 'MEDIA'} Content: {analyzed_media_text}]"
                else:
                    current_message_for_prompt_builder = f"{message_text} [{message_type.upper() if message_type else 'MEDIA'} received, analysis failed or not applicable]"

            processed_current_user_message_text = process_conversation_for_media(
                current_message_for_prompt_builder)

            prompt_str_for_ai, prompt_type = build_member_chat_prompt(
                client_data=metrics_dict,
                current_message=processed_current_user_message_text,
                current_stage=current_stage,
                trial_status=trial_status,
                full_name=calculated_full_name
            )
            ai_raw_response_text = await get_ai_response(prompt_str_for_ai)

            # --- Post-process the response to ensure it's a direct reply from Shannon ---
            if ai_raw_response_text:
                ai_raw_response_text = await filter_shannon_response(ai_raw_response_text, processed_current_user_message_text)

            # --- Enforce soft challenge-offer flow (prevent premature link) ---
            if ai_raw_response_text:
                try:
                    ai_raw_response_text = enforce_challenge_offer_rules(
                        ai_raw_response_text, full_conversation_history)
                except Exception as e:
                    logger.error(f"Challenge offer gating error: {e}")
                # --- Remove repeated questions and rewrite if necessary ---
                ai_raw_response_text = await _dedup_and_rewrite_if_needed(ai_raw_response_text, full_conversation_history)

            if ai_raw_response_text:
                ai_response_for_analytics = ai_raw_response_text
                ai_responses_list_for_manychat = split_response_into_messages(
                    ai_raw_response_text)

                # New: Set response time for general AI replies
                # Default to an invalid state or handle appropriately
                time_diff_seconds_for_bucket = -1.0
                last_bot_sent_ts = manychat_last_bot_sent_timestamps.get(
                    subscriber_id)

                if last_bot_sent_ts is not None:
                    # batch_start_time_s is the timestamp of the current user's message (earliest in batch)
                    time_diff_seconds_for_bucket = batch_start_time_s - last_bot_sent_ts
                    logger.info(
                        f"[GENERAL RESPONSE] User message at {datetime.fromtimestamp(batch_start_time_s).isoformat()}, last bot message at {datetime.fromtimestamp(last_bot_sent_ts).isoformat()}. Difference for bucket: {time_diff_seconds_for_bucket:.2f}s"
                    )
                else:
                    # No in-memory record of the last bot message (likely after a service restart).
                    # Attempt a smarter fallback by inspecting the stored conversation history for the
                    # most recent 'ai' message timestamp. This keeps response-time buckets accurate even
                    # after restarts where the cache is cleared.
                    last_ai_ts_float: Optional[float] = None
                    for _entry in reversed(full_conversation_history):
                        if _entry.get("type") == "ai" and _entry.get("timestamp"):
                            try:
                                last_ai_dt = parser.parse(
                                    _entry["timestamp"], ignoretz=False)
                                last_ai_ts_float = last_ai_dt.timestamp()
                                break
                            except Exception:
                                # Skip entries with unparseable timestamps and keep searching
                                continue

                    if last_ai_ts_float is not None:
                        time_diff_seconds_for_bucket = batch_start_time_s - last_ai_ts_float
                        logger.info(
                            f"[GENERAL RESPONSE] Fallback using history. User message at {datetime.fromtimestamp(batch_start_time_s).isoformat()}, last AI message at {datetime.fromtimestamp(last_ai_ts_float).isoformat()}. Difference for bucket: {time_diff_seconds_for_bucket:.2f}s"
                        )
                    else:
                        # Ultimate fallback – use current processing latency (a few seconds)
                        time_diff_seconds_for_bucket = time.time() - batch_start_time_s
                        logger.info(
                            f"[GENERAL RESPONSE] No last AI message found in history for SID {subscriber_id}. Using processing latency for bucket: {time_diff_seconds_for_bucket:.2f}s"
                        )

                response_time_value_general = get_response_time_bucket(
                    time_diff_seconds_for_bucket)
                logger.info(
                    f"[GENERAL RESPONSE] Calculated time diff for bucket: {time_diff_seconds_for_bucket:.2f}s, Bucket: {response_time_value_general} for SID {subscriber_id}")

                if update_manychat_fields(subscriber_id, {"response time": response_time_value_general}):
                    logger.info(
                        f"Successfully set 'response time' to '{response_time_value_general}' for SID {subscriber_id} (general AI response)")
                    # Short delay before sending message content
                    await asyncio.sleep(random.uniform(1, 2))
                else:
                    logger.error(
                        f"Failed to set 'response time' for SID {subscriber_id} (general AI response)")

                field_names = ["o1 Response", "o1 Response 2", "o1 Response 3"]
                for i, response_text_chunk in enumerate(ai_responses_list_for_manychat):
                    if i < len(field_names):
                        field_name_to_use = field_names[i]
                        field_updates = {
                            field_name_to_use: response_text_chunk}
                        # Directly call update_manychat_fields which is expected to be in this file or imported correctly
                        success = update_manychat_fields(
                            subscriber_id, field_updates)
                        if not success:
                            logger.error(
                                f"Failed to send chunk {i+1} to field {field_name_to_use} for SID {subscriber_id}")
                        # Add a small delay between sending message parts, except for the last one
                    if i < len(ai_responses_list_for_manychat) - 1:
                        await asyncio.sleep(random.uniform(1, 3))
                    else:
                        logger.warning(
                            f"More than {len(field_names)} message chunks generated, but only {len(field_names)} fields are handled. Chunk {i+1} not sent.")

                # Update the timestamp *after* all chunks are sent
                if ai_responses_list_for_manychat:  # If any AI message was actually sent
                    manychat_last_bot_sent_timestamps[subscriber_id] = time.time(
                    )
                    logger.info(
                        f"Updated manychat_last_bot_sent_timestamps for SID {subscriber_id} after sending general AI response parts.")

                ai_onboarding_trigger_phrase = "No worries! Ill let you know when your set up, and youll get an invite via email from me! Let me get into this! Chat in a bit!".lower()
                if ai_onboarding_trigger_phrase in ai_response_for_analytics.lower():
                    logger.info(
                        f"AI response triggered onboarding sequence for {ig_username} (subscriber_id: {subscriber_id}).")
                    post_onboarding_handler = PostOnboardingHandler(
                        gemini_api_key=GEMINI_API_KEY)

                    onboarding_task_payload = functools.partial(
                        post_onboarding_handler.process_onboarding_completion,
                        ig_username=ig_username,
                        subscriber_id=subscriber_id,
                        conversation_history=full_conversation_history
                    )
                    background_tasks.add_task(onboarding_task_payload)
                    logger.info(
                        f"Full onboarding process for {ig_username} (subscriber_id: {subscriber_id}) scheduled in background via buffered handler.")
            else:
                logger.warning(
                    f"No AI response generated for {ig_username} (from combined message)")
                ai_response_for_analytics = "[AI FAILED TO RESPOND]"
        else:
            logger.info(
                f"Action handled for {ig_username} (from combined message), AI response might have been sent by action handler.")
            ai_response_for_analytics = "[Action handled by detect_and_handle_action]"

        # update_analytics_data will save the processed_final_combined_message_text as the user's message
        # and the ai_response_for_analytics as the AI's response to the conversation history.
        # Convert batch_start_time_s to ISO format for the user message timestamp
        user_message_timestamp_iso = datetime.fromtimestamp(
            batch_start_time_s).isoformat()

        update_analytics_data(
            ig_username=ig_username,
            user_message=processed_final_combined_message_text,
            ai_response=ai_response_for_analytics,
            subscriber_id=subscriber_id,
            first_name=first_name_for_analytics,
            last_name=last_name_for_analytics,
            user_message_timestamp=user_message_timestamp_iso  # Pass the actual timestamp
        )
        logger.info(
            f"Finished processing buffered messages for SID {subscriber_id}")

        return PlainTextResponse("Webhook processed", status_code=200)

    except asyncio.CancelledError:
        logger.info(f"Response task for {sender_id} was cancelled.")
    except Exception as e:
        logger.error(
            f"Error in scheduled response task for {sender_id}: {e}", exc_info=True)
        # Optionally try to send an error message to the user
        try:
            await send_instagram_reply(sender_id, "Sorry, something went wrong on my end. Please try again later.")
        except Exception as send_err:
            logger.error(
                f"Failed to send error message to {sender_id}: {send_err}")

# --- Story Comment Handling Functions --- START ---


@app.post("/trainerize/build-program-deprecated")
async def build_trainerize_program(request_data: BuildProgramRequest):
    """
    API endpoint to build a full training program for a client in Trainerize.
    """
    logger.info(
        f"Received request to build program for: {request_data.client_name}")

    try:
        # Create a new TrainerizeAutomation instance
        trainerize = TrainerizeAutomation()
        try:
            # Convert Pydantic model to dictionary list for the method call
            workout_defs_dict = [wd.dict()
                                 for wd in request_data.workout_definitions]

            # Call the method on the instance
            results = trainerize.build_full_program_for_client(
                client_name=request_data.client_name,
                program_name=request_data.program_name,
                workout_definitions=workout_defs_dict
            )

            # Check if the overall process encountered critical failures
            critical_failure = any(step['step'] in ['navigate_to_client', 'navigate_to_training_program',
                                                    'create_program'] and not step['success'] for step in results)

            if critical_failure:
                logger.error(
                    f"Critical failure during program build for {request_data.client_name}. Results: {results}")
                # Return a server error status code if critical steps failed
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": "Failed to build program due to critical error during automation.", "details": results}
                )
            else:
                logger.info(
                    f"Successfully completed program build request for {request_data.client_name}. Results: {results}")
                return JSONResponse(
                    status_code=200,
                    content={"message": "Program build process initiated.",
                             "details": results}
                )
        finally:
            # Always cleanup the instance
            trainerize.cleanup()

    except Exception as e:
        logger.error(
            f"Error calling build_full_program_for_client for {request_data.client_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error during program build: {str(e)}")


def update_manychat_fields(subscriber_id: str, field_updates: Dict[str, str]) -> bool:
    """Update custom fields in ManyChat for a subscriber"""
    # Filter out None and empty string values
    filtered_updates = {
        k: v for k, v in field_updates.items() if v is not None and v != ""}
    if not filtered_updates:
        logger.info("No valid field updates to send to ManyChat.")
        return True  # Nothing to update, consider it success

    # Prepare the data using field_name
    field_data = [
        {"field_name": field_name, "field_value": value}
        for field_name, value in filtered_updates.items()
    ]
    data = {
        "subscriber_id": subscriber_id,
        "fields": field_data
    }

    headers = {
        "Authorization": f"Bearer {MANYCHAT_API_KEY}",
        "Content-Type": "application/json"
    }

    logger.info(
        f"Attempting to update ManyChat fields for subscriber {subscriber_id}: {list(filtered_updates.keys())}")
    # --- ADDED DETAILED PAYLOAD LOGGING ---
    logger.info(f"ManyChat API Request Payload: {json.dumps(data, indent=2)}")
    # --- END ADDED LOGGING ---
    try:
        response = requests.post(
            "https://api.manychat.com/fb/subscriber/setCustomFields", headers=headers, json=data, timeout=10)
        # Log beginning of response
        logger.info(
            f"ManyChat API response: {response.status_code} - {response.text[:500]}")
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        logger.info(
            f"Successfully updated ManyChat fields for subscriber {subscriber_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Error updating ManyChat fields for subscriber {subscriber_id}: {e}", exc_info=True)
        # Log response body if available
        if hasattr(e, 'response') and e.response is not None:
            logger.error(
                f"ManyChat Error Response Body: {e.response.text[:500]}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during ManyChat field update for {subscriber_id}: {e}", exc_info=True)
        return False


# --- ADDED: Dictionary to store last sent timestamp for ManyChat users ---
manychat_last_bot_sent_timestamps: Dict[str, float] = {}
# --- END ADDED ---

# --- ADDED: Message Buffer System ---

# Global dictionaries for message buffering
manychat_message_buffer: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
manychat_last_message_time: Dict[str, float] = {}
BUFFER_WINDOW = 60  # seconds to wait for grouping messages
user_buffer_task_scheduled: Dict[str, bool] = {}  # For new buffering logic
# Store actual task objects for cancellation
user_buffer_tasks: Dict[str, any] = {}

# Track workout edit states
program_edit_pending: Dict[str, str] = {}

# Global message buffer
message_buffer = {}


def add_to_message_buffer(ig_username: str, payload: Dict):
    """Add a message to the buffer for a given user"""
    if ig_username not in message_buffer:
        message_buffer[ig_username] = []
    message_buffer[ig_username].append(
        {'payload': payload, 'timestamp': datetime.now()})
    logger.info(f"Added message to buffer for {ig_username}")


def process_buffered_messages(ig_username: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Process any buffered messages for a given user"""
    try:
        # Get the user's buffered messages
        user_buffer = message_buffer.get(ig_username, [])
        if not user_buffer:
            logger.info(f"No buffered messages found for {ig_username}")
            return None

        # Get the payload from the first message (should contain user info)
        first_message = user_buffer[0]
        payload = first_message.get('payload', {})

        # Extract subscriber_id and other info
        subscriber_id = payload.get('id')
        if not subscriber_id:
            logger.error(
                f"No subscriber_id found in payload for {ig_username}")
            return None

        # Combine all messages
        combined_message_text_parts = []
        for msg in user_buffer:
            msg_text = msg.get('payload', {}).get('last_input_text', '')
            if msg_text:
                if combined_message_text_parts:
                    combined_message_text_parts.append("\n")
                combined_message_text_parts.append(msg_text)

        if not combined_message_text_parts:
            logger.error(f"No message content found for {ig_username}")
            return None

        logger.info(
            f"Successfully processed buffer for {ig_username}: {combined_message_text_parts}")

        # === SMART MESSAGE COMBINATION: Handle repeated messages intelligently ===
        if len(combined_message_text_parts) == 1:
            # Single message - use as-is
            final_combined_message_text = combined_message_text_parts[0].strip(
            )
        elif len(combined_message_text_parts) > 1:
            # Multiple messages - check for repetition
            message_counts = {}
            unique_messages = []

            for msg in combined_message_text_parts:
                msg_clean = msg.strip()
                if msg_clean:
                    if msg_clean in message_counts:
                        message_counts[msg_clean] += 1
                    else:
                        message_counts[msg_clean] = 1
                        unique_messages.append(msg_clean)

            # Build final message with smart formatting
            formatted_parts = []
            for msg in unique_messages:
                count = message_counts[msg]
                if count > 1:
                    formatted_parts.append(f"[{count}x] {msg}")
                else:
                    formatted_parts.append(msg)

            final_combined_message_text = " ".join(formatted_parts)
        else:
            final_combined_message_text = ""
        # === END SMART MESSAGE COMBINATION ===

        return final_combined_message_text, payload

    except Exception as e:
        logger.error(f"Error processing buffered messages: {str(e)}")
        return None
    finally:
        # Always clear the buffer after processing
        message_buffer.pop(ig_username, None)
        logger.info(f"Cleared message buffer for {ig_username}")


async def delayed_message_processing(ig_username: str):
    """Process messages after a delay to allow for grouping."""
    try:
        await asyncio.sleep(BUFFER_WINDOW)  # Wait for messages to accumulate

        logger.info(
            f"\n=== DELAYED MESSAGE PROCESSING START for {ig_username} ===")

        # Get buffered messages
        if ig_username not in message_buffer:
            logger.warning(f"No messages in buffer for {ig_username}")
            return

        messages = message_buffer[ig_username]
        if not messages:
            logger.warning(f"Empty message list in buffer for {ig_username}")
            return

        # Get user data for prompt context
        full_conversation_history, metrics_dict, user_id_key = get_user_data(
            ig_username=ig_username,
            subscriber_id=messages[0].get("subscriber_id", "")
        )

        # Extract needed values from metrics_dict
        current_stage = metrics_dict.get(
            'journey_stage', {}).get('current_stage', 'Topic 1')
        trial_status = metrics_dict.get('client_status', 'Initial Contact')
        full_name = f"{metrics_dict.get('first_name', '')} {metrics_dict.get('last_name', '')}".strip(
        )
        if not full_name:
            full_name = ig_username

        combined_message = " ".join([msg["text"] for msg in messages])
        logger.info(f"Combined message: {combined_message}")

        # Clear buffer after reading
        message_buffer[ig_username] = []

        # Process media URLs in the combined message
        processed_message = process_conversation_for_media(combined_message)
        logger.info(
            f"Processed message (after media handling): {processed_message}")

        # Build chat prompt using build_member_chat_prompt with all required parameters
        chat_prompt, prompt_type = build_member_chat_prompt(
            client_data=metrics_dict,
            current_message=processed_message,
            conversation_history="",
            current_stage=current_stage,
            trial_status=trial_status,
            full_name=full_name
        )

        # Get AI response
        ai_response = await get_ai_response(chat_prompt)
        if not ai_response:
            logger.error("Failed to get AI response")
            return

        # Update analytics data
        update_analytics_data(
            ig_username=ig_username,
            user_message=processed_message,
            ai_response=ai_response,
            subscriber_id=messages[0].get("subscriber_id", ""),
            first_name=messages[0].get("first_name", ""),
            last_name=messages[0].get("last_name", ""),
            set_checkin_flow_false=False
        )

        # Split and send response
        response_messages = split_response_into_messages(ai_response)
        for msg in response_messages:
            await send_manychat_message(
                subscriber_id=messages[0].get("subscriber_id", ""),
                message=msg
            )
            await asyncio.sleep(1)  # Small delay between messages

    except Exception as e:
        logger.error(
            f"Error in delayed_message_processing: {e}", exc_info=True)


@app.post("/webhook/manychat")
async def process_manychat_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    payload_str = raw_body.decode('utf-8')
    logger.info(f"Received raw payload: {payload_str[:1000]}...")

    manychat_signature = request.headers.get('X-ManyChat-Signature')
    if manychat_signature:
        # Assuming verify_manychat_signature function exists and works
        # if not verify_manychat_signature(payload_str, manychat_signature, MANYCHAT_API_KEY):
        #     logger.warning("Invalid X-ManyChat-Signature. Aborting.")
        #     raise HTTPException(status_code=403, detail="Invalid signature")
        logger.info(
            "X-ManyChat-Signature would be verified here (assuming function exists).")
    else:
        logger.info(
            "No X-ManyChat-Signature header found. Proceeding without signature verification.")

    try:
        data = json.loads(payload_str)
        logger.info(f"Parsed payload: {json.dumps(data, indent=2)[:1000]}...")
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON payload.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    subscriber_id = data.get("id")
    if not subscriber_id:
        subscriber_id = data.get("subscriber", {}).get("id", "")
        if not subscriber_id:
            logger.error(
                "[Webhook] Critical: Subscriber ID missing in payload.")
            # Changed to 400
            return PlainTextResponse("Error: Subscriber ID missing", status_code=400)
    logger.info(f"[Webhook] Processing for subscriber_id: {subscriber_id}")

    # --- Start of ig_username extraction (should be robust as per previous edits) ---
    ig_username = None
    ig_username_from_payload = data.get("ig_username")

    # Always get raw_subscriber_data upfront as it's used in multiple fallbacks
    raw_subscriber_data = data.get("subscriber", {})
    if not isinstance(raw_subscriber_data, dict):  # Ensure it's a dict
        raw_subscriber_data = {}
        logger.warning(
            "[Webhook] 'subscriber' field in payload was not a dictionary. Defaulting to empty dict.")

    if ig_username_from_payload and isinstance(ig_username_from_payload, str) and ig_username_from_payload.strip():
        ig_username = ig_username_from_payload.strip()
        logger.info(
            f"[Webhook] Retrieved ig_username '{ig_username}' directly from payload.")

    if not ig_username:
        # raw_subscriber_data is already defined above
        custom_fields = raw_subscriber_data.get("custom_fields", {})
        if isinstance(custom_fields, dict):
            ig_username_from_cf = custom_fields.get("ig_username")
            if ig_username_from_cf and isinstance(ig_username_from_cf, str) and ig_username_from_cf.strip():
                ig_username = ig_username_from_cf.strip()
                logger.info(
                    f"[Webhook] Retrieved ig_username '{ig_username}' from subscriber.custom_fields.ig_username.")

        if not ig_username:
            # Re-get if not already gotten
            raw_subscriber_data = data.get("subscriber", {})
            ig_username_from_sub_name = raw_subscriber_data.get("name")
            if ig_username_from_sub_name and isinstance(ig_username_from_sub_name, str) and ig_username_from_sub_name.strip():
                temp_ig_name = ig_username_from_sub_name.strip()
                is_placeholder = temp_ig_name.startswith(
                    'user_') and temp_ig_name[5:].isdigit()
                if not is_placeholder:
                    ig_username = temp_ig_name
                    logger.info(
                        f"[Webhook] Retrieved ig_username '{ig_username}' from subscriber.name.")
                else:
                    logger.info(
                        f"[Webhook] subscriber.name ('{temp_ig_name}') is placeholder.")

    if not ig_username:
        # Further fallbacks for ig_username
        raw_subscriber_data = data.get("subscriber", {})
        ig_username_from_sub_uname = raw_subscriber_data.get("user_name")
        if ig_username_from_sub_uname and isinstance(ig_username_from_sub_uname, str) and ig_username_from_sub_uname.strip():
            temp_ig_username = ig_username_from_sub_uname.strip()
            is_placeholder_user_id_format = temp_ig_username.startswith(
                'user_') and temp_ig_username[5:] == str(subscriber_id)
            is_generic_placeholder = temp_ig_username.startswith(
                'user_') and temp_ig_username[5:].isdigit()
            if not is_placeholder_user_id_format and not is_generic_placeholder:
                ig_username = temp_ig_username
                logger.info(
                    f"[Webhook] Retrieved ig_username '{ig_username}' from subscriber.user_name.")
            elif is_placeholder_user_id_format or is_generic_placeholder:
                logger.info(
                    f"[Webhook] subscriber.user_name ('{temp_ig_username}') is placeholder.")

    # --- NEW: API call to ManyChat if username is missing or a placeholder ---
    is_placeholder_username = ig_username and ig_username.startswith(
        'user_') and ig_username[5:].isdigit()
    if not ig_username or is_placeholder_username:
        logger.warning(
            f"IG username is missing or a placeholder ('{ig_username}'). Attempting to fetch from ManyChat API for SID {subscriber_id}.")
        try:
            api_username = await get_username_from_manychat(subscriber_id)
            if api_username:
                logger.info(
                    f"Successfully fetched username '{api_username}' from API. Using it.")
                ig_username = api_username
            else:
                logger.warning(
                    f"Could not fetch a valid username from ManyChat API for SID {subscriber_id}. Proceeding with '{ig_username}'.")
        except Exception as api_e:
            logger.error(
                f"An exception occurred while trying to fetch username from ManyChat API: {api_e}")

    if not ig_username:
        ig_username = f"user_{subscriber_id}"  # Final fallback
        logger.warning(
            f"[Webhook] Using generated ig_username: '{ig_username}'.")
    # --- End of ig_username extraction ---

    # Add the current message payload to the user's buffer
    # The 'data' here is the full parsed JSON payload of the current webhook
    if subscriber_id not in manychat_message_buffer:
        manychat_message_buffer[subscriber_id] = []

    # Get 'created_at' or default to now
    user_message_created_at_s = data.get("created_at", time.time())

    manychat_message_buffer[subscriber_id].append(
        {"payload": data, "user_msg_created_at_s": user_message_created_at_s})
    logger.info(
        f"Appended message from SID {subscriber_id} (created_at: {datetime.fromtimestamp(user_message_created_at_s).isoformat()}) to buffer. Buffer size: {len(manychat_message_buffer[subscriber_id])}")

    # Enhanced timer restart logic: Cancel existing task if present and schedule a new one
    # This ensures the 60-second timer restarts with each new message
    if subscriber_id in user_buffer_tasks:
        # Cancel the existing task to restart the timer
        try:
            existing_task = user_buffer_tasks[subscriber_id]
            if existing_task and not existing_task.done():
                existing_task.cancel()
                logger.info(
                    f"⏰ Canceled existing buffer task for SID {subscriber_id} - timer restarting for {BUFFER_WINDOW}s")
        except Exception as e:
            logger.warning(
                f"Error canceling existing task for SID {subscriber_id}: {e}")

    # Always schedule a new task (either first message or restarting timer)
    user_buffer_task_scheduled[subscriber_id] = True
    new_task = background_tasks.add_task(
        run_core_processing_after_buffer, subscriber_id, ig_username, background_tasks)
    user_buffer_tasks[subscriber_id] = new_task

    if len(manychat_message_buffer[subscriber_id]) == 1:
        logger.info(
            f"🆕 Started {BUFFER_WINDOW}s buffer timer for SID: {subscriber_id}, IG: {ig_username}")
    else:
        logger.info(
            f"🔄 Restarted {BUFFER_WINDOW}s buffer timer for SID: {subscriber_id} (message #{len(manychat_message_buffer[subscriber_id])})")

    # --- After extracting ig_username and subscriber_id ---
    # Ensure subscriber_id is written to the user's profile if missing or different
    try:
        import sqlite3
        SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
        conn = sqlite3.connect(SQLITE_PATH)
        c = conn.cursor()
        # Check current subscriber_id for this ig_username
        c.execute(
            "SELECT subscriber_id FROM users WHERE ig_username = ?", (ig_username,))
        row = c.fetchone()
        if row is not None:
            current_subscriber_id = row[0]
            if current_subscriber_id != subscriber_id:
                c.execute("UPDATE users SET subscriber_id = ? WHERE ig_username = ?",
                          (subscriber_id, ig_username))
                conn.commit()
                logger.info(
                    f"Updated subscriber_id for {ig_username} to {subscriber_id} in SQLite DB.")
        conn.close()
    except Exception as e:
        logger.error(
            f"Failed to update subscriber_id for {ig_username} in SQLite DB: {e}")

    return PlainTextResponse("Webhook received, processing deferred.", status_code=200)


@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify the server is running"""
    return {"status": "ok", "message": "Server is running"}


def get_response_time_bucket(time_diff_seconds: float) -> str:
    """
    Convert time difference to ManyChat response time bucket.
    Args:
        time_diff_seconds: Time difference in seconds
    Returns:
        String matching ManyChat's response time conditions
    """
    if time_diff_seconds <= 120:  # 0-2 minutes
        return "response time is 0-2minutes"
    elif time_diff_seconds <= 300:  # 2-5 minutes
        return "response time is 2-5 minutes"
    elif time_diff_seconds <= 600:  # 5-10 minutes
        return "response time is 5-10 minutes"
    elif time_diff_seconds <= 1200:  # 10-20 minutes
        return "response time is 10-20 minutes"
    elif time_diff_seconds <= 1800:  # 20-30 minutes
        return "response time is 20-30 minutes"
    elif time_diff_seconds <= 3600:  # 30-60 minutes
        return "response time is 30-60 minutes"
    elif time_diff_seconds <= 7200:  # 1-2 Hours
        return "response time is 1-2 Hours"
    else:  # This will now catch everything > 7200 seconds (2 hours)
        return "response time is 2-5 Hours"


async def _handle_buffered_messages_for_subscriber(subscriber_id: str, ig_username: str, message_payloads: List[Dict], bg_tasks: BackgroundTasks, batch_start_time_s: float):
    """
    Core logic to process a batch of buffered messages for a subscriber.
    Moved from the main body of process_manychat_webhook.
    """
    logger.info(
        f"[_handle_buffered_messages_for_subscriber] Processing {len(message_payloads)} buffered messages for SID: {subscriber_id}, IG: {ig_username}")

    combined_message_text_parts = []
    last_full_payload = None

    for p_data in message_payloads:
        current_msg_text = p_data.get("last_input_text", "")
        if not current_msg_text:
            current_msg_text = p_data.get("o1 input", "")

        current_media_url = None
        current_message_type = None
        latest_message_object = p_data.get("message")

        if isinstance(latest_message_object, dict):
            if not current_msg_text:
                current_msg_text = latest_message_object.get("text", "")

            # Only proceed to check attachments if latest_message_object is a dictionary
            if "attachments" in latest_message_object and latest_message_object["attachments"]:
                attachment = latest_message_object["attachments"][0]
                current_media_url = attachment.get("url")
                current_message_type = attachment.get("type")
                # Normalize audio type from common file extensions if type is 'file'
                if current_message_type == "file" and current_media_url and any(ext in current_media_url for ext in [".mp3", ".ogg", ".wav", ".m4a"]):
                    current_message_type = "audio"
        # Handle cases where 'message' might be a string
        elif isinstance(latest_message_object, str):
            if not current_msg_text:
                # Reverted: was latest_message_object.get("text", "")
                current_msg_text = latest_message_object
        # If latest_message_object is None or not a dict/str, current_msg_text remains as is (or empty)

        text_for_this_message_segment = current_msg_text
        if current_media_url:
            if not text_for_this_message_segment:
                text_for_this_message_segment = current_media_url
            elif current_media_url not in text_for_this_message_segment:
                text_for_this_message_segment = f"{text_for_this_message_segment} {current_media_url}"

        if text_for_this_message_segment:
            combined_message_text_parts.append(text_for_this_message_segment)

        last_full_payload = p_data

    # === SMART MESSAGE COMBINATION: Handle repeated messages intelligently ===
    if len(combined_message_text_parts) == 1:
        # Single message - use as-is
        final_combined_message_text = combined_message_text_parts[0].strip()
    elif len(combined_message_text_parts) > 1:
        # Multiple messages - check for repetition
        message_counts = {}
        unique_messages = []

        for msg in combined_message_text_parts:
            msg_clean = msg.strip()
            if msg_clean:
                if msg_clean in message_counts:
                    message_counts[msg_clean] += 1
                else:
                    message_counts[msg_clean] = 1
                    unique_messages.append(msg_clean)

        # Build final message with smart formatting
        formatted_parts = []
        for msg in unique_messages:
            count = message_counts[msg]
            if count > 1:
                formatted_parts.append(f"[{count}x] {msg}")
            else:
                formatted_parts.append(msg)

        final_combined_message_text = " ".join(formatted_parts)
    else:
        final_combined_message_text = ""
    # === END SMART MESSAGE COMBINATION ===

    if not final_combined_message_text:
        logger.info(
            f"Buffer for {subscriber_id} (IG: {ig_username}) contained no text after combining. Skipping.")
        return

    logger.info(
        f"Combined message for SID {subscriber_id} (IG: {ig_username}): '{final_combined_message_text[:200]}...'")

    # Process the combined message ONCE for media content.
    # This processed version will be used for history, AI prompts, and logging.
    processed_final_combined_message_text = process_conversation_for_media(
        final_combined_message_text)
    logger.info(
        f"Message after processing media (for history, prompts, logging): {processed_final_combined_message_text[:200]}...")

    # The original final_combined_message_text will be passed to detect_and_handle_action
    # to ensure its internal URL extraction works correctly.
    # The block that created 'text_for_action_detection' by replacing URL with raw analysis is removed.

    first_name_for_analytics = last_full_payload.get("first_name", "")
    last_name_for_analytics = last_full_payload.get("last_name", "")

    # Get user data (including conversation history up to this point)
    # Note: full_conversation_history here is a reference to the list within metrics_dict (or a loaded structure)
    # We will not append the current user message here; update_analytics_data will handle it.
    full_conversation_history, metrics_dict, user_id_key = get_user_data(
        ig_username=ig_username,
        subscriber_id=subscriber_id
    )

    # === NEW: On-demand bio analysis check ===
    # Check if this user has bio analysis data, and trigger analysis if missing
    # This runs as a background task to not block webhook processing
    if ig_username and ig_username.strip():
        bg_tasks.add_task(check_and_trigger_bio_analysis,
                          ig_username, subscriber_id)
        logger.debug(f"🔍 Queued bio analysis check for {ig_username}")
    # === END NEW ===

    # === NEW: Prepare conversation history for the prompt, including the current message(s) ===
    # Start with the history fetched from the DB
    history_for_prompt = full_conversation_history.copy()

    # Add the current user message(s) to the history for the prompt ONLY.
    # Use the batch_start_time_s for the timestamp of the user's message(s).
    # Use get_melbourne_time_str or a similar formatter for consistency if needed, but ISO format is often fine.
    # Using ISO format derived from batch_start_time_s to reflect arrival time more accurately than datetime.now()
    user_message_timestamp_iso = datetime.fromtimestamp(
        batch_start_time_s).isoformat()

    # Skipping adding the processed user message to `history_for_prompt` to avoid
    # duplication in the final prompt (it is already included in the dedicated
    # "Last User Message" block).
    # if processed_final_combined_message_text:
    #     history_for_prompt.append({
    #         "timestamp": user_message_timestamp_iso,
    #         "type": "user",
    #         "text": processed_final_combined_message_text
    #     })

    # Format this expanded history list for the prompt
    formatted_history_for_prompt_str = format_conversation_history(
        history_for_prompt)
    # === END NEW ===

    # detect_and_handle_action receives the ORIGINAL combined message text.
    action_handled = await detect_and_handle_action(ig_username, final_combined_message_text, subscriber_id, last_full_payload, batch_start_time_s)

    ai_response_for_analytics = ""

    if not action_handled:
        logger.info(
            f"No specific action detected for {ig_username} (from combined message), proceeding to general AI response.")
        current_stage = metrics_dict.get(
            'journey_stage', {}).get('current_stage', "Topic 1")
        trial_status = metrics_dict.get('trial_status', "Initial Contact")

        calculated_full_name = f"{first_name_for_analytics} {last_name_for_analytics}".strip(
        )
        if not calculated_full_name:  # Fallback
            full_name_from_metrics_fn = metrics_dict.get('first_name', '')
            full_name_from_metrics_ln = metrics_dict.get('last_name', '')
            calculated_full_name = f"{full_name_from_metrics_fn} {full_name_from_metrics_ln}".strip(
            )
        if not calculated_full_name:
            calculated_full_name = ig_username

        # ---- ADDED: Fetch few-shot examples ----
        few_shot_examples = []  # Default to empty list
        try:
            few_shot_examples = get_good_few_shot_examples(
                limit=100)  # MODIFIED: Fetch up to 100 examples (increased from 50)
            if few_shot_examples:
                logger.info(
                    f"Successfully fetched {len(few_shot_examples)} few-shot examples for {ig_username}.")
            else:
                logger.info(f"No few-shot examples found for {ig_username}.")
        except Exception as e_fs:
            logger.error(
                f"Error fetching few-shot examples for {ig_username}: {e_fs}", exc_info=True)
        # ---- END ADDED ----

        # Use the processed message for the AI prompt
        prompt_str_for_ai, prompt_type = build_member_chat_prompt(
            client_data=metrics_dict,
            current_message=processed_final_combined_message_text,  # Use processed message
            current_stage=current_stage,
            trial_status=trial_status,
            full_name=calculated_full_name,
            # Pass the prepared history string
            full_conversation_string=formatted_history_for_prompt_str,
            few_shot_examples=few_shot_examples  # MODIFIED: Pass examples
        )
        ai_raw_response_text = await get_ai_response(prompt_str_for_ai)

        # Post-process the response using the processed user message for context
        if ai_raw_response_text:
            # Use processed message
            ai_raw_response_text = await filter_shannon_response(ai_raw_response_text, processed_final_combined_message_text)

        if ai_raw_response_text:
            ai_response_for_analytics = ai_raw_response_text  # This is the filtered response

            # ---- NEW: Check for challenge offers and create notifications ----
            offer_notification_created = False
            try:
                import sys
                import os
                app_dashboard_modules_path = os.path.join(
                    os.path.dirname(__file__), 'app', 'dashboard_modules')
                if app_dashboard_modules_path not in sys.path:
                    sys.path.insert(0, app_dashboard_modules_path)

                from notifications import check_ai_response_for_challenge_offer

                # Check if this AI response contains a challenge offer
                if check_ai_response_for_challenge_offer(ai_raw_response_text, ig_username):
                    logger.info(
                        f"🎯 Challenge offer notification created for {ig_username}")
                    offer_notification_created = True  # Set flag if notification was created
            except Exception as notif_e:
                logger.warning(
                    f"Could not check for challenge offer notification: {notif_e}")
            # ---- END NEW ----

            # ---- MODIFICATION: Check Auto Mode and either auto-schedule or queue for review ----
            incoming_msg_ts_iso = datetime.fromtimestamp(
                batch_start_time_s).isoformat()

            review_id = None  # Initialize review_id to None

            # Check auto mode status (both general and vegan modes)
            should_auto_process = False
            try:
                # Import the auto mode checkers
                import sys
                import os
                app_dashboard_modules_path = os.path.join(
                    os.path.dirname(__file__), 'app', 'dashboard_modules')
                if app_dashboard_modules_path not in sys.path:
                    sys.path.insert(0, app_dashboard_modules_path)

                from auto_mode_state import is_auto_mode_active, is_vegan_auto_mode_active

                # Check general auto mode
                general_auto_active = is_auto_mode_active()

                # Check vegan auto mode
                vegan_auto_active = is_vegan_auto_mode_active()

                if general_auto_active:
                    logger.info(
                        f"🤖 GENERAL AUTO MODE ACTIVE - Auto-processing {ig_username}")
                    should_auto_process = True
                elif vegan_auto_active:
                    # Check if user is a fresh vegan
                    try:
                        from dashboard_sqlite_utils import get_db_connection
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT is_fresh_vegan 
                            FROM conversation_strategy_log 
                            WHERE username = ? AND is_fresh_vegan = 1
                            LIMIT 1
                        """, (ig_username,))
                        result = cursor.fetchone()
                        conn.close()

                        if result:
                            logger.info(
                                f"🌱 VEGAN AUTO MODE ACTIVE - Auto-processing fresh vegan {ig_username}")
                            should_auto_process = True
                        else:
                            logger.info(
                                f"🌱 Vegan auto mode active but {ig_username} is not a fresh vegan - manual review required")
                            should_auto_process = False
                    except Exception as e:
                        logger.warning(
                            f"Could not check vegan status for {ig_username}: {e}")
                        should_auto_process = False
                else:
                    logger.info(
                        f"No auto mode active - {ig_username} requires manual review")
                    should_auto_process = False

            except ImportError:
                logger.warning(
                    "Could not import auto_mode_state, assuming Auto Mode is OFF.")
                should_auto_process = False

            if should_auto_process:
                logger.info(
                    f"🤖 AUTO MODE ACTIVE - Auto-scheduling response for {ig_username}")
                try:
                    # Ensure the scheduled responses table exists
                    conn = db_utils.get_db_connection()
                    create_scheduled_responses_table_if_not_exists(conn)
                    conn.close()

                    # Add to the review queue first, but with 'auto_scheduled' status
                    review_id = add_response_to_review_queue(
                        user_ig_username=ig_username,
                        user_subscriber_id=subscriber_id,
                        incoming_message_text=processed_final_combined_message_text,
                        incoming_message_timestamp=user_message_timestamp_iso,
                        generated_prompt_text=prompt_str_for_ai,
                        proposed_response_text=ai_raw_response_text,
                        prompt_type=prompt_type,
                        status='auto_scheduled'  # MODIFIED: Set status directly
                    )

                    if review_id:
                        # Now schedule the response with timing delay
                        from response_review import schedule_auto_response
                        success_schedule, schedule_message, delay_minutes = schedule_auto_response(
                            # Create a mock review_item for the function
                            {
                                'review_id': review_id,
                                'user_ig_username': ig_username,
                                'user_subscriber_id': subscriber_id,
                                'incoming_message_text': processed_final_combined_message_text,
                                'incoming_message_timestamp': user_message_timestamp_iso,
                                'proposed_response': ai_raw_response_text,
                                'status': 'auto_scheduled'
                            },
                            ai_raw_response_text,
                            user_notes="",
                            manual_context=""
                        )

                        if success_schedule:
                            logger.info(
                                f"✅ AUTO-SCHEDULED: {ig_username} - Response queued for {delay_minutes} minutes")
                        else:
                            logger.error(
                                f"❌ Auto-schedule FAILED for {ig_username}: {schedule_message}")
                    else:
                        logger.error(
                            f"❌ Failed to add auto-scheduled review for {ig_username}")

                except Exception as e_auto:
                    logger.error(
                        f"❌ Failed to auto-schedule for {ig_username}, falling back to manual review: {e_auto}", exc_info=True)
                    # Fallback: Add to review queue without scheduling
                    review_id = add_response_to_review_queue(
                        user_ig_username=ig_username,
                        user_subscriber_id=subscriber_id,
                        incoming_message_text=processed_final_combined_message_text,
                        incoming_message_timestamp=user_message_timestamp_iso,
                        generated_prompt_text=prompt_str_for_ai,
                        proposed_response_text=ai_raw_response_text,
                        prompt_type=prompt_type
                    )
            else:
                # --- ADDED: Standard behavior when auto-mode is OFF ---
                logger.info(
                    f"Auto mode is OFF. Adding response for {ig_username} to review queue.")
                review_id = add_response_to_review_queue(
                    user_ig_username=ig_username,
                    user_subscriber_id=subscriber_id,
                    incoming_message_text=processed_final_combined_message_text,
                    incoming_message_timestamp=user_message_timestamp_iso,
                    generated_prompt_text=prompt_str_for_ai,
                    proposed_response_text=ai_raw_response_text,
                    prompt_type=prompt_type
                )
                if review_id:
                    logger.info(
                        f"Successfully added response for {ig_username} to review queue (Review ID: {review_id})")
                else:
                    logger.error(
                        f"Failed to add response to review queue for {ig_username}")
                # --- END ADDED ---

            if review_id:
                logger.info(
                    f"Successfully queued response for review (ID: {review_id}) for SID: {subscriber_id}")
                # Optionally, you could set a generic ManyChat field here to indicate message received, e.g.:
                # update_manychat_fields(subscriber_id, {"last_message_status": "received_processing"})
            else:
                logger.error(
                    f"Failed to queue response for review for SID: {subscriber_id}. The AI response was: {ai_raw_response_text[:100]}...")
                # Decide on fallback: send directly, or send error message?
                # For now, let's log and it won't be sent, nor explicitly error out to user.

            # --- ONBOARDING TRIGGER DETECTION ---
            # Phrase to START the onboarding question sequence (updates analytics, uses ONBOARDING_PROMPT_TEMPLATE next time)
            initiate_onboarding_questions_phrase = "get you onboarded"  # More general phrase
            # Phrase to trigger the PostOnboardingHandler (AFTER onboarding questions are done)
            ai_full_onboarding_complete_phrase = "No worries! Ill let you know when your set up, and youll get an invite via email from me! Let me get into this! Chat in a bit!".lower()

            if initiate_onboarding_questions_phrase.lower() in ai_response_for_analytics.lower():
                logger.info(
                    f"[ONBOARDING QUESTIONS START] AI response '{ai_response_for_analytics[:50]}...' triggered start of onboarding questions for {ig_username} (SubID: {subscriber_id}).")
                analytics_file_path = r"C:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot\\app\\analytics_data_good.json"
                try:
                    with open(analytics_file_path, "r+") as f:  # Open for reading and writing
                        analytics_data = json.load(f)
                        target_user_id_for_onboarding = None
                        conversations_data_onboarding = analytics_data.get(
                            'conversations', {})
                        search_ig_username_lower_onboarding = ig_username.strip().lower()

                        # Find user by subscriber_id first, then by ig_username if not found
                        found_by_sub_id = False
                        for user_id_loop_onboarding, user_data_loop_onboarding in conversations_data_onboarding.items():
                            if isinstance(user_data_loop_onboarding, dict):
                                metrics_data_onboarding = user_data_loop_onboarding.get(
                                    "metrics", {})
                                if isinstance(metrics_data_onboarding, dict) and metrics_data_onboarding.get("subscriber_id") == subscriber_id:
                                    target_user_id_for_onboarding = user_id_loop_onboarding
                                    found_by_sub_id = True
                                    break

                        if not found_by_sub_id:  # Fallback to ig_username if not found by subscriber_id
                            for user_id_loop_onboarding, user_data_loop_onboarding in conversations_data_onboarding.items():
                                if isinstance(user_data_loop_onboarding, dict):
                                    metrics_data_onboarding = user_data_loop_onboarding.get(
                                        "metrics", {})
                                    if isinstance(metrics_data_onboarding, dict):
                                        json_ig_username_onboarding = metrics_data_onboarding.get(
                                            "ig_username", None)
                                        if isinstance(json_ig_username_onboarding, str) and json_ig_username_onboarding.strip().lower() == search_ig_username_lower_onboarding:
                                            target_user_id_for_onboarding = user_id_loop_onboarding
                                            break

                        if target_user_id_for_onboarding and target_user_id_for_onboarding in conversations_data_onboarding:
                            metrics_to_update_onboarding = conversations_data_onboarding[target_user_id_for_onboarding].setdefault(
                                'metrics', {})
                            if not metrics_to_update_onboarding.get('is_onboarding', False):
                                metrics_to_update_onboarding['is_onboarding'] = True
                                # Or your desired first step
                                metrics_to_update_onboarding['expected_onboarding_input'] = "all_meals"
                                # Optionally clear previous target calculations if re-onboarding
                                metrics_to_update_onboarding.pop(
                                    'target_calories', None)
                                metrics_to_update_onboarding.pop(
                                    'target_protein', None)
                                metrics_to_update_onboarding.pop(
                                    'target_carbs', None)
                                metrics_to_update_onboarding.pop(
                                    'target_fats', None)
                                logger.info(
                                    f"[ONBOARDING QUESTIONS START] Set is_onboarding=true for user {target_user_id_for_onboarding}")
                                # Rewind to the beginning of the file
                                f.seek(0)
                                json.dump(analytics_data, f, indent=2)
                                f.truncate()  # Remove remaining part of old file
                                logger.info(
                                    f"[ONBOARDING QUESTIONS START] Saved updated onboarding state for {target_user_id_for_onboarding}")
                            else:
                                logger.info(
                                    f"[ONBOARDING QUESTIONS START] User {target_user_id_for_onboarding} already has is_onboarding=true.")
                        else:
                            logger.error(
                                f"[ONBOARDING QUESTIONS START] Could not find user {ig_username} (SubID: {subscriber_id}) in analytics data to set is_onboarding=true.")
                except (FileNotFoundError, json.JSONDecodeError, IOError) as e_analytics:
                    logger.error(
                        f"[ONBOARDING QUESTIONS START] Error accessing/updating analytics_data_good.json: {e_analytics}")

            # Separated logic for PostOnboardingHandler
            elif ai_full_onboarding_complete_phrase.lower() in ai_response_for_analytics.lower():
                logger.info(
                    f"[POST ONBOARDING HANDLER] AI response triggered PostOnboardingHandler for {ig_username} (subscriber_id: {subscriber_id}).")
                post_onboarding_handler = PostOnboardingHandler(
                    gemini_api_key=GEMINI_API_KEY)

                onboarding_task_payload = functools.partial(
                    post_onboarding_handler.process_onboarding_completion,
                    ig_username=ig_username,
                    subscriber_id=subscriber_id,  # Ensure subscriber_id is passed
                    conversation_history=full_conversation_history  # Pass the up-to-date history
                )
                bg_tasks.add_task(onboarding_task_payload)
                logger.info(
                    f"[POST ONBOARDING HANDLER] Full onboarding process for {ig_username} (subscriber_id: {subscriber_id}) scheduled in background.")
        else:
            logger.warning(
                f"No AI response generated for {ig_username} (from combined message)")
            ai_response_for_analytics = "[AI FAILED TO RESPOND]"
    else:
        logger.info(
            f"Action handled for {ig_username} (from combined message), AI response might have been sent by action handler.")
        # Ensure ai_response_for_analytics is set if an action was handled,
        # for consistent logging to update_analytics_data.
        # This might need to come from the return value of detect_and_handle_action if it sends a response.
        if not ai_response_for_analytics:  # If not already set by a sub-function of action_handled
            ai_response_for_analytics = "[Action implicitly handled by detect_and_handle_action or no AI response needed]"

    # update_analytics_data will save the processed_final_combined_message_text as the user's message
    # and the ai_response_for_analytics as the AI's response to the conversation history.
    # Convert batch_start_time_s to ISO format for the user message timestamp
    user_message_timestamp_iso = datetime.fromtimestamp(
        batch_start_time_s).isoformat()

    update_analytics_data(
        ig_username=ig_username,
        user_message=processed_final_combined_message_text,  # Use processed message
        ai_response=ai_response_for_analytics,
        subscriber_id=subscriber_id,
        first_name=first_name_for_analytics,
        last_name=last_name_for_analytics,
        user_message_timestamp=user_message_timestamp_iso  # Pass the actual timestamp
    )
    logger.info(
        f"Finished processing buffered messages for SID {subscriber_id}")


async def run_core_processing_after_buffer(subscriber_id: str, ig_username: str, bg_tasks: BackgroundTasks):
    """
    Waits for BUFFER_WINDOW, then retrieves and processes all messages for the subscriber.
    """
    logger.info(
        f"[run_core_processing_after_buffer] Task started for SID: {subscriber_id}, IG: {ig_username}. Waiting {BUFFER_WINDOW}s.")

    try:
        await asyncio.sleep(BUFFER_WINDOW)
    except asyncio.CancelledError:
        logger.info(
            f"[run_core_processing_after_buffer] Task was canceled for SID: {subscriber_id} - timer restarted by new message")
        return

    logger.info(
        f"[run_core_processing_after_buffer] Wait finished for SID: {subscriber_id}. Attempting to process buffer.")

    # Clean up task tracking
    user_buffer_task_scheduled.pop(subscriber_id, None)
    user_buffer_tasks.pop(subscriber_id, None)

    # buffered_message_payloads is a list of dicts like {"payload": data, "user_msg_created_at_s": timestamp}
    buffered_message_items = manychat_message_buffer.pop(subscriber_id, [])

    if not buffered_message_items:
        logger.info(
            f"No messages found in buffer for SID: {subscriber_id} after delay. Exiting task.")
        return

    # Extract payloads and find the earliest user message timestamp in the batch
    message_payloads_only = []
    batch_start_time_s = float('inf')
    if buffered_message_items:  # Ensure not empty before trying to access
        batch_start_time_s = buffered_message_items[0].get(
            "user_msg_created_at_s", time.time())  # Default to now if somehow missing

    for item in buffered_message_items:
        message_payloads_only.append(item["payload"])
        if "user_msg_created_at_s" in item:
            batch_start_time_s = min(
                batch_start_time_s, item["user_msg_created_at_s"])

    # If buffer was empty or items had no timestamp
    if batch_start_time_s == float('inf'):
        batch_start_time_s = time.time()
        logger.warning(
            f"Could not determine batch_start_time_s for SID {subscriber_id}, defaulting to current time.")

    logger.info(
        f"🔄 Processing {len(buffered_message_items)} buffered messages for SID {subscriber_id} after {BUFFER_WINDOW}s wait. Batch start: {datetime.fromtimestamp(batch_start_time_s).isoformat()}")

    await _handle_buffered_messages_for_subscriber(subscriber_id, ig_username, message_payloads_only, bg_tasks, batch_start_time_s)

# --- Helper function for actual form check video analysis ---


async def _analyze_form_check_video(ig_username: str, client_name_for_todo: str, video_url: str, user_desc_text: str, subscriber_id: str, batch_start_time_s: float):
    logger.info(
        f"[_analyze_form_check_video] Analyzing: {video_url[:60]} for {ig_username}")
    analysis_result_text = ""
    user_message_for_analytics = f"(Sent form check video: {video_url[:50]}... Description: '{user_desc_text[:30]}')"
    ai_response_for_analytics = ""

    try:
        analysis_result_text = get_video_analysis(
            video_url,
            GEMINI_API_KEY,
            GEMINI_MODEL_PRO,
            GEMINI_MODEL_FLASH,
            GEMINI_MODEL_FLASH_STANDARD
            # user_description=user_desc_text # This parameter is not accepted by get_video_analysis
        )
    except Exception as e:
        logger.error(f"Error calling get_video_analysis: {e}", exc_info=True)
        analysis_result_text = "Sorry, I encountered an error trying to analyze your video. Please try again later."

    if not analysis_result_text or "error" in analysis_result_text.lower() or "failed" in analysis_result_text.lower():
        response_to_user = analysis_result_text if analysis_result_text else "Sorry, couldn't analyze the video. Please try sending it again."
        logger.error(
            f"Video analysis failed for {ig_username}. Result: {analysis_result_text}")
        add_todo_item(ig_username, client_name_for_todo,
                      f"Video form check FAILED for: {video_url[:50]}...")
        ai_response_for_analytics = f"AI FAILED video form check. Reported: {response_to_user[:100]}"
    else:
        response_to_user = analysis_result_text
        add_todo_item(ig_username, client_name_for_todo,
                      f"Video form check COMPLETED for: {video_url[:50]}...", status="completed")
        ai_response_for_analytics = f"AI provided form check analysis. Analysis: {response_to_user[:100]}"

    field_updates = {"o1 Response": response_to_user,
                     "CONVERSATION": user_message_for_analytics}

    # For form check video analysis, explicitly set "response time" to "action"
    field_updates["response time"] = "action"
    logger.info(
        f"[_analyze_form_check_video] Set 'response time' to 'action' for SID {subscriber_id}")
    # Remove time_diff_seconds_for_bucket and related logging as it's not used for the bucket value here.
    # last_bot_sent_ts = manychat_last_bot_sent_timestamps.get(subscriber_id) # Keep if needed for other logic/logging

    # if last_bot_sent_ts is not None:
    #     # batch_start_time_s is the timestamp of the current user's message (earliest in batch that led to this analysis)
    #     time_diff_seconds_for_bucket = batch_start_time_s - last_bot_sent_ts
    #     logger.info(
    #         f"[_analyze_form_check_video] User message at {datetime.fromtimestamp(batch_start_time_s).isoformat()}, last bot message at {datetime.fromtimestamp(last_bot_sent_ts).isoformat()}. Difference for bucket: {time_diff_seconds_for_bucket:.2f}s"
    #     )
    # else:
    #     # Fallback to current reaction time for this analysis if no prior bot message.
    #     time_diff_seconds_for_bucket = time.time() - batch_start_time_s # Bot's actual processing time for this analysis
    #     logger.info(
    #         f"[_analyze_form_check_video] No last bot message timestamp for SID {subscriber_id}. Using current bot reaction time for bucket: {time_diff_seconds_for_bucket:.2f}s"
    #     )

    # response_bucket = get_response_time_bucket(time_diff_seconds_for_bucket) # No longer using this for "action"
    # field_updates["response time"] = response_bucket # Replaced by direct "action"
    # logger.info(
    #     f"[_analyze_form_check_video] Calculated time diff for bucket: {time_diff_seconds_for_bucket:.2f}s, Bucket: {response_bucket} for SID {subscriber_id}")

    if update_manychat_fields(subscriber_id, field_updates):
        manychat_last_bot_sent_timestamps[subscriber_id] = time.time()
