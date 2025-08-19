from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any
import httpx

app = FastAPI(title="Flight Tracker", version="0.2.0")

# Configure static directory
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the front-end page."""
    index_file = STATIC_DIR / "index.html"
    return HTMLResponse(index_file.read_text())

async def fetch_flight_state(callsign: str) -> Dict[str, Any]:
    """Retrieve a single aircraft’s state vector by callsign."""
    url = "https://opensky-network.org/api/states/all"
    callsign_clean = callsign.strip().upper()
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch from OpenSky API")
    for state in resp.json().get("states", []) or []:
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
                "heading": state[10],
                "vertical_rate": state[11],
                "geo_altitude": state[13],
                "squawk": state[14],
                "spi": state[15],
                "position_source": state[16],
            }
    raise HTTPException(status_code=404, detail="Flight not found or not currently tracked")

@app.get("/track")
async def track_flight(callsign: str = Query(..., description="Flight number or callsign (e.g. AA123)")) -> Dict[str, Any]:
    """Endpoint to look up a single flight by callsign."""
    return await fetch_flight_state(callsign)

@app.get("/region")
async def region(
    lamin: float = Query(..., description="Minimum latitude (south)"),
    lomin: float = Query(..., description="Minimum longitude (west)"),
    lamax: float = Query(..., description="Maximum latitude (north)"),
    lomax: float = Query(..., description="Maximum longitude (east)")
) -> JSONResponse:
    """Return all flights in a bounding box."""
    url = "https://opensky-network.org/api/states/all"
    params = {"lamin": lamin, "lomin": lomin, "lamax": lamax, "lomax": lomax}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch region data")
    flights = []
    for s in resp.json().get("states", []) or []:
        callsign = (s[1] or "").strip()
        flights.append({
            "icao24": s[0],
            "callsign": callsign,
            "origin_country": s[2],
            "longitude": s[5],
            "latitude": s[6],
            "altitude": s[7],
            "velocity": s[9],
            "heading": s[10],
        })
    return JSONResponse(flights)
