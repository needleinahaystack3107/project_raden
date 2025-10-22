"""
CMR (Common Metadata Repository) API Client

This module provides functions to interact with NASA's CMR API
to discover Earth observation data.
Documentation: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
"""

import json
import logging
from datetime import datetime, timedelta
from typing import NamedTuple, Optional, Union

import requests

logger = logging.getLogger(__name__)

CMR_BASE_URL = "https://cmr.earthdata.nasa.gov/search"


class SearchParams(NamedTuple):
    """Parameters for CMR search operations"""

    bounding_box: Optional[list[float]] = None
    page_size: int = 100
    page_num: int = 1
    provider: Optional[str] = None


def search_granules(  # noqa: PLR0913
    short_name: str,
    temporal_range: Optional[str] = None,
    bounding_box: Optional[list[float]] = None,
    page_size: int = 100,
    page_num: int = 1,
    provider: Optional[str] = None,
) -> dict:
    """
    Search for granules in CMR based on various parameters.

    Args:
        short_name: Collection short name (e.g., "MOD11A1" for MODIS land surface temperature)
        temporal_range: Temporal range in ISO 8601 format (e.g., "2023-01-01T00:00:00Z,2023-01-02T23:59:59Z")
        bounding_box: Bounding box [west, south, east, north]
        page_size: Number of results per page (default: 100)
        page_num: Page number for pagination (default: 1)
        provider: Provider ID (optional)

    Returns:
        Dictionary containing the granule search results
    """
    url = f"{CMR_BASE_URL}/granules.json"

    # Build query parameters
    query_params = {
        "short_name": short_name,
        "page_size": page_size,
        "page_num": page_num,
    }

    # Add optional parameters
    if temporal_range:
        query_params["temporal"] = temporal_range

    if bounding_box:
        query_params["bounding_box"] = ",".join(str(coord) for coord in bounding_box)

    if provider:
        query_params["provider"] = provider

    logger.info(f"Searching granules with params: {query_params}")

    try:
        response = requests.get(url, params=query_params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error searching CMR granules: {e}")
        return {"error": str(e), "feed": {"entry": []}}


def search_collections(
    keyword: Optional[str] = None,
    concept_id: Optional[str] = None,
    temporal: Optional[str] = None,
    page_size: int = 50,
) -> dict:
    """
    Search for collections in CMR.

    Args:
        keyword: Keyword to search for
        concept_id: Concept ID for a specific collection
        temporal: Temporal range in ISO 8601 format
        page_size: Number of results per page

    Returns:
        Dictionary containing the collection search results
    """
    url = f"{CMR_BASE_URL}/collections.json"

    params = {"page_size": page_size}

    if keyword:
        params["keyword"] = keyword

    if concept_id:
        params["concept_id"] = concept_id

    if temporal:
        params["temporal"] = temporal

    logger.info(f"Searching collections with params: {params}")

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error searching CMR collections: {e}")
        return {"error": str(e), "feed": {"entry": []}}


class LSTParams(NamedTuple):
    """Parameters for LST data retrieval"""

    product: str = "MOD11A1"  # MODIS Terra Land Surface Temperature Daily product
    provider: Optional[str] = None
    get_most_recent: bool = True  # Try to get most recent data


def get_lst_data(  # noqa: PLR0912, PLR0915
    region_bbox: list[float],
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    params: LSTParams = LSTParams(),
) -> dict:
    """
    Get Land Surface Temperature data for a specific region and time range.
    Will try multiple strategies to ensure data is returned.

    Args:
        region_bbox: Bounding box [west, south, east, north]
        start_date: Start date (YYYY-MM-DD or datetime)
        end_date: End date (YYYY-MM-DD or datetime)
        product: Product short name
        provider: Provider ID (optional)
        get_most_recent: Try to get the most recent data available (last 3 months)

    Returns:
        Dictionary with LST data references
    """
    # Convert dates to ISO 8601 format if they're not already
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(start_date, str) and "T" not in start_date:
        start_date = f"{start_date}T00:00:00Z"

    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(end_date, str) and "T" not in end_date:
        end_date = f"{end_date}T23:59:59Z"

    # Determine what temporal range to use
    if params.get_most_recent:
        # If user wants the most recent data, use the last 3 months (90 days)
        today = datetime.now()
        three_months_ago = today - timedelta(days=90)

        # Format dates in ISO 8601
        end_date_recent = today.strftime("%Y-%m-%dT%H:%M:%SZ")
        start_date_recent = three_months_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

        temporal_range = f"{start_date_recent},{end_date_recent}"
        logger.info(f"Searching for the most recent data (last 3 months): {temporal_range}")
    else:
        # Use the user-requested time range
        temporal_range = f"{start_date},{end_date}"

    # List of products to try in order of preference based on structure analysis
    # Our analysis showed these products have identical structure and most recent data
    products_to_try = [
        params.product,  # Try requested product first (should be MOD11A1)
        "MOD11A1",  # Terra LST Daily 1km - confirmed most recent in our analysis
        "MOD11B1",  # Terra LST Daily 6km - same structure, equally recent
        "MOD11C1",  # Terra LST Daily 0.05 deg - same structure, equally recent
        "MYD11A1",  # Aqua LST Daily 1km - same structure, equally recent
        "VNP21",  # VIIRS LST - same structure but slightly older data
    ]

    # Make sure the requested product is first in the list (if it's not already)
    if params.product in products_to_try[1:]:
        products_to_try.remove(params.product)
        products_to_try.insert(0, params.product)

    # Store the final result
    final_result = None
    used_product = None
    most_recent_granule_date = None
    used_temporal_range = temporal_range

    # Try each product until we find data
    for product_name in products_to_try:
        logger.info(f"Trying to find data with product {product_name}")

        # Make search without specifying provider to get more results
        search_params = {
            "short_name": product_name,
            "temporal_range": temporal_range,
            "bounding_box": region_bbox,
            "page_size": 50,
        }

        result = search_granules(**search_params)

        # Check if we got results
        if result.get("feed", {}).get("entry"):
            entries = result["feed"]["entry"]
            count = len(entries)
            logger.info(f"Found {count} granules using {product_name}")

            # Find the most recent granule
            most_recent_date = None

            for granule in entries:
                granule_date = granule.get("time_start")
                if most_recent_date is None or granule_date > most_recent_date:
                    most_recent_date = granule_date

            logger.info(f"Most recent {product_name} granule date: {most_recent_date}")

            # Keep this result if it's the first one we found or if it's more recent
            if final_result is None or (
                most_recent_date and most_recent_date > most_recent_granule_date
            ):
                final_result = result
                used_product = product_name
                most_recent_granule_date = most_recent_date
                logger.info(
                    f"Using {product_name} data from {most_recent_date} as it's more recent"
                )

            # If we found the specific product requested, we can stop searching
            if product_name == params.product:
                break

    # If no results after trying all products, try with a more generic approach
    if not final_result:
        logger.warning(
            "Could not find data with specific products, trying with expanded parameters"
        )

        # Try with expanded bounding box
        expanded_bbox = [
            region_bbox[0] - 0.2,  # west
            region_bbox[1] - 0.2,  # south
            region_bbox[2] + 0.2,  # east
            region_bbox[3] + 0.2,  # north
        ]

        result = search_granules(
            short_name="MOD11A1",
            temporal_range=temporal_range,
            bounding_box=expanded_bbox,
            page_size=50,
        )

        if result.get("feed", {}).get("entry"):
            count = len(result["feed"]["entry"])
            logger.info(f"Found {count} granules using expanded region")
            final_result = result
            used_product = "MOD11A1"

    # Use whatever result we got
    result = final_result

    # Extract relevant information
    granules_info = {
        "product": used_product,
        "original_request": {
            "product": params.product,
            "region": region_bbox,
            "time_range": {
                "start": start_date,
                "end": end_date,
            },
        },
        "actual_data": {"product": used_product, "time_range": used_temporal_range},
        "region": region_bbox,
        "granules": [],
    }

    for granule in result.get("feed", {}).get("entry", []):
        granules_info["granules"].append(
            {
                "id": granule.get("id"),
                "title": granule.get("title"),
                "time_start": granule.get("time_start"),
                "time_end": granule.get("time_end"),
                "links": [
                    link for link in granule.get("links", []) if link.get("rel") == "enclosure"
                ],
                "cloud_cover": granule.get("cloud_cover", 0),
            }
        )

    # Add a note if we had to use different parameters than requested
    if params.product != used_product or f"{start_date},{end_date}" != used_temporal_range:
        granules_info["note"] = "Used alternative parameters to find available data"

    return granules_info


class SaveParams(NamedTuple):
    """Parameters for saving LST data"""

    output_path: str
    get_most_recent: bool = True


def save_lst_data_to_json(  # noqa: PLR0913
    region_id: str,
    bbox: list[float],
    start_date: str,
    end_date: str,
    output_path: str,
    get_most_recent: bool = True,
) -> str:
    """
    Save LST data for a region to a JSON file.

    Args:
        region_id: Region identifier
        bbox: Bounding box [west, south, east, north]
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_path: Output file path or directory
        get_most_recent: Whether to get the most recent 3 months of data (default: True)

    Returns:
        Path to the saved JSON file
    """
    # Get LST data
    lst_params = LSTParams(get_most_recent=get_most_recent)
    lst_data = get_lst_data(
        region_bbox=bbox, start_date=start_date, end_date=end_date, params=lst_params
    )

    # Add region info
    lst_data["region_id"] = region_id

    # We don't need to extract date information for the filename anymore
    # Just use a consistent naming convention
    base_filename = f"{region_id}_lst_data"

    # Ensure output path has .json extension
    if not output_path.endswith(".json"):
        # If output_path is a directory, create a filename
        if output_path.endswith("/"):
            output_path = f"{output_path}{base_filename}.json"
        else:
            output_path = f"{output_path}.json"

    # Save to JSON
    with open(output_path, "w") as f:
        json.dump(lst_data, f, indent=2)

    logger.info(f"Saved LST data to {output_path}")
    return output_path
