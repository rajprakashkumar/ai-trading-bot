#!/usr/bin/env python3
"""
Deploy Flask app to Render.com
Handles: git init, GitHub repo creation, code push, Render service setup
"""

import os
import json
import subprocess
import sys
import webbrowser
import time

def run_cmd(cmd, description=""):
    """Run shell command and return output"""
    try:
        if description:
            print(f"\n▶ {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Error: {result.stderr}")
            return None
        print(f"✓ {result.stdout.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"✗ Exception: {e}")
        return None

def setup_github():
    """Setup GitHub repo and push code"""
    print("\n" + "="*60)
    print("STEP 1: Setup GitHub Repository")
    print("="*60)
    
    # Check if .git exists
    if os.path.exists(".git"):
        print("✓ Git repo already initialized")
    else:
        run_cmd("git init", "Initialize git repository")
        run_cmd("git config user.email 'rajprakashkumar@gmail.com'", "Set git email")
        run_cmd("git config user.name 'prakash kumar'", "Set git name")
    
    run_cmd("git add .", "Stage all files")
    run_cmd('git commit -m "Initial commit - Ready for Render deployment"', "Commit files")
    
    print("\n" + "-"*60)
    print("📝 MANUAL STEP - Create GitHub Repo:")
    print("-"*60)
    print("""
1. Go to https://github.com/new
2. Create repo named: ai-trading-bot
3. Select: Public
4. Click: Create Repository
5. Copy the HTTPS URL (like: https://github.com/YOUR_USERNAME/ai-trading-bot.git)
6. Paste it here:""")
    
    repo_url = input("\nEnter GitHub repo URL: ").strip()
    if not repo_url:
        print("✗ No URL provided")
        return None
    
    run_cmd(f"git remote add origin {repo_url}", "Add GitHub remote")
    run_cmd("git branch -M main", "Rename to main branch")
    run_cmd("git push -u origin main", "Push code to GitHub")
    
    return repo_url

def setup_render(repo_url):
    """Setup Render service"""
    print("\n" + "="*60)
    print("STEP 2: Setup Render Service")
    print("="*60)
    
    print("""
1. Go to https://render.com
2. Sign up with: rajprakashkumar@gmail.com
3. Click: New + > Web Service
4. Select: GitHub (if connected) or paste repo URL
5. Configure:
   - Name: ai-trading-bot
   - Environment: Docker
   - Build Command: (empty - Dockerfile handles it)
   - Start Command: (empty - Dockerfile has CMD)
6. Click: Create Web Service

After service is created:
7. Go to: Settings > Environment
8. Add variables:
   - API_KEY = <your_zerodha_api_key>
   - API_SECRET = <your_zerodha_api_secret>
   - ACCESS_TOKEN = <your_kite_access_token>
   - USER_ID = <your_zerodha_user_id>
9. Click: Save Changes
10. Service will auto-deploy!
""")
    
    # Open Render in browser
    response = input("\nOpen Render in browser now? (y/n): ").strip().lower()
    if response == 'y':
        webbrowser.open("https://render.com/dashboard")
        print("✓ Opening Render dashboard...")
        time.sleep(2)

def main():
    print("\n" + "="*60)
    print("RENDER DEPLOYMENT SCRIPT")
    print("="*60)
    
    os.chdir("c:\\AI Trading bot")
    
    # Step 1: GitHub
    repo_url = setup_github()
    if not repo_url:
        print("✗ GitHub setup failed")
        return
    
    # Step 2: Render
    setup_render(repo_url)
    
    print("\n" + "="*60)
    print("✓ DEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"""
Your GitHub repo: {repo_url}

Next steps:
1. Create Render account at https://render.com
2. Connect GitHub account to Render
3. Create Web Service from this repo
4. Add environment variables
5. Service will deploy automatically!

Your public URL will be: https://ai-trading-bot-xxxx.onrender.com
""")

if __name__ == "__main__":
    main()
