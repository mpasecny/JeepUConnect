#!/usr/bin/env python3
"""
Test different JWT/Token endpoints
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JeepAPITest:
    LOGIN_URL = "https://login.jeep.com/accounts.login"
    
    # Different JWT endpoints to try
    JWT_ENDPOINTS = [
        "https://login.jeep.com/accounts.getJWT",
        "https://login.jeep.com/oauth/token",
        "https://login.jeep.com/accounts.createJWT",
        "https://authz.sdpr-01.fcagcv.com/v2/cognito/identity",
        "https://authz.sdpr-01.fcagcv.com/oauth/token",
    ]
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
    
    def test_all(self):
        print("\n" + "="*80)
        print("TESTING JWT/TOKEN ENDPOINTS")
        print("="*80 + "\n")
        
        # Step 1: Login (should work)
        print("[1] LOGIN")
        login_resp = self.session.post(
            self.LOGIN_URL,
            json={"username": self.username, "password": self.password}
        )
        print(f"  Status: {login_resp.status_code}")
        
        if login_resp.status_code != 200:
            print("  ❌ Login failed!")
            return
        
        login_data = login_resp.json()
        print(f"  Response keys: {list(login_data.keys())}")
        print(f"  Response: {json.dumps(login_data, indent=2)[:500]}\n")
        
        # Step 2: Try different JWT endpoints
        print("[2] TESTING JWT ENDPOINTS\n")
        
        for endpoint in self.JWT_ENDPOINTS:
            print(f"  Testing: {endpoint}")
            
            try:
                # Try with different payloads
                payloads = [
                    {},
                    {"username": self.username},
                    {"sessionId": login_data.get('sessionId')},
                    json.dumps({}),
                ]
                
                for payload in payloads:
                    try:
                        if isinstance(payload, str):
                            resp = self.session.post(endpoint, data=payload, timeout=3)
                        else:
                            resp = self.session.post(endpoint, json=payload, timeout=3)
                        
                        if resp.status_code == 200:
                            print(f"    ✓ {resp.status_code} - SUCCESS!")
                            print(f"      Response: {resp.text[:200]}")
                            print(f"      Keys: {list(resp.json().keys()) if resp.json() else 'N/A'}\n")
                            return
                        elif resp.status_code < 500:
                            print(f"    {resp.status_code} - {resp.text[:50]}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"    ❌ {type(e).__name__}\n")

# Run test
username = input("Email: ")
password = input("Password: ")

test = JeepAPITest(username, password)
test.test_all()
