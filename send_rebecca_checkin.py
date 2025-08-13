import json
from datetime import datetime


def queue_rebecca_checkin():
    """Queue Monday morning check-in for Rebecca with corrected username"""

    # Rebecca's Monday morning check-in message (same as the others)
    message = "Morrrrning!!! Big Week Ahead!! We got some gains to make! Will you be getting to the gym?"

    # Queue file path
    queue_file = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\followup_queue.json"

    # Create message entry
    message_entry = {
        "username": "rebeccadangelo01",  # Corrected username
        "message": message,
        "topic": "Check-in",
        "timestamp": datetime.now().isoformat()
    }

    # Load existing queue or create new one
    try:
        with open(queue_file, 'r') as f:
            queue_data = json.load(f)
    except FileNotFoundError:
        queue_data = {"messages": [], "created_at": datetime.now().isoformat()}

    # Add Rebecca's message to queue
    queue_data["messages"].append(message_entry)
    queue_data["created_at"] = datetime.now().isoformat()

    # Save updated queue
    with open(queue_file, 'w') as f:
        json.dump(queue_data, f, indent=2)

    print(f"✅ Queued Monday morning check-in for @rebeccadangelo01")
    print(f"📝 Message: {message}")
    print(f"🕐 Timestamp: {message_entry['timestamp']}")
    print(f"📁 Queue file: {queue_file}")

    return True


if __name__ == "__main__":
    success = queue_rebecca_checkin()
    if success:
        print("\n🚀 Rebecca's check-in is now queued! The followup manager should pick it up automatically.")
    else:
        print("\n❌ Failed to queue Rebecca's check-in")
