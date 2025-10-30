"""
Bronze Ingestion Pipeline Nodes

This module contains nodes for ingesting raw CMR API data into the bronze layer.
The bronze layer stores data as-is from the source with minimal transformation.
"""

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def prepare_bronze_granules(cmr_discovery_results: dict) -> dict[str, pd.DataFrame]:
    """
    Prepare raw granule data from CMR discovery results for bronze storage.

    This function takes the CMR discovery results and creates bronze-layer
    DataFrames that preserve all original metadata from the API.

    Args:
        cmr_discovery_results: Results from CMR discovery pipeline

    Returns:
        Dictionary mapping region IDs to granule DataFrames
    """
    bronze_data = {}

    for region_id, result in cmr_discovery_results.items():
        if result.get("status") != "success":
            logger.warning(
                f"Skipping region {region_id} due to error: {result.get('error_message')}"
            )
            continue

        # Load the LST data from the file
        import json

        file_path = result.get("file_path")

        if not file_path:
            logger.warning(f"No file path found for region {region_id}")
            continue

        try:
            with open(file_path) as f:
                lst_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading LST data for region {region_id}: {str(e)}")
            continue

        # Extract granules
        granules = lst_data.get("granules", [])

        if not granules:
            logger.warning(f"No granules found for region {region_id}")
            continue

        # Convert to DataFrame preserving all fields
        granule_records = []
        for granule in granules:
            record = {
                "region_id": region_id,
                "granule_id": granule.get("id"),
                "title": granule.get("title"),
                "time_start": granule.get("time_start"),
                "time_end": granule.get("time_end"),
                "cloud_cover": granule.get("cloud_cover", 0),
                "product": lst_data.get("product"),
                "bbox_west": lst_data.get("region", [None, None, None, None])[0],
                "bbox_south": lst_data.get("region", [None, None, None, None])[1],
                "bbox_east": lst_data.get("region", [None, None, None, None])[2],
                "bbox_north": lst_data.get("region", [None, None, None, None])[3],
                "ingestion_timestamp": datetime.now().isoformat(),
                # Store all_links as JSON string for bronze layer (contains download URLs)
                "links": str(granule.get("all_links", granule.get("links", []))),
            }
            granule_records.append(record)

        df = pd.DataFrame(granule_records)

        # Add date column extracted from time_start
        df["date"] = pd.to_datetime(df["time_start"]).dt.date

        bronze_data[region_id] = df

        logger.info(f"Prepared {len(df)} bronze granule records for region {region_id}")

    return bronze_data


