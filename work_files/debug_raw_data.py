import json
import logging
from py_uconnect import brands, Client

# Enable debug logging to see API responses
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Create client
print("=" * 80)
print("CAPTURING RAW API DATA FROM STELLANTIS")
print("=" * 80)

client = Client('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw', pin='4743', brand=brands.JEEP_EU)

# Monkey-patch to capture raw responses
captured_responses = {}

original_request = None
try:
    import requests
    original_request = requests.Session.request
except:
    pass

def capture_request(self, method, url, **kwargs):
    """Intercept and log all API responses"""
    response = original_request(self, method, url, **kwargs)
    
    # Capture vehicle data endpoints
    if 'vehicle' in url.lower() or 'vhr' in url.lower():
        try:
            data = response.json()
            endpoint = url.split('/api/')[-1] if '/api/' in url else url
            captured_responses[endpoint] = data
            
            print(f"\n[RAW API RESPONSE] {endpoint}")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000] + "...\n")
        except:
            pass
    
    return response

if original_request:
    requests.Session.request = capture_request

# Now refresh - this will capture raw data
try:
    print("\n[ACTION] Calling client.refresh()...")
    client.refresh()
    print("✓ Refresh completed\n")
except Exception as e:
    print(f"⚠ Refresh error (expected): {type(e).__name__}")

# Get parsed vehicles
vehicles = client.get_vehicles()

print("\n" + "=" * 80)
print("COMPARISON: RAW API vs PARSED LIBRARY DATA")
print("=" * 80)

for vid, vehicle in vehicles.items():
    print(f"\n🚗 Vehicle: {vehicle.model} (VIN: {vid})")
    print(f"\nParsed fields by py_uconnect library:")
    
    # Get all non-None attributes
    vehicle_dict = vehicle.to_json()
    if isinstance(vehicle_dict, str):
        vehicle_dict = json.loads(vehicle_dict)
    
    print(json.dumps(vehicle_dict, indent=2, ensure_ascii=False))
    
    # Show field count
    non_none = sum(1 for v in vehicle_dict.values() if v is not None)
    total = len(vehicle_dict)
    print(f"\nStats: {non_none}/{total} fields populated")

# Show what raw data was captured
print("\n" + "=" * 80)
print("RAW DATA ENDPOINTS CAPTURED:")
print("=" * 80)

for endpoint, data in captured_responses.items():
    print(f"\n📡 Endpoint: {endpoint}")
    if isinstance(data, dict):
        print(f"   Keys: {list(data.keys())}")
        # Count nested data
        def count_fields(obj, depth=0, max_depth=2):
            if depth > max_depth:
                return 0
            if isinstance(obj, dict):
                return len(obj) + sum(count_fields(v, depth+1) for v in obj.values())
            elif isinstance(obj, list) and obj:
                return count_fields(obj[0], depth+1)
            return 0
        
        field_count = count_fields(data)
        print(f"   Total nested fields: ~{field_count}")

print("\n" + "=" * 80)
print("SAVE RAW DATA TO FILE for further analysis")
print("=" * 80)

if captured_responses:
    with open('raw_api_response.json', 'w', encoding='utf-8') as f:
        json.dump(captured_responses, f, indent=2, ensure_ascii=False)
    print("✓ Saved to raw_api_response.json")
