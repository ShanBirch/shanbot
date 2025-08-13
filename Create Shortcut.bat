@echo off
echo Creating shortcut to Social Media Video Enhancer on Desktop...

REM Get the current directory and the user's desktop folder
set "CURRENT_DIR=%~dp0"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"

REM Create a shortcut to run_enhancer.bat on the desktop using PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\Social Media Video Enhancer.lnk'); $Shortcut.TargetPath = '%CURRENT_DIR%run_enhancer.bat'; $Shortcut.Description = 'Create enhanced fitness videos for social media'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Save()"

echo Shortcut created successfully on your desktop!
echo.
echo You can now double-click "Social Media Video Enhancer" on your desktop to run the program.
echo.
pause 