def create_bronze_manifest(bronze_granules: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Create a manifest of all bronze-layer granule data.

    The manifest provides metadata about the ingested data including:
    - Region coverage
    - Date ranges
    - Record counts
    - Data quality indicators

    Args:
        bronze_granules: Dictionary of region DataFrames

    Returns:
        DataFrame containing manifest information
    """
    manifest_records = []

    # Handle PartitionedDataset - it should be dict-like
    # Try different ways to iterate
    try:
        # When PartitionedDataset.load() is called, it returns a dict where values might be lazy-loaded
        # We need to access them properly via __getitem__
        if hasattr(bronze_granules, "keys"):
            keys = list(bronze_granules.keys())
            items = [(key, bronze_granules[key]) for key in keys]
        else:
            # Fallback to treating as dict
            items = list(bronze_granules.items()) if bronze_granules else []

        logger.info(f"Found {len(items)} partitions in bronze_granules")

        for region_id, value in items:
            # Check if value is callable (lazy loader)
            if callable(value):
                logger.info(f"Partition {region_id} is callable, attempting to call it")
                df = value()
            else:
                df = value

            # Skip if not a DataFrame
            if not isinstance(df, pd.DataFrame):
                logger.warning(f"Partition {region_id} is not a DataFrame: {type(df)}")
                continue

            if df.empty:
                logger.warning(f"Partition {region_id} is empty")
                continue

            record = {
                "region_id": region_id,
                "record_count": len(df),
                "date_min": str(df["date"].min()),
                "date_max": str(df["date"].max()),
                "product": df["product"].iloc[0] if "product" in df.columns else None,
                "ingestion_timestamp": datetime.now().isoformat(),
                "has_missing_dates": False,  # Can be calculated later
                "cloud_cover_mean": float(df["cloud_cover"].mean()),
                "granule_count": len(df["granule_id"].unique()),
            }
            manifest_records.append(record)
    except Exception as e:
        logger.error(f"Error processing bronze_granules: {str(e)}")
        logger.error(f"Type of bronze_granules: {type(bronze_granules)}")
        if hasattr(bronze_granules, "__dict__"):
            logger.error(f"Attributes: {bronze_granules.__dict__}")

    manifest_df = pd.DataFrame(manifest_records)

    logger.info(f"Created bronze manifest with {len(manifest_df)} region entries")

    return manifest_df


def consolidate_bronze_granules(bronze_granules: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Consolidate all region bronze data into a single DataFrame.

    This creates a unified bronze table that can be used for downstream processing.

    Args:
        bronze_granules: Dictionary of region DataFrames

    Returns:
        Consolidated DataFrame with all bronze granule data
    """
    if not bronze_granules:
        logger.warning("No bronze granules to consolidate")
        return pd.DataFrame()

    try:
        # Handle both dict and dict-like objects from PartitionedDataset
        # When PartitionedDataset.load() is called, values might be lazy-loaded
        # Access them via __getitem__ to ensure they're properly loaded
        if hasattr(bronze_granules, "keys"):
            keys = list(bronze_granules.keys())
            granule_dfs = [bronze_granules[key] for key in keys]
        else:
            # Fallback to treating as dict
            granule_dfs = list(bronze_granules.values()) if bronze_granules else []

        logger.info(f"Found {len(granule_dfs)} partitions to consolidate")

        # Handle callable values (lazy loaders)
        loaded_dfs = []
        for item in granule_dfs:
            if callable(item):
                logger.info("Found callable partition, loading it")
                loaded_dfs.append(item())
            else:
                loaded_dfs.append(item)

        granule_dfs = loaded_dfs

        # Filter out any non-DataFrame objects
        granule_dfs = [df for df in granule_dfs if isinstance(df, pd.DataFrame)]

        logger.info(f"After filtering, {len(granule_dfs)} valid DataFrames found")

        if not granule_dfs:
            logger.warning("No valid DataFrames found in bronze_granules")
            logger.warning(f"Type of bronze_granules: {type(bronze_granules)}")
            return pd.DataFrame()

        # Concatenate all DataFrames
        consolidated = pd.concat(granule_dfs, ignore_index=True)

        # Sort by region and date
        consolidated = consolidated.sort_values(["region_id", "date"])

        logger.info(
            f"Consolidated {len(consolidated)} bronze records from {len(granule_dfs)} regions"
        )

        return consolidated

    except Exception as e:
        logger.error(f"Error consolidating bronze granules: {str(e)}")
        logger.error(f"Type of bronze_granules: {type(bronze_granules)}")
        raise


def prepare_bronze_metadata(cmr_discovery_results: dict, regions_list: list[dict]) -> pd.DataFrame:
    """
    Prepare metadata about the bronze ingestion process.

    Args:
        cmr_discovery_results: Results from CMR discovery
        regions_list: List of regions that were processed

    Returns:
        DataFrame with bronze layer metadata
    """
    metadata_records = []

    for region in regions_list:
        region_id = region["id"]
        result = cmr_discovery_results.get(region_id, {})

        record = {
            "region_id": region_id,
            "region_name": region.get("name"),
            "bbox": str(region.get("bbox")),
            "discovery_status": result.get("status", "unknown"),
            "date_range_start": result.get("date_range", {}).get("start"),
            "date_range_end": result.get("date_range", {}).get("end"),
            "file_path": result.get("file_path"),
            "error_message": result.get("error_message"),
            "ingestion_timestamp": datetime.now().isoformat(),
        }
        metadata_records.append(record)

    metadata_df = pd.DataFrame(metadata_records)

    logger.info(f"Prepared bronze metadata for {len(metadata_df)} regions")

    return metadata_df


def prepare_bronze_for_metrics(bronze_granules: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Transform bronze granules into a structure that's closer to the metrics format.

    This prepares the data for silver layer processing where actual LST values
    will be extracted and calculated metrics will be added.

    Args:
        bronze_granules: Dictionary of region DataFrames with granule metadata

    Returns:
        Dictionary of DataFrames structured for metrics calculation
    """
    metrics_prep = {}

    try:
        # Handle PartitionedDataset - access via __getitem__ to ensure proper loading
        if hasattr(bronze_granules, "keys"):
            keys = list(bronze_granules.keys())
            items = [(key, bronze_granules[key]) for key in keys]
        else:
            items = list(bronze_granules.items()) if bronze_granules else []

        logger.info(f"Processing {len(items)} partitions for metrics preparation")

        for region_id, value in items:
            # Check if value is callable (lazy loader)
            if callable(value):
                logger.info(f"Partition {region_id} is callable, loading it")
                df = value()
            else:
                df = value

            # Skip if not a DataFrame
            if not isinstance(df, pd.DataFrame):
                logger.warning(f"Partition {region_id} is not a DataFrame: {type(df)}")
                continue

            if df.empty:
                logger.warning(f"Partition {region_id} is empty")
                continue

            # Create a metrics-ready structure with placeholders
            # These will be populated in the silver layer when actual data is downloaded
            metrics_df = pd.DataFrame(
                {
                    "region_id": df["region_id"],
                    "date": df["date"],
                    "granule_id": df["granule_id"],
                    "title": df["title"],
                    "product": df["product"],
                    "time_start": df["time_start"],
                    "time_end": df["time_end"],
                    "cloud_cover": df["cloud_cover"],
                    # Placeholders for metrics that will be calculated in silver layer
                    "lst_mean_c": None,  # To be calculated from actual raster data
                    "lst_min_c": None,
                    "lst_max_c": None,
                    "cdd": None,  # Cooling degree days
                    "hdd": None,  # Heating degree days
                    "heatwave_flag": 0,  # To be determined from LST values
                    "uhi_index": None,  # Urban heat island index
                    "anomaly_zscore": None,  # Anomaly detection
                    "data_quality_flag": df["cloud_cover"]
                    < 50,  # Simple quality check #noqa: PLR2004
                    "processing_status": "pending",  # Will be updated in silver layer
                }
            )

            # Sort by date
            metrics_df = metrics_df.sort_values("date")

            metrics_prep[region_id] = metrics_df

            logger.info(
                f"Prepared {len(metrics_df)} records for metrics calculation for region {region_id}"
            )

    except Exception as e:
        logger.error(f"Error preparing bronze for metrics: {str(e)}")
        logger.error(f"Type of bronze_granules: {type(bronze_granules)}")
        raise

    return metrics_prep
