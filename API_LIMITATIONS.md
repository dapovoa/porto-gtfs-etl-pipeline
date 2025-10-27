# Why Real-time Bus Movement Cannot Be Implemented

## The Problem

How do you implement realistic real-time bus movement when the API only gives you **disconnected GPS points every 5 seconds with no path information**?

Short answer: You can't. You can only guess, and guessing produces buses that cross buildings.

---

## What the FIWARE API Provides (The Data)

The API is limited to basic snapshot data, forcing HTTP polling every 5 seconds.

```bash
curl "https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType==bus&limit=1"
```
```json
[
  {
    "id": "urn:ngsi-ld:Vehicle:porto:stcp:bus:3373",
    "type": "Vehicle",
    "annotations": {
      "type": "Array",
      "value": [
        "stcp:route:302",
        "stcp:nr_turno:na",
        "stcp:nr_viagem:302_0_3|161|D2|T1|N12",
        "stcp:sentido:0"
      ],
      "metadata": {}
    },
    "bearing": { "type": "Number", "value": 198, "metadata": {} },
    "location": {
      "type": "geo:json",
      "value": { "type": "Point", "coordinates": [ -8.601851463, 41.157554626 ] },
      "metadata": {}
    },
    "observationDateTime": { "type": "DateTime", "value": "2025-10-25T12:28:58.00Z", "metadata": {} },
    "speed": { "type": "Number", "value": 34, "metadata": {} },
    "vehicleType": { "type": "Text", "value": "bus", "metadata": {} }
  }
]
```

**Data provided:**
*   Current position (location)
*   Current speed (speed)
*   Current bearing (bearing)
*   Observation Timestamp (observationDateTime)

**Data NOT provided:**
*   Path history (breadcrumb trail)
*   Intermediate positions between updates
*   Next stops with ETAs
*   Live route adherence/deviation info

**Real Test Results: The Jump**
The data often shows the bus remaining still for 5 seconds, followed by a jump of 150 meters, leaving its actual movement path unknown.
*   **0s:** Position A at [-8.57053566, 41.166854858], Timestamp: "10:37:00"
*   **5s:** SAME POSITION at [-8.57053566, 41.166854858], Timestamp: "10:37:00"
*   **10s:** JUMPED 150 METERS to [-8.568962097, 41.16627121], Timestamp: "10:38:04"
The bus moved 150 meters between t=0 and t=10. The path is a complete unknown.

**What's Fundamentally Missing**
The FIWARE implementation lacks four key features required for smooth, realistic tracking:
*   **Streaming:** Only HTTP polling (min 5s interval). Consequence: Cannot get continuous updates; creates "jumpy" movement.
*   **Path Data:** Only single GPS point. Consequence: Cannot know which streets the bus used between points.
*   **Freshness:** Data can be 30-60 seconds old. Consequence: Bus position is stale, leading to significant inaccuracies.
*   **Context:** No future stops/ETAs. Consequence: Cannot interpolate movement intelligently along the known GTFS route geometry.

**The Scale of the Problem**
At a modest 40 km/h, a bus travels 55 meters in a 5-second interval.
This 55-meter path is entirely invisible. A bus could navigate multiple corners, buildings, and traffic stops, yet the API only provides the starting point (Point A) and the end point (Point B).

**What is Needed (Examples from Other Cities)**
Functional real-time APIs from other major cities provide the necessary context to estimate movement between snapshots.
*   **Breadcrumbs (e.g., London):** Provides path history with sub-second resolution, allowing for true path drawing.
*   **Onward Calls/ETAs (e.g., NYC MTA):** Gives the next stops and expected arrival times, allowing for interpolation along the scheduled route geometry.
*   **Deviation Info (e.g., TransportAPI):** Indicates if the bus is off-route or behind schedule, informing the tracking algorithm.

**The Impossibility**
To implement realistic bus movement, you need either continuous position updates (streaming) OR rich path/contextual data (breadcrumbs, ETAs).
The FIWARE API provides neither.
Any attempt to "fix" the movement by drawing a straight line, following the theoretical GTFS shape, or using a separate routing service is a guess that will fail when the bus deviates from the guess (e.g., stopping, turning, or taking a minor detour).

**Conclusion:** You cannot implement realistic real-time bus movement with the current FIWARE API because the data consists only of disconnected snapshots. Realistic movement requires a smooth, continuous "movie" of the journey, not a few scattered photographs per minute. This is an API limitation problem, not a software development issue.
