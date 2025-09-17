#!/usr/bin/env python3
"""
Fix Missing Data
================
Specifically migrate the critical tables that failed during initial migration.
"""

import sqlite3
import psycopg2
import os
import json

SQLITE_DB_PATH = r"app\analytics_data_good.sqlite"
POSTGRES_URL = os.getenv('DATABASE_URL')


def migrate_critical_data():
    """Migrate critical tables that didn't transfer completely."""
    print("🔄 Migrating critical missing data...")

    # Tables to migrate with their critical status
    critical_tables = [
        'users',
        'messages',
        'pending_reviews',
        'processed_profiles'
    ]

    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    postgres_conn = psycopg2.connect(POSTGRES_URL)

    for table_name in critical_tables:
        print(f"\n📋 Migrating {table_name}...")

        try:
            # Get SQLite data
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
            sqlite_data = [dict(row) for row in sqlite_cursor.fetchall()]

            if not sqlite_data:
                print(f"   ⚠️ No data in {table_name}")
                continue

            print(f"   📊 Found {len(sqlite_data)} records in SQLite")

            # Check PostgreSQL current count
            postgres_cursor = postgres_conn.cursor()
            postgres_cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            pg_count = postgres_cursor.fetchone()[0]
            print(f"   📊 Current PostgreSQL count: {pg_count}")

            if pg_count >= len(sqlite_data):
                print(f"   ✅ {table_name} already has sufficient data")
                continue

            # Clear and reinsert for problem tables
            if table_name in ['users', 'messages', 'pending_reviews']:
                print(f"   🗑️ Clearing {table_name} for fresh insert...")
                postgres_cursor.execute(f'DELETE FROM "{table_name}"')
                postgres_conn.commit()

            # Prepare insert based on table
            if table_name == 'users':
                insert_users_data(postgres_cursor, sqlite_data, postgres_conn)
            elif table_name == 'messages':
                insert_messages_data(
                    postgres_cursor, sqlite_data, postgres_conn)
            elif table_name == 'pending_reviews':
                insert_pending_reviews_data(
                    postgres_cursor, sqlite_data, postgres_conn)
            elif table_name == 'processed_profiles':
                insert_processed_profiles_data(
                    postgres_cursor, sqlite_data, postgres_conn)

            postgres_cursor.close()

        except Exception as e:
            print(f"   ❌ Error migrating {table_name}: {e}")
            postgres_conn.rollback()

    sqlite_conn.close()
    postgres_conn.close()


def insert_users_data(cursor, data, conn):
    """Insert users data with proper column mapping."""
    print("   🔄 Inserting users data...")

    for i, row in enumerate(data):
        try:
            cursor.execute("""
                INSERT INTO users (
                    ig_username, subscriber_id, first_name, last_name, 
                    client_status, journey_stage, is_onboarding,
                    is_in_checkin_flow_mon, is_in_checkin_flow_wed,
                    is_in_ad_flow, ad_script_state, ad_scenario, lead_source,
                    fb_ad, last_interaction_timestamp, client_analysis_json,
                    offer_made, metrics_json, calorie_tracking_json,
                    is_in_calorie_flow, bio, bio_context, client_interests
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (subscriber_id) DO UPDATE SET
                    ig_username = EXCLUDED.ig_username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    client_status = EXCLUDED.client_status,
                    last_interaction_timestamp = EXCLUDED.last_interaction_timestamp
            """, (
                row.get('ig_username'),
                row.get('subscriber_id'),
                row.get('first_name'),
                row.get('last_name'),
                row.get('client_status', 'Not a Client'),
                row.get('journey_stage', 'Initial Inquiry'),
                row.get('is_onboarding', False),
                row.get('is_in_checkin_flow_mon', False),
                row.get('is_in_checkin_flow_wed', False),
                row.get('is_in_ad_flow', False),
                row.get('ad_script_state'),
                row.get('ad_scenario'),
                row.get('lead_source'),
                row.get('fb_ad', False),
                row.get('last_interaction_timestamp'),
                row.get('client_analysis_json'),
                row.get('offer_made', False),
                row.get('metrics_json'),
                row.get('calorie_tracking_json'),
                row.get('is_in_calorie_flow', 0),
                row.get('bio'),
                row.get('bio_context'),
                row.get('client_interests')
            ))

            if (i + 1) % 100 == 0:
                print(f"   📊 Inserted {i + 1} users...")
                conn.commit()

        except Exception as e:
            print(
                f"   ⚠️ Error inserting user {row.get('ig_username', 'unknown')}: {e}")

    conn.commit()
    print(f"   ✅ Completed users insert: {len(data)} records")


