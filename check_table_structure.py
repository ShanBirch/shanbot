#!/usr/bin/env python3
"""
Check the structure of auto mode tables
"""

import sqlite3
import os


def check_table_structure():
    """Check the structure of auto mode tables"""
    db_path = 'app/analytics_data_good.sqlite'

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check auto_mode_activities table
        print("🔍 Checking auto_mode_activities table:")
        try:
            cursor.execute("PRAGMA table_info(auto_mode_activities)")
            columns = cursor.fetchall()
            if columns:
                print("✅ Table exists with columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("❌ Table doesn't exist")
        except Exception as e:
            print(f"❌ Error checking auto_mode_activities: {e}")

        # Check auto_mode_processing table
        print("\n🔍 Checking auto_mode_processing table:")
        try:
            cursor.execute("PRAGMA table_info(auto_mode_processing)")
            columns = cursor.fetchall()
            if columns:
                print("✅ Table exists with columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("❌ Table doesn't exist")
        except Exception as e:
            print(f"❌ Error checking auto_mode_processing: {e}")

        # Check auto_mode_activity table (alternative name)
        print("\n🔍 Checking auto_mode_activity table:")
        try:
            cursor.execute("PRAGMA table_info(auto_mode_activity)")
            columns = cursor.fetchall()
            if columns:
                print("✅ Table exists with columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("❌ Table doesn't exist")
        except Exception as e:
            print(f"❌ Error checking auto_mode_activity: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ Error checking table structure: {e}")


if __name__ == "__main__":
    check_table_structure()
