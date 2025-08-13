$headers = @{
    'x-api-key'    = 'webhook_integration_api_key_123'
    'Content-Type' = 'application/json'
}

$body = @{
    subscriber_id = 'test_user_123'
    field_id      = '11944956'
    field_value   = 'Test field update at ' + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json

Invoke-WebRequest -Uri https://0200-194-223-45-155.ngrok-free.app/test_field_update -Method Post -Headers $headers -Body $body 