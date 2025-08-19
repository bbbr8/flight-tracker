# Flight Tracker

This project is a simple flight tracker built with **FastAPI** and plain HTML/JavaScript.  It
uses the [OpenSky Network](https://opensky-network.org/) live API to retrieve
state vectors for all aircraft currently being tracked and then filters that
data by the callsign you provide.  Because OpenSky’s public API does not
require a key for basic usage, you can test this application without signing
up for any service.

## Features

* Track the live position of an aircraft by entering its flight number or callsign (e.g., `AA123`).
* Displays details such as latitude, longitude, altitude, speed, and origin country.
* No API key required – the app fetches data directly from the free OpenSky API【344555760163538†L16-L22】.

## Running locally

1. **Clone this repository** and navigate into the `flight-tracker` directory.
2. **Install dependencies** using pip:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the server** with Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```
4. Open your browser at `http://localhost:8000`.  Enter a flight callsign (for example, `UAL123`) and click **Track Flight** to see its current position.

## How it works

The FastAPI back end exposes two endpoints:

| Endpoint | Description |
|---------|-------------|
| `GET /` | Serves the front‑end HTML page. |
| `GET /track?callsign=ABC123` | Calls the OpenSky API, searches for the specified callsign and returns its state vector.  If the flight is not found, it returns a 404 error. |

When you click **Track Flight** on the web page, a JavaScript function sends a request to `/track` with your callsign.  The server fetches the latest data from OpenSky, finds the matching flight and returns information such as latitude, longitude, altitude, and velocity.  The page then displays this information as formatted JSON.

## Limitations

* The free OpenSky API is intended for research and non‑commercial use and does **not** provide scheduled flight data or detailed statuses【344555760163538†L16-L22】.  It only returns raw position information derived from ADS‑B broadcasts.
* Because it scans all state vectors, the `/track` endpoint may take a few seconds to respond when the airspace is busy.
* The aircraft must be airborne and broadcasting ADS‑B messages for the API to find it.  If a flight is on the ground or not broadcasting, it will not appear.

If you need richer data (schedules, flight status, delay information, etc.), consider using other flight APIs such as Aviationstack or FlightAware’s AeroAPI; note that those services require an API key and have limited free tiers【815571890606209†L15-L33】【148047195579680†L311-L349】.
