import os
import sys


def fetch_from_postgres(kind: str, limit: int = 10):
    import psycopg2
    from psycopg2.extras import RealDictCursor

    url = os.getenv("DATABASE_URL")
    if not url:
        return []
    with psycopg2.connect(url) as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if kind == "vegan":
            cur.execute(
                """
                SELECT original_prompt_text, edited_response_text
                FROM learning_feedback_log
                WHERE is_good_example_for_few_shot = TRUE
                  AND conversation_type = 'vegan'
                ORDER BY created_timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
        elif kind == "general":
            cur.execute(
                """
                SELECT original_prompt_text, edited_response_text
                FROM learning_feedback_log
                WHERE is_good_example_for_few_shot = TRUE
                  AND (conversation_type IS NULL OR conversation_type = 'general')
                ORDER BY created_timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
        else:
            cur.execute(
                """
                SELECT original_prompt_text, edited_response_text, conversation_type
                FROM learning_feedback_log
                WHERE is_good_example_for_few_shot = TRUE
                ORDER BY created_timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
        return cur.fetchall() or []


def fetch_from_sqlite(kind: str, limit: int = 10):
    import sqlite3

    db_path = os.path.join("app", "analytics_data_good.sqlite")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        if kind == "vegan":
            cur.execute(
                """
                SELECT original_prompt_text, edited_response_text
                FROM learning_feedback_log
                WHERE is_good_example_for_few_shot = 1
                  AND conversation_type = 'vegan'
                ORDER BY datetime(timestamp) DESC
                LIMIT ?
                """,
                (limit,),
            )
        elif kind == "general":
            cur.execute(
                """
                SELECT original_prompt_text, edited_response_text
                FROM learning_feedback_log
                WHERE is_good_example_for_few_shot = 1
                  AND (conversation_type IS NULL OR conversation_type = 'general')
                ORDER BY datetime(timestamp) DESC
                LIMIT ?
                """,
                (limit,),
            )
        else:
            cur.execute(
                """
                SELECT original_prompt_text, edited_response_text, conversation_type
                FROM learning_feedback_log
                WHERE is_good_example_for_few_shot = 1
                ORDER BY datetime(timestamp) DESC
                LIMIT ?
                """,
                (limit,),
            )
        return [dict(row) for row in cur.fetchall() or []]
    finally:
        conn.close()


def main():
    kind = "vegan"  # default for new regeneration
    limit = 10
    for arg in sys.argv[1:]:
        if arg.startswith("--kind="):
            kind = arg.split("=", 1)[1]
        if arg.startswith("--limit="):
            try:
                limit = int(arg.split("=", 1)[1])
            except ValueError:
                pass

    rows = []
    # Prefer Postgres if configured
    if os.getenv("DATABASE_URL"):
        try:
            rows = fetch_from_postgres(kind, limit)
        except Exception as e:
            print(f"[warn] Postgres fetch failed: {e}")

    if not rows:
        try:
            rows = fetch_from_sqlite(kind, limit)
        except Exception as e:
            print(f"[warn] SQLite fetch failed: {e}")

    if not rows:
        print("No few-shot examples found.")
        return

    print(f"\n=== Few-shot examples ({kind}, limit={limit}) ===\n")
    for idx, row in enumerate(rows, start=1):
        inp = (row.get("original_prompt_text")
               or row.get("input") or "").strip()
        out = (row.get("edited_response_text")
               or row.get("output") or "").strip()
        ctype = row.get("conversation_type")
        prefix = f"[{ctype}] " if ctype else ""
        print(f"{idx}. {prefix}User: {inp}")
        print(f"   Shannon: {out}\n")


if __name__ == "__main__":
    main()

