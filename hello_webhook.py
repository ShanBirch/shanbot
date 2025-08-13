from flask import Flask, request, jsonify
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ManyChat API settings
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"
MANYCHAT_API_URL = "https://api.manychat.com/fb"  # For Facebook
MANYCHAT_IG_API_URL = "https://api.manychat.com/instagram"  # For Instagram


@app.route('/webhook/manychat', methods=['POST'])
def webhook():
    """Super simple webhook endpoint for ManyChat"""
    try:
        # Log the entire request
        logger.info(f"Received request headers: {dict(request.headers)}")
        data = request.get_json()
        logger.info(f"Received request body: {data}")

        # Create a simpler response - ManyChat might prefer this format
        response = {
            "version": "v2",
            "content": {
                "messages": [
                    {
                        "type": "text",
                        "text": "Working on your program request..."
                    }
                ],
                "actions": [
                    {
                        "action": "set_field_value",
                        "field_name": "o1 Response",  # Try field_name instead of field_id
                        "value": "Test conversation content for field o1 Response"
                    },
                    {
                        "action": "set_field_value",
                        "field_name": "o1 Response 2",  # Try field_name instead of field_id
                        "value": "Test name value for field o1 Response 2"
                    }
                ]
            }
        }

        # Try to directly update via API as well
        try:
            subscriber_id = None
            if 'id' in data:
                subscriber_id = data['id']
            elif 'subscriber' in data and 'id' in data['subscriber']:
                subscriber_id = data['subscriber']['id']

            if subscriber_id:
                logger.info(
                    f"Attempting direct API update for subscriber {subscriber_id}")
                api_response = update_subscriber_fields(subscriber_id)
                logger.info(f"API response: {api_response}")
        except Exception as api_error:
            logger.error(f"API update failed: {str(api_error)}", exc_info=True)

        logger.info(f"Sending response: {response}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        # Return a minimal response even if there's an error
        return jsonify({
            "version": "v2",
            "content": {
                "messages": [
                    {
                        "type": "text",
                        "text": "We received your request."
                    }
                ]
            }
        })


def update_subscriber_fields(subscriber_id):
    """Update subscriber custom fields via ManyChat API"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MANYCHAT_API_KEY}"
    }

    # Prepare data for API call
    data = {
        "subscriber_id": subscriber_id,
        "fields": {
            "o1 Response": "Test conversation content via API",
            "o1 Response 2": "Test name value via API"
        }
    }

    logger.info(f"Sending API request with data: {data}")

    # Try Instagram API first, then fallback to Facebook if that fails
    try:
        # Try Instagram endpoint
        logger.info("Trying Instagram API...")
        response = requests.post(
            f"{MANYCHAT_IG_API_URL}/subscriber/setCustomFields",
            headers=headers,
            json=data,
            timeout=10
        )

        logger.info(f"Instagram API response status: {response.status_code}")
        logger.info(f"Instagram API response body: {response.text}")

        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            logger.info(
                f"Instagram API failed with status {response.status_code}. Trying Facebook API...")

        # Try Facebook endpoint as fallback
        logger.info("Trying Facebook API...")
        response = requests.post(
            f"{MANYCHAT_API_URL}/subscriber/setCustomFields",
            headers=headers,
            json=data,
            timeout=10
        )

        logger.info(f"Facebook API response status: {response.status_code}")
        logger.info(f"Facebook API response body: {response.text}")

        return response.json()
    except Exception as e:
        logger.error(f"API request failed: {str(e)}", exc_info=True)
        return {"error": str(e)}


@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return "Server is running. Send POST to /webhook/manychat"


if __name__ == '__main__':
    logger.info("Starting simple Flask webhook server on port 8001")
    logger.info(
        "Webhook URL: https://9573-194-223-45-155.ngrok-free.app/webhook/manychat")
    app.run(host='0.0.0.0', port=8001, debug=True)
