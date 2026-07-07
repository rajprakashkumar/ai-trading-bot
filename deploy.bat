@echo off
setlocal enabledelayedexpansion

cd /d "c:\AI Trading bot"

set GIT_PATH="C:\Program Files\Git\bin\git.exe"

echo ============================================================
echo STEP 1: Initialize Git Repository
echo ============================================================

%GIT_PATH% init
%GIT_PATH% config user.email "rajprakashkumar@gmail.com"
%GIT_PATH% config user.name "prakash kumar"

echo.
echo ============================================================
echo STEP 2: Add and Commit Files
echo ============================================================

%GIT_PATH% add .
%GIT_PATH% commit -m "Initial commit - Ready for Render deployment"

echo.
echo ============================================================
echo STEP 3: Add Remote and Push
echo ============================================================

%GIT_PATH% remote add origin https://github.com/rajprakashkumar/ai-trading-bot.git
%GIT_PATH% branch -M main
%GIT_PATH% push -u origin main

echo.
echo ============================================================
echo DEPLOYMENT READY!
echo ============================================================
echo.
echo Your GitHub repo: https://github.com/rajprakashkumar/ai-trading-bot
echo.
echo Next steps:
echo 1. Go to https://render.com/dashboard
echo 2. Click: New + Web Service
echo 3. Select: https://github.com/rajprakashkumar/ai-trading-bot
echo 4. Configure:
echo    - Name: ai-trading-bot
echo    - Environment: Docker
echo    - Build Command: (leave empty)
echo    - Start Command: (leave empty)
echo 5. Click: Create Web Service
echo 6. Go to Settings - Environment
echo 7. Add environment variables:
echo    - API_KEY
echo    - API_SECRET
echo    - ACCESS_TOKEN
echo    - USER_ID
echo.
pause
