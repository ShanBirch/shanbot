#!/usr/bin/env python3
"""
Fix the auto mode table structure
"""

import sqlite3
import os


def fix_table_structure():
    """Fix the auto mode table structure"""
    db_path = 'app/analytics_data_good.sqlite'

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 Fixing auto mode table structure...")

        # Drop and recreate auto_mode_processing table with correct structure
        cursor.execute("DROP TABLE IF EXISTS auto_mode_processing")
        cursor.execute('''
            CREATE TABLE auto_mode_processing (
                id INTEGER PRIMARY KEY,
                processing_status TEXT,
                details TEXT,
                timestamp TEXT
            )
        ''')
        print("✅ Recreated auto_mode_processing table with correct structure")

        # Drop and recreate auto_mode_activities table with correct structure
        cursor.execute("DROP TABLE IF EXISTS auto_mode_activities")
        cursor.execute('''
            CREATE TABLE auto_mode_activities (
                activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT,
                details TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                timestamp TEXT
            )
        ''')
        print("✅ Recreated auto_mode_activities table with correct structure")

        conn.commit()
        conn.close()

        print("🎉 Auto mode table structure fixed!")

    except Exception as e:
        print(f"❌ Error fixing table structure: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_table_structure()
