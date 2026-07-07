import requests
import json

token = 'rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf'
headers = {'Authorization': f'Bearer {token}'}

r = requests.get('https://api.render.com/v1/services', headers=headers)
data = r.json()

print(f'\nTotal services: {len(data)}\n')

for item in data:
    s = item.get('service', {})
    print(f"Service: {s.get('name', 'Unknown')}")
    print(f"ID: {s.get('id', 'no-id')}")
    print(f"Status: {s.get('status', 'building')}")
    print(f"Created: {s.get('createdAt', 'unknown')}")
    print(f"Dashboard: {s.get('dashboardUrl', 'pending')}")
    
    # Wait a moment and check deployment status
    print(f"\nURL check in 5 seconds...")
    import time
    time.sleep(5)
    
    # Get updated status
    service_id = s.get('id')
    if service_id:
        url = f"https://api.render.com/v1/services/{service_id}"
        r2 = requests.get(url, headers=headers)
        if r2.status_code == 200:
            s2 = r2.json()
            print(f"Live URL: {s2.get('serviceUrl', 'building...')}")
    print()


