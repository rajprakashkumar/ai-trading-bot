#!/usr/bin/env python3
"""
Render.com Deployment via CLI using Render API
"""

import requests
import json
import time
import sys
from typing import Optional

class RenderDeployer:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def list_services(self):
        """List all deployed services"""
        print("\n▶ Fetching your Render services...")
        response = requests.get(f"{self.base_url}/services", headers=self.headers)
        
        if response.status_code != 200:
            print(f"✗ Error: {response.text}")
            return []
        
        services = response.json()
        print(f"✓ Found {len(services)} service(s):")
        for svc in services:
            print(f"  - {svc.get('name', 'Unknown')}: {svc.get('status', 'unknown')}")
        
        return services
    
    def get_owner_id(self):
        """Get authenticated user's owner ID"""
        print("\n▶ Getting your account info...")
        response = requests.get(f"{self.base_url}/account", headers=self.headers)
        
        if response.status_code != 200:
            print(f"✗ Error fetching account: {response.text}")
            return None
        
        account = response.json()
        owner_id = account.get("id")
        print(f"✓ Owner ID: {owner_id}")
        return owner_id
    
    def create_web_service(self, name: str, repo_url: str, env_vars: dict, owner_id: str):
        """Create a new web service"""
        print(f"\n▶ Creating web service: {name}")
        
        payload = {
            "name": name,
            "ownerId": owner_id,
            "type": "web_service",
            "environmentId": "docker",
            "repo": repo_url,
            "branch": "main",
            "buildCommand": "",
            "startCommand": "",
            "envVars": [
                {"key": k, "value": v} for k, v in env_vars.items()
            ],
            "plan": "free"
        }
        
        response = requests.post(
            f"{self.base_url}/services",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            print(f"✗ Error: {response.text}")
            return None
        
        service = response.json()
        print(f"✓ Service created: {service.get('id')}")
        return service
    
    def deploy(self, service_id: str):
        """Trigger deployment"""
        print(f"\n▶ Triggering deployment for service: {service_id}")
        
        response = requests.post(
            f"{self.base_url}/services/{service_id}/deploys",
            headers=self.headers
        )
        
        if response.status_code not in [200, 201]:
            print(f"✗ Error: {response.text}")
            return None
        
        deploy = response.json()
        print(f"✓ Deployment triggered: {deploy.get('id')}")
        return deploy
    
    def get_service_status(self, service_id: str):
        """Get service deployment status"""
        response = requests.get(
            f"{self.base_url}/services/{service_id}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            return None
        
        service = response.json()
        return {
            "status": service.get("status"),
            "url": service.get("serviceUrl"),
            "name": service.get("name")
        }

def main():
    print("\n" + "="*60)
    print("RENDER CLI DEPLOYMENT")
    print("="*60)
    
    print("\nOption 1: Use API Token (Auto-Deploy)")
    print("Option 2: Check Existing Services")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    
    if choice == "2":
        token = input("Enter your Render API Token: ").strip()
        deployer = RenderDeployer(token)
        services = deployer.list_services()
        
        if services:
            print("\n✓ Services found. Check Render dashboard for status:")
            print("  https://render.com/dashboard")
        else:
            print("\n✗ No services found. Create one via web UI.")
        return
    
    # Option 1: Full deployment
    token = input("Enter your Render API Token: ").strip()
    
    print("\n" + "-"*60)
    print("Service Configuration")
    print("-"*60)
    
    name = input("Service name (default: ai-trading-bot): ").strip() or "ai-trading-bot"
    repo = input("GitHub repo URL: ").strip() or "https://github.com/rajprakashkumar/ai-trading-bot"
    
    print("\nEnvironment Variables (press Enter to skip):")
    env_vars = {}
    for var in ["API_KEY", "API_SECRET", "ACCESS_TOKEN", "USER_ID"]:
        value = input(f"  {var} = ").strip()
        if value:
            env_vars[var] = value
    
    # Deploy
    deployer = RenderDeployer(token)
    
    owner_id = deployer.get_owner_id()
    if not owner_id:
        print("✗ Could not get owner ID. Check your API token.")
        return
    
    print("\n" + "="*60)
    print("DEPLOYING...")
    print("="*60)
    
    service = deployer.create_web_service(name, repo, env_vars, owner_id)
    
    if service:
        service_id = service.get("id")
        
        # Optional: trigger deploy
        deploy_now = input("\nTrigger deployment now? (y/n): ").strip().lower()
        if deploy_now == 'y':
            deployer.deploy(service_id)
            
            # Check status
            print("\n▶ Checking deployment status...")
            for i in range(30):
                time.sleep(2)
                status = deployer.get_service_status(service_id)
                if status:
                    print(f"  Status: {status['status']} | URL: {status.get('url', 'pending...')}")
                    if status['status'] == 'live':
                        print(f"\n✓ LIVE: {status['url']}")
                        break
        else:
            print(f"\n✓ Service created. Check dashboard: https://render.com/dashboard")

if __name__ == "__main__":
    main()
