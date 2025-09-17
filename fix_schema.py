#!/usr/bin/env python3
"""
Schema Fix Script
=================
Fixes column mismatches between SQLite and PostgreSQL schemas.
"""

import psycopg2
import os

POSTGRES_URL = os.getenv('DATABASE_URL')


def check_and_fix_schema():
    """Check and fix schema issues."""
    print("🔧 Checking and fixing PostgreSQL schema...")

    if not POSTGRES_URL:
        print("❌ DATABASE_URL not set")
        return

    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()

    try:
        # Check pending_reviews table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pending_reviews'
        """)
        pending_reviews_cols = [row[0] for row in cursor.fetchall()]
        print(f"📋 pending_reviews columns: {pending_reviews_cols}")

        # Add missing columns to pending_reviews if needed
        required_columns = {
            'user_subscriber_id': 'TEXT',
            'category': 'TEXT DEFAULT \'general_chat\'',
            'is_approved': 'BOOLEAN DEFAULT FALSE',
            'ai_response_text': 'TEXT'
        }

        for col_name, col_def in required_columns.items():
            if col_name not in pending_reviews_cols:
                print(f"🔧 Adding missing column: {col_name}")
                cursor.execute(
                    f'ALTER TABLE pending_reviews ADD COLUMN {col_name} {col_def}')
                conn.commit()

        # Check processing_queue table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'processing_queue'
        """)
        processing_queue_exists = cursor.fetchone()

        if processing_queue_exists:
            print("✅ processing_queue table exists")
        else:
            print("❌ processing_queue table missing - this should have been migrated")

        # Check users table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        users_cols = [row[0] for row in cursor.fetchall()]
        print(f"📋 users columns: {users_cols}")

        # Add missing columns to users if needed
        user_required_columns = {
            'metrics_json': 'TEXT',
            'calorie_tracking_json': 'TEXT',
            'is_in_calorie_flow': 'INTEGER DEFAULT 0',
            'bio': 'TEXT',
            'bio_context': 'TEXT',
            'client_interests': 'TEXT'
        }

        for col_name, col_def in user_required_columns.items():
            if col_name not in users_cols:
                print(f"🔧 Adding missing column to users: {col_name}")
                cursor.execute(
                    f'ALTER TABLE users ADD COLUMN {col_name} {col_def}')
                conn.commit()

        # Check messages table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'messages'
        """)
        messages_cols = [row[0] for row in cursor.fetchall()]
        print(f"📋 messages columns: {messages_cols}")

        # Add missing columns to messages if needed
        if 'type' not in messages_cols and 'message_type' in messages_cols:
            print("🔧 Adding 'type' column to messages (alias for message_type)")
            cursor.execute('ALTER TABLE messages ADD COLUMN type TEXT')
            cursor.execute('UPDATE messages SET type = message_type')
            conn.commit()

        print("✅ Schema fixes completed!")

    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def test_schema():
    """Test the fixed schema with sample queries."""
    print("🧪 Testing schema fixes...")

    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()

    try:
        # Test pending_reviews
        cursor.execute("SELECT COUNT(*) FROM pending_reviews")
        pending_count = cursor.fetchone()[0]
        print(f"✅ pending_reviews: {pending_count} records")

        # Test processing_queue
        cursor.execute("SELECT COUNT(*) FROM processing_queue")
        processing_count = cursor.fetchone()[0]
        print(f"✅ processing_queue: {processing_count} records")

        # Test users
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        print(f"✅ users: {users_count} records")

        # Test messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        messages_count = cursor.fetchone()[0]
        print(f"✅ messages: {messages_count} records")

        print("🎉 All schema tests passed!")

    except Exception as e:
        print(f"❌ Schema test failed: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """Main function."""
    print("🗄️ PostgreSQL Schema Fix Tool")
    print("=" * 40)

    check_and_fix_schema()
    print()
    test_schema()


if __name__ == "__main__":
    main()

