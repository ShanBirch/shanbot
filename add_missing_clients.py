import sqlite3
import json
from datetime import datetime
from typing import List, Tuple

# --- Configuration ---
SQLITE_PATH = r"C:\Users\Shannon\OneDrive\Desktop\shanbot\app\analytics_data_good.sqlite"

# Missing clients from check_client_data.py output
MISSING_CLIENTS = [
    "Anna_Somogyi",
    "Claire_Ruberu",
    "Danny_Birch",
    "Elena_Green",
    "Jo_Foy",
    "Kylie_Pinder",
    "Nicole_Lynch",
    "Rebecca_DAngelo",
    "Rick_Preston",
    "Sarika_Ramani",
    "Tony_Strupl"
]


def parse_client_name(client_name_str: str) -> Tuple[str, str]:
    """Parse client name into first and last name."""
    # Handle special cases like Rebecca_DAngelo
    parts = client_name_str.replace("_", " ").strip().split(" ")
    if not parts:
        return "", ""

    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first_name, last_name


def create_default_user_data(client_name: str, first_name: str, last_name: str) -> dict:
    """Create default user data structure for a new client."""
    # Use the client name (with underscores) as the ig_username since they don't have Instagram
    ig_username = client_name.lower()

    current_time = datetime.now().isoformat()

    # Create metrics JSON structure
    metrics = {
        'ig_username': ig_username,
        'profile_complete': False,
        'last_updated': current_time,
        'created_date': current_time,
        'source': 'trainerize_manual_add',
        'conversation_history': [],
        'user_messages': 0,
        'total_messages': 0,
        'last_interaction_timestamp': None,
        'journey_stage': {
            'current_stage': 'New Client',
            'is_paying_client': True,  # They're Trainerize clients so they're paying
            'trial_start_date': None,
            'trial_end_date': None,
            'topic_progress': {}
        }
    }

    # Create client analysis JSON structure
    client_analysis = {
        'profile_bio': {
            'PERSON NAME': f"{first_name} {last_name}",
            'INTERESTS': [],
            'PERSONALITY TRAITS': [],
            'LIFESTYLE': 'Fitness enthusiast using Trainerize'
        },
        'conversation_topics': [
            "Topic 1 - Discuss their favorite plant-based protein sources for muscle growth and any creative vegetarian recipes they've discovered recently.",
            "Topic 2 - Explore their approach to tracking progress with clients, specifically what metrics they prioritize beyond just weight loss and how they use fitness apps.",
            "Topic 3 - Talk about their experience adapting resistance training techniques for clients with different fitness levels and what common mistakes they see people make.",
            "Topic 4 - Share tips on incorporating high-protein vegetarian meals into a busy schedule and how they advise clients to make healthy eating more convenient in Melbourne."
        ],
        'posts_analyzed': 0,
        'interests': ['Fitness', 'Health', 'Training'],
        'recent_activities': ['Using Trainerize for workout tracking']
    }

    return {
        'ig_username': ig_username,
        'first_name': first_name,
        'last_name': last_name,
        'subscriber_id': '',  # Will be populated when they connect to ManyChat
        'metrics': metrics,
        'client_analysis': client_analysis,
        'bio': f"Trainerize client: {first_name} {last_name}"
    }


def add_client_to_database(client_name: str) -> bool:
    """Add a single client to the database."""
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        first_name, last_name = parse_client_name(client_name)
        ig_username = client_name.lower()

        # Check if client already exists
        cursor.execute(
            "SELECT ig_username FROM users WHERE ig_username = ?", (ig_username,))
        if cursor.fetchone():
            print(f"  Client {client_name} already exists as {ig_username}")
            return True

        # Create user data
        user_data = create_default_user_data(
            client_name, first_name, last_name)

        # Insert into users table
        cursor.execute("""
            INSERT INTO users (
                ig_username, first_name, last_name, subscriber_id, 
                metrics_json, client_analysis_json, bio,
                is_onboarding, is_in_checkin_flow_mon, is_in_checkin_flow_wed,
                client_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data['ig_username'],
            user_data['first_name'],
            user_data['last_name'],
            user_data['subscriber_id'],
            json.dumps(user_data['metrics']),
            json.dumps(user_data['client_analysis']),
            user_data['bio'],
            0,  # is_onboarding = False
            0,  # is_in_checkin_flow_mon = False
            0,  # is_in_checkin_flow_wed = False
            'paying_client'  # client_status
        ))

        conn.commit()
        print(
            f"  ✅ Added {client_name} as {ig_username} ({first_name} {last_name})")
        return True

    except sqlite3.Error as e:
        print(f"  ❌ Database error adding {client_name}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error adding {client_name}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    print("🔄 Adding missing Trainerize clients to database...")
    print(f"Database: {SQLITE_PATH}")
    print(f"Clients to add: {len(MISSING_CLIENTS)}\n")

    added_count = 0
    failed_count = 0

    for client_name in MISSING_CLIENTS:
        print(f"Processing: {client_name}")
        if add_client_to_database(client_name):
            added_count += 1
        else:
            failed_count += 1

    print(f"\n📊 Summary:")
    print(f"✅ Successfully added: {added_count}")
    print(f"❌ Failed to add: {failed_count}")
    print(f"📝 Total processed: {len(MISSING_CLIENTS)}")

    if added_count > 0:
        print(f"\n🎯 These clients can now be linked when checkin_good runs!")
        print("💡 Their ig_username will be their Trainerize name in lowercase:")
        for client_name in MISSING_CLIENTS:
            print(f"   • {client_name} → {client_name.lower()}")


if __name__ == "__main__":
    main()
