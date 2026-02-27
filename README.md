# Jeep UConnect API - Direct Client

A standalone Python client for the Jeep/Stellantis UConnect API without dependencies on `py-uconnect`.

## Project Structure

### Core Files
- **`jeep_api_direct.py`** - Main standalone API client (production-ready)
- **`my_uconnect.py`** - Wrapper around py_uconnect with error handling
- **`requirements.txt`** - Python dependencies

### Data Files
- **`jeep_vehicles_api.json`** - API response: vehicle list with capabilities
- **`jeep_status_api.json`** - API response: detailed vehicle status and sensor data
- **`vehicle.json`** - Local vehicle metadata

### Documentation
- **`JEEP_API_SUCCESS.md`** - Implementation details and authentication flow

### Development
- **`work_files/`** - Temporary scripts, debug output, and exploration files

## Quick Start

```bash
python jeep_api_direct.py \
  --username your-email@example.com \
  --password your-password \
  --vin 1C4JJXR66MW811502
```

## API Features

✅ Full authentication flow (Gigya → JWT → OAuth → AWS SigV4)  
✅ Vehicle list retrieval  
✅ Vehicle status with all sensor data  
✅ Proper error handling and logging  
✅ No external API client library dependency  

## Usage Example

```python
from jeep_api_direct import JeepAPIClient

client = JeepAPIClient('email@example.com', 'password')
if client.authenticate():
    vehicles = client.get_vehicles()
    status = client.get_vehicle_status('1C4JJXR66MW811502')
    print(status['vehicleInfo']['fuel'])
```

## Authentication Details

See `JEEP_API_SUCCESS.md` for complete authentication flow documentation.

## Dependencies

- `requests` - HTTP client
- `boto3` - AWS Cognito integration
- `requests-auth-aws-sigv4` - AWS SigV4 request signing
