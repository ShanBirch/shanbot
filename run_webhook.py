import subprocess
import time
import os
import sys
from fastapi import FastAPI, Request
import uvicorn
import requests
import json
import traceback

app = FastAPI(title="ManyChat Webhook Receiver")

# ManyChat API settings
MANYCHAT_API_KEY = "996573:5b6dc180662de1be343655db562ee918"
MANYCHAT_API_URL = "https://api.manychat.com/fb"  # For Facebook
MANYCHAT_IG_API_URL = "https://api.manychat.com/instagram"  # For Instagram


@app.post("/webhook/manychat")
async def manychat_webhook(request: Request):
    """
    Endpoint to receive ManyChat webhook payloads.
    """
    try:
        # Parse the request body as JSON
        body = await request.json()
        print("Received webhook payload:", json.dumps(body, indent=2))

        # Try to extract the subscriber ID from the webhook payload
        subscriber_id = None
        if 'subscriber' in body and 'id' in body['subscriber']:
            subscriber_id = body['subscriber']['id']
        elif 'chat' in body and 'id' in body['chat']:
            subscriber_id = body['chat']['id']

        # Prepare hardcoded test values
        conversation_value = "Test conversation content"
        name_value = "Test name value"

        # If we have a subscriber ID, try to update fields via API
        if subscriber_id:
            print(f"Found subscriber ID: {subscriber_id}")
            try:
                # Update fields via API
                api_response = update_subscriber_fields(
                    subscriber_id,
                    {
                        "11944956": conversation_value,  # o1 Response
                        "11967919": name_value           # o1 Response 2
                    }
                )
                print("API response:", api_response)
            except Exception as e:
                print(f"Error updating fields: {str(e)}")
                traceback.print_exc()
        else:
            print("No subscriber ID found in webhook payload")

        # Always return a success response to prevent ManyChat from retrying
        return {
            "version": "v2",
            "content": {
                "messages": [
                    {
                        "type": "text",
                        "text": "Processing your request..."
                    }
                ],
                "actions": [
                    {
                        "action": "set_field_value",
                        "field_id": 11944956,  # o1 Response
                        "value": conversation_value
                    },
                    {
                        "action": "set_field_value",
                        "field_id": 11967919,  # o1 Response 2
                        "value": name_value
                    }
                ]
            }
        }

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        traceback.print_exc()
        # Return a basic success response to prevent retries
        return {
            "version": "v2",
            "content": {
                "messages": [
                    {
                        "type": "text",
                        "text": "Processing your request..."
                    }
                ]
            }
        }


def update_subscriber_fields(subscriber_id, field_values):
    """Update subscriber custom fields via ManyChat API"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MANYCHAT_API_KEY}"
    }

    # Prepare data for API call
    data = {
        "subscriber_id": subscriber_id,
        "fields": {}
    }

    # Add each field ID and value
    for field_id, value in field_values.items():
        data["fields"][field_id] = value

    print(f"Sending API request with data: {json.dumps(data, indent=2)}")

    # Try Instagram API first, then fallback to Facebook if that fails
    try:
        # Try Instagram endpoint
        print("Trying Instagram API...")
        response = requests.post(
            f"{MANYCHAT_IG_API_URL}/subscriber/setCustomFields",
            headers=headers,
            json=data,
            timeout=10
        )

        print(f"Instagram API response status: {response.status_code}")
        print(f"Instagram API response body: {response.text}")

        # Check response
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Instagram API failed with status {response.status_code}. Trying Facebook API...")

        # Try Facebook endpoint as fallback
        print("Trying Facebook API...")
        response = requests.post(
            f"{MANYCHAT_API_URL}/subscriber/setCustomFields",
            headers=headers,
            json=data,
            timeout=10
        )

        print(f"Facebook API response status: {response.status_code}")
        print(f"Facebook API response body: {response.text}")

        return response.json()
    except Exception as e:
        print(f"API request failed: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/")
async def root():
    """Simple health check endpoint"""
    return {"message": "Server is running. Send POST to /webhook/manychat"}


def run_ngrok():
    ngrok_path = r"C:\Users\Shannon\Downloads\ngrok-temp\ngrok.exe"

    # Start ngrok in a separate process
    print("Starting ngrok tunnel...")
    try:
        ngrok_process = subprocess.Popen(
            [ngrok_path, "http", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait a bit for ngrok to start
        time.sleep(5)

        # Display information to the user
        print("\n" + "="*60)
        print("Ngrok is running - your public URL will be visible in the ngrok interface")
        print("Use the URL shown in the ngrok terminal that ends with /webhook/manychat")
        print("For example: https://xxxx-xx-xx-xxx-xxx.ngrok-free.app/webhook/manychat")
        print("="*60 + "\n")

        # Return the process so it can be terminated later
        return ngrok_process
    except Exception as e:
        print(f"Error starting ngrok: {str(e)}")
        return None


if __name__ == "__main__":
    print("Starting ManyChat webhook server with Instagram and Facebook API integration...")

    # Start ngrok in a separate thread
    ngrok_process = run_ngrok()

    # Run the API server
    try:
        print("Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean up processes
        if ngrok_process:
            ngrok_process.terminate()
            print("Ngrok tunnel stopped")
