"""
FastAPI backend for Rayden Rules Climate Analysis Platform
"""

import json
import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configuration
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"

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


def get_data_path():
    """Get the base data directory path"""
    # Try from current working directory first
    if os.path.exists("data"):
        return Path("data")
    # Fallback for development
    script_dir = Path(__file__).parent
    data_path = script_dir / ".." / ".." / ".." / "data"
    return data_path.resolve()


def load_region_metrics(region_id: str):
    """
    Load metrics data for a specific region.

    Args:
        region_id: Region identifier (e.g., 'NYC001')

    Returns:
        Dictionary with region metrics data
    """
    data_path = get_data_path()

    if USE_MOCK_DATA:
        # Load mock data
        mock_path = data_path / "01_raw" / "data_samples" / "metrics_mock.json"
        with open(mock_path) as f:
            return json.load(f)
    else:
        # Load real data from gold feature layer
        gold_path = data_path / "04_feature" / "metrics_by_region" / f"{region_id}.json"
        if not gold_path.exists():
            raise FileNotFoundError(f"No data found for region {region_id}")
        with open(gold_path) as f:
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


class Alert(BaseModel):
    name: str
    region_id: str
    rule: str
    channel: str
    recipients: str


# Routes
@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Rayden Rules API is running",
        "version": "0.1.0",
        "mode": "mock" if USE_MOCK_DATA else "production",
        "data_source": "mock metrics" if USE_MOCK_DATA else "gold feature layer",
    }


@app.get("/v1/regions")
def get_regions():
    """List available regions (both built-in and custom)"""
    if USE_MOCK_DATA:
        # Return static mock regions
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
    else:
        # Load regions from gold feature layer
        try:
            data_path = get_data_path()
            gold_metrics_path = data_path / "04_feature" / "metrics_by_region"

            regions = []
            if gold_metrics_path.exists():
                for json_file in gold_metrics_path.glob("*.json"):
                    with open(json_file) as f:
                        data = json.load(f)
                        meta = data.get("meta", {})
                        regions.append(
                            {
                                "id": meta.get("region_id", json_file.stem),
                                "name": meta.get("region_name", json_file.stem),
                                "bbox": meta.get("bbox"),
                                "type": "builtin",
                                "last_updated": meta.get("last_updated"),
                            }
                        )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading regions: {str(e)}")

    return regions


@app.get("/v1/metrics")
def get_metrics(
    region_id: str = Query(..., description="Region identifier"),
    from_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    vars: str = Query(
        "lst_mean_c,cdd,hdd,heatwave_flag,uhi_index,anomaly_zscore",
        description="Comma-separated list of variables to include",
    ),
):
    """Get climate metrics for a region within a date range"""

    # Parse requested variables
    requested_vars = vars.split(",")

    # Load data for the region
    try:
        data = load_region_metrics(region_id)
        metrics = data.get("metrics", [])

        # Filter metrics by date range if specified
        filtered_metrics = []
        for metric in metrics:
            metric_date = metric.get("date")

            # Apply date range filter if specified
            if from_date and metric_date < from_date:
                continue
            if to_date and metric_date > to_date:
                continue

            # Filter metrics to include only requested variables
            filtered_metric = {var: metric[var] for var in requested_vars if var in metric}
            filtered_metric["date"] = metric_date  # Always include date
            filtered_metrics.append(filtered_metric)

        return {
            "region_id": region_id,
            "from": from_date or (filtered_metrics[0]["date"] if filtered_metrics else None),
            "to": to_date or (filtered_metrics[-1]["date"] if filtered_metrics else None),
            "count": len(filtered_metrics),
            "metrics": filtered_metrics,
            "meta": data.get("meta", {}),
            "kpi_summary": data.get("kpi_summary", {}),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
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


# Run with: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
