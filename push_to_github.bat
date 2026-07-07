@echo off
cd /d "c:\AI Trading bot"

setlocal enabledelayedexpansion
set GIT_PATH="C:\Program Files\Git\bin\git.exe"

if not exist %GIT_PATH% (
    echo Git not found at %GIT_PATH%
    exit /b 1
)

echo Initializing git repository...
%GIT_PATH% init

echo Setting git config...
%GIT_PATH% config user.email "rajprakashkumar@gmail.com"
%GIT_PATH% config user.name "prakash kumar"

echo Staging files...
%GIT_PATH% add .

echo Committing...
%GIT_PATH% commit -m "Initial commit - Ready for Render deployment"

echo Adding remote...
%GIT_PATH% remote add origin https://github.com/rajprakashkumar/ai-trading-bot.git

echo Renaming branch...
%GIT_PATH% branch -M main

echo Pushing to GitHub...
%GIT_PATH% push -u origin main

echo.
echo Done! Check GitHub: https://github.com/rajprakashkumar/ai-trading-bot
