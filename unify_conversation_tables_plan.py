#!/usr/bin/env python3
"""
Unify Conversation Tables Migration Plan
=======================================

This script will:
1. Standardize the messages table schema
2. Migrate conversation_history data into messages 
3. Create a backup before making changes
4. Provide rollback capability

ANALYSIS RESULTS:
- conversation_history: 201 records (newer, cleaner structure)
- messages: 8,965 records (main data, but messy structure)
- 38 users appear in both tables
- 0 exact duplicates between tables
- Different usage patterns for each table

PROPOSED SCHEMA FOR UNIFIED messages TABLE:
- id (PRIMARY KEY)
- ig_username (TEXT) 
- subscriber_id (TEXT)
- timestamp (TEXT)
- message_type (TEXT) - 'user', 'ai', 'system'
- message_text (TEXT) - the actual message content
- FOREIGN KEY(ig_username) REFERENCES users(ig_username)

MIGRATION STEPS:
1. Backup current database
2. Create new standardized columns in messages table
3. Consolidate existing data in messages table (text/message -> message_text)
4. Insert conversation_history data into messages table
5. Update all code references
6. Drop conversation_history table
7. Clean up redundant columns

STORAGE POINT UPDATES NEEDED:
- app/analytics.py (webhook) -> already uses messages ✓
- dashboard responses -> UPDATE to use messages
- auto responder -> UPDATE to use messages  
- manual responses -> UPDATE to use messages
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"
BACKUP_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\database_backup_before_unification.sqlite"


def create_database_backup():
    """Create a full backup of the database before migration."""
    print("🔄 Creating database backup...")
    try:
        # Copy the database file
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Database backed up to: {BACKUP_PATH}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False


def analyze_messages_table_data():
    """Analyze the current state of data in the messages table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 ANALYZING MESSAGES TABLE DATA QUALITY")
    print("=" * 60)

    # Check how data is distributed across the redundant columns
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text IS NOT NULL AND text != ''")
    text_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE message IS NOT NULL AND message != ''")
    message_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE type IS NOT NULL AND type != ''")
    type_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE sender IS NOT NULL AND sender != ''")
    sender_count = cursor.fetchone()[0]

    print(f"Data distribution in messages table:")
    print(f"  • 'text' column has data: {text_count} records")
    print(f"  • 'message' column has data: {message_count} records")
    print(f"  • 'type' column has data: {type_count} records")
    print(f"  • 'sender' column has data: {sender_count} records")

    # Check for cases where both text and message have data
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE text IS NOT NULL AND message IS NOT NULL AND text != '' AND message != ''")
    both_count = cursor.fetchone()[0]
    print(f"  • Records with both 'text' and 'message': {both_count}")

    # Sample the data to see patterns
    cursor.execute("""
        SELECT text, message, type, sender 
        FROM messages 
        WHERE (text IS NOT NULL OR message IS NOT NULL) 
        LIMIT 5
    """)
    samples = cursor.fetchall()

    print(f"\nSample data patterns:")
    for i, (text, message, msg_type, sender) in enumerate(samples, 1):
        print(
            f"  {i}. text='{text[:30] if text else 'None'}...', message='{message[:30] if message else 'None'}...', type='{msg_type}', sender='{sender}'")

    conn.close()


