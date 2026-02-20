from py_uconnect import brands, Client

# Create client
client = Client('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw', pin='4743', brand=brands.JEEP_EU)

# Fetch the vehicle data into cache
try:
    client.refresh()
except TypeError as e:
    if "'NoneType' object is not subscriptable" in str(e):
        print(f"Warning: API response incomplete (missing battery data): {e}")
        print("Continuing with partial data...")
    else:
        raise

# List vehicles
vehicles = client.get_vehicles()
for vehicle in vehicles.values():
    print(vehicle.to_json(indent=2))

