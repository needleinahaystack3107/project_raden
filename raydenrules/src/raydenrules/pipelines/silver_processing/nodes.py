"""
Silver Layer Processing Nodes

This module contains nodes for downloading NASA granules, extracting LST values,
and calculating climate metrics.
"""

import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Constants
CLOUD_COVER_THRESHOLD = 50  # Maximum acceptable cloud cover percentage

# Optional imports for raster processing
try:
    import rasterio
    from rasterio.warp import transform_bounds

    RASTERIO_AVAILABLE = True
except ImportError:
    rasterio = None  # type: ignore
    transform_bounds = None  # type: ignore
    RASTERIO_AVAILABLE = False
    logger.warning("rasterio not available - LST extraction from HDF files will not work")


def parse_granule_links(links_str: str) -> list[dict]:
    """
    Parse the links string from bronze layer into a list of link dictionaries.

    Args:
        links_str: String representation of links list

    Returns:
        List of link dictionaries
    """
    import ast

    try:
        return ast.literal_eval(links_str)
    except Exception:
        return []


def get_download_url(granule_row: pd.Series) -> str | None:
    """
    Extract the HTTPS download URL from granule metadata.

    Args:
        granule_row: Row from bronze granules DataFrame

    Returns:
        HTTPS download URL or None
    """
    links = parse_granule_links(granule_row.get("links", "[]"))

    for link in links:
        if isinstance(link, dict):
            href = link.get("href", "")
            # Prefer HTTPS data links
            if href.startswith("https://") and "data.lpdaac" in href and href.endswith(".hdf"):
                return href

    return None


