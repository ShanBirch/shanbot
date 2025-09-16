#!/usr/bin/env python3
"""
Database initialization script for Render deployment.
Creates required tables in PostgreSQL database.
"""

import os
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all required database tables."""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
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
                journey_stage TEXT DEFAULT 'Initial Inquiry',
                is_onboarding BOOLEAN DEFAULT FALSE,
                is_in_checkin_flow_mon BOOLEAN DEFAULT FALSE,
                is_in_checkin_flow_wed BOOLEAN DEFAULT FALSE,
                is_in_ad_flow BOOLEAN DEFAULT FALSE,
                last_interaction_timestamp TEXT,
                profile_bio_text TEXT,
                interests_json TEXT DEFAULT '[]',
                conversation_topics_json TEXT DEFAULT '[]',
                client_analysis_json TEXT DEFAULT '{}',
                goals_text TEXT,
                current_fitness_level_text TEXT,
                injuries_limitations_text TEXT,
                preferred_workout_types_text TEXT,
                lifestyle_factors_text TEXT,
                engagement_preferences_text TEXT,
                meal_plan_summary TEXT,
                weekly_workout_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                ig_username TEXT,
                subscriber_id TEXT,
                message_type TEXT,
                message_text TEXT,
                sender TEXT,
                message TEXT,
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
                prompt_type TEXT,
                status TEXT DEFAULT 'pending',
                created_timestamp TEXT,
                reviewed_timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create analytics_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_data (
                id SERIAL PRIMARY KEY,
                subscriber_id TEXT,
                ig_username TEXT,
                message_text TEXT,
                message_direction TEXT,
                timestamp TEXT,
                first_name TEXT,
                last_name TEXT,
                client_status TEXT,
                journey_stage TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Commit changes
        conn.commit()
        logger.info("✅ All database tables created successfully")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False


if __name__ == "__main__":
    success = create_tables()
    if success:
        print("✅ Database initialization completed successfully")
    else:
        print("❌ Database initialization failed")
        exit(1)
