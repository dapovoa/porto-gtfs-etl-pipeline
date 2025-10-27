## Porto (STCP) GTFS ETL Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Archived](https://img.shields.io/badge/Status-ARCHIVED-red.svg)](https://github.com/dapovoa/porto-gtfs-etl-pipeline)
[![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-05998b?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)

![Dashboard Screenshot](img/screenshot.png)

This project is the fossil record of a failed attempt to build a **real-time bus tracker for Porto**. It's **archived** because Porto's public transit data infrastructure (provided by STCP and Porto Digital) is fundamentally incapable of supporting a functional real-time application.

The goal was simple: show buses moving smoothly on a map. The reality is that the public "real-time" data is a creative interpretation of the term, consisting of GPS snapshots that are **30-60 seconds old**. Attempting to track movement with this data results in buses driving through buildings.

After an embarrassing amount of time, the project was pivoted to do what was actually possible.

---

## What This Project Actually Does

Since real-time tracking is a fantasy, this project focuses on the robust, **static GTFS data** and basic fleet analytics:

* Processes the **static GTFS data** (timetables, routes, stops), which is accurate.
* Provides a web dashboard and a **REST API** for exploring this static data (e.g., all stops for a given route).
* Calculates basic fleet-wide analytics based on the limited FIWARE data, like "how many buses are currently on the road".

**What it absolutely does NOT do:** Show you a bus moving on a map.

---

## The Investigation: Why Did the Real-Time Attempt Fail?

The problem is a spectacular, multi-layered failure in implementation, not technology.

### 1. The Technology (FIWARE) - Capable but Restricted

Porto uses the open-source **[FIWARE](https://www.fiware.org/)** platform, which is fully capable of providing real-time, event-driven push notifications via subscriptions. The technology is sound.

### 2. The Implementation (Porto Digital) - The Plot Twist

Porto Digital uses FIWARE's real-time subscription features **internally**. I found a public endpoint confirming they have an internal subscription that has fired over 397 million times.

For the public, they force developers to **poll a REST endpoint every few seconds** like it's 2005. They have the modern, real-time system but keep it to themselves.

### 3. The Data (From STCP's Buses) - The Final Disappointment

Even if they provided the real-time stream, the data is poor. It's a single GPS point, fundamentally missing the context needed for a real bus tracker:

* No history of where the bus has been (breadcrumb trail).
* No info on where it's going next.
* No Estimated Times of Arrival (ETAs).

---

## Who Needs to Fix What

This isn't a developer problem; it's a platform and data problem.

* **For STCP (The Bus Operator):** The onboard hardware needs to provide **richer data**, including a breadcrumb trail of recent GPS points and the next scheduled stop.
* **For Porto Digital (The Platform Operator):** **Expose the subscription functionality** to the public. Let developers subscribe to push notifications instead of forcing pointless polling. You have the infrastructure; just unlock the door.

---

## Documentation

If you want to see the evidence for yourself, the technical deep-dive is here:

* **[API Limitations](API_LIMITATIONS.md)**: The full, sarcastic breakdown of the technical issues.
* **[Project Details](PROJECT.md)**: The gory internals of how this is all bolted together.

---

## Official Links & Sources

For those who enjoy comparing optimistic documentation with grim reality:

* **[Open Data Portal Page](https://opendata.porto.digital/dataset/urban-platform-bus-location)**: Where they claim this is "real-time" data.
* **[The Actual API Endpoint](https://broker.fiware.urbanplatform.portodigital.pt/v2/entities?q=vehicleType==bus&limit=1)**: The URL you have to poll continuously.
* **[The Forbidden Subscriptions Endpoint](https://broker.fiware.urbanplatform.portodigital.pt/v2/subscriptions)**: A tantalizing glimpse at the real-time system you're not allowed to use.


## License

This project is under the MIT License. See the [LICENSE](LICENSE) file for details.