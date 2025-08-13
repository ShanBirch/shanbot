#!/usr/bin/env python3
"""
Reset Instagram Analysis Utility
Allows you to reset the Instagram analysis status for specific users or all users,
forcing them to be re-analyzed by the auto analyzer.
"""

import os
import sys
import json
import sqlite3
import argparse
from typing import List, Optional

# Add the project root to sys.path for imports
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database utilities
try:
    from app.dashboard_modules.dashboard_sqlite_utils import get_db_connection
    # Import the specific function directly to avoid conflicts
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "analyzer", "anaylize_followers.py")
    analyzer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer_module)
    has_complete_instagram_analysis_sqlite = analyzer_module.has_complete_instagram_analysis_sqlite
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"


def get_all_users_with_analysis():
    """Get all users that currently have Instagram analysis"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ig_username, metrics_json
            FROM users 
            WHERE ig_username IS NOT NULL 
            AND ig_username != '' 
            AND ig_username NOT LIKE 'user_%'
            AND metrics_json IS NOT NULL
            ORDER BY ig_username
        """)

        users_with_analysis = []
        for row in cursor.fetchall():
            ig_username = row[0]
            if has_complete_instagram_analysis_sqlite(ig_username):
                users_with_analysis.append(ig_username)

        conn.close()
        return users_with_analysis

    except Exception as e:
        print(f"Error getting users with analysis: {e}")
        return []


def reset_user_analysis(ig_username: str, remove_completely: bool = False) -> bool:
    """Reset Instagram analysis for a specific user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current metrics
        cursor.execute(
            "SELECT metrics_json FROM users WHERE ig_username = ?",
            (ig_username,)
        )
        result = cursor.fetchone()

        if not result or not result[0]:
            print(f"No metrics found for user {ig_username}")
            conn.close()
            return False

        # Parse current metrics
        try:
            metrics_data = json.loads(result[0])
        except (json.JSONDecodeError, TypeError):
            print(f"Invalid metrics JSON for user {ig_username}")
            conn.close()
            return False

        if remove_completely:
            # Remove all Instagram analysis data
            metrics_data.pop('client_analysis', None)
            metrics_data.pop('analysis_source', None)
            print(f"Completely removed Instagram analysis for {ig_username}")
        else:
            # Just mark as incomplete by removing key fields
            client_analysis = metrics_data.get('client_analysis', {})
            if client_analysis:
                # Remove key fields to make it incomplete
                client_analysis.pop('posts_analyzed', None)
                client_analysis.pop('interests', None)
                client_analysis.pop('conversation_topics', None)
                metrics_data['client_analysis'] = client_analysis
            print(f"Marked Instagram analysis as incomplete for {ig_username}")

        # Update the database
        cursor.execute(
            "UPDATE users SET metrics_json = ? WHERE ig_username = ?",
            (json.dumps(metrics_data), ig_username)
        )
        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"Error resetting analysis for {ig_username}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Reset Instagram analysis status')
    parser.add_argument('--user', type=str, help='Specific username to reset')
    parser.add_argument('--all', action='store_true', help='Reset all users')
    parser.add_argument('--list', action='store_true',
                        help='List users with complete analysis')
    parser.add_argument('--remove-completely', action='store_true',
                        help='Completely remove analysis data instead of just marking incomplete')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without actually doing it')

    args = parser.parse_args()

    if args.list:
        print("Users with complete Instagram analysis:")
        users = get_all_users_with_analysis()
        for i, username in enumerate(users, 1):
            print(f"{i:3d}. {username}")
        print(f"\nTotal: {len(users)} users")
        return

    if args.user:
        if args.dry_run:
            print(
                f"DRY RUN: Would reset Instagram analysis for user: {args.user}")
            if has_complete_instagram_analysis_sqlite(args.user):
                print(f"✅ User {args.user} currently has complete analysis")
            else:
                print(f"❌ User {args.user} does not have complete analysis")
        else:
            print(f"Resetting Instagram analysis for user: {args.user}")
            if reset_user_analysis(args.user, args.remove_completely):
                print(f"✅ Successfully reset analysis for {args.user}")
            else:
                print(f"❌ Failed to reset analysis for {args.user}")

    elif args.all:
        users = get_all_users_with_analysis()
        print(f"Found {len(users)} users with complete Instagram analysis")

        if args.dry_run:
            print("DRY RUN: Would reset Instagram analysis for all users:")
            for username in users:
                print(f"  - {username}")
        else:
            confirm = input(
                f"Are you sure you want to reset Instagram analysis for {len(users)} users? (yes/no): ")
            if confirm.lower() == 'yes':
                success_count = 0
                for username in users:
                    if reset_user_analysis(username, args.remove_completely):
                        success_count += 1
                        print(f"✅ Reset {username}")
                    else:
                        print(f"❌ Failed to reset {username}")

                print(
                    f"\nCompleted: {success_count}/{len(users)} users reset successfully")
            else:
                print("Operation cancelled")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
