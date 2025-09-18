#!/usr/bin/env python3
"""
Clear Postgres conversation history for a specific IG username.

- Deletes from messages, pending_reviews, review_queue, analytics_data (if they exist)
- Matches by ig_username, and also by subscriber_id if resolvable from users

Usage:
  python scripts/clear_user_history_pg.py --db-url <DATABASE_URL> --username cocos_pt_studio

Notes:
  - Safe to re-run; only affects rows tied to the specified user
  - Does NOT delete the users row
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import psycopg2
from psycopg2.extras import RealDictCursor


def ensure_sslmode_require(db_url: str) -> str:
    """Ensure sslmode=require is present in the connection string.

    Works with URLs with or without existing query params.
    """
    try:
        parsed = urlparse(db_url)
        query = dict(parse_qsl(parsed.query))
        # Preserve existing value if set; otherwise require
        query.setdefault("sslmode", "require")
        new_query = urlencode(query)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        # If parsing fails, fall back to naive append if not present
        return db_url if ("sslmode=" in db_url) else (db_url + ("?" if "?" not in db_url else "&") + "sslmode=require")


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SELECT to_regclass(%s) IS NOT NULL AS exists",
                   (f"public.{table_name}",))
    row = cursor.fetchone()
    return bool(row and row.get("exists"))


def fetch_subscriber_id(cursor, ig_username: str) -> str | None:
    cursor.execute(
        """
        SELECT subscriber_id
        FROM users
        WHERE ig_username = %s
        LIMIT 1
        """,
        (ig_username,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    # Row may be dict or tuple depending on cursor factory
    return row.get("subscriber_id") if isinstance(row, dict) else row[0]


def delete_user_history(conn, ig_username: str) -> dict:
    """Delete rows for the given IG username across known tables.

    Returns a mapping of table -> rows_deleted.
    """
    deleted: dict[str, int] = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        subscriber_id = fetch_subscriber_id(cur, ig_username)

        def run_delete(sql: str, params: tuple, table_key: str):
            cur.execute(sql, params)
            count = cur.rowcount if cur.rowcount is not None else 0
            deleted[table_key] = deleted.get(table_key, 0) + max(count, 0)

        # messages
        if table_exists(cur, "messages"):
            if subscriber_id:
                run_delete(
                    "DELETE FROM messages WHERE ig_username = %s OR subscriber_id = %s",
                    (ig_username, subscriber_id),
                    "messages",
                )
            else:
                run_delete(
                    "DELETE FROM messages WHERE ig_username = %s",
                    (ig_username,),
                    "messages",
                )

        # pending_reviews (variant 1)
        if table_exists(cur, "pending_reviews"):
            if subscriber_id:
                run_delete(
                    (
                        "DELETE FROM pending_reviews\n"
                        " WHERE user_ig_username = %s\n"
                        "    OR user_subscriber_id = %s\n"
                        "    OR subscriber_id = %s"
                    ),
                    (ig_username, subscriber_id, subscriber_id),
                    "pending_reviews",
                )
            else:
                run_delete(
                    "DELETE FROM pending_reviews WHERE user_ig_username = %s",
                    (ig_username,),
                    "pending_reviews",
                )

        # review_queue (variant 2)
        if table_exists(cur, "review_queue"):
            if subscriber_id:
                run_delete(
                    (
                        "DELETE FROM review_queue\n"
                        " WHERE user_ig_username = %s\n"
                        "    OR user_subscriber_id = %s"
                    ),
                    (ig_username, subscriber_id),
                    "review_queue",
                )
            else:
                run_delete(
                    "DELETE FROM review_queue WHERE user_ig_username = %s",
                    (ig_username,),
                    "review_queue",
                )

        # analytics_data (dashboard copies)
        if table_exists(cur, "analytics_data"):
            if subscriber_id:
                run_delete(
                    "DELETE FROM analytics_data WHERE ig_username = %s OR subscriber_id = %s",
                    (ig_username, subscriber_id),
                    "analytics_data",
                )
            else:
                run_delete(
                    "DELETE FROM analytics_data WHERE ig_username = %s",
                    (ig_username,),
                    "analytics_data",
                )

    conn.commit()
    return deleted


def count_remaining(conn, ig_username: str) -> dict:
    remaining: dict[str, int] = {}
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        def add_count(table: str, where_sql: str, params: tuple):
            if table_exists(cur, table):
                cur.execute(
                    f"SELECT COUNT(*) AS c FROM {table} {where_sql}", params)
                remaining[table] = int(cur.fetchone()["c"])  # type: ignore

        # We only check by ig_username for verification simplicity
        add_count("messages", "WHERE ig_username = %s", (ig_username,))
        add_count("pending_reviews",
                  "WHERE user_ig_username = %s", (ig_username,))
        add_count("review_queue", "WHERE user_ig_username = %s", (ig_username,))
        add_count("analytics_data", "WHERE ig_username = %s", (ig_username,))
    return remaining


def main():
    parser = argparse.ArgumentParser(
        description="Clear Postgres history for an IG username")
    parser.add_argument("--db-url", required=True,
                        help="Full PostgreSQL connection URL")
    parser.add_argument("--username", required=True,
                        help="IG username, e.g., cocos_pt_studio")
    args = parser.parse_args()

    db_url = ensure_sslmode_require(args.db_url)

    try:
        conn = psycopg2.connect(db_url)
    except Exception as e:
        print(f"Failed to connect to Postgres: {e}")
        sys.exit(1)

    try:
        # Perform deletion
        deleted = delete_user_history(conn, args.username)
        # Verify
        remaining = count_remaining(conn, args.username)

        # Report
        if deleted:
            print("Deleted rows by table:")
            for table, cnt in deleted.items():
                print(f"  - {table}: {cnt}")
        else:
            print("No rows were deleted (nothing matched or tables missing).")

        if remaining:
            print("\nRemaining rows by table (should be 0):")
            for table, cnt in remaining.items():
                print(f"  - {table}: {cnt}")
        else:
            print("\nNo matching tables found to verify.")

        print("\nDone.")

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
