#!/usr/bin/env python3
"""
Quick test script to verify 1NCE API credentials.
Run this before starting the full FastAPI service.
"""

import requests
import sys
import os
from datetime import datetime

# Get credentials from environment or prompt
USERNAME = os.getenv("ONCE_USERNAME")
PASSWORD = os.getenv("ONCE_PASSWORD")

if not USERNAME or not PASSWORD:
    print("Error: Please set ONCE_USERNAME and ONCE_PASSWORD environment variables")
    print("\nExample:")
    print("  export ONCE_USERNAME='your_username'")
    print("  export ONCE_PASSWORD='your_password'")
    sys.exit(1)

TOKEN_URL = "https://api.1nce.com/management-api/oauth/token"
BASE_URL = "https://api.1nce.com/management-api/v1"

print("=" * 60)
print("1NCE API Credential Test")
print("=" * 60)
print(f"\nUsername: {USERNAME}")
print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n" + "=" * 60)

# Step 1: Test Authentication
print("\n[1/3] Testing authentication...")
try:
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "password",
            "username": USERNAME,
            "password": PASSWORD
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Authentication successful!")
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")
        
        print(f"   Token expires in: {expires_in} seconds ({expires_in/3600:.1f} hours)")
        
        # Try to extract organization ID
        org_id = None
        if "organisation" in token_data:
            org_id = token_data["organisation"].get("id")
        elif "organization" in token_data:
            org_id = token_data["organization"].get("id")
        
        if org_id:
            print(f"   Organization ID: {org_id}")
        else:
            print("   Organization ID: Not found in token (you may need to provide it manually)")
        
    else:
        print(f"❌ Authentication failed!")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error during authentication: {e}")
    sys.exit(1)

# Step 2: Test SIM List API
print("\n[2/3] Testing SIM list API...")
try:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    # Try with org_id if we have it, otherwise try without
    if org_id:
        url = f"{BASE_URL}/sims?organisationId={org_id}&page=1&pageSize=10"
    else:
        url = f"{BASE_URL}/sims?page=1&pageSize=10"
    
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        print("✅ SIM list API accessible!")
        data = response.json()
        
        total_items = data.get("totalItems", 0)
        items = data.get("items", [])
        
        print(f"   Total SIMs: {total_items}")
        print(f"   Returned in this page: {len(items)}")
        
        if items and len(items) > 0:
            print(f"   Sample SIM ICCID: {items[0].get('iccid', 'N/A')}")
            
    elif response.status_code == 401:
        print("❌ Unauthorized - token may be invalid")
        print(f"   Response: {response.text}")
    else:
        print(f"⚠️  SIM list request returned status {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error fetching SIM list: {e}")

# Step 3: Test Usage API
print("\n[3/3] Testing usage data API...")
try:
    from datetime import timedelta
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    if org_id:
        url = f"{BASE_URL}/integrate/usage/data-volume?organisationId={org_id}&startDate={start_date}&endDate={end_date}&grouping=daily"
    else:
        url = f"{BASE_URL}/integrate/usage/data-volume?startDate={start_date}&endDate={end_date}&grouping=daily"
    
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        print("✅ Usage data API accessible!")
        data = response.json()
        
        if isinstance(data, list):
            print(f"   Data points retrieved: {len(data)}")
            if data:
                print(f"   Date range: {data[0].get('date', 'N/A')} to {data[-1].get('date', 'N/A')}")
        elif isinstance(data, dict):
            print(f"   Response keys: {list(data.keys())}")
            
    elif response.status_code == 401:
        print("❌ Unauthorized - token may be invalid")
    else:
        print(f"⚠️  Usage data request returned status {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error fetching usage data: {e}")

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("\n✅ Your credentials are working!")
print("\nYou can now start the FastAPI service:")
print("  python test_1nce_api.py")
print("\nOr:")
print("  uvicorn test_1nce_api:app --reload")
print("\nThen visit: http://localhost:8000/docs")
print("\n" + "=" * 60)
