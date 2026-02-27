#!/usr/bin/env python3
"""
Stellantis Connected Vehicle API Direct Client

This script provides direct access to Stellantis API endpoints bypassing py_uconnect
and allowing full access to all available methods.

Documentation: https://developers.stellantis.com/apidocs.html
"""

import requests
import json
import argparse
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class StellantisDirect:
    """Direct Stellantis API Client - Jeep/FCA Login"""
    
    # Jeep-specific endpoints discovered from py_uconnect
    LOGIN_URL = "https://login.jeep.com/accounts.login"
    JWT_URL = "https://login.jeep.com/accounts.getJWT"
    TOKEN_URL = "https://authz.sdpr-01.fcagcv.com/v2/cognito/identity/token"
    CHANNELS_URL = "https://channels.sdpr-01.fcagcv.com"
    
    def __init__(self, username: str, password: str, base_url: str = None, region: str = "na"):
        self.username = username
        self.password = password
        self.region = region
        
        self.token = None
        self.jwt_token = None
        self.session = requests.Session()
        self.account_id = None
        
        logger.info("Initialized Jeep/FCA API Client")
        logger.info(f"  Login: {self.LOGIN_URL}")
        logger.info(f"  Channels: {self.CHANNELS_URL}")
        
    def authenticate(self) -> bool:
        """Get bearer token for API access"""
        try:
            url = f"{self.base_url}/v1/auth/token"
            response = self.session.post(
                url,
                json={"email": self.username, "password": self.password},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                logger.info("✓ Authentication successful")
                return True
            else:
                logger.error(f"✗ Authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"✗ Authentication error: {e}")
            return False
    
    def get_account(self) -> Dict:
        """GET /v1/account - Get account details"""
        return self._request("GET", "/v1/account")
    
    def get_vehicle_data(self, vin: str, limit: int = 100, offset: int = 0) -> Dict:
        """GET /v1/{vin}/data/ - Get recent vehicle sensor data"""
        params = {"limit": limit, "offset": offset}
        return self._request("GET", f"/v1/{vin}/data/", params=params)
    
    def get_vehicle_last_known(self, vin: str) -> Dict:
        """GET /v1/{vin}/data/lastknown - Get last known vehicle data"""
        return self._request("GET", f"/v1/{vin}/data/lastknown")
    
    def send_remote_command(self, vin: str, command: str, parameters: Dict = None) -> Dict:
        """POST /v1/{vin}/remote - Send command to vehicle
        
        Available commands:
        - LOCK, UNLOCK
        - LIGHTS_ON, LIGHTS_OFF
        - ENGINE_START, ENGINE_STOP
        - CLIMATE_ON, CLIMATE_OFF
        - CHARGE_START, CHARGE_STOP
        """
        data = {
            "command": command,
            "parameters": parameters or {}
        }
        return self._request("POST", f"/v1/{vin}/remote", json=data)
    
    def get_streaming_endpoints(self, vin: str) -> Dict:
        """GET /v1/stream/{vin} - Get streaming endpoints for vehicle"""
        return self._request("GET", f"/v1/stream/{vin}")
    
    def add_streaming_endpoint(self, vin: str, endpoints: List[str]) -> Dict:
        """POST /v1/stream/{vin} - Add streaming endpoints"""
        data = {"endpoints": endpoints}
        return self._request("POST", f"/v1/stream/{vin}", json=data)
    
    def remove_streaming_endpoint(self, vin: str, endpoint: str) -> Dict:
        """POST /v1/stream/{vin}/remove - Remove streaming endpoint"""
        data = {"endpoint": endpoint}
        return self._request("POST", f"/v1/stream/{vin}/remove", json=data)
    
    def delete_streaming(self, vin: str) -> Dict:
        """DELETE /v1/stream/{vin} - Delete streaming endpoints"""
        return self._request("DELETE", f"/v1/stream/{vin}")
    
    def get_geofence_breaches(self, vin: str = None, limit: int = 100) -> Dict:
        """GET /v1/geofence-breaches - Get geofence breach events"""
        params = {"limit": limit}
        if vin:
            params["vin"] = vin
        return self._request("GET", "/v1/geofence-breaches", params=params)
    
    def create_geofence_collection(self, name: str, entries: List[Dict]) -> Dict:
        """POST /v1/geofence-collection - Create geofence collection"""
        data = {"name": name, "entries": entries}
        return self._request("POST", "/v1/geofence-collection", json=data)
    
    def get_subscriptions(self) -> Dict:
        """GET /v1/geofencing-notifications/subscriptions - Get all subscriptions"""
        return self._request("GET", "/v1/geofencing-notifications/subscriptions")
    
    def submit_feedback(self, message: str, email: str = None) -> Dict:
        """POST /v1/feedback - Submit feedback to Stellantis"""
        data = {
            "message": message,
            "email": email or self.username
        }
        return self._request("POST", "/v1/feedback", json=data)
    
    def submit_bug(self, title: str, description: str, steps: str, email: str = None) -> Dict:
        """POST /v1/bugs - Submit bug report"""
        data = {
            "title": title,
            "description": description,
            "steps": steps,
            "email": email or self.username
        }
        return self._request("POST", "/v1/bugs", json=data)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to API"""
        url = self.base_url + endpoint
        
        try:
            logger.info(f"[{method}] {endpoint}")
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code >= 400:
                logger.warning(f"  Status: {response.status_code}")
                logger.warning(f"  Response: {response.text[:500]}")
            
            return {
                "status": response.status_code,
                "success": response.status_code < 400,
                "data": response.json() if response.text else None,
                "raw_text": response.text
            }
        except Exception as e:
            logger.error(f"  Error: {e}")
            return {
                "status": None,
                "success": False,
                "error": str(e)
            }

def main():
    parser = argparse.ArgumentParser(
        description="Direct Stellantis API Client",
        epilog="""
Examples:
  python stellantis_direct.py --username user@email.com --password PW --region na
  python stellantis_direct.py --username user@email.com --password PW --base-url https://custom.api.com
  python stellantis_direct.py --username user@email.com --password PW --test-urls
        """
    )
    parser.add_argument("--username", required=True, help="API username")
    parser.add_argument("--password", required=True, help="API password")
    parser.add_argument("--vin", help="Vehicle VIN")
    parser.add_argument("--region", 
        choices=["eu", "na", "na-alt", "uconnect"],
        default="na",
        help="API region/endpoint (default: na for North America)"
    )
    parser.add_argument("--base-url", help="Custom API base URL (overrides region)")
    parser.add_argument("--action", 
        choices=["auth", "account", "vehicle-data", "streaming", "geofences", "subscriptions", "all"],
        default="all",
        help="Action to perform"
    )
    parser.add_argument("--test-urls", action="store_true", help="Test all available URLs for connectivity")
    
    args = parser.parse_args()
    
    # Test URLs if requested
    if args.test_urls:
        print("\n" + "="*80)
        print("TESTING STELLANTIS API ENDPOINTS")
        print("="*80 + "\n")
        
        for name, url in StellantisDirect.BASE_URLS.items():
            print(f"Testing {name:12} - {url}")
            try:
                response = requests.head(url, timeout=5)
                print(f"  ✓ Connection OK (status: {response.status_code})\n")
            except requests.exceptions.ConnectionError as e:
                print(f"  ✗ Connection failed: {type(e).__name__}\n")
            except requests.exceptions.Timeout:
                print(f"  ✗ Timeout\n")
            except Exception as e:
                print(f"  ✗ Error: {type(e).__name__}: {str(e)[:50]}\n")
        
        return
    
    client = StellantisDirect(args.username, args.password, base_url=args.base_url, region=args.region)
    
    if not client.authenticate():
        print("\n❌ Failed to authenticate")
        print("\nTroubleshooting:")
        print("1. Check username and password are correct")
        print("2. Try different region: --region eu, --region na-alt, --region uconnect")
        print("3. Test endpoints: python stellantis_direct.py --username user --password pwd --test-urls")
        print("4. Check network connectivity")
        return
    
    print("\n" + "="*80)
    print("STELLANTIS API DIRECT ACCESS")
    print("="*80 + "\n")
    
    # Store all results
    all_results = {}
    
    # First get account info to find VIN if not provided
    if args.action in ["all", "account"]:
        print("[1/5] Fetching Account Information...")
        result = client.get_account()
        all_results["account"] = result
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Extract VIN from account if available
        if not args.vin and result.get("data"):
            try:
                # Try to find VIN in account data
                if isinstance(result["data"], dict) and "vehicles" in result["data"]:
                    args.vin = result["data"]["vehicles"][0].get("vin") if result["data"]["vehicles"] else None
            except:
                pass
    
    # Get vehicle data if VIN available
    if args.vin:
        if args.action in ["all", "vehicle-data"]:
            print("\n[2/5] Fetching Vehicle Data (Last Known)...")
            result = client.get_vehicle_last_known(args.vin)
            all_results["vehicle_data"] = result
            print(f"Vehicle: {args.vin}")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if args.action in ["all", "streaming"]:
            print("\n[3/5] Fetching Streaming Endpoints...")
            result = client.get_streaming_endpoints(args.vin)
            all_results["streaming"] = result
            print(f"Streaming for: {args.vin}")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Geofences
    if args.action in ["all", "geofences"]:
        print("\n[4/5] Fetching Geofence Breaches...")
        result = client.get_geofence_breaches(vin=args.vin)
        all_results["geofences"] = result
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Subscriptions
    if args.action in ["all", "subscriptions"]:
        print("\n[5/5] Fetching Subscriptions...")
        result = client.get_subscriptions()
        all_results["subscriptions"] = result
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Single action mode
    if args.action not in ["all"]:
        if args.action == "account":
            result = client.get_account()
            print("Account Information:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.action == "vehicle-data":
            if not args.vin:
                print("Error: --vin required for vehicle-data")
                return
            result = client.get_vehicle_last_known(args.vin)
            print(f"Last Known Data for {args.vin}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.action == "streaming":
            if not args.vin:
                print("Error: --vin required for streaming")
                return
            result = client.get_streaming_endpoints(args.vin)
            print(f"Streaming Endpoints for {args.vin}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.action == "geofences":
            result = client.get_geofence_breaches(vin=args.vin)
            print("Geofence Breaches:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.action == "subscriptions":
            result = client.get_subscriptions()
            print("All Subscriptions:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Save all results to file if "all" action was used
    if args.action == "all" and all_results:
        output_file = "stellantis_api_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ All data saved to {output_file}\n")

if __name__ == "__main__":
    main()
