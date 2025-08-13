#!/usr/bin/env python3
"""
Manual script to tag blissedlia for vegan weight loss challenge flow
"""

import json
import os
from datetime import datetime

def tag_blissedlia_manual():
    """Manually tag blissedlia for vegan weight loss challenge flow"""
    
    # File paths to try
    file_paths = [
        "app/analytics_data_good.json",
        "analytics_data_good.json",
        "app/analytics_data.json"
    ]
    
    analytics_file = None
    for path in file_paths:
        if os.path.exists(path):
            analytics_file = path
            break
    
    if not analytics_file:
        print("❌ Could not find analytics data file")
        return
    
    print(f"📁 Found analytics file: {analytics_file}")
    
    try:
        # Load analytics data
        with open(analytics_file, 'r') as f:
            analytics_data = json.load(f)
        
        conversations = analytics_data.get('conversations', {})
        user_found = False
        
        # Search for blissedlia
        for user_id, user_data in conversations.items():
            if user_data.get('ig_username', '').lower() == 'blissedlia':
                print(f"✅ Found blissedlia with ID: {user_id}")
                
                # Update lead source and ad flow flags
                user_data['lead_source'] = 'plant_based_challenge'
                user_data['is_in_ad_flow'] = True
                user_data['ad_script_state'] = 'step1'
                user_data['ad_scenario'] = 1
                user_data['updated_at'] = datetime.now().isoformat()
                
                user_found = True
                break
        
        if not user_found:
            print("📝 blissedlia not found, creating new entry...")
            
            # Create new user entry
            new_user_id = f"user_{len(conversations) + 1}"
            conversations[new_user_id] = {
                'ig_username': 'blissedlia',
                'subscriber_id': '402069007',
                'lead_source': 'plant_based_challenge',
                'is_in_ad_flow': True,
                'ad_script_state': 'step1',
                'ad_scenario': 1,
                'conversation_history': [],
                'metrics': {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        # Save updated data
        with open(analytics_file, 'w') as f:
            json.dump(analytics_data, f, indent=2)
        
        print("✅ Successfully tagged blissedlia for vegan weight loss challenge flow!")
        print("Lead source: plant_based_challenge")
        print("Ad flow: Enabled")
        print("Script state: step1")
        print("Scenario: 1 (vegan)")
        
    except Exception as e:
        print(f"❌ Error updating analytics file: {e}")

if __name__ == "__main__":
    tag_blissedlia_manual() 