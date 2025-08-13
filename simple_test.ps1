# Script to test the field update endpoint with a real subscriber
# This sends a request to update a field for a real subscriber

# Set the API key and headers for the request
$headers = @{
    'x-api-key'    = 'webhook_integration_api_key_123'
    'Content-Type' = 'application/json'
}

# Get current date and time
$currentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Create the request body with the real subscriber ID
$body = @{
    subscriber_id = "459582207"  # Real subscriber ID
    field_id      = "11944956"  # Field ID for o1 response
    field_value   = "Test field update at $currentTime - Real subscriber test"
} | ConvertTo-Json

# Display the headers and body for debugging
Write-Output "Headers:"
$headers | ConvertTo-Json
Write-Output "Body:"
$body

try {
    # Send the request to the field update endpoint using ngrok URL
    $response = Invoke-WebRequest -Uri "https://0200-194-223-45-155.ngrok-free.app/test_field_update" -Method Post -Headers $headers -Body $body
    
    # Display the response status code and content
    Write-Output "StatusCode: $($response.StatusCode)"
    Write-Output "Content: $($response.Content)"
}
catch {
    # Display any errors
    Write-Output "Error:"
    Write-Output $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Output $responseBody
        $reader.Close()
    }
} 