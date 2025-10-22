"""
Manual API test script for Rayden Rules API using mocks instead of real HTTP requests
"""

import json
import logging
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"  # Not actually used with mocks, kept for reference

# Mock response data
MOCK_RESPONSES = {
    "/": {"status_code": 200, "json": {"status": "ok", "message": "Rayden Rules API is running"}},
    "/v1/regions": {
        "status_code": 200,
        "json": [
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
                "bbox": [-87.9402, 41.6445, -87.5245, 42.0229],
                "type": "builtin",
            },
            {
                "id": "MIA001",
                "name": "Miami",
                "bbox": [-80.3187, 25.7095, -80.1155, 25.8901],
                "type": "builtin",
            },
            {
                "id": "CUSTOM001",
                "name": "Downtown Manhattan",
                "bbox": [-74.0315, 40.7002, -73.9701, 40.7382],
                "type": "custom",
            },
        ],
    },
    "/v1/metrics": {
        "status_code": 200,
        "json": {
            "region_id": "NYC001",
            "from": "2025-10-01",
            "to": "2025-10-10",
            "metrics": [
                {
                    "date": "2025-10-01",
                    "lst_mean_c": 23.4,
                    "cdd": 8.4,
                    "hdd": 0.0,
                    "heatwave_flag": 0,
                    "uhi_index": 3.2,
                    "anomaly_zscore": 1.2,
                },
                {
                    "date": "2025-10-02",
                    "lst_mean_c": 24.1,
                    "cdd": 9.1,
                    "hdd": 0.0,
                    "heatwave_flag": 0,
                    "uhi_index": 3.4,
                    "anomaly_zscore": 1.4,
                },
            ],
        },
    },
    "/v1/tiles/lst/10/100/200.png": {
        "status_code": 200,
        "json": {"url": "https://mock-cdn.example.com/tiles/lst/10/100/200.png"},
    },
    "/v1/regions_post": {
        "status_code": 200,
        "json": {
            "id": "CUSTOM002",
            "name": "API Test Region",
            "type": "custom",
            "status": "success",
            "created": "2025-10-21T14:30:00Z",
        },
    },
    "/v1/alerts": {
        "status_code": 200,
        "json": {
            "id": "ALERT001",
            "name": "API Test Alert",
            "region_id": "NYC001",
            "rule": "lst_mean_c > 30 for 2 days",
            "channel": "email",
            "recipients": "test@example.com",
            "status": "active",
            "created": "2025-10-21T14:30:00Z",
        },
    },
    "/v1/backfill": {
        "status_code": 200,
        "json": {
            "region_id": "NYC001",
            "job_id": "JOB001",
            "status": "queued",
            "estimated_completion_minutes": 15,
        },
    },
}


# Helper functions for testing individual endpoints
def test_root_endpoint():
    """Test the root endpoint"""
    logger.info("1. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        logger.info(f"Status: {response.status_code}")
        logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        logger.error(f"Error testing root endpoint: {e}")


def test_regions_endpoint():
    """Test the regions endpoint"""
    logger.info("2. Testing regions endpoint...")
    response = requests.get(f"{BASE_URL}/v1/regions")
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")


def test_metrics_endpoint():
    """Test the metrics endpoint"""
    logger.info("3. Testing metrics endpoint...")
    today = date.today()
    params = {
        "region_id": "NYC001",
        "from_date": str(today - timedelta(days=10)),
        "to_date": str(today),
        "vars": "lst_mean_c,cdd,hdd,heatwave_flag",
    }
    response = requests.get(f"{BASE_URL}/v1/metrics", params=params)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")


def test_tiles_endpoint():
    """Test the tiles endpoint"""
    logger.info("4. Testing tiles endpoint...")
    response = requests.get(f"{BASE_URL}/v1/tiles/lst/10/100/200.png")
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")


def test_create_region_endpoint():
    """Test the create region endpoint"""
    logger.info("5. Testing create region endpoint...")
    # Sample GeoJSON data
    sample_geojson = {
        "type": "Feature",
        "properties": {"name": "Test Area"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[-74.0, 40.7], [-73.9, 40.7], [-73.9, 40.8], [-74.0, 40.8], [-74.0, 40.7]]
            ],
        },
    }

    # With mocks, we don't need to create actual files
    files = {"geojson": ("test_region.geojson", json.dumps(sample_geojson), "application/json")}
    data = {"name": "API Test Region"}
    response = requests.post(f"{BASE_URL}/v1/regions", files=files, data=data)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")


def test_create_alert_endpoint():
    """Test the create alert endpoint"""
    logger.info("6. Testing create alert endpoint...")
    alert_data = {
        "name": "API Test Alert",
        "region_id": "NYC001",
        "rule": "lst_mean_c > 30 for 2 days",
        "channel": "email",
        "recipients": "test@example.com",
    }
    response = requests.post(f"{BASE_URL}/v1/alerts", json=alert_data)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")


def test_backfill_endpoint():
    """Test the backfill endpoint"""
    logger.info("7. Testing backfill endpoint...")
    today = date.today()
    backfill_data = {
        "region_id": "NYC001",
        "from_date": str(today - timedelta(days=30)),
        "to_date": str(today),
    }
    response = requests.post(f"{BASE_URL}/v1/backfill", json=backfill_data)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")


@patch("requests.get")
@patch("requests.post")
def test_all_endpoints(mock_post, mock_get):
    """Test all API endpoints using mocks instead of real HTTP requests"""
    logger.info("==== RAYDEN RULES API TEST ====")

    # Configure the mock responses
    def mock_response(endpoint, **kwargs):
        mock_resp = MagicMock()
        if endpoint in MOCK_RESPONSES:
            data = MOCK_RESPONSES[endpoint]
            mock_resp.status_code = data["status_code"]
            mock_resp.json.return_value = data["json"]
            mock_resp.text = json.dumps(data["json"])
        else:
            mock_resp.status_code = 404
            mock_resp.json.return_value = {"error": "Not found"}
            mock_resp.text = '{"error": "Not found"}'
        return mock_resp

    # Configure mocks
    mock_get.side_effect = lambda url, **kwargs: mock_response(url.replace(BASE_URL, ""))
    mock_post.side_effect = lambda url, **kwargs: mock_response(
        url.replace(BASE_URL, "") if not url.endswith("regions") else "/v1/regions_post"
    )

    # Run individual test functions
    test_root_endpoint()
    test_regions_endpoint()
    test_metrics_endpoint()
    test_tiles_endpoint()
    test_create_region_endpoint()
    test_create_alert_endpoint()
    test_backfill_endpoint()

    logger.info("==== TEST COMPLETE ====")


if __name__ == "__main__":
    # Run the tests with mocked API calls
    test_all_endpoints()


if __name__ == "__main__":
    test_all_endpoints()
