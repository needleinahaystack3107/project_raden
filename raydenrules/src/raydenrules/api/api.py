"""
FastAPI backend for Rayden Rules Climate Analysis Platform
"""

import json
import os
from datetime import date

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Rayden Rules API",
    description="API for Climate Analysis and Heat Monitoring Platform",
    version="0.1.0",
)

# Add CORS middleware to allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load mock data
def load_mock_data():
    """Load mock metrics data from JSON file"""
    # Path is relative to the API running directory
    try:
        data_path = "data/01_raw/data_samples/metrics_mock.json"
        with open(data_path) as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback for development
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(
            script_dir, "..", "..", "..", "data", "01_raw", "data_samples", "metrics_mock.json"
        )
        with open(data_path) as f:
            return json.load(f)


# Models
class Region(BaseModel):
    id: str
    name: str
    bbox: list[float]
    type: str


class Metric(BaseModel):
    date: str
    lst_mean_c: float
    cdd: float
    hdd: float
    heatwave_flag: int
    uhi_index: float
    anomaly_zscore: float


class BackfillRequest(BaseModel):
    region_id: str
    from_date: date
    to_date: date


class Alert(BaseModel):
    name: str
    region_id: str
    rule: str
    channel: str
    recipients: str


# Routes
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Rayden Rules API is running"}


@app.get("/v1/regions")
def get_regions():
    """List available regions (both built-in and custom)"""
    regions = [
        {
            "id": "NYC001",
            "name": "New York City",
            "bbox": [-74.2589, 40.4774, -73.7004, 40.9176],
            "type": "builtin",
        },
        {
            "id": "LAX001",
            "name": "Los Angeles",
            "bbox": [-118.6682, 33.7037, -118.1553, 34.3373],
            "type": "builtin",
        },
        {
            "id": "CHI001",
            "name": "Chicago",
            "bbox": [-87.9402, 41.6446, -87.5241, 42.0230],
            "type": "builtin",
        },
        {
            "id": "MIA001",
            "name": "Miami",
            "bbox": [-80.3198, 25.7095, -80.1398, 25.8557],
            "type": "builtin",
        },
        {
            "id": "CUSTOM001",
            "name": "Downtown Manhattan",
            "bbox": [-74.0151, 40.7001, -73.9696, 40.7310],
            "type": "custom",
        },
    ]
    return regions


@app.get("/v1/metrics")
def get_metrics(
    region_id: str = Query(..., description="Region identifier"),
    from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    vars: str = Query(
        "lst_mean_c,cdd,hdd,heatwave_flag,uhi_index,anomaly_zscore",
        description="Comma-separated list of variables to include",
    ),
):
    """Get climate metrics for a region within a date range"""

    # Parse requested variables
    requested_vars = vars.split(",")

    # Load mock data
    try:
        data = load_mock_data()
        metrics = data["metrics"]

        # Filter metrics by date range (simplified for mock data)
        filtered_metrics = []
        for metric in metrics:
            # Filter metrics to include only requested variables
            filtered_metric = {var: metric[var] for var in requested_vars if var in metric}
            filtered_metric["date"] = metric["date"]  # Always include date
            filtered_metrics.append(filtered_metric)

        return {
            "region_id": region_id,
            "from": from_date,
            "to": to_date,
            "metrics": filtered_metrics,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/tiles/{layer}/{z}/{x}/{y}.png")
def get_tile(
    layer: str,
    z: int,
    x: int,
    y: int,
    date: str = Query(None, description="Optional date (YYYY-MM-DD)"),
):
    """Get map tile for specified layer"""
    # In a real implementation, this would generate or retrieve a tile from S3/CloudFront
    # For the POC, we'll simulate a URL return

    # Mock CloudFront URL
    tile_url = f"https://mock-cdn.example.com/tiles/{layer}/{z}/{x}/{y}.png"
    if date:
        tile_url += f"?date={date}"

    return {"url": tile_url}


@app.post("/v1/regions")
async def create_region(name: str = Form(...), geojson: UploadFile = File(...)):
    """Upload a new region as GeoJSON"""
    # In a real implementation, this would:
    # 1. Validate the GeoJSON
    # 2. Store it in S3
    # 3. Register it in a database

    # For the POC, we'll just return a mock response
    return {
        "id": "CUSTOM002",
        "name": name,
        "type": "custom",
        "created": str(date.today()),
        "status": "success",
    }


@app.post("/v1/alerts")
async def create_alert(alert: Alert):
    """Create a new alert rule"""
    # In a real implementation, this would store the alert in a database
    return {
        "id": "alert-003",
        "name": alert.name,
        "region_id": alert.region_id,
        "rule": alert.rule,
        "channel": alert.channel,
        "recipients": alert.recipients,
        "status": "active",
        "created": str(date.today()),
    }


@app.post("/v1/backfill")
async def request_backfill(request: BackfillRequest):
    """Request a data backfill for a region and date range"""
    # In a real implementation, this would:
    # 1. Validate the request
    # 2. Enqueue an SQS job
    # 3. Return a job ID

    return {
        "job_id": f"BF-{date.today().strftime('%Y-%m-%d')}-001",
        "region_id": request.region_id,
        "from_date": request.from_date,
        "to_date": request.to_date,
        "status": "queued",
        "estimated_completion_minutes": 15,
    }


# Run with: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
