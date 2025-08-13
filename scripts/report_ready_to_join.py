import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(
    __file__)), "app", "analytics_data_good.sqlite")
REPORTS_DIR = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "reports")
REPORT_FILE = os.path.join(REPORTS_DIR, "ready_to_join_vegan_challenge.csv")


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None


def get_columns(conn: sqlite3.Connection, table_name: str) -> set:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def build_match_clause(column_sql: str):
    """Build a WHERE clause that matches common phrase variants OR token sets.
    Returns (clause_sql, params_list)
    """
    phrase_patterns = [
        "%i'm ready to join the vegan challenge%",
        "%im ready to join the vegan challenge%",
        "%i’m ready to join the vegan challenge%",
        "%i am ready to join the vegan challenge%",
        "%ready to join the vegan challenge%",
        "%ready to join%challenge%",
        "%ready to start the vegan challenge%",
        "%ready to start%challenge%",
        "%sign me up%vegan challenge%",
        "%sign me up%challenge%",
        "%i want to join%challenge%",
        "%want to join%challenge%",
        "%keen to join%challenge%",
        "%keen to join%vegan%",
        "%i'm in%challenge%",
        "%im in%challenge%",
        "%count me in%challenge%",
        "%join the vegan challenge%",
        "%join the challenge%",
        "%sign up for the vegan challenge%",
    ]
    phrase_likes = [f"LOWER({column_sql}) LIKE ?"] * len(phrase_patterns)
    phrase_clause = "(" + " OR ".join(phrase_likes) + ")"

    token_sets = [
        ["ready", "join", "challenge"],
        ["sign", "up", "challenge"],
        ["keen", "join", "challenge"],
        ["ready", "start", "challenge"],
        ["28", "day", "challenge"],
        ["28-day", "challenge"],
        ["ready", "vegan", "challenge"],
        ["join", "vegan", "challenge"],
    ]
    token_clauses = []
    token_params = []
    for tokens in token_sets:
        ands = [f"LOWER({column_sql}) LIKE ?" for _ in tokens]
        token_clauses.append("(" + " AND ".join(ands) + ")")
        token_params.extend([f"%{t}%" for t in tokens])

    full_clause = "(" + phrase_clause + (" OR " +
                                         " OR ".join(token_clauses) if token_clauses else "") + ")"
    params = [p for p in phrase_patterns]
    params.extend(token_params)
    return full_clause, params


def query_messages(conn: sqlite3.Connection):
    results = []

    # Prefer unified 'messages' table if present
    if table_exists(conn, "messages"):
        cols = get_columns(conn, "messages")

        # Determine text and type columns
        text_col = None
        for candidate in ("message_text", "text", "message"):
            if candidate in cols:
                text_col = candidate
                break
        if text_col is None:
            # No usable text column
            pass
        else:
            type_col = None
            for candidate in ("message_type", "type", "sender"):
                if candidate in cols:
                    type_col = candidate
                    break

            has_timestamp = "timestamp" in cols

            like_clause, like_params = build_match_clause(text_col)

            sql = [
                "SELECT ig_username",
                ", MIN(timestamp) AS first_match_ts" if has_timestamp else ", NULL AS first_match_ts",
                ", MAX(timestamp) AS last_match_ts" if has_timestamp else ", NULL AS last_match_ts",
                ", COUNT(*) AS match_count",
                ", MAX(" + text_col + ") AS sample_text",
                " FROM messages",
                " WHERE ",
                like_clause,
            ]

            params = like_params[:]

            # Do not filter by sender/type to maximize recall

            sql.append(" GROUP BY ig_username")
            sql.append(
                " ORDER BY (last_match_ts IS NULL) ASC, last_match_ts DESC, match_count DESC")

            query = "".join(sql)
            cur = conn.cursor()
            cur.execute(query, [p.lower() for p in params])
            results.extend(cur.fetchall())

    # Also check legacy 'conversation_history'
    if table_exists(conn, "conversation_history"):
        cols = get_columns(conn, "conversation_history")
        if {"ig_username", "message_text"}.issubset(cols):
            like_clause, like_params = build_match_clause("message_text")
            has_timestamp = "timestamp" in cols
            has_type = "message_type" in cols

            sql = [
                "SELECT ig_username",
                ", MIN(timestamp) AS first_match_ts" if has_timestamp else ", NULL AS first_match_ts",
                ", MAX(timestamp) AS last_match_ts" if has_timestamp else ", NULL AS last_match_ts",
                ", COUNT(*) AS match_count",
                ", MAX(message_text) AS sample_text",
                " FROM conversation_history",
                " WHERE ",
                like_clause,
            ]
            params = like_params[:]
            # Do not filter by sender/type to maximize recall
            sql.append(" GROUP BY ig_username")
            sql.append(
                " ORDER BY (last_match_ts IS NULL) ASC, last_match_ts DESC, match_count DESC")

            query = "".join(sql)
            cur = conn.cursor()
            cur.execute(query, [p.lower() for p in params])
            results.extend(cur.fetchall())

    # results rows: (ig_username, first_match_ts, last_match_ts, match_count, sample_text)
    return results


def dedupe_by_username(rows):
    by_user = {}
    for row in rows:
        ig_username, first_ts, last_ts, count, sample = row
        existing = by_user.get(ig_username)
        if existing is None:
            by_user[ig_username] = [ig_username,
                                    first_ts, last_ts, count, sample]
        else:
            # Merge: update min first_ts, max last_ts, sum counts, keep latest sample
            existing[1] = min(filter(None, [existing[1], first_ts])) if (
                existing[1] or first_ts) else None
            existing[2] = max(filter(None, [existing[2], last_ts])) if (
                existing[2] or last_ts) else None
            existing[3] = (existing[3] or 0) + (count or 0)
            existing[4] = sample or existing[4]
    return list(by_user.values())


def main():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Database not found at: {DB_PATH}")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = query_messages(conn)
        rows = dedupe_by_username(rows)

        # Sort by last_match_ts desc, nulls last, then by match_count desc
        def parse_ts(ts):
            if not ts:
                return None
            try:
                return datetime.fromisoformat(ts)
            except Exception:
                return None

        def sort_key(r):
            dt = parse_ts(r[2])
            if dt is None:
                return (1, 0.0, 0)
            try:
                # Works for aware and naive datetimes; naive uses local time
                ts_val = dt.timestamp()
            except Exception:
                ts_val = 0.0
            return (0, -ts_val, -(r[3] or 0))

        rows.sort(key=sort_key)

        # Write CSV
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(
                "ig_username,first_match_timestamp,last_match_timestamp,match_count,sample_text\n")
            for ig_username, first_ts, last_ts, count, sample in rows:
                # Escape quotes in sample
                sample_safe = (sample or "").replace('"', '""')
                first_ts_val = first_ts or ""
                last_ts_val = last_ts or ""
                count_val = count or 0
                f.write(
                    f'"{ig_username}","{first_ts_val}","{last_ts_val}",{count_val},"{sample_safe}"\n')

        # Print a compact summary to stdout
        print(
            f"Found {len(rows)} users with messages matching 'ready to join the vegan challenge'.")
        for ig_username, first_ts, last_ts, count, _ in rows[:50]:
            print(f"- {ig_username} (matches={count}, last={last_ts})")
        if len(rows) > 50:
            print(f"... and {len(rows) - 50} more. Full report: {REPORT_FILE}")
        else:
            print(f"Full report saved to: {REPORT_FILE}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
