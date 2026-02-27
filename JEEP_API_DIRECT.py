#!/usr/bin/env python3
"""
Direct Jeep API Client - using correct authentication flow from py_uconnect
"""

import requests
import json
import logging
import uuid
import boto3
from typing import Dict, Optional
from requests_auth_aws_sigv4 import AWSSigV4

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class JeepAPIClient:
    """Direct Jeep API Client - correct flow"""
    
    # From JEEP_EU brand configuration
    LOGIN_URL = "https://login.jeep.com"
    TOKEN_URL = "https://authz.sdpr-01.fcagcv.com/v2/cognito/identity/token"
    CHANNELS_BASE = "https://channels.sdpr-01.fcagcv.com"
    LOGIN_API_KEY = "3_ZvJpoiZQ4jT5ACwouBG5D1seGEntHGhlL0JYlZNtj95yERzqpH4fFyIewVMmmK7j"
    API_KEY = "2wGyL6PHec9o1UeLPYpoYa1SkEWqeBur9bLsi24i"
    AWS_REGION = "eu-west-1"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.uid = None
        self.aws_auth = None
        
        logger.info("[*] Jeep API Client initialized")
    
    def _with_default_params(self, params: Dict) -> Dict:
        """Add default parameters for login endpoints"""
        return {
            **params,
            "targetEnv": "jssdk",
            "loginMode": "standard",
            "sdk": "js_latest",
            "authMode": "cookie",
            "sdkBuild": "12234",
            "format": "json",
            "APIKey": self.LOGIN_API_KEY,
        }
    
    def _default_aws_headers(self) -> Dict:
        """Default headers for API calls (matches py_uconnect)"""
        return {
            "x-clientapp-name": "CWP",
            "x-clientapp-version": "1.0",
            "clientrequestid": uuid.uuid4().hex.upper()[0:16],
            "x-api-key": self.API_KEY,
            "locale": "de_de",
            "x-originator-type": "web",
            "content-type": "application/json",
        }
    
    def authenticate(self) -> bool:
        """Authenticate and get AWS credentials"""
        try:
            logger.info("[1/4] Bootstrapping...")
            
            # Step 1: Bootstrap
            resp = self.session.get(
                f"{self.LOGIN_URL}/accounts.webSdkBootstrap",
                params={"apiKey": self.LOGIN_API_KEY}
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("statusCode") != 200:
                logger.error(f"Bootstrap failed: {data}")
                return False
            
            logger.info("[+] Bootstrap OK")
            
            # Step 2: Login
            logger.info("[2/4] Logging in...")
            resp = self.session.post(
                f"{self.LOGIN_URL}/accounts.login",
                params=self._with_default_params({
                    "loginID": self.username,
                    "password": self.password,
                    "sessionExpiration": 300,
                    "include": "profile,data,emails,subscriptions,preferences",
                })
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("statusCode") != 200:
                logger.error(f"Login failed: {data}")
                return False
            
            self.uid = data["UID"]
            login_token = data["sessionInfo"]["login_token"]
            logger.info(f"[+] Login OK (UID: {self.uid})")
            
            # Step 3: Get JWT
            logger.info("[3/4] Getting JWT...")
            resp = self.session.post(
                f"{self.LOGIN_URL}/accounts.getJWT",
                params=self._with_default_params({
                    "login_token": login_token,
                    "fields": "profile.firstName,profile.lastName,profile.email,country,locale,data.disclaimerCodeGSDP",
                })
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("statusCode") != 200:
                logger.error(f"JWT failed: {data}")
                return False
            
            id_token = data["id_token"]
            logger.info("[+] JWT obtained")
            
            # Step 4: Get OAuth token
            logger.info("[4/4] Getting OAuth token...")
            logger.debug(f"OAuth URL: {self.TOKEN_URL}")
            logger.debug(f"OAuth Payload: {{'gigya_token': id_token[:50]}}")
            
            resp = self.session.post(
                self.TOKEN_URL,
                headers=self._default_aws_headers(),
                json={"gigya_token": id_token}  # KEY: Use gigya_token, not jwt!
            )
            
            if resp.status_code != 200:
                logger.error(f"OAuth token failed: {resp.status_code}")
                try:
                    error_data = resp.json()
                    logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error(f"Response text: {resp.text[:500]}")
                return False
            
            data = resp.json()
            
            token = data.get("Token")
            identity_id = data.get("IdentityId")
            
            if not token or not identity_id:
                logger.error(f"Missing Token or IdentityId in response: {data}")
                return False
            
            logger.info("[+] Authentication successful! Setting up AWS credentials...")
            
            # Step 5: Get AWS credentials from Cognito
            try:
                cognito = boto3.client("cognito-identity", region_name=self.AWS_REGION)
                creds_resp = cognito.get_credentials_for_identity(
                    IdentityId=identity_id,
                    Logins={"cognito-identity.amazonaws.com": token}
                )
                
                creds = creds_resp.get("Credentials")
                if not creds:
                    logger.error(f"No credentials in response: {creds_resp}")
                    return False
                
                # Set up AWS SigV4 authentication
                self.aws_auth = AWSSigV4(
                    service="execute-api",
                    region=self.AWS_REGION,
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretKey"],
                    aws_session_token=creds["SessionToken"],
                )
                
                logger.info("[+] AWS SigV4 auth configured\n")
                return True
                
            except Exception as e:
                logger.error(f"Failed to get AWS credentials: {e}")
                return False
            
        except Exception as e:
            logger.error(f"✗ Auth error: {type(e).__name__}: {e}")
            return False
    
    def get_vehicles(self) -> Optional[Dict]:
        """Get list of vehicles"""
        try:
            logger.info("Fetching vehicles...")
            url = f"{self.CHANNELS_BASE}/v4/accounts/{self.uid}/vehicles"
            
            resp = self.session.get(
                url,
                headers=self._default_aws_headers() | {"content-type": "application/json"},
                auth=self.aws_auth,
                params={"stage": "ALL"}
            )
            
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"[+] Got {len(data.get('vehicles', []))} vehicles")
            return data
                
        except Exception as e:
            logger.error(f"Error getting vehicles: {e}")
            return None
    
    def get_vehicle_status(self, vin: str) -> Optional[Dict]:
        """Get vehicle status/data"""
        try:
            logger.info(f"Fetching status for {vin}...")
            url = f"{self.CHANNELS_BASE}/v2/accounts/{self.uid}/vehicles/{vin}/status"
            
            resp = self.session.get(
                url,
                headers=self._default_aws_headers() | {"content-type": "application/json"},
                auth=self.aws_auth
            )
            
            resp.raise_for_status()
            data = resp.json()
            logger.info("[+] Got vehicle status")
            return data
                
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Direct Jeep API Client")
    parser.add_argument("--username", required=True, help="Jeep account email")
    parser.add_argument("--password", required=True, help="Jeep account password")
    parser.add_argument("--vin", help="Vehicle VIN (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set log level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    client = JeepAPIClient(args.username, args.password)
    
    if not client.authenticate():
        logger.error("Authentication failed!")
        return
    
    print("\n" + "="*80)
    print("JEEP API DATA")
    print("="*80 + "\n")
    
    # Get vehicles
    vehicles = client.get_vehicles()
    if vehicles:
        print("[VEHICLES]")
        print(json.dumps(vehicles, indent=2, ensure_ascii=False)[:2000])
        print("\n")
    
    # Get status if VIN provided
    if args.vin:
        status = client.get_vehicle_status(args.vin)
        if status:
            print(f"[STATUS FOR {args.vin}]")
            print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
