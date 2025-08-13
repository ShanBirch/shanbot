"""
Script to update the analytics dashboard with today's bot activity
"""
import os
import json
import datetime
from app.conversation_analytics_integration import analytics


def update_daily_analytics():
    """Updates the analytics dashboard with today's activity"""
    # Load daily stats
    stats_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "daily_stats.json")

    try:
        # Load the existing stats file
        with open(stats_path, "r") as f:
            stats = json.load(f)

        # Get today's date
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Make sure today exists in the stats
        if today not in stats:
            stats[today] = {"count": 0, "responses": 0}

        # Increment today's count (simulating new messages)
        stats[today]["count"] += 1

        # Save the updated stats
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)

        print(f"Updated daily stats for {today}: {stats[today]}")

        # Now update the analytics dashboard
        # Initialize analytics
        if not hasattr(analytics, 'global_metrics'):
            analytics.load_analytics()

        # Update bot stats in analytics
        global_metrics = analytics.global_metrics

        # Initialize bot_message_stats if needed
        if "bot_message_stats" not in global_metrics:
            global_metrics["bot_message_stats"] = {
                "total_messages_sent": 0,
                "total_messages_responded": 0,
                "daily_messages_sent": {},
                "daily_messages_responded": {}
            }

        # Update bot stats
        bot_stats = global_metrics["bot_message_stats"]

        # Calculate totals from daily stats
        total_sent = 0
        total_responded = 0

        for date, day_stats in stats.items():
            if isinstance(day_stats, dict):
                # Update daily counts
                bot_stats["daily_messages_sent"][date] = day_stats.get(
                    "count", 0)
                bot_stats["daily_messages_responded"][date] = day_stats.get(
                    "responses", 0)

                # Add to totals
                total_sent += day_stats.get("count", 0)
                total_responded += day_stats.get("responses", 0)

        # Update total counts
        bot_stats["total_messages_sent"] = total_sent
        bot_stats["total_messages_responded"] = total_responded

        # Save analytics updates
        analytics.export_analytics()

        print(
            f"Updated analytics dashboard with {total_sent} total messages sent")

        # Print the last 7 days of activity
        today_dt = datetime.datetime.now()
        print("\nLast 7 days of activity:")
        for i in range(7):
            date = (today_dt - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            sent = bot_stats["daily_messages_sent"].get(date, 0)
            responded = bot_stats["daily_messages_responded"].get(date, 0)
            print(f"{date}: Sent {sent}, Responded {responded}")

        return True

    except Exception as e:
        import traceback
        print(f"Error updating analytics: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Updating analytics dashboard with today's activity...")
    update_daily_analytics()
    print("\nDone! You can now view the updated dashboard by running:")
    print("streamlit run app/analytics_dashboard.py")
