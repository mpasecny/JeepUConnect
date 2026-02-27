#!/usr/bin/env python3
"""
Capture the exact OAuth token request from py_uconnect
"""

import sys
import json

# Intercept requests
import requests
original_post = requests.Session.post

captured = {}

def intercept_post(self, url, **kwargs):
    if 'cognito/identity/token' in url:
        print("\n" + "="*80)
        print("CAPTURED OAUTH TOKEN REQUEST")
        print("="*80)
        print(f"\nURL: {url}")
        print(f"Headers: {dict(self.headers)}")
        
        if 'json' in kwargs:
            print(f"JSON Body: {json.dumps(kwargs['json'], indent=2)}")
        if 'data' in kwargs:
            print(f"Data Body: {kwargs['data']}")
        
        captured['oauth_request'] = {
            'url': url,
            'headers': dict(self.headers),
            'json': kwargs.get('json'),
            'data': kwargs.get('data')
        }
    
    return original_post(self, url, **kwargs)

requests.Session.post = intercept_post

# Now use py_uconnect
from py_uconnect import brands, Client

print("Starting py_uconnect to capture OAuth request...")
try:
    client = Client('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw', pin='4743', brand=brands.JEEP_EU)
    client.refresh()
except Exception as e:
    print(f"Error (expected): {type(e).__name__}")

if captured:
    print("\n" + "="*80)
    print("SAVED OAUTH REQUEST DETAILS")
    print("="*80)
    print(json.dumps(captured, indent=2))
    
    # Save to file
    with open('oauth_request_format.json', 'w') as f:
        json.dump(captured, f, indent=2)
    print("\n✓ Saved to oauth_request_format.json")
else:
    print("\nNo OAuth request was captured")
