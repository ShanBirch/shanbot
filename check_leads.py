import sqlite3
import json

SQLITE_DB_PATH = r"app/analytics_data_good.sqlite"


def check_new_leads():
    """Checks for new leads in the database and prints them."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Fetch new leads
        cursor.execute(
            "SELECT username, coaching_reasons, analysis_data FROM new_leads WHERE status = 'new'")
        leads = cursor.fetchall()

        conn.close()

        if not leads:
            print("No new potential clients found yet.")
            return

        print(f"Found {len(leads)} new potential clients:")
        for i, (username, reasons_json, analysis_json) in enumerate(leads, 1):
            reasons = json.loads(reasons_json)
            analysis = json.loads(analysis_json)
            source = analysis.get('source_influencer') or analysis.get(
                'hashtag_found', 'Unknown')

            print(f"\n{i}. @{username}")
            print(f"   - Found via: {source}")
            print(f"   - Reason: {reasons[0] if reasons else 'N/A'}")

    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print(
                "The 'new_leads' table does not exist yet. The script may not have found any leads to save.")
        else:
            print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    check_new_leads()