def download_granule(
    url: str, output_dir: Path, granule_id: str, auth_token: str | None = None
) -> Path | None:
    """
    Download a granule HDF file from NASA.

    Args:
        url: Download URL
        output_dir: Directory to save the file
        granule_id: Granule ID for naming
        auth_token: Optional NASA Earthdata authentication token

    Returns:
        Path to downloaded file or None if failed
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{granule_id}.hdf"

        # Skip if already downloaded
        if output_file.exists():
            logger.info(f"Granule {granule_id} already downloaded")
            return output_file

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        logger.info(f"Downloading {granule_id} from {url}")

        response = requests.get(url, headers=headers, stream=True, timeout=300)
        response.raise_for_status()

        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Successfully downloaded {granule_id}")
        return output_file

    except Exception as e:
        logger.error(f"Failed to download {granule_id}: {str(e)}")
        return None


def extract_lst_via_gdal_subprocess(
    hdf_file: Path, bbox: tuple[float, float, float, float], subdataset_name: str = "LST_Day_1km"
) -> dict[str, float] | None:
    """
    Extract LST statistics using GDAL command-line tools (fallback when rasterio unavailable).

    Args:
        hdf_file: Path to HDF file
        bbox: Bounding box (west, south, east, north)
        subdataset_name: Name of the LST subdataset

    Returns:
        Dictionary with LST statistics or None if failed
    """
    try:
        abs_path = hdf_file.resolve()

        # Get subdatasets list using gdalinfo
        result = subprocess.run(
            ["gdalinfo", str(abs_path)], capture_output=True, text=True, timeout=30, check=False
        )

        if result.returncode != 0:
            logger.error(f"gdalinfo failed for {hdf_file}")
            return None

        # Find the LST subdataset path
        lst_subdataset = None
        for line in result.stdout.split("\n"):
            if "SUBDATASET_" in line and subdataset_name in line and "_NAME=" in line:
                # Extract the subdataset path
                lst_subdataset = line.split("=", 1)[1].strip()
                break

        if not lst_subdataset:
            logger.error(f"LST subdataset '{subdataset_name}' not found in {hdf_file}")
            return None

        logger.info(f"Using GDAL subprocess to read: {lst_subdataset}")

        # Use gdal_translate to extract data to a temporary GeoTIFF
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Extract the subdataset to GeoTIFF
            # Note: Not clipping to bbox since HDF is in sinusoidal projection
            # We'll read the entire 1200x1200 tile
            result = subprocess.run(
                ["gdal_translate", "-of", "GTiff", lst_subdataset, tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                logger.error(f"gdal_translate failed: {result.stderr}")
                return None

            # Read the GeoTIFF and calculate statistics using numpy
            import numpy as np
            from PIL import Image

            img = Image.open(tmp_path)
            data = np.array(img)

            # Apply scale factor and offset (MODIS LST is in Kelvin * 50)
            scale_factor = 0.02  # Convert to Kelvin
            valid_range = (7500, 65535)  # Valid data range

            # Mask invalid values
            valid_mask = (data >= valid_range[0]) & (data <= valid_range[1])
            valid_data = data[valid_mask] * scale_factor

            if len(valid_data) == 0:
                logger.warning(f"No valid LST data in {hdf_file}")
                return None

            # Convert Kelvin to Celsius
            valid_data_c = valid_data - 273.15

            return {
                "lst_mean_k": float(np.mean(valid_data)),
                "lst_mean_c": float(np.mean(valid_data_c)),
                "lst_min_c": float(np.min(valid_data_c)),
                "lst_max_c": float(np.max(valid_data_c)),
                "lst_std_c": float(np.std(valid_data_c)),
                "valid_pixel_count": int(np.sum(valid_mask)),
                "total_pixel_count": int(data.size),
            }

        finally:
            # Clean up temp file
            import os

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        logger.error(f"Failed to extract LST via GDAL subprocess: {str(e)}")
        return None


def extract_lst_from_hdf(
    hdf_file: Path, bbox: tuple[float, float, float, float], subdataset_name: str = "LST_Day_1km"
) -> dict[str, float] | None:
    """
    Extract LST statistics from HDF file for a given bounding box.

    Args:
        hdf_file: Path to HDF file
        bbox: Bounding box (west, south, east, north)
        subdataset_name: Name of the LST subdataset

    Returns:
        Dictionary with LST statistics or None if failed
    """
    if not RASTERIO_AVAILABLE:
        logger.warning("rasterio not available - attempting to use GDAL command-line tools")
        # Try using GDAL via subprocess as fallback
        return extract_lst_via_gdal_subprocess(hdf_file, bbox, subdataset_name)

    try:
        # Convert to absolute path for GDAL
        abs_path = hdf_file.resolve()

        # Verify file exists
        if not abs_path.exists():
            logger.error(f"HDF file does not exist: {abs_path}")
            return None

        # Open HDF subdataset using absolute path
        hdf_dataset_path = (
            f'HDF4_EOS:EOS_GRID:"{abs_path}":MODIS_Grid_Daily_1km_LST:{subdataset_name}'
        )
        logger.debug(f"Opening HDF dataset: {hdf_dataset_path}")

        with rasterio.open(hdf_dataset_path) as src:
            # Transform bbox to dataset CRS if needed
            # MODIS uses sinusoidal projection
            window = src.window(*bbox)

            # Read data
            data = src.read(1, window=window)

            # Apply scale factor and offset (MODIS LST is in Kelvin * 50)
            scale_factor = 0.02  # Convert to Kelvin
            valid_range = (7500, 65535)  # Valid data range

            # Mask invalid values
            valid_mask = (data >= valid_range[0]) & (data <= valid_range[1])
            valid_data = data[valid_mask] * scale_factor

            if len(valid_data) == 0:
                logger.warning(f"No valid LST data in {hdf_file}")
                return None

            # Convert Kelvin to Celsius
            valid_data_c = valid_data - 273.15

            return {
                "lst_mean_k": float(np.mean(valid_data)),
                "lst_mean_c": float(np.mean(valid_data_c)),
                "lst_min_c": float(np.min(valid_data_c)),
                "lst_max_c": float(np.max(valid_data_c)),
                "lst_std_c": float(np.std(valid_data_c)),
                "valid_pixel_count": int(np.sum(valid_mask)),
                "total_pixel_count": int(data.size),
            }

    except Exception as e:
        logger.error(f"Failed to extract LST from {hdf_file}: {str(e)}")
        return None


def calculate_degree_days(lst_mean_c: float, base_temp_c: float = 18.0) -> tuple[float, float]:
    """
    Calculate cooling and heating degree days.

    Args:
        lst_mean_c: Mean LST in Celsius
        base_temp_c: Base temperature for degree day calculation

    Returns:
        Tuple of (cooling_degree_days, heating_degree_days)
    """
    cdd = max(0.0, lst_mean_c - base_temp_c)
    hdd = max(0.0, base_temp_c - lst_mean_c)
    return cdd, hdd


def calculate_heatwave_flag(
    df: pd.DataFrame, temp_threshold: float = 32.0, consecutive_days: int = 3
) -> pd.Series:
    """
    Flag heatwave periods based on consecutive hot days.

    Args:
        df: DataFrame with lst_mean_c column
        temp_threshold: Temperature threshold in Celsius
        consecutive_days: Minimum consecutive days for heatwave

    Returns:
        Series of boolean flags
    """
    # Check if temperature exceeds threshold
    hot_days = df["lst_mean_c"] >= temp_threshold

    # Count consecutive hot days
    flags = []
    streak = 0

    for is_hot in hot_days:
        if is_hot:
            streak += 1
        else:
            streak = 0

        # Flag as heatwave if in a streak of consecutive_days or more
        flags.append(1 if streak >= consecutive_days else 0)

    return pd.Series(flags, index=df.index)


def calculate_anomaly_zscore(df: pd.DataFrame, baseline_window: int = 30) -> pd.Series:
    """
    Calculate temperature anomaly z-scores.

    Args:
        df: DataFrame with lst_mean_c column
        baseline_window: Rolling window size for baseline calculation

    Returns:
        Series of z-scores
    """
    # Calculate rolling mean and std
    rolling_mean = df["lst_mean_c"].rolling(window=baseline_window, min_periods=1).mean()
    rolling_std = df["lst_mean_c"].rolling(window=baseline_window, min_periods=1).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0, 1)

    # Calculate z-score
    zscore = (df["lst_mean_c"] - rolling_mean) / rolling_std

    return zscore


def calculate_uhi_index(urban_temp: float, rural_baseline: float = 20.0) -> float:
    """
    Calculate Urban Heat Island index.

    Args:
        urban_temp: Urban area temperature in Celsius
        rural_baseline: Rural baseline temperature in Celsius

    Returns:
        UHI index (temperature difference)
    """
    return urban_temp - rural_baseline


def process_region_granules(  # noqa: PLR0912, PLR0915
    bronze_granules: dict[str, pd.DataFrame],
    download_dir: str = "data/01_raw/nasa_granules",
    enable_download: bool = False,
    auth_token: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Process granules for all regions: download and extract LST metrics.

    Args:
        bronze_granules: Dictionary of region granules from bronze layer
        download_dir: Directory to store downloaded HDF files
        enable_download: Whether to actually download files (False for testing)
        auth_token: NASA Earthdata authentication token

    Returns:
        Dictionary of region DataFrames with calculated metrics
    """
    processed_regions = {}
    download_path = Path(download_dir)

    # Handle PartitionedDataset - access via __getitem__ to ensure proper loading
    if hasattr(bronze_granules, "keys"):
        keys = list(bronze_granules.keys())
        items = [(key, bronze_granules[key]) for key in keys]
    else:
        items = list(bronze_granules.items()) if bronze_granules else []

    logger.info(f"Processing {len(items)} regions for silver layer")

    for region_id, value in items:
        # Check if value is callable (lazy loader)
        if callable(value):
            logger.info(f"Loading partition {region_id}")
            df = value()
        else:
            df = value

        if not isinstance(df, pd.DataFrame) or df.empty:
            logger.warning(f"Skipping {region_id}: invalid or empty data")
            continue

        logger.info(f"Processing {len(df)} granules for region {region_id}")

        # Get bbox from first row
        bbox = (
            df.iloc[0]["bbox_west"],
            df.iloc[0]["bbox_south"],
            df.iloc[0]["bbox_east"],
            df.iloc[0]["bbox_north"],
        )

        # Process each granule
        metrics_records = []

        for idx, row in df.iterrows():
            record = {
                "region_id": row["region_id"],
                "date": str(row["date"]),
                "granule_id": row["granule_id"],
                "title": row["title"],
                "product": row["product"],
                "time_start": row["time_start"],
                "time_end": row["time_end"],
                "cloud_cover": row["cloud_cover"],
            }

            if enable_download:
                # Download and extract actual LST data
                url = get_download_url(row)

                if url:
                    hdf_file = download_granule(
                        url, download_path / region_id, row["granule_id"], auth_token
                    )

                    if hdf_file:
                        lst_stats = extract_lst_from_hdf(hdf_file, bbox)

                        if lst_stats:
                            record.update(lst_stats)

                            # Calculate degree days
                            cdd, hdd = calculate_degree_days(lst_stats["lst_mean_c"])
                            record["cdd"] = cdd
                            record["hdd"] = hdd

                            # Calculate UHI (using fixed rural baseline for now)
                            record["uhi_index"] = calculate_uhi_index(lst_stats["lst_mean_c"])
                        else:
                            # Failed to extract - set to None
                            record.update(
                                {
                                    "lst_mean_c": None,
                                    "lst_min_c": None,
                                    "lst_max_c": None,
                                    "cdd": None,
                                    "hdd": None,
                                    "uhi_index": None,
                                }
                            )
                    else:
                        # Download failed - set to None
                        record.update(
                            {
                                "lst_mean_c": None,
                                "lst_min_c": None,
                                "lst_max_c": None,
                                "cdd": None,
                                "hdd": None,
                                "uhi_index": None,
                            }
                        )
                else:
                    logger.warning(f"No download URL for {row['granule_id']}")
                    record.update(
                        {
                            "lst_mean_c": None,
                            "lst_min_c": None,
                            "lst_max_c": None,
                            "cdd": None,
                            "hdd": None,
                            "uhi_index": None,
                        }
                    )
            else:
                # Mock mode: generate synthetic data for testing
                # This allows testing the pipeline without downloading large files
                mock_temp = 20 + np.random.uniform(-5, 10)
                record["lst_mean_c"] = round(float(mock_temp), 2)
                record["lst_min_c"] = round(float(mock_temp - 3), 2)
                record["lst_max_c"] = round(float(mock_temp + 3), 2)

                cdd, hdd = calculate_degree_days(record["lst_mean_c"])
                record["cdd"] = round(cdd, 2)
                record["hdd"] = round(hdd, 2)
                record["uhi_index"] = round(calculate_uhi_index(record["lst_mean_c"]), 2)

            # Add placeholder for time-series metrics
            record["heatwave_flag"] = 0
            record["anomaly_zscore"] = 0.0
            record["data_quality_flag"] = row["cloud_cover"] < CLOUD_COVER_THRESHOLD
            record["processing_status"] = (
                "processed" if record.get("lst_mean_c") is not None else "failed"
            )

            metrics_records.append(record)

        # Create DataFrame
        metrics_df = pd.DataFrame(metrics_records)

        # Calculate time-series metrics (heatwave, anomaly)
        if not metrics_df.empty and "lst_mean_c" in metrics_df.columns:
            # Sort by date
            metrics_df = metrics_df.sort_values("date")

            # Calculate heatwave flags
            metrics_df["heatwave_flag"] = calculate_heatwave_flag(metrics_df)

            # Calculate anomaly z-scores
            metrics_df["anomaly_zscore"] = calculate_anomaly_zscore(metrics_df)
            # Convert to numeric and round (handles NaN properly)
            metrics_df["anomaly_zscore"] = pd.to_numeric(
                metrics_df["anomaly_zscore"], errors="coerce"
            ).round(2)

        processed_regions[region_id] = metrics_df

        successful = metrics_df[metrics_df["processing_status"] == "processed"].shape[0]
        logger.info(
            f"Processed {len(metrics_df)} granules for {region_id}: "
            f"{successful} successful, {len(metrics_df) - successful} failed"
        )

    return processed_regions


