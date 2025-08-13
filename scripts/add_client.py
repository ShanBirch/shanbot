from app.dashboard_modules.dashboard_sqlite_utils import (
    upsert_nutrition_targets,
    upsert_user_nutrition_profile,
    update_analytics_data,
    reset_daily_calorie_tracking_if_new_day,
)
import sys
import os
import argparse
from datetime import datetime

# Ensure workspace root on path
sys.path.insert(0, os.path.abspath('.'))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add/Update a client with nutrition targets")
    parser.add_argument("--ig", required=True,
                        help="Instagram username (ig_username)")
    parser.add_argument("--first", required=True, help="First name")
    parser.add_argument("--last", default="", help="Last name")
    parser.add_argument("--cal", type=int, required=True,
                        help="Daily calories")
    parser.add_argument("--protein", type=int,
                        required=True, help="Daily protein (g)")
    parser.add_argument("--carbs", type=int, required=True,
                        help="Daily carbs (g)")
    parser.add_argument("--fats", type=int, required=True,
                        help="Daily fats (g)")
    parser.add_argument("--goal", default="loss",
                        help="Main goal (loss/muscle/recomp)")
    args = parser.parse_args()

    ig_username = args.ig.strip()

    # 1) Upsert targets
    targets = {
        "target_calories": args.cal,
        "target_protein": args.protein,
        "target_carbs": args.carbs,
        "target_fats": args.fats,
    }
    if not upsert_nutrition_targets(ig_username, targets):
        print("Failed to upsert nutrition targets")
        return 1

    # 2) Upsert nutrition profile (minimal; goal stored)
    upsert_user_nutrition_profile(
        ig_username=ig_username,
        sex=None,
        dob=None,
        age=None,
        height_cm=None,
        weight_kg=None,
        activity_level=None,
        main_goal=args.goal,
    )

    # 3) Update analytics/user row as client
    now_iso = datetime.now().isoformat()
    update_analytics_data(
        ig_username=ig_username,
        message_text="Added/updated client via add_client.py",
        reply_text="",
        subscriber_id=ig_username,
        first_name=args.first,
        last_name=args.last,
        timestamp=now_iso,
        client_status="Client",
        journey_stage="Client",
        interests_json=None,
        is_in_checkin_flow=False,
        is_in_mono_checkin_flow=False,
        is_in_checkin_flow_mon=True,
        is_in_checkin_flow_wed=True,
        last_bot_response="",
        message_direction="system",
        offer_made=False,
        is_in_ad_flow=False,
        ad_script_state=None,
        ad_scenario=None,
        lead_source="manual",
    )

    # 4) Ensure daily counters are aligned to today
    reset_daily_calorie_tracking_if_new_day(ig_username)

    print(f"Client '{args.first}' (@{ig_username}) added/updated with targets: cal={args.cal}, P={args.protein}g, C={args.carbs}g, F={args.fats}g")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

