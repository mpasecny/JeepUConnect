#!/usr/bin/env python3
"""
Debug OAuth token request to see what's being sent
"""

import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG)

class JeepAPIDebug:
    LOGIN_URL = "https://login.jeep.com/accounts.login"
    JWT_URL = "https://login.jeep.com/accounts.getJWT"
    TOKEN_URL = "https://authz.sdpr-01.fcagcv.com/v2/cognito/identity/token"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
    
    def debug_auth(self):
        print("\n" + "="*80)
        print("DEBUGGING JEEP API AUTHENTICATION")
        print("="*80 + "\n")
        
        # Step 1: Login
        print("[1] LOGIN REQUEST")
        print(f"  URL: {self.LOGIN_URL}")
        login_data = {"username": self.username, "password": self.password}
        print(f"  Data: {json.dumps(login_data)}\n")
        
        login_resp = self.session.post(self.LOGIN_URL, json=login_data, timeout=10)
        print(f"  Status: {login_resp.status_code}")
        print(f"  Headers: {dict(login_resp.headers)}")
        print(f"  Response: {login_resp.text[:500]}\n")
        
        # Step 2: JWT
        print("[2] JWT REQUEST")
        print(f"  URL: {self.JWT_URL}")
        jwt_data = {}
        print(f"  Data: {json.dumps(jwt_data)}\n")
        
        jwt_resp = self.session.post(self.JWT_URL, json=jwt_data, timeout=10)
        print(f"  Status: {jwt_resp.status_code}")
        print(f"  Response: {jwt_resp.text[:500]}\n")
        
        jwt_token = jwt_resp.json().get('jwt')
        
        # Step 3: Token - DEBUG
        print("[3] OAUTH TOKEN REQUEST")
        print(f"  URL: {self.TOKEN_URL}")
        
        # Try different payload formats
        token_payloads = [
            {"jwt": jwt_token},
            {"access_token": jwt_token},
            {"token": jwt_token},
            {"idToken": jwt_token},
            {"id_token": jwt_token},
            jwt_token,  # Raw token as body
        ]
        
        for i, payload in enumerate(token_payloads):
            print(f"\n  [Attempt {i+1}] Payload format:")
            if isinstance(payload, str):
                print(f"    Raw token: {payload[:50]}...")
                payload_str = payload
            else:
                print(f"    {json.dumps(payload, indent=6)}")
                payload_str = json.dumps(payload)
            
            # Try different content types
            for content_type in ["application/json", "application/x-www-form-urlencoded", None]:
                headers = {}
                if content_type:
                    headers['Content-Type'] = content_type
                
                try:
                    if isinstance(payload, str):
                        if content_type == "application/x-www-form-urlencoded":
                            resp = self.session.post(self.TOKEN_URL, data=payload, headers=headers, timeout=5)
                        else:
                            resp = self.session.post(self.TOKEN_URL, data=payload, headers=headers, timeout=5)
                    else:
                        resp = self.session.post(self.TOKEN_URL, json=payload, headers=headers, timeout=5)
                    
                    ct_str = content_type or "default"
                    print(f"      {ct_str:30} → {resp.status_code}")
                    
                    if resp.status_code == 200:
                        print(f"      ✓ SUCCESS! Response: {resp.text[:200]}")
                        return
                    elif resp.status_code in [400, 401, 403]:
                        print(f"      Error: {resp.text[:100]}")
                        
                except Exception as e:
                    print(f"      Error: {type(e).__name__}")

# Run debug
username = input("Email: ")
password = input("Password: ")

client = JeepAPIDebug(username, password)
client.debug_auth()
