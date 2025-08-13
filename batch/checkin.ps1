# PowerShell script for fitness check-in
Write-Host "Running fitness check-in for Shannon Birch..." -ForegroundColor Green

# Run the Python script directly
python "$env:USERPROFILE\OneDrive\Desktop\run_video.py"

Write-Host "Done!" -ForegroundColor Green
Pause 