import json
import logging
from py_uconnect import brands, Client

# Enable debug logging to see API calls
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Create client
print("Initializing Stellantis/Jeep client...")
client = Client('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw', pin='4743', brand=brands.JEEP_EU)

# Check if authenticated or need to login
print("\nClient object created. Attempting refresh...")

# Fetch the vehicle data into cache
try:
    client.refresh()
    print("✓ Refresh successful")
except (TypeError, AttributeError, KeyError) as e:
    # Ignore errors when battery or other optional data is missing
    print(f"⚠ Partial data fetch (missing optional fields like battery): {type(e).__name__}")
    print("  Continuing with available data...")
except Exception as e:
    print(f"✗ Unexpected error: {type(e).__name__}: {e}")
    raise

# List vehicles
print("\n" + "="*60)
print("VEHICLES FOUND:")
print("="*60)

vehicles = client.get_vehicles()

if not vehicles:
    print("❌ No vehicles returned! This suggests authentication may have failed.")
    print("\nDebug info:")
    print(f"  - Client type: {type(client)}")
    print(f"  - Client attributes: {dir(client)}")
    if hasattr(client, 'vehicles'):
        print(f"  - client.vehicles: {client.vehicles}")
    if hasattr(client, '_vehicles'):
        print(f"  - client._vehicles: {client._vehicles}")
else:
    for vid, vehicle in vehicles.items():
        print(f"\nVehicle ID: {vid}")
        print(f"  VIN/Model: {vehicle.model if hasattr(vehicle, 'model') else 'N/A'}")
        
        # Print actual JSON to see what fields are null
        json_out = vehicle.to_json(indent=2)
        print(f"  Full data:\n{json_out}")
        
        # Count null fields
        data = json.loads(json_out)
        null_count = sum(1 for v in data.values() if v is None)
        total_count = len(data)
        print(f"  Null fields: {null_count}/{total_count}")


