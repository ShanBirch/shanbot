#!/usr/bin/env python3
"""
Simplified webhook for Render deployment with PostgreSQL support
"""

import os
import logging
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Request, HTTPException
import google.generativeai as genai
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_webhook")

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MANYCHAT_API_KEY = os.getenv("MANYCHAT_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not all([GEMINI_API_KEY, MANYCHAT_API_KEY, DATABASE_URL]):
    logger.error("Missing required environment variables")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="Shanbot Webhook", version="1.0.0")


def ensure_tables():
    """Create database tables if they don't exist"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                ig_username TEXT UNIQUE,
                subscriber_id TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                client_status TEXT DEFAULT 'Not a Client',
                is_in_ad_flow BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                ig_username TEXT,
                subscriber_id TEXT,
                message_text TEXT,
                sender TEXT,
                timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create pending_reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_reviews (
                id SERIAL PRIMARY KEY,
                user_ig_username TEXT,
                subscriber_id TEXT,
                user_message TEXT,
                ai_response_text TEXT,
                final_response_text TEXT,
                status TEXT DEFAULT 'pending',
                created_timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✅ Database tables created successfully")

    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")


def get_or_create_user(ig_username: str, subscriber_id: str, first_name: str = "", last_name: str = ""):
    """Get or create user in database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Try to find existing user
        cursor.execute(
            "SELECT * FROM users WHERE subscriber_id = %s", (subscriber_id,))
        user = cursor.fetchone()

        if not user:
            # Create new user
            cursor.execute("""
                INSERT INTO users (ig_username, subscriber_id, first_name, last_name)
                VALUES (%s, %s, %s, %s) RETURNING *
            """, (ig_username, subscriber_id, first_name, last_name))
            user = cursor.fetchone()
            conn.commit()
            logger.info(f"Created new user: {ig_username}")

        cursor.close()
        conn.close()
        return dict(user) if user else None

    except Exception as e:
        logger.error(f"Error with user data: {e}")
        return None


def save_message(ig_username: str, subscriber_id: str, message_text: str, sender: str):
    """Save message to database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO messages (ig_username, subscriber_id, message_text, sender, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (ig_username, subscriber_id, message_text, sender, timestamp))

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Saved message from {ig_username}")

    except Exception as e:
        logger.error(f"Error saving message: {e}")


def add_to_review_queue(ig_username: str, subscriber_id: str, user_message: str, ai_response: str):
    """Add response to review queue"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO pending_reviews (user_ig_username, subscriber_id, user_message, ai_response_text, created_timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (ig_username, subscriber_id, user_message, ai_response, timestamp))

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Added to review queue: {ig_username}")

    except Exception as e:
        logger.error(f"Error adding to review queue: {e}")


async def generate_ai_response(message: str, ig_username: str) -> str:
    """Generate AI response using Gemini"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""You are Shannon, a friendly vegan fitness coach. Respond to this message from @{ig_username}:

"{message}"

Keep your response conversational, supportive, and under 150 words. Ask engaging follow-up questions about their fitness journey."""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return "Hey! Thanks for your message. I'm excited to help you on your fitness journey! Could you tell me a bit more about your goals?"


async def send_manychat_response(subscriber_id: str, message: str) -> bool:
    """Send response back via ManyChat"""
    try:
        url = "https://api.manychat.com/fb/sending/sendContent"
        headers = {
            "Authorization": f"Bearer {MANYCHAT_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "subscriber_id": subscriber_id,
            "data": {
                "version": "v2",
                "content": {
                    "messages": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            logger.info(f"✅ Sent response to {subscriber_id}")
            return True
        else:
            logger.error(f"❌ Failed to send response: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error sending ManyChat response: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Simple webhook starting up...")
    ensure_tables()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "simple_webhook"}


@app.post("/webhook/manychat")
async def manychat_webhook(request: Request):
    """Handle ManyChat webhook"""
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body, indent=2)}")

        # Extract data
        ig_username = body.get("ig_username", "unknown")
        subscriber_id = body.get("id")
        first_name = body.get("first_name", "")
        last_name = body.get("last_name", "")
        message_text = body.get("last_input_text", "")

        if not all([subscriber_id, message_text]):
            logger.warning("Missing required fields")
            return {"status": "error", "message": "Missing required fields"}

        logger.info(f"Processing message from {ig_username}: {message_text}")

        # Get or create user
        user = get_or_create_user(
            ig_username, subscriber_id, first_name, last_name)

        # Save incoming message
        save_message(ig_username, subscriber_id, message_text, "user")

        # Generate AI response
        ai_response = await generate_ai_response(message_text, ig_username)
        logger.info(f"Generated response: {ai_response}")

        # Save AI response
        save_message(ig_username, subscriber_id, ai_response, "ai")

        # Add to review queue
        add_to_review_queue(ig_username, subscriber_id,
                            message_text, ai_response)

        # Send response via ManyChat
        await send_manychat_response(subscriber_id, ai_response)

        return {"status": "success", "response": ai_response}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
