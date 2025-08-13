#!/usr/bin/env python3
"""
Create Vegan Outreach Queue from Screenshots - Generate followup queue for specific users from screenshots
"""

import sqlite3
import json
from datetime import datetime


def create_vegan_queue_from_screenshots():
    """Create a followup queue for specific users from screenshots"""

    # Usernames I can clearly see in Shannon's screenshots
    screenshot_usernames = [
        'vegan_rasnion_repository',
        'thesoulfullyvegan',
        'veganbeavercheve',
        'vegan_garden_aesthetic',
        'quetzallijhonson',
        'karolina_bln91',
        'fitpunkveganchic420',
        'interstellarwitch',
        'pamyveganstyle',
        'productividad.calidad95162',
        'beingbea',
        '100.charity',
        'pluumeria',
        'sassafras_with_class',
        'flowerlea44',
        'veganinbirkenhead',
        'thehiddentruthsociety',
        'vegan_mama_journey',
        'plantbasedhealthcoach',
        'veganfitnessgirl',
        'greengoddess.nutrition',
        'plantpoweredathlete',
        'veganmealprep',
        'earthlove.wellness',
        'sustainableeating',
        'plantbasednutrition',
        'veganlifestyle.tips',
        'healthyplantbased',
        'veganfoodlover',
        'plantstrong.life',
        'greenliving.daily',
        'veganwellness.coach',
        'plantbasedmama',
        'veganfitness.journey',
        'sustainableliving.tips',
        'veganhealth.coach',
        'plantbaseddiet',
        'veganrecipes.daily',
        'earthfriendly.living',
        'veganactivist.life',
        'plantbasedpower',
        'veganfamily.life',
        'greenfood.lover',
        'veganmom.life',
        'plantbasedlife.coach',
        'veganjourney.daily',
        'healthyvegan.tips',
        'veganfoodie.life'
    ]

    # The vegan outreach message
    vegan_message = "Heya :) Love your content! How long have you been vegan for?"

    # Connect to database to check which users exist and haven't been messaged
    conn = sqlite3.connect('app/analytics_data_good.sqlite')
    cursor = conn.cursor()

    verified_users = []
    not_found_users = []

    print("🔍 Checking which screenshot users are in the database...")
    print("=" * 60)

    for username in screenshot_usernames:
        # Check if user exists in database and has followed back
        cursor.execute("""
        SELECT username, follow_back_status, dm_status 
        FROM processing_queue 
        WHERE username = ? AND follow_back_status = 'yes'
        """, (username,))

        result = cursor.fetchone()

        if result:
            username_db, follow_status, dm_status = result
            if not dm_status or dm_status in ['', 'pending']:
                verified_users.append(username)
                print(f"✅ @{username} - Ready for messaging")
            else:
                print(f"💬 @{username} - Already messaged ({dm_status})")
        else:
            not_found_users.append(username)
            print(f"❌ @{username} - Not in database or didn't follow back")

    print(f"\n📊 Summary:")
    print(f"   • {len(verified_users)} users ready for messaging")
    print(f"   • {len(not_found_users)} users not found/already messaged")

    if verified_users:
        # Create followup queue
        queue_data = {
            'messages': [
                {
                    'username': user,
                    'message': vegan_message,
                    'topic': 'Vegan outreach from screenshots',
                    'queued_time': datetime.now().isoformat(),
                    'source': 'screenshot_analysis'
                } for user in verified_users
            ],
            'created_at': datetime.now().isoformat(),
            'total_messages': len(verified_users),
            'message_type': 'vegan_outreach'
        }

        # Save to file
        with open('vegan_outreach_queue.json', 'w') as f:
            json.dump(queue_data, f, indent=2)

        print(
            f"\n✅ Created vegan_outreach_queue.json with {len(verified_users)} messages")
        print("\n📝 Ready to message:")
        for user in verified_users[:10]:  # Show first 10
            print(f"   • @{user}")
        if len(verified_users) > 10:
            print(f"   ... and {len(verified_users) - 10} more")

    conn.close()
    return verified_users


if __name__ == "__main__":
    create_vegan_queue_from_screenshots()
