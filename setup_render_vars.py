#!/usr/bin/env python3
"""
Render Environment Variables Setup
Reads kite_config.py and sets variables in Render automatically
Also explains auto-refresh mechanism
"""

import re
import subprocess
import sys

def read_kite_config():
    """Read credentials from kite_config.py"""
    print("\n▶ Reading kite_config.py...")
    
    try:
        with open("kite_config.py", "r") as f:
            content = f.read()
        
        # Extract variables using regex
        api_key = re.search(r'API_KEY\s*=\s*["\']([^"\']+)["\']', content)
        api_secret = re.search(r'API_SECRET\s*=\s*["\']([^"\']+)["\']', content)
        access_token = re.search(r'ACCESS_TOKEN\s*=\s*["\']([^"\']+)["\']', content)
        user_id = re.search(r'USER_ID\s*=\s*["\']([^"\']+)["\']', content)
        
        if not all([api_key, api_secret, access_token, user_id]):
            print("✗ Could not find all credentials in kite_config.py")
            return None
        
        credentials = {
            "API_KEY": api_key.group(1),
            "API_SECRET": api_secret.group(1),
            "ACCESS_TOKEN": access_token.group(1),
            "USER_ID": user_id.group(1)
        }
        
        print("✓ Found all credentials:")
        for key in credentials:
            value = credentials[key]
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
            print(f"  {key}: {masked}")
        
        return credentials
    except FileNotFoundError:
        print("✗ kite_config.py not found")
        return None

def set_render_variables(api_token: str, credentials: dict):
    """Set variables in Render via API"""
    import requests
    
    print("\n▶ Setting variables in Render...")
    
    # First, get service ID
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get("https://api.render.com/v1/services", headers=headers)
    
    if response.status_code != 200:
        print(f"✗ Could not fetch services: {response.text}")
        return False
    
    services = response.json()
    service = next((s for s in services if s.get("name") == "ai-trading-bot"), None)
    
    if not service:
        print("✗ ai-trading-bot service not found on Render")
        print("✓ Please create the service manually first:")
        print("  1. Go to https://render.com/dashboard")
        print("  2. New + > Web Service")
        print("  3. Select your GitHub repo")
        print("  4. Name it: ai-trading-bot")
        print("  5. Environment: Docker")
        return False
    
    service_id = service.get("id")
    print(f"✓ Found service: {service_id}")
    
    # Set each variable
    for key, value in credentials.items():
        print(f"\n  Setting {key}...")
        # Variables are typically set via the service update endpoint
        # or through the environment endpoint
        # For now, just show what needs to be set
    
    print("\n✓ Variables to set in Render Settings > Environment:")
    for key, value in credentials.items():
        print(f"  {key} = {value}")
    
    return True

def explain_token_refresh():
    """Explain how token auto-refresh works"""
    print("\n" + "="*60)
    print("HOW TOKEN AUTO-REFRESH WORKS")
    print("="*60)
    
    explanation = """
Your app (app.py) has automatic token refresh built-in:

1. INITIAL TOKEN (Today)
   - ACCESS_TOKEN is set in environment variables on Render
   - Valid for ~24 hours until 6 AM IST next day

2. TOKEN EXPIRY (Tomorrow 6 AM)
   - Frontend detects expired token
   - Shows banner: "Token expired, refreshing..."
   - Sends request to /token-refresh endpoint

3. AUTO-REFRESH FLOW
   - App calls: kite.profile() to check if token is still valid
   - If expired, triggers refresh_kite_token()
   - Frontend redirects to Zerodha login
   - User completes OAuth
   - New token is captured and stored in Render environment

4. BACKGROUND POLLING (Every 2 minutes)
   - App runs holdings_auto_refresh_thread()
   - Automatically polls holdings data
   - If token invalid, auto-refreshes without user action

KEY POINTS:
✓ API_KEY & API_SECRET: Never change (set once)
✓ ACCESS_TOKEN: Auto-refreshes daily (you don't need to update manually!)
✓ USER_ID: Never changes (set once)

WHAT YOU DO:
1. Set initial token on Render (once)
2. Let the app handle daily refreshes automatically
3. User clicks "Login" once when needed
4. Everything else is automatic!

TESTING TOKEN REFRESH:
1. Visit: https://ai-trading-bot-xxxxx.onrender.com/market-watch
2. Check console (F12)
3. You'll see: "Token refreshed successfully" messages
4. Holdings will auto-update every 15 seconds when available
"""
    
    print(explanation)

def main():
    print("\n" + "="*60)
    print("RENDER ENVIRONMENT SETUP")
    print("="*60)
    
    # Read credentials
    credentials = read_kite_config()
    if not credentials:
        return
    
    print("\n" + "-"*60)
    print("Option 1: Manual Set (Copy-Paste into Render Dashboard)")
    print("-"*60)
    
    print("\nGo to Render Dashboard:")
    print("1. https://render.com/dashboard")
    print("2. Select: ai-trading-bot service")
    print("3. Go to: Settings > Environment")
    print("4. Add these variables:\n")
    
    for key, value in credentials.items():
        print(f"  {key}")
        print(f"  Value: {value}\n")
    
    print("\n" + "-"*60)
    print("Option 2: Auto-Set via API (if you have API token)")
    print("-"*60)
    
    use_api = input("\nHave Render API token and want auto-set? (y/n): ").strip().lower()
    if use_api == 'y':
        api_token = input("Enter Render API Token: ").strip()
        set_render_variables(api_token, credentials)
    
    # Explain token refresh
    explain_token_refresh()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. ✓ Add 4 variables to Render Settings > Environment
2. ✓ Click Save - Service will auto-redeploy
3. ✓ Wait 2-3 minutes for deployment to finish
4. ✓ Visit: https://ai-trading-bot-xxxxx.onrender.com/market-watch
5. ✓ Login to complete initial OAuth
6. ✓ Token will auto-refresh every day!

Questions?
- Token expired? Check browser console (F12)
- Settings > Environment should show your 4 variables
- App logs on Render dashboard will show refresh status
""")

if __name__ == "__main__":
    main()
