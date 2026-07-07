#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import re
import time

# Read credentials
with open("kite_config.py", "r") as f:
    content = f.read()

api_key = re.search(r'API_KEY\s*=\s*["\']([^"\']+)["\']', content).group(1)
api_secret = re.search(r'API_SECRET\s*=\s*["\']([^"\']+)["\']', content).group(1)
access_token = re.search(r'ACCESS_TOKEN\s*=\s*["\']([^"\']+)["\']', content).group(1)
user_id = re.search(r'USER_ID\s*=\s*["\']([^"\']+)["\']', content).group(1)

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
service_id = "srv-d96i7cnavr4c739i4l6g"
headers = {"Authorization": f"Bearer {token}"}

print("Updating service environment variables...")

# Update service with env vars
url = f"https://api.render.com/v1/services/{service_id}"
payload = {
    "envVars": [
        {"key": "API_KEY", "value": api_key},
        {"key": "API_SECRET", "value": api_secret},
        {"key": "ACCESS_TOKEN", "value": access_token},
        {"key": "USER_ID", "value": user_id}
    ]
}

response = requests.patch(url, json=payload, headers=headers)
print(f"Update Status: {response.status_code}")

if response.status_code == 200:
    print("✓ Environment variables updated!")
    
    print("\nTriggering redeploy...")
    deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"
    deploy_resp = requests.post(deploy_url, json={}, headers=headers)
    
    print(f"Deploy Status: {deploy_resp.status_code}")
    
    if deploy_resp.status_code == 201:
        print("✓ Redeploy triggered!")
        print("\nMonitoring...")
        
        for i in range(120):
            time.sleep(5)
            
            deps_url = f"https://api.render.com/v1/services/{service_id}/deploys"
            deps_resp = requests.get(deps_url, headers=headers)
            
            if deps_resp.status_code == 200:
                deploys = deps_resp.json()
                if deploys:
                    latest = deploys[0]['deploy']
                    status = latest.get('status')
                    print(f"[{i+1}/120] Status: {status}")
                    
                    if status == "live":
                        # Get service details
                        svc_url = f"https://api.render.com/v1/services/{service_id}"
                        svc_resp = requests.get(svc_url, headers=headers)
                        if svc_resp.status_code == 200:
                            svc = svc_resp.json().get('service', {})
                            print(f"\n{'='*60}")
                            print("SUCCESS! Service is LIVE!")
                            print(f"{'='*60}")
                            print(f"\nService URL: {svc.get('serviceUrl')}")
                            print(f"Dashboard URL: {svc.get('dashboardUrl')}")
                            print(f"\nVisit: {svc.get('serviceUrl')}/market-watch")
                        break
                    
                    elif status in ["update_failed", "build_failed"]:
                        print(f"\n✗ Deployment failed with status: {status}")
                        print("Try checking the Render dashboard for detailed error logs")
                        break
else:
    print(f"✗ Error updating env vars: {response.text}")