def insert_messages_data(cursor, data, conn):
    """Insert messages data with proper column mapping."""
    print("   🔄 Inserting messages data...")

    for i, row in enumerate(data):
        try:
            cursor.execute("""
                INSERT INTO messages (
                    ig_username, subscriber_id, message_type, type,
                    message_text, timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row.get('ig_username'),
                row.get('subscriber_id'),
                row.get('message_type'),
                row.get('message_type'),  # Copy to 'type' column
                row.get('message_text'),
                row.get('timestamp')
            ))

            if (i + 1) % 1000 == 0:
                print(f"   📊 Inserted {i + 1} messages...")
                conn.commit()

        except Exception as e:
            print(f"   ⚠️ Error inserting message {i}: {e}")

    conn.commit()
    print(f"   ✅ Completed messages insert: {len(data)} records")


def insert_pending_reviews_data(cursor, data, conn):
    """Insert pending_reviews data with proper column mapping."""
    print("   🔄 Inserting pending_reviews data...")

    for i, row in enumerate(data):
        try:
            cursor.execute("""
                INSERT INTO pending_reviews (
                    user_ig_username, user_subscriber_id, subscriber_id,
                    user_message, ai_response_text, final_response_text,
                    status, created_timestamp, prompt_type, category, is_approved
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row.get('user_ig_username'),
                row.get('user_subscriber_id'),
                row.get('subscriber_id'),
                row.get('user_message'),
                row.get('ai_response_text'),
                row.get('final_response_text'),
                row.get('status', 'pending_review'),
                row.get('created_timestamp'),
                row.get('prompt_type', 'general_chat'),
                row.get('category', 'general_chat'),
                row.get('is_approved', False)
            ))

        except Exception as e:
            print(f"   ⚠️ Error inserting pending review {i}: {e}")

    conn.commit()
    print(f"   ✅ Completed pending_reviews insert: {len(data)} records")


def insert_processed_profiles_data(cursor, data, conn):
    """Insert processed_profiles data with boolean conversion."""
    print("   🔄 Inserting processed_profiles data...")

    for i, row in enumerate(data):
        try:
            # Convert integer to boolean for was_lead field
            was_lead = bool(row.get('was_lead', 0))

            cursor.execute("""
                INSERT INTO processed_profiles (
                    ig_username, full_name, bio, followers_count, following_count,
                    is_private, is_verified, processed_at, source, was_lead, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row.get('ig_username'),
                row.get('full_name'),
                row.get('bio'),
                row.get('followers_count'),
                row.get('following_count'),
                row.get('is_private', False),
                row.get('is_verified', False),
                row.get('processed_at'),
                row.get('source'),
                was_lead,
                row.get('notes')
            ))

            if (i + 1) % 1000 == 0:
                print(f"   📊 Inserted {i + 1} processed profiles...")
                conn.commit()

        except Exception as e:
            print(f"   ⚠️ Error inserting processed profile {i}: {e}")

    conn.commit()
    print(f"   ✅ Completed processed_profiles insert: {len(data)} records")


def main():
    """Main function."""
    print("🔧 Critical Data Migration Fix")
    print("=" * 40)

    if not POSTGRES_URL:
        print("❌ DATABASE_URL not set")
        return

    migrate_critical_data()
    print("\n🎉 Critical data migration completed!")


if __name__ == "__main__":
    main()

