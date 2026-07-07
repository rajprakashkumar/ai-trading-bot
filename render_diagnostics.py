#!/usr/bin/env python3
"""
Render API Diagnostics - Find owner ID
"""

import requests
import json

token = "rnd_RrYgnJeD7xhXLyASjEUFsT9xx3nf"
headers = {"Authorization": f"Bearer {token}"}

print("\n" + "="*60)
print("RENDER API DIAGNOSTICS")
print("="*60)

# Test different endpoints
endpoints = [
    ("GET", "https://api.render.com/v1", "Root"),
    ("GET", "https://api.render.com/v1/", "Root with slash"),
    ("GET", "https://api.render.com/v1/owners", "Owners"),
    ("GET", "https://api.render.com/v1/owner", "Owner singular"),
    ("GET", "https://api.render.com/v1/teams", "Teams"),
    ("GET", "https://api.render.com/v1/user", "User"),
    ("GET", "https://api.render.com/v1/account", "Account"),
    ("GET", "https://api.render.com/v1/profile", "Profile"),
    ("GET", "https://api.render.com/v1/me", "Me"),
]

for method, url, label in endpoints:
    print(f"\n▶ Testing: {label}")
    print(f"  URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code < 400:
            try:
                data = response.json()
                # Pretty print first 500 chars
                json_str = json.dumps(data, indent=2)
                print(f"  Response:\n{json_str[:500]}")
                
                # Try to find owner/id fields
                if isinstance(data, dict):
                    if "id" in data:
                        print(f"\n  ✓ FOUND ID: {data['id']}")
                    if "ownerId" in data:
                        print(f"  ✓ FOUND OWNERID: {data['ownerId']}")
                    # Check nested
                    for key, value in data.items():
                        if key == "owner" and isinstance(value, dict) and "id" in value:
                            print(f"  ✓ FOUND OWNER.ID: {value['id']}")
                elif isinstance(data, list) and len(data) > 0:
                    print(f"  ✓ Got list with {len(data)} items")
                    if isinstance(data[0], dict):
                        print(f"  First item keys: {list(data[0].keys())[:5]}")
                        if "id" in data[0]:
                            print(f"  ✓ FOUND ID in first item: {data[0]['id']}")
            except:
                print(f"  Response: {response.text[:200]}")
        else:
            print(f"  Error: {response.text[:200]}")
    
    except Exception as e:
        print(f"  Exception: {e}")

print("\n" + "="*60)
print("SEARCHING FOR PATTERNS...")
print("="*60)

# Try to find services and extract owner info from them
print("\n▶ Getting services to find owner pattern...")
response = requests.get("https://api.render.com/v1/services", headers=headers)
if response.status_code == 200:
    services = response.json()
    print(f"✓ Got {len(services)} service(s)")
    if services:
        first_service = services[0]
        print(f"\nFirst service keys: {list(first_service.keys())}")
        print(f"Service data:\n{json.dumps(first_service, indent=2)[:800]}")
        
        # Look for owner-related fields
        for key in first_service:
            if "owner" in key.lower() or "id" in key.lower():
                print(f"\n✓ POTENTIAL OWNER FIELD: {key} = {first_service[key]}")

print("\n" + "="*60)
