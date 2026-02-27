Analysis of explorer outputs

Files examined:
- explorer_location.json
- explorer_notifications.json
- explorer_status_v2.json
- explorer_status_v1_remote.json
- explorer_commands.json
- explorer_services_v4.json
- explorer_vehicles_v4.json

Summary:

1) location (explorer_location.json)
- HTTP 404; body: NOT_FOUND.
- Conclusion: GET /v2/.../location is not a defined GET route. The service likely uses a different path or HTTP method (or the account lacks location service).

2) notifications (explorer_notifications.json)
- HTTP 404; body: NOT_FOUND.
- Conclusion: Notifications endpoint not available via GET at that route.

3) status_v2 (explorer_status_v2.json)
- HTTP 200; rich JSON returned.
- Contains: odometer, fuel (48.0 L, 467 km), oilLevel (95), tyrePressure (all NORMAL), batteryInfo (voltage 14.5V), tripsInfo, evInfo.totalRange=467, timestamps.
- This is the primary working status endpoint for this vehicle.

4) status_v1_remote (explorer_status_v1_remote.json)
- HTTP 200 but empty JSON ({})
- Conclusion: endpoint exists but returns blank for this vehicle/permissions; use v2/status instead.

5) commands (explorer_commands.json)
- HTTP 404; body: NOT_FOUND.
- Conclusion: GET not allowed for commands; commands are usually POST operations (submit remote commands) or different route.

6) services_v4 (explorer_services_v4.json)
- HTTP 404; body: NOT_FOUND.
- But vehicles_v4 returned a `services` array inside each vehicle object, so the per-vehicle /services GET may be not exposed; the vehicle list already includes service capability information.

7) vehicles_v4 (explorer_vehicles_v4.json)
- HTTP 200; returns user vehicles array and `services` list per vehicle (many service flags).
- Useful to determine which services are vehicle-capable and enabled.

Recommendations / next steps:
- Use `/v2/.../status` (works) and `/v4/accounts/{uid}/vehicles` (vehicles list + services).
- For location, commands, notifications, and services endpoints: try alternative methods or routes (POST for commands), or inspect API docs/py_uconnect calls for exact routes and required headers/params.
- If you want, I can add automated trials: try POST for `commands`, test alternate location routes, or iterate over the services array to find actionable service names.

Saved files:
- explorer_analysis.md (this file)

