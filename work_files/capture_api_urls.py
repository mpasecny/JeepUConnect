#!/usr/bin/env python3
"""
Debug script to capture actual API URLs used by py_uconnect
"""

import sys
import json
import logging
from urllib.parse import urlparse
from collections import defaultdict

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

# Monkey-patch requests to log all URLs
import requests
original_request = requests.Session.request

captured_urls = []

def log_request(self, method, url, **kwargs):
    captured_urls.append({
        'method': method,
        'url': url,
        'full_url': url,
        'parsed': str(urlparse(url))
    })
    print(f"\n🔗 {method} {url}")
    
    try:
        response = original_request(self, method, url, **kwargs)
        print(f"   Status: {response.status_code}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {str(e)[:100]}")
        raise

requests.Session.request = log_request

# Now import and use py_uconnect
print("="*80)
print("CAPTURING API CALLS FROM py_uconnect")
print("="*80)

try:
    from py_uconnect import brands, Client
    
    print("\n[1] Creating client...")
    client = Client('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw', pin='4743', brand=brands.JEEP_EU)
    
    print("\n[2] Calling refresh()...")
    try:
        client.refresh()
        print("\n✓ Refresh completed")
    except Exception as e:
        print(f"\n⚠ Refresh error (expected): {type(e).__name__}")
        if captured_urls:
            print("  (But we captured URL before error!)")
    
    print("\n[3] Getting vehicles...")
    try:
        vehicles = client.get_vehicles()
        print(f"✓ Got {len(vehicles)} vehicles")
    except Exception as e:
        print(f"⚠ Error: {e}")

except ImportError as e:
    print(f"✗ Cannot import py_uconnect: {e}")
    sys.exit(1)

# Display captured URLs
print("\n" + "="*80)
print("CAPTURED API ENDPOINTS")
print("="*80)

if captured_urls:
    # Group by domain
    by_domain = defaultdict(list)
    for req in captured_urls:
        parsed = urlparse(req['url'])
        domain = f"{parsed.scheme}://{parsed.netloc}"
        endpoint = parsed.path
        by_domain[domain].append({
            'method': req['method'],
            'endpoint': endpoint,
            'full_url': req['url']
        })
    
    for domain, requests_list in sorted(by_domain.items()):
        print(f"\n📡 Domain: {domain}")
        for req in requests_list:
            print(f"   {req['method']:6} {req['endpoint']}")
            print(f"         Full: {req['full_url']}")
    
    # Save to file
    with open('captured_api_urls.json', 'w', encoding='utf-8') as f:
        json.dump({
            'captured_requests': captured_urls,
            'by_domain': dict(by_domain)
        }, f, indent=2)
    
    print(f"\n✓ Saved to captured_api_urls.json")
    
    # Extract base URL
    if captured_urls:
        first_url = captured_urls[0]['url']
        parsed = urlparse(first_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        print(f"\n🎯 RECOMMENDED BASE URL for API:")
        print(f"   {base_url}")
        
else:
    print("\n❌ No API requests captured")
    print("This means py_uconnect didn't make any HTTP calls (or failed immediately)")
