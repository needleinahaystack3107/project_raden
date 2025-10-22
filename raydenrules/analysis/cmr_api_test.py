"""
Direct test script for CMR API functionality
"""

import json
import logging
from datetime import datetime, timedelta

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("cmr_api_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# CMR API base URL
CMR_BASE_URL = "https://cmr.earthdata.nasa.gov/search"

# Constants
MAX_RESPONSE_SIZE = 1000  # Max size for detailed logging


def test_cmr_direct_query():
    """
    Direct test of CMR API without going through our application code
    """
    # Chicago region coordinates
    bbox = [-87.9402, 41.6446, -87.5241, 42.023]

    # Test parameters - using 2023 data (recent but not future)
    params = {
        "short_name": "MOD11A1",
        "page_size": 10,
        "temporal": "2023-06-01T00:00:00Z,2023-06-30T23:59:59Z",
        "bounding_box": ",".join(str(coord) for coord in bbox),
        "provider": "LPDAAC_ECS",
    }

    logger.info(f"Testing CMR API with params: {params}")
    url = f"{CMR_BASE_URL}/granules.json"

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        logger.info(f"Response status code: {response.status_code}")

        result = response.json()
        logger.info(f"API Response structure: {list(result.keys())}")

        # Print the full structure if the response is very small
        if len(json.dumps(result)) < MAX_RESPONSE_SIZE:
            logger.debug(f"Full response: {json.dumps(result, indent=2)}")

        # Print the number of granules found
        granule_count = len(result.get("feed", {}).get("entry", []))
        logger.info(f"Found {granule_count} granules in the response")

        # Print the first granule if any were found
        if granule_count > 0:
            logger.info("First granule details:")
            logger.debug(json.dumps(result["feed"]["entry"][0], indent=2))
        else:
            logger.warning("No granules found. This suggests either:")
            logger.warning("1. The API may not be responding with data as expected")
            logger.warning("2. Your search criteria may be too restrictive")
            logger.warning("3. There genuinely may not be data for this region/time period")
            logger.warning("4. You might need authentication to access this data")

        return result
    except requests.RequestException as e:
        logger.error(f"Error querying CMR API: {e}")
        return None


# Try a second query with different parameters
def test_cmr_alternate_query():
    """
    Test with a different product and date range
    """
    params = {
        "short_name": "MOD13Q1",  # NDVI product
        "page_size": 10,
        "temporal": "2020-01-01T00:00:00Z,2020-12-31T23:59:59Z",  # Full year 2020
    }

    logger.info(f"Trying alternate query with params: {params}")
    url = f"{CMR_BASE_URL}/granules.json"

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        # Print the number of granules found
        granule_count = len(result.get("feed", {}).get("entry", []))
        logger.info(f"Found {granule_count} granules in the response")

        # Print the first granule if any were found
        if granule_count > 0:
            logger.info("Success! API is working but may need parameter adjustments.")
            logger.info("First granule details:")
            entry = result["feed"]["entry"][0]
            # Just print key info
            logger.info(f"Title: {entry.get('title')}")
            logger.info(f"ID: {entry.get('id')}")
            logger.info(f"Time: {entry.get('time_start')} to {entry.get('time_end')}")
        else:
            logger.warning("No granules found with alternate parameters either.")

        return result
    except requests.RequestException as e:
        logger.error(f"Error querying CMR API: {e}")
        return None


def test_recent_lst_data():  # noqa: PLR0912, PLR0915
    """
    Test specifically for recent MOD11A1 (Land Surface Temperature) data
    Try multiple time periods to see what's available
    """
    logger.info("=== TESTING FOR RECENT LST (MOD11A1) DATA ===")

    # Chicago region coordinates
    chicago_bbox = [-87.9402, 41.6446, -87.5241, 42.023]
    # Try a slightly larger area around Chicago
    expanded_chicago_bbox = [-88.5, 41.0, -87.0, 42.5]

    # New York region for comparison
    nyc_bbox = [-74.2589, 40.4774, -73.7004, 40.9176]

    # Try multiple time periods
    time_periods = [
        ("2023 (Recent)", "2023-06-01T00:00:00Z,2023-06-30T23:59:59Z"),
        ("2022 (Full year)", "2022-01-01T00:00:00Z,2022-12-31T23:59:59Z"),
    ]

    # Test with specific version V061
    logger.info("Testing with specific MOD11A1 V061 collection:")

    # Try with different product specifications for V061
    product_variants = [
        ("MOD11A1", "Standard short name"),
        ("MOD11A1.061", "Version-specific short name"),
        (
            "C2237679601-LPCLOUD",
            "MODIS Collection 6.1 concept ID",
        ),  # This is the concept ID for MOD11A1 V061
    ]

    for product_name, desc in product_variants:
        logger.info(f"Trying with {desc}: {product_name}")
        params = {
            "temporal": "2023-01-01T00:00:00Z,2023-06-30T23:59:59Z",
            "page_size": 5,
        }

        # Add the appropriate parameter based on product type
        if product_name.startswith("C"):
            params["concept_id"] = product_name
        else:
            params["short_name"] = product_name

        url = f"{CMR_BASE_URL}/granules.json"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            granule_count = len(result.get("feed", {}).get("entry", []))
            if granule_count > 0:
                first_granule = result["feed"]["entry"][0]
                logger.info(f"Found {granule_count} granules without location filter")
                logger.info(
                    f"Example: {first_granule.get('title')} ({first_granule.get('time_start')})"
                )

                # If we find granules without location, try with Chicago location
                logger.info("Testing with Chicago location:")
                location_params = params.copy()
                location_params["bounding_box"] = ",".join(str(coord) for coord in chicago_bbox)

                location_response = requests.get(url, params=location_params)
                location_response.raise_for_status()
                location_result = location_response.json()

                location_count = len(location_result.get("feed", {}).get("entry", []))
                if location_count > 0:
                    logger.info(f"Found {location_count} granules WITH Chicago location filter")
                else:
                    logger.warning("No granules found when adding Chicago location filter")
            else:
                logger.warning("No granules found for this product variant")

        except requests.RequestException as e:
            logger.error(f"Error: {e}")

    # Test each time period with both Chicago and NYC regions using standard approach
    for region_name, bbox in [
        ("Chicago", chicago_bbox),
        ("Chicago (expanded)", expanded_chicago_bbox),
        ("New York", nyc_bbox),
    ]:
        logger.info(f"Searching for MOD11A1 data in {region_name} region:")

        for period_name, temporal in time_periods:
            params = {
                "short_name": "MOD11A1",
                "page_size": 5,
                "temporal": temporal,
                "bounding_box": ",".join(str(coord) for coord in bbox),
                "provider": "LPDAAC_ECS",
            }

            url = f"{CMR_BASE_URL}/granules.json"

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                result = response.json()

                granule_count = len(result.get("feed", {}).get("entry", []))
                if granule_count > 0:
                    first_granule = result["feed"]["entry"][0]
                    logger.info(
                        f"{period_name}: Found {granule_count} granules - Example: {first_granule.get('title')} ({first_granule.get('time_start')})"
                    )
                else:
                    logger.warning(f"{period_name}: No data found")

            except requests.RequestException as e:
                logger.error(f"{period_name}: Error - {e}")


def test_alternative_temp_products():
    """
    Test for alternative temperature data products from MODIS/VIIRS
    """
    logger.info("=== TESTING ALTERNATIVE TEMPERATURE PRODUCTS ===")

    # Chicago region coordinates
    chicago_bbox = [-87.9402, 41.6446, -87.5241, 42.023]

    # List of alternative temperature products to try
    alternative_products = [
        (
            "MYD11A1",
            "MODIS Aqua Land Surface Temperature (similar to MOD11A1 but from Aqua satellite)",
        ),
        ("MOD11A2", "MODIS Terra Land Surface Temperature 8-Day"),
        ("MOD11B1", "MODIS Terra Land Surface Temperature/Emissivity Daily 6km"),
        ("MOD11C1", "MODIS Terra Land Surface Temperature/Emissivity Daily 0.05Deg"),
        ("VNP21", "VIIRS Land Surface Temperature"),
    ]

    for product, description in alternative_products:
        logger.info(f"Testing {product}: {description}")
        params = {
            "short_name": product,
            "page_size": 5,
            "temporal": "2023-01-01T00:00:00Z,2023-06-30T23:59:59Z",
        }

        url = f"{CMR_BASE_URL}/granules.json"

        try:
            # First test without location to see if product exists
            response = requests.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            granule_count = len(result.get("feed", {}).get("entry", []))
            if granule_count > 0:
                first_granule = result["feed"]["entry"][0]
                logger.info(f"Found {granule_count} granules without location filter")
                logger.info(
                    f"Example: {first_granule.get('title')} ({first_granule.get('time_start')})"
                )

                # Now test with Chicago location
                location_params = params.copy()
                location_params["bounding_box"] = ",".join(str(coord) for coord in chicago_bbox)

                location_response = requests.get(url, params=location_params)
                location_response.raise_for_status()
                location_result = location_response.json()

                location_count = len(location_result.get("feed", {}).get("entry", []))
                if location_count > 0:
                    first_loc_granule = location_result["feed"]["entry"][0]
                    logger.info(f"Found {location_count} granules WITH Chicago location filter")
                    logger.info(
                        f"Example: {first_loc_granule.get('title')} ({first_loc_granule.get('time_start')})"
                    )
                else:
                    logger.warning("No granules found when adding Chicago location filter")
            else:
                logger.warning("No granules found for this product")

        except requests.RequestException as e:
            logger.error(f"Error: {e}")


def test_very_recent_data():
    """
    Test for very recent data (last week) across all temperature products
    """
    logger.info("=== TESTING FOR VERY RECENT TEMPERATURE DATA (LAST WEEK) ===")

    # Calculate date range for last week
    today = datetime.now()
    one_week_ago = today - timedelta(days=7)

    # Format dates in ISO 8601
    end_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    start_date = one_week_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    temporal_range = f"{start_date},{end_date}"
    logger.info(f"Testing date range: {start_date} to {end_date}")

    # Chicago region coordinates
    chicago_bbox = [-87.9402, 41.6446, -87.5241, 42.023]
    chicago_bbox_str = ",".join(str(coord) for coord in chicago_bbox)

    # All temperature products to test
    all_products = [
        "MOD11A1",  # Terra LST Daily 1km
        "MOD11B1",  # Terra LST Daily 6km
        "MOD11C1",  # Terra LST Daily 0.05°
        "MOD11A2",  # Terra LST 8-Day
        "MYD11A1",  # Aqua LST Daily 1km
        "VNP21",  # VIIRS LST
    ]

    for product in all_products:
        logger.info(f"Checking for recent {product} data:")

        # Try with no location first
        params = {
            "short_name": product,
            "page_size": 5,
            "temporal": temporal_range,
        }

        url = f"{CMR_BASE_URL}/granules.json"

        try:
            # First test without location to see if product exists
            response = requests.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            granule_count = len(result.get("feed", {}).get("entry", []))
            if granule_count > 0:
                most_recent = None
                most_recent_date = None

                # Find the most recent granule
                for granule in result.get("feed", {}).get("entry", []):
                    granule_date = granule.get("time_start")
                    if most_recent_date is None or granule_date > most_recent_date:
                        most_recent = granule
                        most_recent_date = granule_date

                logger.info(f"Found {granule_count} recent granules without location filter")
                logger.info(f"Most recent: {most_recent.get('title')} ({most_recent_date})")

                # Try with Chicago location
                location_params = params.copy()
                location_params["bounding_box"] = chicago_bbox_str

                location_response = requests.get(url, params=location_params)
                location_response.raise_for_status()
                location_result = location_response.json()

                location_count = len(location_result.get("feed", {}).get("entry", []))
                if location_count > 0:
                    # Find the most recent Chicago granule
                    most_recent_chicago = None
                    most_recent_chicago_date = None

                    for granule in location_result.get("feed", {}).get("entry", []):
                        granule_date = granule.get("time_start")
                        if (
                            most_recent_chicago_date is None
                            or granule_date > most_recent_chicago_date
                        ):
                            most_recent_chicago = granule
                            most_recent_chicago_date = granule_date

                    logger.info(f"Found {location_count} recent granules FOR CHICAGO")
                    logger.info(
                        f"Most recent: {most_recent_chicago.get('title')} ({most_recent_chicago_date})"
                    )
                else:
                    logger.warning("No recent Chicago granules found")
            else:
                logger.warning("No recent granules found for this product")

        except requests.RequestException as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    logger.info("=== CMR API TEST ===")
    # Comment out previous tests to focus only on the new one
    # test_cmr_direct_query()
    # test_cmr_alternate_query()
    # test_recent_lst_data()
    # test_alternative_temp_products()
    test_very_recent_data()
