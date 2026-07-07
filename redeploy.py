#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import time

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
service_id = "srv-d96i7cnavr4c739i4l6g"
headers = {"Authorization": f"Bearer {token}"}

print("Triggering manual redeploy...")

url = f"https://api.render.com/v1/services/{service_id}/deploys"
response = requests.post(url, json={}, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code in [200, 201]:
    print("\n✓ Redeploy triggered!")
    print("\nMonitoring deployment...")
    
    for i in range(60):
        time.sleep(5)
        
        # Check deployment status
        deps_url = f"https://api.render.com/v1/services/{service_id}/deploys"
        deps_resp = requests.get(deps_url, headers=headers)
        
        if deps_resp.status_code == 200:
            deploys = deps_resp.json()
            if deploys:
                latest_deploy = deploys[0]['deploy']
                status = latest_deploy.get('status')
                print(f"[{i+1}/60] Status: {status}")
                
                if status == "live":
                    # Get service URL
                    svc_url = f"https://api.render.com/v1/services/{service_id}"
                    svc_resp = requests.get(svc_url, headers=headers)
                    if svc_resp.status_code == 200:
                        svc = svc_resp.json().get('service', {})
                        url = svc.get('serviceUrl')
                        print(f"\n✓ LIVE! URL: {url}")
                    break
else:
    print(f"✗ Error: {response.text}")
