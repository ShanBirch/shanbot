#!/usr/bin/env python3
"""
Extract client metrics from SQLite database and recreate JSON files for video generation.
This recovers data after the cleanup function accidentally deleted the files.
"""

import sqlite3
import json
import os
from datetime import datetime


def extract_and_recreate_json_files():
    """Extract metrics from SQLite and recreate JSON files for video generation"""

    # Database and output paths
    db_path = "app/analytics_data_good.sqlite"
    output_dir = "output/checkin_reviews"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Client name mapping (IG username to full name)
    client_mapping = {
        'forster.alice': 'Alice Forster',
        'rebeccadangelo': 'Rebecca DAngelo',
        'kelly.smith': 'Kelly Smith',
        'sarika_ramani': 'Sarika Ramani',
        'nicole.lynch': 'Nicole Lynch',
        'elena.green': 'Elena Green',
        'kristy.cooper': 'Kristy Cooper',
        'rick.preston': 'Rick Preston',
        'claire.ruberu': 'Claire Ruberu',
        'kylie.pinder': 'Kylie Pinder',
        'jo.foy': 'Jo Foy',
        'tony.strupl': 'Tony Strupl',
        'anna.somogyi': 'Anna Somogyi',
        'danny.birch': 'Danny Birch',
        'shane.minahan': 'Shane Minahan',
        # Add new clients
        'jen.frayne': 'Jen Frayne',
        'jo.schiavetta': 'Jo Schiavetta',
        'raechel.muller': 'Raechel Muller'
    }

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query to get all users with metrics
        cursor.execute("""
            SELECT ig_username, first_name, last_name, metrics_json 
            FROM users 
            WHERE metrics_json IS NOT NULL AND metrics_json != ''
        """)

        users = cursor.fetchall()
        print(f"Found {len(users)} users with metrics data")

        recovered_count = 0

        for ig_username, first_name, last_name, metrics_json in users:
            try:
                # Parse metrics JSON
                metrics_data = json.loads(metrics_json)

                # Determine client name
                client_name = None
                if ig_username in client_mapping:
                    client_name = client_mapping[ig_username]
                elif first_name and last_name:
                    client_name = f"{first_name} {last_name}"
                else:
                    # Skip if we can't determine client name
                    continue

                # Create JSON filename
                client_name_clean = client_name.replace(' ', '_')
                today = datetime.now().strftime('%Y-%m-%d')
                json_filename = f"{client_name_clean}_{today}_fitness_wrapped_data.json"
                json_path = os.path.join(output_dir, json_filename)

                # Add client name to metrics data if not present
                if 'name' not in metrics_data:
                    metrics_data['name'] = client_name

                # Write JSON file
                with open(json_path, 'w') as f:
                    json.dump(metrics_data, f, indent=2)

                print(f"✓ Recovered: {json_filename}")
                recovered_count += 1

            except json.JSONDecodeError as e:
                print(f"✗ JSON decode error for {ig_username}: {e}")
            except Exception as e:
                print(f"✗ Error processing {ig_username}: {e}")

        conn.close()

        print(
            f"\n🎉 Successfully recovered {recovered_count} client JSON files!")
        print(f"📁 Files saved to: {output_dir}")
        print("🎬 Ready for video generation!")

        return recovered_count

    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return 0


if __name__ == "__main__":
    print("🔄 Extracting client metrics from SQLite database...")
    recovered = extract_and_recreate_json_files()

    if recovered > 0:
        print(f"\n✅ Recovery complete! {recovered} files restored.")
        print("You can now run video generation or the full automation workflow.")
    else:
        print("\n❌ No files recovered. Check database path and client mapping.")
