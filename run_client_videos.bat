@echo off
echo Running setup for client folders...
python setup_client_folders.py

echo.
echo Generating videos for all clients...
python simple_blue_video_client_folders.py --all

echo.
echo Videos have been generated in each client's folder.
echo Look for the videos in: C:\Users\Shannon\OneDrive\Desktop\shanbot\clients\[CLIENT_NAME]\weekly_checkin.mp4
echo.
pause 