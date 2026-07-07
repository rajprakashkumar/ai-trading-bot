#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
service_id = "srv-d96i7cnavr4c739i4l6g"
headers = {"Authorization": f"Bearer {token}"}

print(f"Checking deployments for service: {service_id}\n")

# Get deployments
url = f"https://api.render.com/v1/services/{service_id}/deploys"
response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response:\n{response.text[:1500]}")

if response.status_code == 200:
    deploys = response.json()
    print(f"\n\nDeployments:\n")
    
    if isinstance(deploys, list) and len(deploys) > 0:
        for deploy in deploys[:1]:  # First deployment
            print(json.dumps(deploy, indent=2)[:500])
