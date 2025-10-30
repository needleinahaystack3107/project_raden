"""
Gold Feature Engineering Nodes
Transform silver metrics into API-ready feature datasets
"""

import logging
from collections.abc import Callable
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)


def aggregate_region_metrics(silver_metrics: dict[str, Callable]) -> dict[str, dict]:
    """
    Aggregate silver metrics from all regions into API-ready format.

    Args:
        silver_metrics: Dictionary of callables that return DataFrames, keyed by region_id

    Returns:
        Dictionary of region metrics in API format
    """
    logger.info(f"Aggregating metrics for {len(silver_metrics)} regions")

    aggregated_metrics = {}

    for region_id, load_func in silver_metrics.items():
        # Load the actual dataframe by calling the loader function
        df = load_func()
        logger.info(f"Processing region: {region_id}, records: {len(df)}")

        # Sort by date
        df = df.sort_values("date")

        # Select and format metrics for API
        metrics_list = []
        for _, row in df.iterrows():
            metric = {
                "date": str(row["date"]),
                "lst_mean_c": float(row["lst_mean_c"]),
                "cdd": float(row["cdd"]),
                "hdd": float(row["hdd"]),
                "heatwave_flag": int(row["heatwave_flag"]),
                "uhi_index": float(row["uhi_index"]),
                "anomaly_zscore": (
                    float(row["anomaly_zscore"]) if pd.notna(row["anomaly_zscore"]) else 0.0
                ),
            }
            metrics_list.append(metric)

        # Calculate KPI summary for the region
        kpi_summary = calculate_kpi_summary(df)

        # Get region metadata (assumes it's available in the dataframe)
        # In a real scenario, this might come from a separate regions catalog
        region_name = region_id  # Default to ID if name not available
        bbox = None  # Could be loaded from regions catalog

        # Create API-ready structure
        aggregated_metrics[region_id] = {
            "meta": {
                "region_id": region_id,
                "region_name": region_name,
                "bbox": bbox,
                "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            "metrics": metrics_list,
            "kpi_summary": kpi_summary,
        }

    logger.info(f"Successfully aggregated metrics for {len(aggregated_metrics)} regions")
    return aggregated_metrics


def calculate_kpi_summary(df: pd.DataFrame) -> dict:
    """
    Calculate KPI summary statistics from metrics DataFrame.

    Args:
        df: DataFrame with metrics

    Returns:
        Dictionary with YTD and latest metrics
    """
    # YTD statistics
    ytd_stats = {
        "avg_lst_c": float(df["lst_mean_c"].mean()),
        "heatwave_days": int(df["heatwave_flag"].sum()),
        "max_uhi_index": float(df["uhi_index"].max()),
        "max_anomaly_zscore": (
            float(df["anomaly_zscore"].max()) if df["anomaly_zscore"].notna().any() else 0.0
        ),
    }

    # Latest day metrics (most recent date)
    latest = df.iloc[-1]
    today_stats = {
        "lst_mean_c": float(latest["lst_mean_c"]),
        "cdd": float(latest["cdd"]),
        "hdd": float(latest["hdd"]),
        "anomaly_zscore": (
            float(latest["anomaly_zscore"]) if pd.notna(latest["anomaly_zscore"]) else 0.0
        ),
    }

    return {"ytd": ytd_stats, "today": today_stats}


def add_region_metadata(aggregated_metrics: dict[str, dict], regions_list: list) -> dict[str, dict]:
    """
    Enrich aggregated metrics with region metadata.

    Args:
        aggregated_metrics: Dictionary of aggregated metrics
        regions_list: List of region metadata dictionaries

    Returns:
        Enriched aggregated metrics
    """
    logger.info("Enriching metrics with region metadata")

    # Create a map from region_id to region info
    region_map = {r["id"]: r for r in regions_list}

    for region_id, metrics_data in aggregated_metrics.items():
        if region_id in region_map:
            region_info = region_map[region_id]
            metrics_data["meta"]["region_name"] = region_info.get("name", region_id)
            metrics_data["meta"]["bbox"] = region_info.get("bbox")
            metrics_data["meta"]["center"] = region_info.get("center")

    logger.info(f"Enriched {len(aggregated_metrics)} regions with metadata")
    return aggregated_metrics
