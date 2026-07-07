@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Zerodha Holdings Dashboard API...
python app.py

pause
