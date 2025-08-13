#!/usr/bin/env python3
"""
Check the structure of the pending_reviews table
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def check_pending_reviews_structure():
    """Check the structure of the pending_reviews table"""

    print("📋 CHECKING PENDING_REVIEWS TABLE STRUCTURE")
    print("=" * 50)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check the structure of pending_reviews table
        cursor.execute("PRAGMA table_info(pending_reviews)")
        columns = cursor.fetchall()

        print("📋 Pending Reviews table structure:")
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")
        print()

        # Get a sample record for @xbraxeletx
        cursor.execute("""
            SELECT * FROM pending_reviews
            WHERE user_ig_username = 'xbraxeletx'
            ORDER BY review_id DESC
            LIMIT 1
        """)

        sample = cursor.fetchone()
        if sample:
            print("📋 Sample record for @xbraxeletx:")
            for i, col in enumerate(columns):
                print(f"  • {col[1]}: {sample[i]}")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_pending_reviews_structure()
