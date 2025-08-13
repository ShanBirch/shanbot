import requests
import json
import logging
import time
from datetime import datetime

# Set up logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ManyChat API configuration
API_KEY = "996573:5b6dc180662de1be343655db562ee918"

# Correct API endpoints - these are the most likely endpoints based on ManyChat API structure
API_ENDPOINT = "https://api.manychat.com/fb/subscriber/setCustomFields"
API_ENDPOINT_BYID = "https://api.manychat.com/fb/subscriber/setCustomFields"
API_ENDPOINT_UPDATE_SUBSCRIBER = "https://api.manychat.com/fb/subscriber/updateSubscriber"
API_ENDPOINT_GET_BOTINFO = "https://api.manychat.com/fb/page/getInfo"
API_ENDPOINT_LIST_SUBSCRIBERS = "https://api.manychat.com/fb/subscriber/list"

# Field IDs and names - these should be real field IDs from your ManyChat account
FIELD_IDS = {
    "o1 Response": 11944956,
    "o1 Response 2": 11967919
}

# Values to set in the fields
FIELD_VALUES = {
    "o1 Response": "Testing via direct API",
    "o1 Response 2": "Testing second field"
}

# Using the subscriber ID provided by the user
SUBSCRIBER_ID = "1243475080"


def update_subscriber_fields():
    """Update subscriber custom fields using current API format"""
    logging.info(
        "Attempting to update fields for subscriber_id: %s", SUBSCRIBER_ID)

    # Try updating a field that we confirmed exists on the subscriber
    # Format fields exactly as per API requirements
    data = {
        "subscriber_id": SUBSCRIBER_ID,
        "fields": [
            {
                "field_id": 11821126,  # CONVERSATION field that exists on the subscriber
                "field_value": "Updated via API " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
    }

    logging.info("Prepared request data: %s", json.dumps(data))

    # Send the request
    response = send_api_request(API_ENDPOINT, data)

    # Log the response
    logging.info("Response status: %s", response.status_code)
    logging.info("Response body: %s", response.text)

    return response.status_code == 200


def update_subscriber_data():
    """Update subscriber profile data using updateSubscriber endpoint"""
    logging.info(
        "Attempting to update subscriber profile for subscriber_id: %s", SUBSCRIBER_ID)

    # Prepare the data for subscriber update with valid phone format
    data = {
        "subscriber_id": SUBSCRIBER_ID,
        "first_name": "Test",
        "last_name": "User",
        "phone": "+61423456789",  # Using proper Australian format
        "email": "test@example.com",
        "has_opt_in_sms": True,
        "has_opt_in_email": True,
        "consent_phrase": "Consent given during API testing",
        "consent_type": "API"
    }

    logging.info("Prepared subscriber update data: %s", json.dumps(data))

    # Send the request
    response = send_api_request(API_ENDPOINT_UPDATE_SUBSCRIBER, data)

    # Log the response
    logging.info("Response status: %s", response.status_code)
    logging.info("Response body: %s", response.text)

    return response.status_code == 200


def update_by_field_name():
    """Update subscriber fields using field names instead of IDs"""
    logging.info(
        "Attempting to update fields by name for subscriber_id: %s", SUBSCRIBER_ID)

    # Prepare the data using field names instead of IDs
    # Format fields exactly as per API requirements
    data = {
        "subscriber_id": SUBSCRIBER_ID,
        "fields": [
            {
                "field_name": "CONVERSATION",
                "field_value": "Testing via field name API " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "field_name": "o1 Response",
                "field_value": "Testing via direct API"
            }
        ]
    }

    logging.info("Prepared request data (name method): %s", json.dumps(data))

    # Send the request
    response = send_api_request(API_ENDPOINT, data)

    # Log the response
    logging.info("Response status: %s", response.status_code)
    logging.info("Response body: %s", response.text)

    return response.status_code == 200


def send_api_request(url, data):
    """Send request to ManyChat API with proper headers."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    # Log the full request details for debugging
    logging.info(f"Sending request to {url}")
    logging.info(f"Headers: {headers}")
    logging.info(f"Data: {json.dumps(data)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        # Create a dummy response object to return

        class DummyResponse:
            def __init__(self):
                self.status_code = 500
                self.text = str(e)
        return DummyResponse()


def try_get_subscriber():
    """Try a simple GET request to retrieve subscriber info"""
    logging.info("Testing API connectivity by retrieving subscriber info")

    url = f"https://api.manychat.com/fb/subscriber/getInfo?subscriber_id={SUBSCRIBER_ID}"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        logging.info(f"Testing endpoint: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")

        # Extract and display field data from the response
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
                if "data" in data and "custom_fields" in data["data"]:
                    custom_fields = data["data"]["custom_fields"]
                    logging.info(
                        f"Found {len(custom_fields)} custom fields on this subscriber:")
                    for field in custom_fields:
                        logging.info(
                            f"  Field ID: {field.get('id')}, Name: {field.get('name')}, Value: {field.get('value')}")
            except json.JSONDecodeError:
                logging.error("Failed to parse JSON response")

        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error testing endpoint {url}: {str(e)}")
        return False


def get_bot_info():
    """Get info about the ManyChat bot/page to verify API key is working"""
    logging.info("Getting bot/page information")

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        logging.info(f"Testing endpoint: {API_ENDPOINT_GET_BOTINFO}")
        response = requests.get(API_ENDPOINT_GET_BOTINFO,
                                headers=headers, timeout=10)
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")

        if response.status_code == 200:
            try:
                # Parse the JSON response
                data = json.loads(response.text)
                if "data" in data:
                    page_name = data["data"].get("name", "Unknown Page")
                    page_id = data["data"].get("id", "Unknown ID")
                    logging.info(
                        f"Connected to ManyChat bot: {page_name} (ID: {page_id})")
                    return True
            except json.JSONDecodeError:
                logging.error(
                    "Failed to parse JSON response from get bot info")

        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error getting bot info: {str(e)}")
        return False


def list_subscribers():
    """List subscribers to get valid subscriber IDs"""
    logging.info(
        "Attempting to list subscribers - note: this may not work with your current API permissions")

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        url = "https://api.manychat.com/fb/subscribers"  # Try alternate endpoint
        logging.info(f"Testing alternative subscribers endpoint: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")

        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error listing subscribers: {str(e)}")
        return False


def get_available_custom_fields():
    """Get a list of available custom fields in the account"""
    logging.info("Getting list of available custom fields")

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        url = "https://api.manychat.com/fb/page/getCustomFields"
        logging.info(f"Testing custom fields endpoint: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")

        if response.status_code == 200:
            try:
                data = json.loads(response.text)
                if "data" in data:
                    fields = data["data"]
                    logging.info(
                        f"Found {len(fields)} custom fields in your account:")
                    for field in fields:
                        field_id = field.get("id", "Unknown")
                        field_name = field.get("name", "Unnamed")
                        field_type = field.get("type", "Unknown type")
                        logging.info(
                            f"  Field ID: {field_id}, Name: {field_name}, Type: {field_type}")
            except json.JSONDecodeError:
                logging.error(
                    "Failed to parse JSON response from custom fields")

        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error getting custom fields: {str(e)}")
        return False


if __name__ == "__main__":
    logging.info(
        "============================================================")
    logging.info("STARTING MANYCHAT FIELD UPDATE SCRIPT")
    logging.info(
        "============================================================")

    # First verify that the API key is working by getting bot info
    if get_bot_info():
        logging.info(
            "API key is valid - successfully retrieved bot information")

        # Try to get available custom fields to know what fields we can update
        if get_available_custom_fields():
            logging.info("Successfully retrieved custom fields")
        else:
            logging.warning(
                "Failed to get custom fields - check API permissions")

        # Try to list subscribers (though this might not work due to API permissions)
        if list_subscribers():
            logging.info("Successfully listed subscribers")
        else:
            logging.warning(
                "Failed to list subscribers - this is likely due to API permissions")
    else:
        logging.warning(
            "Failed to get bot information - API key may be invalid")

    # Try to get subscriber info to verify subscriber existence and see existing custom fields
    if try_get_subscriber():
        logging.info("Successfully retrieved subscriber information")

        # Now try updating fields
        time.sleep(1)  # Add a delay between requests

        # Try all methods to see which one works
        if update_subscriber_fields():
            logging.info(
                "Successfully updated subscriber fields using ID method")
        else:
            logging.warning(
                "Failed to update subscriber fields using ID method")

        time.sleep(1)  # Add a delay between requests

        if update_by_field_name():
            logging.info(
                "Successfully updated subscriber fields using name method")
        else:
            logging.warning(
                "Failed to update subscriber fields using name method")

        time.sleep(1)  # Add a delay between requests

        if update_subscriber_data():
            logging.info("Successfully updated subscriber profile data")
        else:
            logging.warning("Failed to update subscriber profile data")
    else:
        logging.warning(
            "Failed to retrieve subscriber information - subscriber ID is invalid or doesn't exist")

    logging.info(
        "============================================================")
    logging.info("FIELD UPDATE ATTEMPT COMPLETED")
    logging.info(
        "============================================================")