def format_for_api(processed_metrics: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """
    Format processed metrics to match the API schema.

    Args:
        processed_metrics: Dictionary of region DataFrames with metrics

    Returns:
        Dictionary formatted for API consumption
    """
    api_data = {}

    # Handle PartitionedDataset - access via __getitem__ to ensure proper loading
    if hasattr(processed_metrics, "keys"):
        keys = list(processed_metrics.keys())
        items = [(key, processed_metrics[key]) for key in keys]
    else:
        items = list(processed_metrics.items()) if processed_metrics else []

    logger.info(f"Formatting {len(items)} regions for API")

    for region_id, value in items:
        # Check if value is callable (lazy loader)
        if callable(value):
            logger.info(f"Loading partition {region_id} for API formatting")
            df = value()
        else:
            df = value
        if df.empty:
            continue

        # Extract metadata from first row
        meta = {
            "region_id": region_id,
            "product": df.iloc[0]["product"],
            "bbox": (
                [
                    df.iloc[0].get("bbox_west"),
                    df.iloc[0].get("bbox_south"),
                    df.iloc[0].get("bbox_east"),
                    df.iloc[0].get("bbox_north"),
                ]
                if "bbox_west" in df.columns
                else None
            ),
            "date_range": {
                "start": str(df["date"].min()),
                "end": str(df["date"].max()),
            },
            "record_count": len(df),
            "last_updated": datetime.now().isoformat(),
        }

        # Format metrics
        metrics = []
        for _, row in df.iterrows():
            metric = {
                "date": str(row["date"]),
                "lst_mean_c": row.get("lst_mean_c"),
                "cdd": row.get("cdd"),
                "hdd": row.get("hdd"),
                "heatwave_flag": int(row.get("heatwave_flag", 0)),
                "uhi_index": row.get("uhi_index"),
                "anomaly_zscore": row.get("anomaly_zscore"),
            }
            metrics.append(metric)

        api_data[region_id] = {
            "meta": meta,
            "metrics": metrics,
        }

    logger.info(f"Formatted API data for {len(api_data)} regions")

    return api_data
