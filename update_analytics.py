"""
Script to test analytics update functionality
"""
import os
import json
from app.conversation_analytics_integration import analytics


def load_daily_stats():
    """Load the daily statistics from the stats file."""
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    stats_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "daily_stats.json")
    try:
        if os.path.exists(stats_path):
            with open(stats_path, "r") as f:
                stats = json.load(f)
                print(f"Loaded daily stats: {stats}")
                return stats
        else:
            print(f"No daily stats file found at {stats_path}")
            stats = {today: {"count": 0, "responses": 0}}
            return stats
    except Exception as e:
        print(f"Error loading daily stats: {e}")
        return {today: {"count": 0, "responses": 0}}


def update_analytics_with_bot_stats(stats):
    """Update analytics data with bot message statistics for the dashboard."""
    try:
        # Get the current global metrics
        global_metrics = analytics.global_metrics
        print(f"Current global metrics: {global_metrics.keys()}")

        # Initialize bot_message_stats if it doesn't exist
        if "bot_message_stats" not in global_metrics:
            global_metrics["bot_message_stats"] = {
                "total_messages_sent": 0,
                "total_messages_responded": 0,
                "daily_messages_sent": {},
                "daily_messages_responded": {}
            }
            print("Initialized bot_message_stats in global metrics")

        # Update the bot stats
        bot_stats = global_metrics["bot_message_stats"]

        # Process each day's stats
        total_sent = 0
        total_responded = 0

        for date, day_stats in stats.items():
            if isinstance(day_stats, dict):
                # Update daily sent messages
                message_count = day_stats.get("count", 0)
                bot_stats["daily_messages_sent"][date] = message_count
                total_sent += message_count

                # Update daily responded messages
                response_count = day_stats.get("responses", 0)
                bot_stats["daily_messages_responded"][date] = response_count
                total_responded += response_count
            elif isinstance(day_stats, (int, float)):
                # Legacy format handling
                bot_stats["daily_messages_sent"][date] = day_stats
                total_sent += day_stats

        # Update totals
        bot_stats["total_messages_sent"] = total_sent
        bot_stats["total_messages_responded"] = total_responded

        # Print summary of update
        print(f"Updated analytics with bot stats:")
        print(f"- Total messages sent: {total_sent}")
        print(f"- Total messages responded: {total_responded}")
        print(
            f"- Daily tracking for {len(bot_stats['daily_messages_sent'])} days")

        # Save the updated analytics
        analytics.export_analytics()
        print("Successfully exported updated analytics data")

        return global_metrics
    except Exception as e:
        import traceback
        print(f"Error updating analytics with bot stats: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Loading daily stats and updating analytics...")
    daily_stats = load_daily_stats()

    # Make sure analytics is initialized
    if not hasattr(analytics, 'global_metrics'):
        print("Analytics not initialized, loading data...")
        analytics.load_analytics()

    # Update the analytics with bot stats
    updated_metrics = update_analytics_with_bot_stats(daily_stats)

    if updated_metrics:
        print("Successfully updated analytics!")

        # Show a summary of the bot metrics
        bot_stats = updated_metrics.get("bot_message_stats", {})
        print("\nBot Message Statistics Summary:")
        print(
            f"Total messages sent: {bot_stats.get('total_messages_sent', 0)}")
        print(
            f"Total responses received: {bot_stats.get('total_messages_responded', 0)}")

        # Show daily stats for the last 7 days
        import datetime
        today = datetime.datetime.now()
        print("\nLast 7 days activity:")
        for i in range(7):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            sent = bot_stats.get("daily_messages_sent", {}).get(date, 0)
            responded = bot_stats.get(
                "daily_messages_responded", {}).get(date, 0)
            print(f"{date}: Sent: {sent}, Responded: {responded}")
    else:
        print("Failed to update analytics.")
