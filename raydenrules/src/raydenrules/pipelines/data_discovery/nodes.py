"""
Data Discovery Pipeline Nodes

This module contains the functions that form the nodes in the data discovery pipeline.
"""

import json
import logging
import os
from datetime import datetime, timedelta

from raydenrules.pipelines.data_discovery.cmr_api import save_lst_data_to_json

logger = logging.getLogger(__name__)


def get_all_regions() -> list[dict]:
    """
    Retrieve all available regions from the API or local configuration.

    Returns:
        List of region dictionaries with id, name, and bbox
    """
    # In a real implementation, this would call the API to get the regions
    # For now, we'll return a hardcoded list of regions
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
    ]

    logger.info(f"Retrieved {len(regions)} regions for data discovery")
    return regions


def discover_lst_data_for_regions(
    regions: list[dict],
    date_range: dict[str, str],
    get_most_recent: bool = True,
) -> dict:
    """
    Discover LST data for each region and save the results.

    Args:
        regions: List of region dictionaries
        date_range: Dictionary with 'start' and 'end' date strings (YYYY-MM-DD)
        get_most_recent: Whether to get the most recent 3 months of data (default: True)

    Returns:
        Dictionary with discovery results for each region
    """
    # Get the date range to use
    if get_most_recent:
        logger.info("Using most recent data mode (last 3 months)")
        today = datetime.now()
        three_months_ago = today - timedelta(days=90)
        start_date = three_months_ago.strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        logger.info(f"Using date range: {start_date} to {end_date}")
    else:
        start_date = date_range["start"]
        end_date = date_range["end"]
        logger.info(f"Using specific date range: {start_date} to {end_date}")

    results = {}
    output_dir = os.path.join("data", "01_raw", "cmr_discovery")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for region in regions:
        region_id = region["id"]
        bbox = region["bbox"]

        try:
            # Create consistent output paths that don't depend on dates
            output_path = os.path.join(output_dir, f"{region_id}_lst_data.json")

            # Save LST data for this region
            file_path = save_lst_data_to_json(
                region_id=region_id,
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                output_path=output_path,
                get_most_recent=get_most_recent,
            )

            results[region_id] = {
                "status": "success",
                "file_path": file_path,
                "region": region,
                "date_range": {"start": start_date, "end": end_date},
            }

            logger.info(f"Successfully discovered LST data for region {region_id}")

        except Exception as e:
            logger.error(f"Error discovering LST data for region {region_id}: {str(e)}")
            results[region_id] = {
                "status": "error",
                "error_message": str(e),
                "region": region,
                "date_range": {"start": start_date, "end": end_date},
            }

    # Save the overall results summary
    summary_path = os.path.join(output_dir, f"discovery_summary_{start_date}_{end_date}.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    return results
