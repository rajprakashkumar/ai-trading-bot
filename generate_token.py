#!/usr/bin/env python
"""
Zerodha Kite Access Token Generator
This script helps you get an access token from your API Key and Secret.
"""

from kiteconnect import KiteConnect
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs

# Import your config
from kite_config import API_KEY, API_SECRET

print("=" * 60)
print("🔐 Zerodha Kite Access Token Generator")
print("=" * 60)
print()

# Step 1: Create Kite instance
kite = KiteConnect(api_key=API_KEY)

# Step 2: Generate login URL
login_url = kite.login_url()
print(f"📱 Opening login URL...")
print(f"🔗 URL: {login_url}")
print()
print("A browser window should open. Please:")
print("1. Log in with your Zerodha credentials")
print("2. Enter your PIN/TOTP if prompted")
print("3. You'll be redirected - copy the URL from your browser")
print()

# Try to open in browser
try:
    webbrowser.open(login_url)
    print("✅ Browser opened automatically")
except:
    print("⚠️  Couldn't open browser. Please visit the URL above manually.")

print()

# Step 3: Get request token from user
request_token = input("📋 Enter the REQUEST_TOKEN (from redirect URL parameter): ").strip()

if not request_token:
    print("❌ Request token is required!")
    exit(1)

print()
print("🔄 Exchanging request token for access token...")

try:
    # Step 4: Get access token
    session = kite.generate_session(request_token, api_secret=API_SECRET)
    
    access_token = session.get('access_token')
    user_id = session.get('user_id')
    
    if access_token:
        print()
        print("=" * 60)
        print("✅ SUCCESS! Access token generated!")
        print("=" * 60)
        print()
        print("📝 Update your kite_config.py with:")
        print()
        print(f'ACCESS_TOKEN = "{access_token}"')
        print(f'USER_ID = "{user_id}"')
        print()
        print("Then restart the Flask server!")
        print()
        print("=" * 60)
        
        # Option to auto-update config
        try:
            update = input("Would you like me to update kite_config.py automatically? (y/n): ").strip().lower()
            if update == 'y':
                with open('kite_config.py', 'r') as f:
                    content = f.read()
                
                content = content.replace(
                    'ACCESS_TOKEN = "get_token_using_generate_token.py"',
                    f'ACCESS_TOKEN = "{access_token}"'
                )
                content = content.replace(
                    'USER_ID = "your_user_id_here"',
                    f'USER_ID = "{user_id}"'
                )
                
                with open('kite_config.py', 'w') as f:
                    f.write(content)
                
                print("✅ kite_config.py updated successfully!")
                print()
                print("🚀 The Flask server should auto-reload now.")
                print("   Go to http://localhost:5000 to see your real holdings!")
        except Exception as e:
            print(f"❌ Couldn't auto-update: {e}")
            print("Please update manually.")
    else:
        print("❌ No access token received. Please try again.")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Troubleshooting:")
    print("1. Make sure your request_token is correct")
    print("2. Check your API Key and Secret in kite_config.py")
    print("3. Request tokens expire after 10 minutes")
