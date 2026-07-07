#!/usr/bin/env python3
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import requests

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
service_id = "srv-d96i7cnavr4c739i4l6g"
deploy_id = "dep-d96i7d7avr4c739i4mc0"
headers = {"Authorization": f"Bearer {token}"}

print(f"Getting build logs for deployment: {deploy_id}\n")

# Get logs
url = f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/logs"
response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    print("Build Logs:")
    print("="*60)
    print(response.text)
else:
    print(f"Error: {response.text}")
