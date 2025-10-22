"""
Manual API test script for Rayden Rules API
"""

import json
import logging
import os
from datetime import date, timedelta

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"


def test_all_endpoints():
    """Test all API endpoints and log results"""
    logger.info("==== RAYDEN RULES API TEST ====")

    # Test 1: Root endpoint
    logger.info("1. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 2: Regions endpoint
    logger.info("2. Testing regions endpoint...")
    response = requests.get(f"{BASE_URL}/v1/regions")
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 3: Metrics endpoint
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

    # Test 4: Tiles endpoint
    logger.info("4. Testing tiles endpoint...")
    response = requests.get(f"{BASE_URL}/v1/tiles/lst/10/100/200.png")
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test 5: Create region endpoint
    logger.info("5. Testing create region endpoint...")
    # Create a sample GeoJSON file if it doesn't exist
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

    with open("test_region.geojson", "w") as f:
        json.dump(sample_geojson, f)

    try:
        with open("test_region.geojson", "rb") as f:
            files = {"geojson": ("test_region.geojson", f, "application/json")}
            data = {"name": "API Test Region"}
            response = requests.post(f"{BASE_URL}/v1/regions", files=files, data=data)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
    finally:
        # Clean up
        if os.path.exists("test_region.geojson"):
            os.remove("test_region.geojson")

    # Test 6: Create alert endpoint
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

    # Test 7: Backfill endpoint
    logger.info("7. Testing backfill endpoint...")
    backfill_data = {
        "region_id": "NYC001",
        "from_date": str(today - timedelta(days=30)),
        "to_date": str(today),
    }
    response = requests.post(f"{BASE_URL}/v1/backfill", json=backfill_data)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")

    logger.info("==== TEST COMPLETE ====")


if __name__ == "__main__":
    test_all_endpoints()
