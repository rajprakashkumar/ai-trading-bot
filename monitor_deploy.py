#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import time

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
service_id = "srv-d96i7cnavr4c739i4l6g"
headers = {"Authorization": f"Bearer {token}"}

print("Monitoring deployment...\n")

for i in range(120):
    resp = requests.get(f"https://api.render.com/v1/services/{service_id}/deploys", headers=headers)
    
    if resp.status_code == 200:
        deploys = resp.json()
        if deploys:
            latest = deploys[0]['deploy']
            status = latest.get('status')
            print(f"[{i+1}/120] Status: {status}")
            
            if status == "live":
                svc_resp = requests.get(f"https://api.render.com/v1/services/{service_id}", headers=headers)
                if svc_resp.status_code == 200:
                    svc = svc_resp.json().get('service', {})
                    print(f"\n{'='*60}")
                    print("✅ SUCCESS! Service is LIVE!")
                    print(f"{'='*60}")
                    print(f"URL: {svc.get('serviceUrl')}")
                    print(f"Visit: {svc.get('serviceUrl')}/market-watch")
                break
            
            elif status in ["update_failed", "build_failed"]:
                print(f"\n❌ Deployment failed: {status}")
                print(f"Commit: {latest['commit']['message']}")
                break
    
    time.sleep(5)

print("\nDone.")
