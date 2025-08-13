@echo off
echo Running path verification script and saving output to verification_results.txt
python verify_paths.py > verification_results.txt
echo Done. Results saved to verification_results.txt
echo.
echo Press any key to exit...
pause > nul 