
import json
import logging
from collections import defaultdict
from py_uconnect import brands, Client

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

print("=" * 80)
print("STELLANTIS API ENDPOINT DISCOVERY")
print("=" * 80)

# Track all endpoints
endpoints_called = defaultdict(list)
endpoint_details = {}

# Monkey-patch to capture all HTTP requests
try:
    import requests
    original_request = requests.Session.request
    
    def track_request(self, method, url, **kwargs):
        """Intercept and track all API requests"""
        response = original_request(self, method, url, **kwargs)
        
        # Extract endpoint path
        if 'api' in url.lower():
            # Parse URL to extract endpoint
            parts = url.split('/')
            
            # Find index of 'api' and get path after it
            try:
                api_idx = [i for i, p in enumerate(parts) if 'api' in p.lower()][0]
                endpoint_path = '/'.join(parts[api_idx:])
            except:
                endpoint_path = url
            
            # Store details
            endpoints_called[method].append({
                'url': url,
                'endpoint': endpoint_path,
                'status': response.status_code,
                'timestamp': str(response.headers.get('date', 'N/A'))
            })
            
            endpoint_details[endpoint_path] = {
                'method': method,
                'status': response.status_code,
                'url': url,
                'response_size': len(response.text),
                'content_type': response.headers.get('content-type', 'unknown')
            }
        
        return response
    
    requests.Session.request = track_request
    
except ImportError:
    print("⚠ requests library not found - endpoint tracking unavailable")

# Create client
client = Client('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw', pin='4743', brand=brands.JEEP_EU)

# Trigger various API calls
print("\n[SCANNING] Calling client.refresh()...")
try:
    client.refresh()
    print("✓ Refresh completed")
except Exception as e:
    print(f"⚠ Error: {type(e).__name__} (expected if battery data missing)")

# Also try to get vehicles
try:
    vehicles = client.get_vehicles()
    print(f"✓ Got {len(vehicles)} vehicles")
except Exception as e:
    print(f"⚠ Error getting vehicles: {e}")

# Display results
print("\n" + "=" * 80)
print("ENDPOINTS DISCOVERED")
print("=" * 80)

if not endpoint_details:
    print("❌ No endpoints captured. Make sure requests library is installed.")
else:
    # Group by method
    methods = defaultdict(list)
    for endpoint, details in endpoint_details.items():
        methods[details['method']].append((endpoint, details))
    
    for method in sorted(methods.keys()):
        print(f"\n📍 {method} Requests ({len(methods[method])} endpoints):")
        print("-" * 80)
        
        for endpoint, details in sorted(methods[method]):
            print(f"\n  Endpoint: {endpoint}")
            print(f"    URL: {details['url']}")
            print(f"    Status: {details['status']}")
            print(f"    Response Size: {details['response_size']} bytes")
            print(f"    Content-Type: {details['content_type']}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total unique endpoints: {len(endpoint_details)}")
print(f"GET requests: {len([e for e in endpoint_details.values() if e['method'] == 'GET'])}")
print(f"POST requests: {len([e for e in endpoint_details.values() if e['method'] == 'POST'])}")
print(f"PUT requests: {len([e for e in endpoint_details.values() if e['method'] == 'PUT'])}")

# Save to file
output_file = 'endpoints_discovered.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'endpoints': endpoint_details,
        'by_method': {method: list(details) for method, details in endpoints_called.items()}
    }, f, indent=2, ensure_ascii=False)

print(f"\n✓ Full details saved to {output_file}")

# Print endpoint patterns
print("\n" + "=" * 80)
print("ENDPOINT PATTERNS")
print("=" * 80)

patterns = defaultdict(int)
for endpoint in endpoint_details.keys():
    # Extract base pattern
    parts = endpoint.split('/')
    if len(parts) > 3:
        pattern = '/'.join(parts[:4]) + '/...'
    else:
        pattern = endpoint
    patterns[pattern] += 1

for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
    print(f"  {pattern:60} ({count} endpoint{'s' if count > 1 else ''})")
