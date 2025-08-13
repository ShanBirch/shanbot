#!/usr/bin/env python3
"""
Cleanup script to remove the old conversation_history table and redundant columns.
Run this ONLY after verifying everything works correctly.
"""

import sqlite3

DB_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

def cleanup_old_structures():
    """Clean up old conversation_history table and redundant columns."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🧹 CLEANING UP OLD CONVERSATION STRUCTURES")
    print("=" * 60)
    
    # Drop conversation_history table
    try:
        cursor.execute("DROP TABLE IF EXISTS conversation_history")
        print("✅ Dropped conversation_history table")
    except Exception as e:
        print(f"❌ Error dropping conversation_history: {e}")
    
    # Note: We're keeping the old columns (text, message, type, sender) for now
    # in case any code still references them. They can be dropped later after
    # more thorough testing.
    
    conn.commit()
    conn.close()
    
    print("🎉 Cleanup complete!")
    print("📝 Old columns (text, message, type, sender) are kept for compatibility")
    print("   They can be dropped later after thorough testing")

if __name__ == "__main__":
    cleanup_old_structures()
