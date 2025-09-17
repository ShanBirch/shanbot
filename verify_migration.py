#!/usr/bin/env python3
"""
Migration Verification Script
============================
Verifies that your SQLite data was successfully migrated to PostgreSQL.
"""

import sqlite3
import psycopg2
import os
import json
from typing import Dict, List

SQLITE_DB_PATH = r"app\analytics_data_good.sqlite"
POSTGRES_URL = os.getenv('DATABASE_URL')


def compare_databases():
    """Compare record counts between SQLite and PostgreSQL."""
    print("🔍 Comparing SQLite and PostgreSQL databases...")
    print("=" * 60)

    if not POSTGRES_URL:
        print("❌ DATABASE_URL environment variable not set")
        return

    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite database not found: {SQLITE_DB_PATH}")
        return

    # Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    postgres_conn = psycopg2.connect(POSTGRES_URL)

    # Get tables from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    total_differences = 0

    for table in tables:
        try:
            # Count SQLite records
            sqlite_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            sqlite_count = sqlite_cursor.fetchone()[0]

            # Count PostgreSQL records
            postgres_cursor = postgres_conn.cursor()
            postgres_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            postgres_count = postgres_cursor.fetchone()[0]
            postgres_cursor.close()

            # Compare counts
            if sqlite_count == postgres_count:
                status = "✅"
                print(
                    f"{status} {table:<30} SQLite: {sqlite_count:>6} | PostgreSQL: {postgres_count:>6}")
            else:
                status = "⚠️"
                difference = abs(sqlite_count - postgres_count)
                total_differences += difference
                print(
                    f"{status} {table:<30} SQLite: {sqlite_count:>6} | PostgreSQL: {postgres_count:>6} (diff: {difference})")

        except Exception as e:
            print(f"❌ {table:<30} Error: {str(e)[:40]}...")

    print("=" * 60)
    if total_differences == 0:
        print("🎉 Perfect match! All data migrated successfully.")
    else:
        print(f"⚠️ Found {total_differences} total record differences.")
        print("   This might be normal if you've added new data since migration.")

    sqlite_conn.close()
    postgres_conn.close()


def test_postgresql_connection():
    """Test basic PostgreSQL connectivity and permissions."""
    print("🔗 Testing PostgreSQL connection...")

    if not POSTGRES_URL:
        print("❌ DATABASE_URL environment variable not set")
        return False

    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL: {version[:50]}...")

        # Test table access
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        print(
            f"✅ Found {len(tables)} tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")

        # Test sample data
        if 'users' in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"✅ Users table: {user_count} records")

        if 'messages' in tables:
            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            print(f"✅ Messages table: {message_count} records")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def sample_data_check():
    """Check a sample of migrated data for integrity."""
    print("\n📊 Checking sample data integrity...")

    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()

        # Check recent users
        cursor.execute(
            "SELECT ig_username, first_name, last_name FROM users LIMIT 5")
        users = cursor.fetchall()
        print(f"✅ Sample users ({len(users)}):")
        for user in users:
            print(f"   • {user[0]} ({user[1]} {user[2]})")

        # Check recent messages
        cursor.execute(
            "SELECT ig_username, message_type, LEFT(message_text, 30) FROM messages ORDER BY timestamp DESC LIMIT 3")
        messages = cursor.fetchall()
        print(f"✅ Recent messages ({len(messages)}):")
        for msg in messages:
            print(f"   • {msg[0]} ({msg[1]}): {msg[2]}...")

        # Check JSON data integrity
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE client_analysis_json IS NOT NULL")
        json_count = cursor.fetchone()[0]
        print(f"✅ Users with JSON data: {json_count}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Sample data check failed: {e}")


def main():
    """Main verification function."""
    print("🔍 PostgreSQL Migration Verification")
    print("=" * 50)

    # Test connection first
    if test_postgresql_connection():
        print()
        # Compare databases
        compare_databases()

        # Check sample data
        sample_data_check()

        print("\n🎯 Migration verification complete!")
        print("If everything looks good, your data is ready for production.")
    else:
        print("\n❌ Cannot verify migration due to connection issues.")
        print("Check your DATABASE_URL and try again.")


if __name__ == "__main__":
    main()

