# Jeep API Direct Client - SUCCESS

## Summary

Successfully built a **fully functional standalone Jeep/FCA API client** that works without depending on the `py_uconnect` library.

## Key Achievements

✅ **Correct Authentication Flow Implemented**
- Step 1: Bootstrap via `/accounts.webSdkBootstrap` endpoint
- Step 2: Login via `/accounts.login` with query parameters
- Step 3: Get JWT via `/accounts.getJWT` with query parameters
- Step 4: Get OAuth token via `/v2/cognito/identity/token` with `{"gigya_token": id_token}` payload
- Step 5: Get AWS SigV4 credentials from Cognito using boto3

✅ **Vehicle Data Retrieval Working**
- `/v4/accounts/{uid}/vehicles` - Get vehicles list
- `/v2/accounts/{uid}/vehicles/{vin}/status` - Get detailed vehicle status with all sensor data

✅ **Correct API Configuration**
- Login URL: `https://login.jeep.com`
- Auth Token URL: `https://authz.sdpr-01.fcagcv.com/v2/cognito/identity/token`
- Data URL: `https://channels.sdpr-01.fcagcv.com`
- AWS Region: `eu-west-1`

✅ **Critical Missing Headers Discovered**
- `clientrequestid`: Must be unique UUID in hex format (0-16 chars)
- All headers matching `_default_aws_headers()` from py_uconnect

## Complete Authentication Flow

```
1. Bootstrap (GET)
   URL: /accounts.webSdkBootstrap
   Params: apiKey={LOGIN_API_KEY}

2. Login (POST)
   URL: /accounts.login
   Params: (query) loginID, password, sessionExpiration, include, + default params
   Response: UID, sessionInfo.login_token

3. Get JWT (POST)
   URL: /accounts.getJWT
   Params: (query) login_token, fields, + default params
   Response: id_token

4. Get OAuth Token (POST)
   URL: https://authz.sdpr-01.fcagcv.com/v2/cognito/identity/token
   Headers: x-clientapp-name, x-clientapp-version, clientrequestid, x-api-key, locale, x-originator-type, content-type
   Body: {"gigya_token": id_token}
   Response: Token, IdentityId

5. Get AWS Credentials (boto3 Cognito)
   cognito.get_credentials_for_identity(IdentityId, Logins)
   Response: Credentials with AccessKeyId, SecretKey, SessionToken

6. Setup AWS SigV4 Auth
   Create AWSSigV4 object with credentials for signing all subsequent requests
```

## API Data Retrieved

### Vehicles List (`jeep_vehicles_api.json` - 20.7 KB)
```
- Vehicle metadata: VIN, model, year, color, market, fuel type
- Service capabilities: 40+ services with enabled/disabled status
- Registration status and timestamps
```

### Vehicle Status (`jeep_status_api.json` - 3.4 KB)
```
- Odometer: 35,125 km
- Fuel: 48.0L (78% full), 467 km range
- Oil level: 95%
- Tire pressure: FL/FR/RL/RR with values and status
- Battery info: 14.5V, state of charge (hybrid vehicle)
- Trip info: TripA and TripB with distance, energy usage, electric/hybrid breakdown
- EV info: Battery range, electric distance
- Timestamps and status updates
```

## Technical Highlights

### Critical Discovery: clientrequestid Header
The OAuth endpoint was returning `400 Bad Request: INVALID_REQUEST_PARAMETER` because the `clientrequestid` header was missing. This header must:
- Be present on ALL AWS API calls
- Be a unique 16-character hex string
- Use `uuid.uuid4().hex.upper()[0:16]` format

### Endpoint Corrections
- Status endpoint: `/v2/accounts/{uid}/vehicles/{vin}/status` (NOT `/v1/.../remote/status`)
- Vehicles list endpoint: `/v4/accounts/{uid}/vehicles` with `?stage=ALL` param

### Two Authorization Layers
1. **Initial Auth**: Gigya → JWT → OAuth token (for getting AWS credentials)
2. **Request Auth**: AWS SigV4 signatures on all subsequent vehicle data requests

## Files Created

- `jeep_api_direct.py` - Complete standalone client (200+ lines)
- `jeep_vehicles_api.json` - Vehicle list response
- `jeep_status_api.json` - Vehicle status response

## Usage

```python
from jeep_api_direct import JeepAPIClient

client = JeepAPIClient('email@example.com', 'password')
if client.authenticate():
    vehicles = client.get_vehicles()
    status = client.get_vehicle_status('1C4JJXR66MW811502')
    print(f"Range: {status['evInfo']['battery']['totalRange']} km")
```

Or via command line:
```bash
python jeep_api_direct.py \
  --username marek.pasecny@gmail.com \
  --password KK@fUTJzPq%7Wsw \
  --vin 1C4JJXR66MW811502
```

## Status

🎉 **FULLY FUNCTIONAL** - The direct API client successfully:
- ✅ Authenticates with Jeep/FCA servers
- ✅ Retrieves vehicle list
- ✅ Retrieves complete vehicle status with all sensor data
- ✅ Handles AWS SigV4 authentication correctly
- ✅ Provides clean JSON output

**No dependency on py_uconnect library required.**
