import os
import sys
import json
import sqlite3
from datetime import date
import argparse


def ensure_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Minimal user_nutrition_profiles table in case it's missing
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_nutrition_profiles (
            ig_username TEXT PRIMARY KEY,
            sex TEXT,
            dob TEXT,
            age INTEGER,
            height_cm INTEGER,
            weight_kg REAL,
            activity_level TEXT,
            main_goal TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.commit()


def load_json(s: str):
    try:
        return json.loads(s) if s else {}
    except Exception:
        return {}


def upsert_user(conn: sqlite3.Connection, ig: str, sid: str, first_name: str, client_status: str = "Client") -> None:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE ig_username=?", (ig,))
    if cur.fetchone():
        cur.execute(
            "UPDATE users SET subscriber_id=?, first_name=?, client_status=? WHERE ig_username=?",
            (sid, first_name, client_status, ig),
        )
    else:
        cur.execute(
            "INSERT INTO users (ig_username, subscriber_id, first_name, client_status) VALUES (?,?,?,?)",
            (ig, sid, first_name, client_status),
        )
    conn.commit()


def set_targets(conn: sqlite3.Connection, ig: str, cal: int, protein: int, carbs: int, fats: int) -> None:
    tracking = {
        "daily_target": int(cal),
        "current_date": date.today().isoformat(),
        "calories_consumed": 0,
        "remaining_calories": int(cal),
        "macros": {
            "protein": {"daily_target": int(protein), "consumed": 0, "remaining": int(protein)},
            "carbs": {"daily_target": int(carbs), "consumed": 0, "remaining": int(carbs)},
            "fats": {"daily_target": int(fats), "consumed": 0, "remaining": int(fats)},
        },
        "meals_today": [],
    }
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET calorie_tracking_json=? WHERE ig_username=?",
        (json.dumps(tracking), ig),
    )
    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO users (ig_username, calorie_tracking_json) VALUES (?, ?)",
            (ig, json.dumps(tracking)),
        )
    conn.commit()

    # Mirror into metrics_json
    cur.execute("SELECT metrics_json FROM users WHERE ig_username=?", (ig,))
    row = cur.fetchone()
    metrics = load_json(row[0]) if row else {}
    metrics.setdefault("nutrition", {})
    metrics["nutrition"].update(
        {
            "calories_consumed_today": 0,
            "remaining_calories_today": int(cal),
        }
    )
    # Clear pending states that block flow
    metrics["pending_calorie_setup"] = False
    try:
        if "nutrition" in metrics and isinstance(metrics["nutrition"], dict):
            metrics["nutrition"].pop("pending_meal", None)
    except Exception:
        pass

    cur.execute(
        "UPDATE users SET metrics_json=? WHERE ig_username=?",
        (json.dumps(metrics), ig),
    )
    conn.commit()


def upsert_profile(conn: sqlite3.Connection, ig: str, goal: str) -> None:
    from datetime import datetime

    now = datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM user_nutrition_profiles WHERE ig_username=?", (ig,))
    if cur.fetchone():
        cur.execute(
            "UPDATE user_nutrition_profiles SET main_goal=?, updated_at=? WHERE ig_username=?",
            (goal, now, ig),
        )
    else:
        cur.execute(
            "INSERT INTO user_nutrition_profiles (ig_username, main_goal, created_at, updated_at) VALUES (?,?,?,?)",
            (ig, goal, now, now),
        )
    conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Quick fix a user's calorie setup and targets")
    ap.add_argument("--ig", required=True, help="Instagram username")
    ap.add_argument("--sid", required=True, help="ManyChat subscriber_id")
    ap.add_argument("--first", default="", help="First name")
    ap.add_argument("--cal", type=int, required=True, help="Daily calories")
    ap.add_argument("--protein", type=int, required=True,
                    help="Daily protein g")
    ap.add_argument("--carbs", type=int, required=True, help="Daily carbs g")
    ap.add_argument("--fats", type=int, required=True, help="Daily fats g")
    ap.add_argument("--goal", default="loss",
                    help="Main goal (loss/muscle/recomp)")
    args = ap.parse_args()

    db_path = os.path.join("app", "analytics_data_good.sqlite")
    conn = sqlite3.connect(db_path)
    try:
        ensure_tables(conn)
        upsert_user(conn, args.ig, args.sid, args.first or "")
        set_targets(conn, args.ig, args.cal,
                    args.protein, args.carbs, args.fats)
        upsert_profile(conn, args.ig, args.goal)
        print("OK")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

