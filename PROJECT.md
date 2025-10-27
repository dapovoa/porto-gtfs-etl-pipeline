## Project Details: The Gory Internals

This was supposed to be a real-time bus tracker. It's not. It's now a glorified GTFS data processor and analytics platform. If you want to know why, the whole tragic story is in [API_LIMITATIONS.md](API_LIMITATIONS.md).

---

## Architecture: How I Bolted This Thing Together

I ended up with a pretty standard ETL pipeline, with a sad little add-on to poll the "real-time" API.

### The ETL Pipeline

1.  **Extract:** A script wakes up daily, scrapes Porto's Open Data Portal to find the latest GTFS zip file, and downloads it if it's newer than the one I already have.
2.  **Transform:** I use **Pandas** to wrestle with the 9 different types of GTFS files (`stops.txt`, `trips.txt`, etc.). This involves cleaning up some... *creative* data entries and getting it all into a sane format.
3.  **Load:** Everything gets dumped into a **PostgreSQL** database. I used two schemas: `raw` holds the data pretty much as-is, and `analytics` has a bunch of pre-calculated views that make the API and dashboard actually performant.

### Data Exposure

4.  **Expose:** A **FastAPI** service slings the data from the `analytics` schema, and a simple **Vanilla JS** dashboard with a **Leaflet** map tries to make sense of it all.

---

## The Tech Stack I Used

These are the tools I chose before I discovered the data was a dead end.

* **Python 3.x**: The language holding it all together.
* **Prefect 2**: For orchestrating the daily ETL pipeline.
* **PostgreSQL 16 + PostGIS**: The data warehouse. **PostGIS** is great for geographic queries.
* **FastAPI**: For the REST API. The automatic docs are a nice perk.
* **Pandas**: For the data transformation nightmare.
* **SQLAlchemy**: To talk to the database without writing raw SQL everywhere.
* **Docker Compose**: To run all of this in containers so I don't have to install it all manually.
* **Nginx**: As a reverse proxy in front of the FastAPI server.

---

## API Endpoints

I exposed a few endpoints to get at the processed GTFS data.

* `GET /api/kpi`: General stats (total stops, routes, etc.).
* `GET /api/paragens`: All the bus stops, for plotting on the map.
* `GET /api/linhas`: All the bus routes.
* `GET /api/top-stops`: The 10 busiest stops.

And then there's this one:

* `GET /api/fleet-status`: This hits the FIWARE API to get the "live" fleet status. It has a **10-second timeout** because the API is spectacularly slow. It still fails sometimes. That's a *feature* of their API, not a bug in my code.

Full **Swagger** docs are at `/api/docs` if you run the project.

---

## Known Issues & Quirks

* **FIWARE API Timeouts:** As mentioned, the `fleet-status` endpoint will time out. I can't fix their infrastructure.
* **GTFS Data Quality:** Porto's GTFS feed is special. Some stop names are just a single dot (`.`), and there are occasional invalid time formats. I added validation logic in the ETL script to handle this.
* **No Real-Time Bus Positions:** This is the main *feature* of this project. The fact that it doesn't exist. The API doesn't provide the data for it. This will never be "fixed" unless Porto has a fundamental change of heart about its infrastructure.

---

## Future Work (That Will Never Happen)

If the data source wasn't a lost cause, I would have built:

* Historical trend analysis.
* Service reliability reporting.
* Actual real-time position tracking.

But here we are. Feel free to fork this and adapt it for a city with a functional transit API.