#!/usr/bin/env python3
"""
Complete Render Deployment via CLI
Creates service, sets all env vars, and deploys
"""

import sys
import io

# Fix emoji encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import re
import json
import time
import sys

def read_kite_config():
    """Read credentials from kite_config.py"""
    print("▶ Reading credentials from kite_config.py...")
    
    with open("kite_config.py", "r") as f:
        content = f.read()
    
    api_key = re.search(r'API_KEY\s*=\s*["\']([^"\']+)["\']', content).group(1)
    api_secret = re.search(r'API_SECRET\s*=\s*["\']([^"\']+)["\']', content).group(1)
    access_token = re.search(r'ACCESS_TOKEN\s*=\s*["\']([^"\']+)["\']', content).group(1)
    user_id = re.search(r'USER_ID\s*=\s*["\']([^"\']+)["\']', content).group(1)
    
    credentials = {
        "API_KEY": api_key,
        "API_SECRET": api_secret,
        "ACCESS_TOKEN": access_token,
        "USER_ID": user_id
    }
    
    print("✓ Credentials loaded")
    return credentials

def get_services(token):
    """Get all services"""
    url = "https://api.render.com/v1/services"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

def create_service(token, owner_id, credentials):
    """Create web service"""
    print("\n▶ Creating web service...")
    
    url = "https://api.render.com/v1/services"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "ai-trading-bot",
        "ownerId": owner_id,
        "type": "web_service",
        "repo": "https://github.com/rajprakashkumar/ai-trading-bot",
        "branch": "main",
        "serviceDetails": {
            "env": "docker"
        },
        "envVars": [
            {"key": "API_KEY", "value": credentials["API_KEY"]},
            {"key": "API_SECRET", "value": credentials["API_SECRET"]},
            {"key": "ACCESS_TOKEN", "value": credentials["ACCESS_TOKEN"]},
            {"key": "USER_ID", "value": credentials["USER_ID"]}
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        service = response.json()
        print(f"✓ Service created: {service.get('id')}")
        return service
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return None

def update_service_vars(token, service_id, credentials):
    """Update environment variables"""
    print(f"\n▶ Setting environment variables for service {service_id}...")
    
    url = f"https://api.render.com/v1/services/{service_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "envVars": [
            {"key": "API_KEY", "value": credentials["API_KEY"]},
            {"key": "API_SECRET", "value": credentials["API_SECRET"]},
            {"key": "ACCESS_TOKEN", "value": credentials["ACCESS_TOKEN"]},
            {"key": "USER_ID", "value": credentials["USER_ID"]}
        ]
    }
    
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✓ Environment variables set successfully")
        return True
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return False

def redeploy_service(token, service_id):
    """Redeploy service"""
    print(f"\n▶ Redeploying service...")
    
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json={}, headers=headers)
    
    if response.status_code in [200, 201]:
        deploy = response.json()
        print(f"✓ Deployment triggered: {deploy.get('id')}")
        return deploy
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return None

def get_service_url(token, service_id):
    """Get service URL"""
    url = f"https://api.render.com/v1/services/{service_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        service = response.json()
        return service.get("serviceUrl")
    return None

def wait_for_live(token, service_id, max_wait=300):
    """Wait for service to go live"""
    print(f"\n▶ Waiting for deployment to complete...")
    
    url = f"https://api.render.com/v1/services/{service_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    start = time.time()
    while time.time() - start < max_wait:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            service = response.json()
            status = service.get("status")
            print(f"  Status: {status}")
            
            if status == "live":
                return True
        
        time.sleep(5)
    
    print("✗ Timeout waiting for deployment")
    return False

def get_owner_id(token):
    """Get owner ID from /v1/owners endpoint"""
    print("▶ Getting owner information...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("https://api.render.com/v1/owners", headers=headers)
        if response.status_code == 200:
            owners = response.json()
            if owners and len(owners) > 0:
                owner_id = owners[0]["owner"]["id"]
                owner_name = owners[0]["owner"]["name"]
                print(f"✓ Owner: {owner_name}")
                print(f"✓ Owner ID: {owner_id}")
                return owner_id
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("✗ Could not determine owner ID")
    return None

def main():
    print("\n" + "="*60)
    print("RENDER DEPLOYMENT VIA CLI")
    print("="*60)
    
    # Use existing API token
    token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
    print(f"\n✓ Using Render API Token")
    
    # Read credentials
    credentials = read_kite_config()
    
    # Check existing services
    print("\n▶ Checking existing services...")
    services = get_services(token)
    existing = next((s for s in services if s.get("name") == "ai-trading-bot"), None)
    
    if existing:
        print(f"✓ Service already exists: {existing.get('id')}")
        service_id = existing.get('id')
        action = input("\nUpdate variables and redeploy? (y/n): ").strip().lower()
        
        if action == 'y':
            update_service_vars(token, service_id, credentials)
            redeploy_service(token, service_id)
    else:
        print("✗ Service not found. Creating new one...")
        
        # Get owner ID
        owner_id = get_owner_id(token)
        if not owner_id:
            return
        
        # Create service
        service = create_service(token, owner_id, credentials)
        if not service:
            return
        
        service_id = service.get('id')
    
    # Wait for deployment
    if wait_for_live(token, service_id):
        # Get URL
        url = get_service_url(token, service_id)
        
        print("\n" + "="*60)
        print("✓ DEPLOYMENT COMPLETE!")
        print("="*60)
        print(f"""
Your AI Trading Bot is now LIVE!

🌐 URL: {url}
📊 Dashboard: {url}/market-watch
🔗 API: {url}/api

Environment Variables Set:
  ✓ API_KEY
  ✓ API_SECRET
  ✓ ACCESS_TOKEN
  ✓ USER_ID

Next Steps:
1. Visit: {url}/market-watch
2. Search: "nifty july"
3. Check console (F12) for logs
4. Token will auto-refresh daily at 6 AM IST!

Token Refresh Testing:
- Open DevTools: F12
- Go to Console tab
- You'll see auto-refresh messages
- Holdings update every 15 seconds

Need to check logs?
- Go to: https://render.com/dashboard
- Select: ai-trading-bot
- Logs tab shows all activity
""")
    else:
        print("\n✗ Deployment timed out")
        print("Check Render dashboard for status: https://render.com/dashboard")

if __name__ == "__main__":
    main()
