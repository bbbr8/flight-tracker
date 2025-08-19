"""
Flight Tracker application using FastAPI.

This simple service allows users to track the live position of an aircraft by
its callsign (flight number) using the free OpenSky Network API.  Because
OpenSky does not require an API key for its public endpoints, this app can
function out of the box without additional configuration.  It fetches the
current state vector for all observed aircraft and searches for the
user‑provided callsign.

Endpoints
~~~~~~~~~

* ``GET /`` – Serves the HTML front‑end.
* ``GET /track`` – Accepts a ``callsign`` query parameter and returns
  information about the matching flight if found.

To run this service locally, install the dependencies listed in
``requirements.txt`` and start the application with Uvicorn::

    pip install -r requirements.txt
    uvicorn main:app --reload

Then open your browser to ``http://localhost:8000``.
"""

from pathlib import Path
from typing import Any, Dict

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


# Initialize FastAPI application
app = FastAPI(title="Flight Tracker", version="0.1.0")

# Determine the static directory relative to this file
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the landing page from the static directory."""
    index_file = STATIC_DIR / "index.html"
    return HTMLResponse(index_file.read_text())


async def fetch_flight_state(callsign: str) -> Dict[str, Any]:
    """Fetch the state vector for a given callsign from the OpenSky API.

    Parameters
    ----------
    callsign: str
        The flight number or callsign to look up (e.g., ``AA123``).

    Returns
    -------
    dict
        A dictionary containing key flight attributes such as position and
        velocity.  Raises ``HTTPException`` if the flight cannot be found or
        if the external API request fails.
    """
    # Endpoint for retrieving all state vectors
    url = "https://opensky-network.org/api/states/all"
    # Normalize callsign by stripping whitespace and uppercasing
    callsign_clean = callsign.strip().upper()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch data from OpenSky API")
        data = resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Error contacting OpenSky API: {exc}") from exc

    states = data.get("states", []) or []
    # Search through the list of state vectors; each state is a list defined by the API
    for state in states:
        # state[1] is the callsign; it may be None or padded with spaces
        state_callsign = (state[1] or "").strip().upper()
        if state_callsign == callsign_clean:
            return {
                "icao24": state[0],
                "callsign": state_callsign,
                "origin_country": state[2],
                "time_position": state[3],
                "last_contact": state[4],
                "longitude": state[5],
                "latitude": state[6],
                "baro_altitude": state[7],
                "on_ground": state[8],
                "velocity": state[9],
                "true_track": state[10],
                "vertical_rate": state[11],
                # state[12] is sensors (ignored here)
                "geo_altitude": state[13],
                "squawk": state[14],
                "spi": state[15],
                "position_source": state[16],
            }
    # If we reach this point, the flight was not found
    raise HTTPException(status_code=404, detail="Flight not found or not currently tracked")


@app.get("/track")
async def track_flight(callsign: str = Query(..., description="Flight number or callsign (e.g., AA123)")) -> Dict[str, Any]:
    """Endpoint to track a flight by callsign.

    Returns JSON data describing the flight's last known state.  If the
    callsign does not match any state vectors, a 404 error is returned.
    """
    return await fetch_flight_state(callsign)
