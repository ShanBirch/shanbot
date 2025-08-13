#!/usr/bin/env python3
"""
Test script to check ad detection functionality
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ad_detection():
    """Test ad detection functionality"""
    print("🧪 Testing Ad Detection...")
    
    try:
        # Import the webhook functions
        from webhook0605 import detect_ad_intent_with_context
        
        print("✅ Successfully imported ad detection function")
        
        # Test cases
        test_cases = [
            ("I want to learn more about your vegan challenge", "Should detect vegan challenge"),
            ("Tell me more about your vegetarian challenge", "Should detect vegetarian challenge"),
            ("I'm interested in your vegan challenge", "Should detect vegan challenge"),
            ("Hi, how are you?", "Should NOT detect ad"),
            ("I saw your ad about the vegan challenge", "Should detect vegan challenge"),
            ("Can you tell me more about your Vegan Weight Loss Challenge", "Should detect exact trigger"),
        ]
        
        for message, description in test_cases:
            print(f"\n📝 Testing: '{message}'")
            print(f"   Description: {description}")
            
            # Mock conversation history (empty for new conversations)
            conversation_history = []
            
            try:
                is_ad, scenario, confidence = await detect_ad_intent_with_context(
                    ig_username="test_user",
                    message_text=message,
                    conversation_history=conversation_history
                )
                
                challenge_types = {1: 'vegan', 2: 'vegetarian', 3: 'plant_based'}
                challenge_type = challenge_types.get(scenario, 'plant_based')
                
                print(f"   ✅ Result: is_ad={is_ad}, scenario={scenario} ({challenge_type}), confidence={confidence}%")
                
                if is_ad and confidence >= 70:
                    print(f"   🎯 AD DETECTED! Would trigger vegan challenge flow")
                else:
                    print(f"   ❌ No ad detected or low confidence")
                    
            except Exception as e:
                print(f"   ❌ Error testing: {e}")
                
    except Exception as e:
        print(f"❌ Error testing ad detection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ad_detection()) 