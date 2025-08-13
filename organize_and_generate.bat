@echo off
echo =====================================================
echo STEP 1: Organizing data files into client folders...
echo =====================================================
python organize_data_files.py

echo.
echo =====================================================
echo STEP 2: Generating videos for all clients...
echo =====================================================
python simple_blue_video_client_folders.py --all

echo.
echo =====================================================
echo PROCESS COMPLETE!
echo =====================================================
echo.
echo Your client videos have been created and saved to:
echo C:\Users\Shannon\OneDrive\Desktop\shanbot\clients\[CLIENT_NAME]\weekly_checkin.mp4
echo.
echo All data files have been preserved in:
echo C:\Users\Shannon\OneDrive\Desktop\shanbot\clients\[CLIENT_NAME]\data\
echo.
pause 