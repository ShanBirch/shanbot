# This script installs NSSM (Non-Sucking Service Manager) and sets up your 
# webhook and ngrok as Windows services

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script needs to be run as Administrator. Please restart PowerShell as Administrator and try again."
    exit
}

# Define paths
$nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$nssmZip = "$env:TEMP\nssm.zip"
$nssmDir = "$env:ProgramFiles\nssm"

# Download and extract NSSM
if (-not (Test-Path $nssmDir)) {
    Write-Host "Downloading NSSM..."
    Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
    
    Write-Host "Extracting NSSM..."
    Expand-Archive -Path $nssmZip -DestinationPath "$env:TEMP\nssm" -Force
    
    # Find the win64 directory
    $nssmExeDir = Get-ChildItem -Path "$env:TEMP\nssm" -Recurse -Filter "win64" | Select-Object -First 1
    
    # Create the directory and copy files
    New-Item -ItemType Directory -Path $nssmDir -Force
    Copy-Item -Path "$($nssmExeDir.FullName)\*" -Destination $nssmDir -Recurse -Force
    
    # Clean up
    Remove-Item -Path $nssmZip -Force
    Remove-Item -Path "$env:TEMP\nssm" -Recurse -Force
}

# Add NSSM to PATH if not already there
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
if (-not $env:Path.Contains($nssmDir)) {
    Write-Host "Adding NSSM to PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$env:Path;$nssmDir", "Machine")
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

# Install webhook service
Write-Host "Installing webhook service..."
& "$nssmDir\nssm.exe" install "Shannon-Webhook" "python" "-m app.manychat_webhook_fixed"
& "$nssmDir\nssm.exe" set "Shannon-Webhook" AppDirectory "C:\Users\Shannon\OneDrive\Desktop\shanbot"
& "$nssmDir\nssm.exe" set "Shannon-Webhook" DisplayName "Shannon ManyChat Webhook"
& "$nssmDir\nssm.exe" set "Shannon-Webhook" Description "Shannon's ManyChat Webhook integration with Gemini AI"
& "$nssmDir\nssm.exe" set "Shannon-Webhook" AppStdout "C:\Users\Shannon\OneDrive\Desktop\shanbot\logs\webhook_stdout.log"
& "$nssmDir\nssm.exe" set "Shannon-Webhook" AppStderr "C:\Users\Shannon\OneDrive\Desktop\shanbot\logs\webhook_stderr.log"
& "$nssmDir\nssm.exe" set "Shannon-Webhook" AppRotateFiles 1
& "$nssmDir\nssm.exe" set "Shannon-Webhook" AppRotateBytes 10485760
& "$nssmDir\nssm.exe" set "Shannon-Webhook" AppRestartDelay 5000
& "$nssmDir\nssm.exe" set "Shannon-Webhook" Start SERVICE_AUTO_START

# Install ngrok service (adjust path if needed)
Write-Host "Installing ngrok service..."
& "$nssmDir\nssm.exe" install "Shannon-Ngrok" "C:\Users\Shannon\ngrok\ngrok.exe" "http 8000"
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" AppDirectory "C:\Users\Shannon\ngrok"
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" DisplayName "Shannon Ngrok Tunnel"
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" Description "Ngrok tunnel for Shannon's webhook service"
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" AppStdout "C:\Users\Shannon\OneDrive\Desktop\shanbot\logs\ngrok_stdout.log"
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" AppStderr "C:\Users\Shannon\OneDrive\Desktop\shanbot\logs\ngrok_stderr.log"
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" AppRotateFiles 1
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" AppRotateBytes 10485760
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" AppRestartDelay 5000
& "$nssmDir\nssm.exe" set "Shannon-Ngrok" Start SERVICE_AUTO_START

# Create logs directory if it doesn't exist
if (-not (Test-Path "C:\Users\Shannon\OneDrive\Desktop\shanbot\logs")) {
    New-Item -ItemType Directory -Path "C:\Users\Shannon\OneDrive\Desktop\shanbot\logs" -Force
}

# Start the services
Write-Host "Starting services..."
Start-Service -Name "Shannon-Webhook"
Start-Service -Name "Shannon-Ngrok"

Write-Host "Services installed and started successfully."
Write-Host "You can manage them in the Windows Services console (services.msc)" 