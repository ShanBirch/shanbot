@echo off
echo 🚀 DUAL-MODE SMART LEAD FINDER
echo ================================
echo 🌱 ONLINE MODE: cocos_connected (Vegan clients)
echo 🏠 LOCAL MODE: cocos_pt_studio (Bayside gym clients)
echo 🔄 Both running in HEADLESS mode (no browser windows)
echo 📊 Daily limit: 75 follows per account (150 total)
echo ================================
echo.
echo Starting dual-mode lead finder...
python dual_mode_smart_finder.py --mode dual
echo.
echo Script completed. Press any key to close...
pause > nul 