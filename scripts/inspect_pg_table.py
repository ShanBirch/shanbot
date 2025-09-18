#!/usr/bin/env python3
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db-url", required=True)
    p.add_argument("--table", required=True)
    args = p.parse_args()

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position",
        (args.table,),
    )
    print(f"Columns for {args.table}:")
    for r in cur.fetchall():
        print(f" - {r['column_name']}: {r['data_type']}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
