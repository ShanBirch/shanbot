#!/usr/bin/env python3
"""
Generate a simple contacts file with IG usernames for key clients.

Looks up approximate matches in the SQLite users table using
first_name, last_name, and ig_username.
"""

from __future__ import annotations

import os
import json
import sqlite3
from typing import Dict, List, Tuple


WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(WORKSPACE_DIR, "app", "analytics_data_good.sqlite")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "docs")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "client_contacts.md")


# Source list provided by user
CLIENT_SPECS: List[Dict[str, List[str]]] = [
    {"name": "Libby",   "terms": ["libby"]},
    {"name": "Amy",     "terms": ["amy", "burcherella", "burchella", "burcherella"]},
    {"name": "Staci",   "terms": ["staci", "stacy", "stacey"]},
    {"name": "Vlad",    "terms": ["vlad"]},
    {"name": "Linda",   "terms": ["linda"]},
    {"name": "Dana",    "terms": ["dana"]},
    {"name": "Sab",     "terms": ["sab", "sabrina"]},
    {"name": "Shane",   "terms": ["shane", "shane_minahan"]},
    {"name": "Kristy",  "terms": ["kristy", "kristie", "kristylee"]},
]


def find_matches(cursor: sqlite3.Cursor, term: str) -> List[Tuple[str, str, str, str]]:
    like = f"%{term.lower()}%"
    query = """
        SELECT ig_username, first_name, last_name, COALESCE(client_status, '')
        FROM users
        WHERE lower(COALESCE(ig_username,'')) LIKE ?
           OR lower(COALESCE(first_name,'')) LIKE ?
           OR lower(COALESCE(last_name,'')) LIKE ?
        ORDER BY ig_username
        LIMIT 50
    """
    return cursor.execute(query, (like, like, like)).fetchall()


def status_rank(status: str) -> int:
    s = (status or "").lower()
    if any(k in s for k in ("paying", "paid", "active")):
        return 0
    if "trial" in s:
        return 1
    return 2


def pick_best(matches: List[Tuple[str, str, str, str]]) -> Tuple[str, str, str, str] | None:
    if not matches:
        return None
    # Deduplicate by ig_username
    seen = set()
    uniq: List[Tuple[str, str, str, str]] = []
    for row in matches:
        ig = row[0] or ""
        if ig and ig not in seen:
            seen.add(ig)
            uniq.append(row)
    uniq.sort(key=lambda r: status_rank(r[3]))
    return uniq[0] if uniq else None


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    results: List[Dict[str, str]] = []

    for spec in CLIENT_SPECS:
        accumulated: List[Tuple[str, str, str, str]] = []
        for t in spec["terms"]:
            try:
                accumulated.extend(find_matches(cur, t))
            except Exception:
                # Keep going even if a single term errors
                pass
        chosen = pick_best(accumulated)
        results.append({
            "name": spec["name"],
            "ig_username": (chosen[0] if chosen else None),
            "first_name": (chosen[1] if chosen else None),
            "last_name": (chosen[2] if chosen else None),
            "status": (chosen[3] if chosen else None),
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("## Client Contacts\n\n")
        for r in results:
            ig = f"@{r['ig_username']}" if r["ig_username"] else "TODO"
            status = r["status"] or "Unknown"
            f.write(f"- **{r['name']}**: {ig} (Status: {status})\n")

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nWROTE: {OUTPUT_PATH}")

    conn.close()


if __name__ == "__main__":
    main()


