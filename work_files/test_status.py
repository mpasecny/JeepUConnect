#!/usr/bin/env python3
from jeep_api_direct import JeepAPIClient, logger
import logging
import json
import traceback

# Enable debug logging
logger.setLevel(logging.DEBUG)
for handler in logger.handlers:
    handler.setLevel(logging.DEBUG)

try:
    client = JeepAPIClient('marek.pasecny@gmail.com', 'KK@fUTJzPq%7Wsw')
    if client.authenticate():
        print('Auth OK')
        status = client.get_vehicle_status('1C4JJXR66MW811502')
        print(f'Status returned: {status is not None}')
        print(f'Status type: {type(status)}')
        if isinstance(status, dict):
            print(f'Status dict has {len(status)} keys')
            if status:
                print(f'Keys: {list(status.keys())[:10]}')
                with open('jeep_status_api.json', 'w', encoding='utf-8') as f:
                    json.dump(status, f, indent=2)
                print('File saved OK')
            else:
                print(f'Status dict is EMPTY!')
                print(f'Status: {status}')
except Exception as e:
    print(f'ERROR: {e}')
    traceback.print_exc()
