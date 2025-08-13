$Action = New-ScheduledTaskAction -Execute "C:\Users\Shannon\OneDrive\Desktop\shanbot\run_followup_manager.bat"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 60)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

$Task = Register-ScheduledTask -TaskName "Instagram Follow-up Manager" `
                             -Action $Action `
                             -Trigger $Trigger `
                             -Settings $Settings `
                             -Description "Runs the Instagram follow-up manager every hour" `
                             -RunLevel Highest

Write-Host "Task created successfully. You can find it in Task Scheduler under 'Instagram Follow-up Manager'" 