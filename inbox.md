# Inbox Management Workflow Instructions

## Overview
This is a text-based alternative to the dashboard's Response & Review section. Instead of loading the dashboard, you can ask me to check your "inbox" (messages waiting for responses) and I'll help you manage them efficiently.

## Commands You Can Use

### 1. Check Inbox Summary
**Command:** "How many messages are in my inbox?"
**What I'll Do:** Query the database for messages that need responses and give you a summary.

**Example Response:**
```
📬 Inbox Summary:
- 5 messages waiting for review
- 3 from leads, 2 from clients
- 2 urgent (asking about meal plans)

Messages:
1. @aussiepotter: "Hey Shannon, can you help me with my meal plan?"
2. @kristyleecoop: *sent progress pics*
3. @shaneminehan: "What's the best time to train this week?"
4. @hannahjanedevlin: "When does the challenge start?"
5. @rebeccadangelo01: "Can you check my form on squats?"
```

### 2. View Specific Message
**Command:** "Show me message #1" or "Show me @aussiepotter's message"
**What I'll Do:** Pull full context from database and generate a response.

**Example Response:**
```
@aussiepotter (Marc Potter)
Status: Paying Client
Message: "Hey Shannon, can you help me with my meal plan? I'm struggling with protein"
Conversation History: [Full chat history from database]
Profile: Vegan, into fitness, started challenge last week

→ My Response: "Hey Marc! Yeah for sure, what's been the biggest struggle with hitting your protein targets?"
→ [APPROVE] [EDIT] [REJECT]
```

### 3. Generate Response
**Command:** "Generate response for @username"
**What I'll Do:** Create a Shannon-style response based on the message and context.

### 4. Approve and Send
**Command:** "Approve and send" or "Send message #1"
**What I'll Do:** Use the Instagram automation to send the approved response.

### 5. Batch Processing
**Command:** "Generate responses for all messages"
**What I'll Do:** Create responses for all pending messages at once.

**Command:** "Send all approved responses"
**What I'll Do:** Send all approved responses via Instagram automation.

## Database Integration

I'll query these tables:
- `messages` table for incoming messages
- `users` table for client info
- `conversations` table for chat history
- Filter by messages that need responses (same as Response & Review section)

## Workflow Examples

### Example 1: Quick Check
You: "How many messages are in my inbox?"
Me: "📬 3 messages waiting for review..."
You: "Show me message #1"
Me: "Here's the context and my suggested response..."
You: "Approve and send"
Me: "✅ Message sent to @username"

### Example 2: Batch Processing
You: "Generate responses for all messages"
Me: "Here are responses for all 5 messages..."
You: "Send all approved responses"
Me: "✅ Sent all 5 messages via Instagram automation"

## Benefits

✅ **Much faster** - No dashboard loading, direct database queries
✅ **Better responses** - Full context from database
✅ **Your control** - See exactly what I'm sending before it goes
✅ **Batch processing** - Handle multiple messages efficiently
✅ **Natural flow** - Just tell me what you need

## Commands Summary

- "How many messages are in my inbox?"
- "Show me message #[number]"
- "Show me @username's message"
- "Generate response for @username"
- "Generate responses for all messages"
- "Approve and send"
- "Send message #[number]"
- "Send all approved responses"

## Notes

- This replaces the dashboard's Response & Review section
- I have access to the same database data as the dashboard
- Responses follow Shannon's tone and style from prompts.py
- Instagram automation handles the actual sending
- You maintain full control over what gets sent 