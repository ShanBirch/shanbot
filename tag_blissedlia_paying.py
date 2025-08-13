#!/usr/bin/env python3
"""
Script to tag blissedlia as a paying member
"""

import json
import os
from datetime import datetime

def tag_blissedlia_paying():
    """Tag blissedlia as a paying member"""
    
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
                
                # Update to paying member status
                user_data['lead_source'] = 'paying_member'
                user_data['is_in_ad_flow'] = False  # Not in ad flow anymore
                user_data['ad_script_state'] = 'completed'
                user_data['ad_scenario'] = 1
                user_data['member_status'] = 'active'
                user_data['payment_status'] = 'paid'
                user_data['updated_at'] = datetime.now().isoformat()
                
                user_found = True
                break
        
        if not user_found:
            print("📝 blissedlia not found, creating new paying member entry...")
            
            # Create new paying member entry
            new_user_id = f"user_{len(conversations) + 1}"
            conversations[new_user_id] = {
                'ig_username': 'blissedlia',
                'subscriber_id': '402069007',
                'lead_source': 'paying_member',
                'is_in_ad_flow': False,
                'ad_script_state': 'completed',
                'ad_scenario': 1,
                'member_status': 'active',
                'payment_status': 'paid',
                'conversation_history': [],
                'metrics': {},
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        # Save updated data
        with open(analytics_file, 'w') as f:
            json.dump(analytics_data, f, indent=2)
        
        print("✅ Successfully tagged blissedlia as a paying member!")
        print("Lead source: paying_member")
        print("Member status: active")
        print("Payment status: paid")
        print("Ad flow: Completed")
        
    except Exception as e:
        print(f"❌ Error updating analytics file: {e}")

if __name__ == "__main__":
    tag_blissedlia_paying() 