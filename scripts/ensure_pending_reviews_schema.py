#!/usr/bin/env python3
"""
Ensure Render Postgres has the right pending_reviews schema for Regenerate.

Actions:
- Add proposed_response_text (TEXT), regeneration_count (INTEGER DEFAULT 0), reviewed_timestamp (TIMESTAMP)
- If reviewed_timestamp exists as TEXT, convert to TIMESTAMP

Usage:
  python scripts/ensure_pending_reviews_schema.py --db-url <DATABASE_URL>
"""

from __future__ import annotations

import argparse
import sys

import psycopg2
from psycopg2.extras import RealDictCursor


def ensure_schema(database_url: str) -> None:
    conn = psycopg2.connect(database_url)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Add columns if missing
        cur.execute("ALTER TABLE IF EXISTS pending_reviews ADD COLUMN IF NOT EXISTS proposed_response_text TEXT")
        cur.execute("ALTER TABLE IF EXISTS pending_reviews ADD COLUMN IF NOT EXISTS regeneration_count INTEGER DEFAULT 0")
        # Add reviewed_timestamp if missing; start as TIMESTAMP directly
        cur.execute("ALTER TABLE IF EXISTS pending_reviews ADD COLUMN IF NOT EXISTS reviewed_timestamp TIMESTAMP")

        # If reviewed_timestamp is TEXT in this DB, convert to TIMESTAMP safely
        cur.execute(
            """
            SELECT data_type FROM information_schema.columns
            WHERE table_name='pending_reviews' AND column_name='reviewed_timestamp'
            """
        )
        row = cur.fetchone()
        if row and row.get("data_type") == "text":
            cur.execute(
                """
                ALTER TABLE pending_reviews
                ALTER COLUMN reviewed_timestamp TYPE TIMESTAMP USING NULLIF(reviewed_timestamp,'')::timestamp
                """
            )

        conn.commit()

        # Print the final state for visibility
        cur.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name='pending_reviews' AND column_name IN ('proposed_response_text','regeneration_count','reviewed_timestamp') "
            "ORDER BY column_name"
        )
        for r in cur.fetchall():
            print(f"{r['column_name']}: {r['data_type']}")

        cur.close()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ensure pending_reviews schema")
    parser.add_argument("--db-url", required=True, help="Postgres connection string")
    args = parser.parse_args()

    try:
        ensure_schema(args.db_url)
        print("Schema ensured.")
    except Exception as e:
        print(f"Failed to ensure schema: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


