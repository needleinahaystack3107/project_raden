"""
Analyze CMR API response structure for LST products.
This will help us identify which products have compatible structures.
"""

import logging
from datetime import datetime, timedelta

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("lst_structure_analyzer.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Calculate dates for recent data (last 3 months)
today = datetime.now()
three_months_ago = today - timedelta(days=90)
end_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
start_date = three_months_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
temporal_range = f"{start_date},{end_date}"

# Chicago coordinates
chicago_bbox = [-87.9402, 41.6446, -87.5241, 42.023]
bbox_str = ",".join(str(coord) for coord in chicago_bbox)

# All LST products to test
lst_products = [
    "MOD11A1",  # Terra LST Daily 1km
    "MOD11B1",  # Terra LST Daily 6km
    "MOD11C1",  # Terra LST Daily 0.05°
    "MYD11A1",  # Aqua LST Daily 1km
    "VNP21",  # VIIRS LST
]


def get_product_structure(product_name):
    """Get API response structure for a specific product"""
    logger.info(f"\n======== {product_name} STRUCTURE ========")

    url = "https://cmr.earthdata.nasa.gov/search/granules.json"
    params = {
        "short_name": product_name,
        "temporal": temporal_range,
        "bounding_box": bbox_str,
        "page_size": 1,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Get entry if available
        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            logger.warning(f"No entries found for {product_name}")
            return None

        entry = entries[0]

        # Print basic structure info
        logger.info(f"Top-level keys: {list(data.keys())}")
        logger.info(f"Feed keys: {list(data['feed'].keys())}")
        logger.info(f"Entry keys count: {len(entry.keys())}")

        # Print time information
        if "time_start" in entry:
            logger.info(f"Time start: {entry['time_start']}")

        # Check for specific important fields
        key_fields = [
            "id",
            "title",
            "time_start",
            "time_end",
            "dataset_id",
            "granule_size",
            "browse_flag",
        ]
        for field in key_fields:
            if field in entry:
                present = "✓"
            else:
                present = "✗"
            logger.info(f"{field}: {present}")

        # Check links structure
        if "links" in entry and entry["links"]:
            logger.info("\nLinks structure:")
            sample_link = entry["links"][0]
            logger.info(f"Link keys: {list(sample_link.keys())}")
            if "rel" in sample_link:
                logger.info(f"Link relationships: {[link['rel'] for link in entry['links'][:3]]}")

        return entry
    except Exception as e:
        logger.error(f"Error getting data for {product_name}: {str(e)}")
        return None


def compare_structures(products, entries):
    """Compare structure of different products"""
    logger.info("\n======== STRUCTURE COMPARISON ========")

    if not all(entries.values()):
        logger.warning("Can't compare - some products didn't return data")
        return

    # Compare field sets
    common_fields = set(entries[products[0]].keys())
    for product in products[1:]:
        common_fields &= set(entries[product].keys())

    logger.info(f"Common fields across all products: {len(common_fields)}")
    logger.info(f"Common fields: {sorted(list(common_fields))}")

    # Compare important specific fields
    key_fields = ["time_start", "time_end", "id", "title", "links"]
    for field in key_fields:
        products_with_field = [p for p in products if field in entries[p]]
        logger.info(f"{field}: Found in {len(products_with_field)}/{len(products)} products")


def find_most_recent(products):
    """Find the most recent data across products"""
    logger.info("\n======== MOST RECENT DATA ========")

    most_recent_data = {}

    for product in products:
        url = "https://cmr.earthdata.nasa.gov/search/granules.json"
        params = {
            "short_name": product,
            "temporal": temporal_range,
            "bounding_box": bbox_str,
            "page_size": 10,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                logger.warning(f"No entries found for {product}")
                continue

            # Find most recent entry
            most_recent = None
            most_recent_date = None

            for entry in entries:
                if "time_start" not in entry:
                    continue

                date_str = entry["time_start"]
                if most_recent_date is None or date_str > most_recent_date:
                    most_recent = entry
                    most_recent_date = date_str

            if most_recent:
                most_recent_data[product] = {
                    "date": most_recent_date,
                    "title": most_recent.get("title", "Unknown"),
                }
                logger.info(f"{product}: Most recent data is {most_recent_date}")

        except Exception as e:
            logger.error(f"Error getting most recent data for {product}: {str(e)}")

    # Find overall most recent
    if most_recent_data:
        overall_most_recent = max(most_recent_data.items(), key=lambda x: x[1]["date"])
        logger.info(
            f"\nOverall most recent: {overall_most_recent[0]} - {overall_most_recent[1]['date']}"
        )
    else:
        logger.info("\nNo recent data found for any product")


if __name__ == "__main__":
    logger.info(f"Testing LST products for date range: {start_date} to {end_date}")

    # Get structure for each product
    entries = {}
    for product in lst_products:
        entries[product] = get_product_structure(product)

    # Compare structures
    compare_structures(lst_products, entries)

    # Find most recent data
    find_most_recent(lst_products)
