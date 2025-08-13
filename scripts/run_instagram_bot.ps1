# PowerShell script to run the Instagram Bot with logging
$ScriptPath = "C:\Users\Shannon\OneDrive\Desktop\shanbot\scripts"
$LogFile = "$ScriptPath\instagram_bot_schedule_log.txt"

# Get current timestamp for logging
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Navigate to script directory
Set-Location -Path $ScriptPath

# Add timestamp to log
Add-Content -Path $LogFile -Value "[$Timestamp] Starting Instagram Bot scheduled run..."

try {
    # Start the Python script
    Write-Output "Starting Instagram Bot..."
    Add-Content -Path $LogFile -Value "[$Timestamp] Launching Python script..."
    
    # Run the Python script and capture output
    $output = & python story1.py 2>&1
    
    # Log the output
    Add-Content -Path $LogFile -Value "[$Timestamp] Script output:"
    Add-Content -Path $LogFile -Value $output
    
    # Log completion
    $EndTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "[$EndTimestamp] Instagram Bot run completed successfully."
    Write-Output "Instagram Bot run completed. See $LogFile for details."
}
catch {
    # Log errors
    $ErrorTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "[$ErrorTimestamp] ERROR: $($_.Exception.Message)"
    Write-Output "An error occurred. See $LogFile for details."
}
