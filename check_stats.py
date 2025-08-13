import sqlite3
from datetime import datetime, timedelta


def check_follow_stats():
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    c = conn.cursor()

    print("=== FOLLOW-BACK STATISTICS ===")

    # Overall stats
    c.execute('SELECT follow_back_status, COUNT(*) FROM processing_queue WHERE follow_back_status IS NOT NULL GROUP BY follow_back_status')
    overall_stats = c.fetchall()

    print("\n📊 Overall Follow-back Stats:")
    total_checked = 0
    followed_back = 0

    for status, count in overall_stats:
        print(f"  {status}: {count}")
        total_checked += count
        if status == 'yes':
            followed_back = count

    if total_checked > 0:
        percentage = (followed_back / total_checked) * 100
        print(
            f"\n✅ Follow-back Rate: {followed_back}/{total_checked} ({percentage:.1f}%)")

    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT follow_back_status, COUNT(*) FROM processing_queue WHERE DATE(follow_back_checked_at) = ? AND follow_back_status IS NOT NULL GROUP BY follow_back_status', (today,))
    today_stats = c.fetchall()

    print(f"\n📅 Today's Stats ({today}):")
    today_total = 0
    today_followed = 0

    for status, count in today_stats:
        print(f"  {status}: {count}")
        today_total += count
        if status == 'yes':
            today_followed = count

    if today_total > 0:
        today_percentage = (today_followed / today_total) * 100
        print(
            f"\n✅ Today's Follow-back Rate: {today_followed}/{today_total} ({today_percentage:.1f}%)")

    # DM stats
    c.execute(
        'SELECT dm_status, COUNT(*) FROM processing_queue WHERE dm_status IS NOT NULL GROUP BY dm_status')
    dm_stats = c.fetchall()

    print(f"\n💬 DM Stats:")
    for status, count in dm_stats:
        print(f"  {status}: {count}")

    conn.close()


if __name__ == "__main__":
    check_follow_stats()
