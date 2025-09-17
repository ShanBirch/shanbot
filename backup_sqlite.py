#!/usr/bin/env python3
"""
SQLite Backup Script
===================
Creates a backup of your SQLite database before migration.
"""

import sqlite3
import shutil
import os
from datetime import datetime

SQLITE_DB_PATH = r"app\analytics_data_good.sqlite"


def create_backup():
    """Create a timestamped backup of the SQLite database."""
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ SQLite database not found: {SQLITE_DB_PATH}")
        return False

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"app/analytics_data_good_backup_{timestamp}.sqlite"

    try:
        # Copy the database file
        shutil.copy2(SQLITE_DB_PATH, backup_path)

        # Verify the backup
        if os.path.exists(backup_path):
            original_size = os.path.getsize(SQLITE_DB_PATH)
            backup_size = os.path.getsize(backup_path)

            print(f"✅ Backup created successfully!")
            print(f"📂 Original: {SQLITE_DB_PATH} ({original_size:,} bytes)")
            print(f"📂 Backup:   {backup_path} ({backup_size:,} bytes)")

            if original_size == backup_size:
                print("✅ Backup size matches original")
                return True
            else:
                print("⚠️ Backup size differs from original")
                return False
        else:
            print("❌ Backup file was not created")
            return False

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def main():
    """Main backup function."""
    print("💾 SQLite Database Backup")
    print("=" * 30)

    success = create_backup()

    if success:
        print("\n🎉 Backup completed successfully!")
        print("Your original database is now safely backed up.")
        print("You can proceed with the migration.")
    else:
        print("\n❌ Backup failed!")
        print("Please resolve the issue before proceeding with migration.")


if __name__ == "__main__":
    main()

