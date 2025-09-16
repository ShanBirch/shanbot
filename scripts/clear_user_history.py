import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def resolve_db_path() -> Path:
    """Return absolute path to the project's SQLite database."""
    repo_root = Path(__file__).resolve().parents[1]
    db_path = repo_root / "app" / "analytics_data_good.sqlite"
    return db_path


def backup_database(db_path: Path) -> Path:
    """Create a timestamped backup of the database and return the backup path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_suffix(db_path.suffix + f".bak_{timestamp}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def get_all_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cur.fetchall()]


def get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cur.fetchall()]
    except sqlite3.Error:
        return []


def delete_user_from_table(
    conn: sqlite3.Connection, table: str, username: str
) -> Tuple[int, Optional[str]]:
    """Delete rows for username from table if it has an IG username column.

    Returns (deleted_count, column_used or None).
    """
    columns = get_table_columns(conn, table)
    candidate_cols = [c for c in ("ig_username", "username") if c in columns]
    if not candidate_cols:
        return 0, None

    column = candidate_cols[0]
    cur = conn.cursor()
    cur.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (username,))
    count = cur.fetchone()[0] or 0
    if count:
        cur.execute(f"DELETE FROM {table} WHERE {column} = ?", (username,))
    return count, column


def clear_user_history(username: str, make_backup: bool = True) -> Dict[str, int]:
    db_path = resolve_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    if make_backup:
        backup_path = backup_database(db_path)
        print(f"✅ Backup created: {backup_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        tables = get_all_tables(conn)
        deleted_by_table: Dict[str, int] = {}

        # Prefer likely tables first for clearer output ordering
        likely_tables = [
            "messages",
            "conversation_history",
            "response_review_queue",
            "scheduled_responses",
            "pending_responses",
            "response_log",
        ]
        seen = set()
        ordered_tables = [t for t in likely_tables if t in tables]
        ordered_tables += [t for t in tables if t not in set(ordered_tables)]

        for table in ordered_tables:
            if table in seen:
                continue
            seen.add(table)
            try:
                deleted, col = delete_user_from_table(conn, table, username)
                if deleted:
                    deleted_by_table[table] = deleted
            except sqlite3.Error as e:
                print(f"⚠️  Skipped table {table} due to error: {e}")

        conn.commit()
        return deleted_by_table
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Clear conversation history for a user.")
    parser.add_argument(
        "username", help="Instagram username, e.g., cocos_pt_studio")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup before deletion",
    )
    args = parser.parse_args()

    deleted_map = clear_user_history(
        args.username, make_backup=not args.no_backup)
    total_deleted = sum(deleted_map.values())

    if deleted_map:
        print("🧹 Deleted rows by table:")
        for table, count in deleted_map.items():
            print(f"  - {table}: {count}")
    else:
        print("No rows found to delete for the specified user.")

    print(f"✅ Done. Total rows deleted: {total_deleted}")


if __name__ == "__main__":
    main()
