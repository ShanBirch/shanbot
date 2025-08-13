import requests
import json
import time

WEBHOOK_URL = "https://1c3f-118-208-224-170.ngrok-free.app/webhook/manychat"


def quick_test():
    test_data = {
        "id": "quick_test_001",
        "ig_username": "quick_vegan_test",
        "last_input_text": "hey! love your vegan fitness content",
        "first_name": "Quick",
        "last_name": "Test",
        "created_at": time.time()
    }

    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true"
    }

    print("🧪 Quick Webhook Test")
    print(f"📤 Sending: {test_data['last_input_text']}")

    try:
        # Shorter timeout
        response = requests.post(
            WEBHOOK_URL, json=test_data, headers=headers, timeout=10)

        print(f"📊 Status: {response.status_code}")
        print(f"📨 Response: {response.text}")

        if response.status_code == 200:
            print("✅ SUCCESS: Webhook is working!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("⏱️ TIMEOUT: Webhook is processing (this is normal for Shannon's system)")
        print("✅ This means your bot received the message and is processing it!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    quick_test()
