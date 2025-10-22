"""
Unit tests for the Rayden Rules API endpoints
"""

import json

# Import the FastAPI app
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.raydenrules.api.api import app

# Create a test client
client = TestClient(app)

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_422_UNPROCESSABLE_ENTITY = 422

# Other constants
MIN_REGIONS = 4  # Minimum number of regions expected in API response

# Mock data for tests
MOCK_DATA = {
    "meta": {
        "region_id": "NYC001",
        "region_name": "New York City",
        "bbox": [-74.2589, 40.4774, -73.7004, 40.9176],
    },
    "metrics": [
        {
            "date": "2025-10-01",
            "lst_mean_c": 23.4,
            "cdd": 8.4,
            "hdd": 0.0,
            "heatwave_flag": 0,
            "uhi_index": 3.2,
            "anomaly_zscore": 1.2,
        }
    ],
    "kpi_summary": {
        "ytd": {
            "avg_lst_c": 24.3,
            "heatwave_days": 4,
            "max_uhi_index": 4.7,
            "max_anomaly_zscore": 3.0,
        },
        "today": {"lst_mean_c": 19.5, "cdd": 4.5, "hdd": 0.0, "anomaly_zscore": 0.0},
    },
}


# Tests
def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok", "message": "Rayden Rules API is running"}


def test_get_regions():
    """Test the regions endpoint"""
    response = client.get("/v1/regions")
    assert response.status_code == HTTP_200_OK
    regions = response.json()
    assert len(regions) >= MIN_REGIONS  # At least 4 regions should be returned
    assert all(
        "id" in region and "name" in region and "bbox" in region and "type" in region
        for region in regions
    )

    # Check if NYC is in the list
    nyc = next((region for region in regions if region["id"] == "NYC001"), None)
    assert nyc is not None
    assert nyc["name"] == "New York City"


@patch("src.raydenrules.api.api.load_mock_data")
def test_get_metrics(mock_load_data):
    """Test the metrics endpoint"""
    # Mock the data loading function
    mock_load_data.return_value = MOCK_DATA

    # Test with required parameters
    response = client.get("/v1/metrics?region_id=NYC001&from_date=2025-10-01&to_date=2025-10-10")
    assert response.status_code == HTTP_200_OK
    data = response.json()

    assert data["region_id"] == "NYC001"
    assert data["from"] == "2025-10-01"
    assert data["to"] == "2025-10-10"
    assert "metrics" in data
    assert len(data["metrics"]) > 0

    # Test with specific variables
    response = client.get(
        "/v1/metrics?region_id=NYC001&from_date=2025-10-01&to_date=2025-10-10&vars=lst_mean_c,cdd"
    )
    assert response.status_code == HTTP_200_OK
    data = response.json()

    # Check that only requested variables are included (plus date which is always included)
    assert all(
        set(metric.keys()).issubset({"date", "lst_mean_c", "cdd"}) for metric in data["metrics"]
    )


def test_get_tile():
    """Test the tile endpoint"""
    response = client.get("/v1/tiles/lst/10/100/200.png")
    assert response.status_code == HTTP_200_OK
    assert "url" in response.json()
    assert "https://mock-cdn.example.com/tiles/lst/10/100/200.png" == response.json()["url"]

    # Test with date parameter
    response = client.get("/v1/tiles/lst/10/100/200.png?date=2025-10-01")
    assert response.status_code == HTTP_200_OK
    assert "url" in response.json()
    assert (
        "https://mock-cdn.example.com/tiles/lst/10/100/200.png?date=2025-10-01"
        == response.json()["url"]
    )


def test_create_region():
    """Test the region creation endpoint"""
    # Create a mock GeoJSON file
    mock_geojson = json.dumps(
        {
            "type": "Feature",
            "properties": {"name": "Test Region"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[-74.0, 40.7], [-73.9, 40.7], [-73.9, 40.8], [-74.0, 40.8], [-74.0, 40.7]]
                ],
            },
        }
    )

    response = client.post(
        "/v1/regions",
        files={"geojson": ("test.geojson", mock_geojson, "application/json")},
        data={"name": "Test Region"},
    )

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Region"
    assert data["type"] == "custom"
    assert "id" in data
    assert "created" in data
    assert data["status"] == "success"


def test_create_alert():
    """Test the alert creation endpoint"""
    alert_data = {
        "name": "Test Alert",
        "region_id": "NYC001",
        "rule": "heatwave_flag >= 1 for 3 days",
        "channel": "email",
        "recipients": "test@example.com",
    }

    response = client.post("/v1/alerts", json=alert_data)

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Alert"
    assert data["region_id"] == "NYC001"
    assert data["rule"] == "heatwave_flag >= 1 for 3 days"
    assert data["channel"] == "email"
    assert data["recipients"] == "test@example.com"
    assert data["status"] == "active"
    assert "id" in data
    assert "created" in data


def test_request_backfill():
    """Test the backfill request endpoint"""
    today = date.today()
    backfill_data = {
        "region_id": "NYC001",
        "from_date": str(today - timedelta(days=30)),
        "to_date": str(today),
    }

    response = client.post("/v1/backfill", json=backfill_data)

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["region_id"] == "NYC001"
    assert "job_id" in data
    assert data["status"] == "queued"
    assert "estimated_completion_minutes" in data


# Additional test for error handling
def test_get_metrics_missing_params():
    """Test the metrics endpoint with missing parameters"""
    # Missing region_id
    response = client.get("/v1/metrics?from_date=2025-10-01&to_date=2025-10-10")
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY  # Unprocessable Entity

    # Missing from_date
    response = client.get("/v1/metrics?region_id=NYC001&to_date=2025-10-10")
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    # Missing to_date
    response = client.get("/v1/metrics?region_id=NYC001&from_date=2025-10-01")
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