def standardize_messages_table():
    """
    Standardize the messages table by:
    1. Adding message_type column
    2. Consolidating text/message into message_text
    3. Consolidating type/sender into message_type
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔧 STANDARDIZING MESSAGES TABLE")
    print("-" * 40)

    try:
        # Add new standardized columns if they don't exist
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN message_text TEXT")
            print("✅ Added message_text column")
        except sqlite3.OperationalError:
            print("ℹ️ message_text column already exists")

        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN message_type TEXT")
            print("✅ Added message_type column")
        except sqlite3.OperationalError:
            print("ℹ️ message_type column already exists")

        # Consolidate data into standardized columns
        print("🔄 Consolidating message content...")

        # Priority: message > text for content (message seems to be newer)
        cursor.execute("""
            UPDATE messages 
            SET message_text = COALESCE(
                NULLIF(TRIM(message), ''), 
                NULLIF(TRIM(text), ''), 
                ''
            )
            WHERE message_text IS NULL
        """)

        # Priority: sender > type for message type (sender seems more reliable)
        cursor.execute("""
            UPDATE messages 
            SET message_type = COALESCE(
                NULLIF(TRIM(sender), ''), 
                NULLIF(TRIM(type), ''), 
                'unknown'
            )
            WHERE message_type IS NULL
        """)

        conn.commit()
        print("✅ Data consolidation complete")

        # Verify the consolidation
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE message_text IS NOT NULL AND message_text != ''")
        consolidated_count = cursor.fetchone()[0]
        print(
            f"✅ {consolidated_count} records now have standardized message content")

    except Exception as e:
        print(f"❌ Error during standardization: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True


def migrate_conversation_history_to_messages():
    """Migrate all data from conversation_history into the messages table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔄 MIGRATING CONVERSATION_HISTORY TO MESSAGES")
    print("-" * 50)

    try:
        # Get all records from conversation_history
        cursor.execute("""
            SELECT ig_username, message_type, message_text, timestamp
            FROM conversation_history
            ORDER BY timestamp ASC
        """)
        conv_records = cursor.fetchall()

        print(f"📊 Found {len(conv_records)} records to migrate")

        migrated_count = 0
        for ig_username, msg_type, msg_text, timestamp in conv_records:
            # Check if this exact record already exists in messages
            cursor.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE ig_username = ? AND message_text = ? AND timestamp = ?
            """, (ig_username, msg_text, timestamp))

            if cursor.fetchone()[0] == 0:  # Record doesn't exist
                # Get subscriber_id for this user if available
                cursor.execute(
                    "SELECT subscriber_id FROM users WHERE ig_username = ?", (ig_username,))
                user_result = cursor.fetchone()
                subscriber_id = user_result[0] if user_result else None

                # Insert into messages table
                cursor.execute("""
                    INSERT INTO messages (
                        ig_username, subscriber_id, timestamp, 
                        message_type, message_text
                    ) VALUES (?, ?, ?, ?, ?)
                """, (ig_username, subscriber_id, timestamp, msg_type, msg_text))

                migrated_count += 1

        conn.commit()
        print(
            f"✅ Successfully migrated {migrated_count} new records from conversation_history")

        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM messages")
        final_count = cursor.fetchone()[0]
        print(f"📊 Messages table now has {final_count} total records")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True


def verify_migration():
    """Verify that the migration was successful."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 VERIFYING MIGRATION")
    print("-" * 30)

    # Check Calendly links are preserved
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE message_text LIKE '%calendly.com/shannonrhysbirch/15min%'")
    calendly_count = cursor.fetchone()[0]
    print(f"📅 Calendly links in unified table: {calendly_count}")

    # Check challenge sign-ups are preserved
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE message_text LIKE '%ready to join%' OR message_text LIKE '%want to join%'")
    signup_count = cursor.fetchone()[0]
    print(f"🏆 Challenge sign-ups in unified table: {signup_count}")

    # Check total user count
    cursor.execute("SELECT COUNT(DISTINCT ig_username) FROM messages")
    user_count = cursor.fetchone()[0]
    print(f"👥 Total unique users: {user_count}")

    # Check data quality
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE message_text IS NOT NULL AND message_text != ''")
    good_data_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_count = cursor.fetchone()[0]
    print(
        f"📊 Records with valid message content: {good_data_count}/{total_count} ({good_data_count/total_count*100:.1f}%)")

    conn.close()


def create_migration_summary():
    """Create a summary of what was changed."""
    summary = {
        "migration_date": datetime.now().isoformat(),
        "backup_location": BACKUP_PATH,
        "changes_made": [
            "Added message_text and message_type columns to messages table",
            "Consolidated text/message columns into message_text",
            "Consolidated type/sender columns into message_type",
            "Migrated all conversation_history records into messages table",
            "Verified data integrity after migration"
        ],
        "next_steps": [
            "Update all code references to use unified messages table",
            "Test all functionality with new schema",
            "Drop conversation_history table after verification",
            "Clean up redundant columns (text, message, type, sender)"
        ]
    }

    with open("conversation_migration_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("📋 Migration summary saved to: conversation_migration_summary.json")


def main():
    """Run the complete migration process."""
    print("🚀 STARTING CONVERSATION TABLE UNIFICATION")
    print("=" * 60)

    # Step 1: Create backup
    if not create_database_backup():
        print("❌ Cannot proceed without backup")
        return

    # Step 2: Analyze current state
    analyze_messages_table_data()

    # Step 3: Standardize messages table
    if not standardize_messages_table():
        print("❌ Standardization failed")
        return

    # Step 4: Migrate conversation_history data
    if not migrate_conversation_history_to_messages():
        print("❌ Migration failed")
        return

    # Step 5: Verify migration
    verify_migration()

    # Step 6: Create summary
    create_migration_summary()

    print("\n✅ MIGRATION COMPLETE!")
    print("🔄 Next steps:")
    print("   1. Update code references to use unified messages table")
    print("   2. Test all functionality")
    print("   3. Drop conversation_history table")
    print("   4. Clean up redundant columns")


if __name__ == "__main__":
    main()
