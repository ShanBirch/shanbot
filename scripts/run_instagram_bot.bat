@echo off
echo Starting Instagram Bot at %date% %time%
cd /d "C:\Users\Shannon\OneDrive\Desktop\shanbot\scripts"
"C:\Users\Shannon\AppData\Local\Microsoft\WindowsApps\python.exe" followersbot.py --daily-limit 500
echo Instagram Bot finished at %date% %time% 