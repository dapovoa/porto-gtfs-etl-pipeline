# Why Real-time Bus Movement Cannot Be Implemented

## The Problem

How do you implement realistic real-time bus movement when the API only gives you disconnected GPS points every 5 seconds with no path information?

Short answer: You can't. You can only guess, and guessing produces buses that cross buildings.

## What FIWARE API Provides

```bash
curl "https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType==bus&limit=1"
```

```json
{
  "vehicle": "3349",
  "route": "stcp:route:804",
  "location": [-8.57053566, 41.166854858],
  "speed": 0,
  "bearing": 186,
  "time": "2025-10-25T10:37:00.00Z"
}
```

That's it. One GPS point. No path. No history. No context.

**Update method:** HTTP polling every 5 seconds
**Data provided:** Current position, current speed, current bearing
**Data NOT provided:** Everything else

## Real Test Results

Three consecutive requests, 5 seconds apart:

```
t=0s:  location: [-8.57053566, 41.166854858]
       time: "10:37:00"

t=5s:  location: [-8.57053566, 41.166854858]  <- SAME POSITION
       time: "10:37:00"                        <- SAME TIMESTAMP

t=10s: location: [-8.568962097, 41.16627121]  <- JUMPED 150 METERS
       time: "10:38:04"
```

The bus moved 150 meters somewhere between t=0 and t=10. When? Which path? No idea.

## What's Missing

**No streaming**
- API: HTTP polling only
- Cannot get updates faster than 5 seconds
- No WebSocket, no Server-Sent Events, nothing

**No path data**
- API: Single GPS point
- No trajectory, no breadcrumb trail, no route history
- Cannot know which streets bus used

**No intermediate positions**
- API: Point A at t=0, Point B at t=5
- Everything between A and B: invisible
- Bus could have done anything in those 5 seconds

**No real-time context**
- API: Route ID only
- No traffic conditions, no roadworks, no detours
- No reason for deviations

**Stale data**
- API: `observationDateTime` = when GPS was captured
- Data can be 30-60 seconds old
- No guarantee of freshness

## The Scale of the Problem

At 40 km/h, buses travel **55 meters in 5 seconds**.

In 55 meters:
- 2-3 street corners
- 4-5 buildings
- Multiple lane changes
- Traffic lights, pedestrians, stops

All invisible. API shows: Point A, then Point B.

## What Would Be Needed (Examples from Other Cities)

### London Transport API
```json
{
  "vehicleId": "LT123",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "timestamp": "2024-10-25T10:37:00Z",
  "nextStopId": "490000123",
  "distanceToNextStop": 250,
  "breadcrumbs": [
    {"lat": 51.5073, "lng": -0.1279, "t": "10:36:58"},
    {"lat": 51.5073, "lng": -0.1279, "t": "10:36:59"},
    {"lat": 51.5074, "lng": -0.1278, "t": "10:37:00"}
  ]
}
```

Note the `breadcrumbs` field - actual path taken with sub-second timestamps.

### NYC MTA Bus Time API
```json
{
  "VehicleRef": "MTA_1234",
  "MonitoredCall": {
    "VehicleLocation": {
      "Latitude": "40.7589",
      "Longitude": "-73.9851"
    },
    "ProgressRate": "normalProgress",
    "ProgressStatus": "approaching"
  },
  "OnwardCalls": [
    {"StopPointRef": "400561", "ExpectedArrivalTime": "2024-10-25T10:38:00"},
    {"StopPointRef": "400562", "ExpectedArrivalTime": "2024-10-25T10:39:30"}
  ]
}
```

Note `OnwardCalls` - future stops with timing. Allows interpolation along known route.

### TransportAPI (UK)
```json
{
  "request_time": "2024-10-25T10:37:00+00:00",
  "departures": {
    "vehicle": "bus",
    "location": {
      "coordinates": [51.5074, -0.1278],
      "bearing": 90,
      "speed": 15
    },
    "route_deviation": false,
    "next_stop_distance": 120,
    "schedule_deviation": -30
  }
}
```

Note `route_deviation` and `schedule_deviation` - context about bus behavior.

## What FIWARE Doesn't Provide

```
FIWARE gives:           What's needed:
- GPS point             - GPS stream (sub-second updates)
- Speed                 - Acceleration/deceleration
- Bearing               - Turn angles
- Timestamp             - Path history (breadcrumbs)
- Route ID              - Next stops with timing
                        - Route deviation info
                        - Schedule adherence
                        - Traffic context
```

## The Impossibility

**To implement realistic movement, you need:**
1. Continuous position updates (sub-second) OR
2. Path history between points OR
3. Next stops with expected timing OR
4. Route geometry with live adherence data

**FIWARE provides:**
1. Position snapshots every 5 seconds
2. Nothing else

**Result:**
- Must guess path between points
- GTFS shapes = theoretical route (not real)
- OpenRouteService = calculated route (no traffic data)
- Straight line = crosses buildings

All three methods fail because **the API doesn't tell you where the bus actually went**.

## Conclusion

You cannot implement real-time bus movement with FIWARE API because:
- No streaming (5-second polling only)
- No path data (disconnected GPS points)
- No movement context (just position + speed + bearing)
- No real-time route information

The API gives you snapshots. Realistic movement requires a movie. You can't make a movie from 12 photographs per minute.

This is not a software problem. This is an API limitation problem.
