#!/usr/bin/env python3
"""
Check Render deployment status
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import time

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
service_id = "srv-d96i7cnavr4c739i4l6g"

headers = {"Authorization": f"Bearer {token}"}
url = f"https://api.render.com/v1/services/{service_id}"

print("\n" + "="*60)
print("RENDER DEPLOYMENT STATUS")
print("="*60)

for i in range(60):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        service = response.json()
        status = service.get("status")
        service_url = service.get("serviceUrl")
        
        print(f"\n[{i+1}/60] Status: {status}")
        if service_url:
            print(f"       URL: {service_url}")
        
        if status == "live":
            print("\n" + "="*60)
            print("SUCCESS! Service is LIVE!")
            print("="*60)
            print(f"\nPublic URL: {service_url}")
            print(f"Dashboard:  {service.get('dashboardUrl', 'N/A')}")
            print("\nYour app is ready!")
            print(f"Visit: {service_url}/market-watch")
            break
        
        elif status == "build_failed":
            print("\nBuild Failed! Checking logs...")
            # Try to get build logs
            print(f"Check dashboard: https://dashboard.render.com/web/{service_id}")
            break
    
    time.sleep(5)

print("\n" + "="*60)
