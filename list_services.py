#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
headers = {"Authorization": f"Bearer {token}"}

print("Checking all services...")
response = requests.get("https://api.render.com/v1/services", headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"Found {len(data)} service(s):\n")
    
    for item in data:
        svc = item.get('service', {})
        print(f"Name: {svc.get('name')}")
        print(f"ID: {svc.get('id')}")
        print(f"Type: {svc.get('type')}")
        print(f"Status: {svc.get('status')}")
        print(f"URL: {svc.get('serviceUrl')}")
        print(f"Dashboard: {svc.get('dashboardUrl')}")
        print(f"Created: {svc.get('createdAt')}")
        
        # Check for deployments
        print(f"\nFull service data keys:")
        print(list(svc.keys())[:10])
        print("-" * 60)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
