@echo off
echo Running check-in script to collect data for last week...
python checkin_lastweek.py

echo.
echo Organizing data files into client folders...
python organize_data_files.py

echo.
echo Now generating videos with the collected data...
python simple_blue_video_client_folders.py --all

echo.
echo Process complete! Videos have been saved to client folders.
echo Look for the videos in: C:\Users\Shannon\OneDrive\Desktop\shanbot\clients\[CLIENT_NAME]\weekly_checkin.mp4
echo.
pause 