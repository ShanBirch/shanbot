# Script to test the webhook endpoint
# This sends a webhook simulating an Instagram DM to the FastAPI application

# Set up API key
$apiKey = "webhook_integration_api_key_123"

# Set up headers
$headers = @{
    'x-api-key'    = $apiKey
    'Content-Type' = 'application/json'
}

# Get current date and time
$currentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Set up body for an Instagram DM webhook
$body = @{
    trigger_type = "instagram_dm"
    subscriber   = @{
        id            = "459582207"  # Real subscriber ID
        first_name    = "Test User"
        custom_fields = @{
            "General Chat" = $true
            "CONVERSATION" = "Test User: Hi Shannon, I'm interested in getting fit this year!"
        }
    }
    conversation = @{
        message = "Hi Shannon, I'm interested in getting fit this year!"
    }
} | ConvertTo-Json -Depth 5

# Send request to ngrok URL
Invoke-WebRequest -Uri "https://0200-194-223-45-155.ngrok-free.app/" -Method Post -Headers $headers -Body $body 