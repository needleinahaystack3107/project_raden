"""
Silver Processing Pipeline

This pipeline processes bronze granules to extract actual LST metrics from NASA data.
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import format_for_api, process_region_granules


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create the silver processing pipeline.

    This pipeline:
    1. Takes bronze granules with metadata
    2. Downloads actual HDF raster files from NASA (optional)
    3. Extracts LST values from raster data
    4. Calculates climate metrics (CDD, HDD, UHI, anomalies, heatwaves)
    5. Formats data for API consumption
    6. Stores in primary layer

    Returns:
        A pipeline for silver data processing
    """
    return pipeline(
        [
            node(
                func=process_region_granules,
                inputs={
                    "bronze_granules": "bronze_granules_partitioned",
                    "download_dir": "params:silver.download_dir",
                    "enable_download": "params:silver.enable_download",
                    "auth_token": "params:silver.nasa_auth_token",
                },
                outputs="silver_metrics_partitioned",
                name="process_region_granules",
            ),
            node(
                func=format_for_api,
                inputs="silver_metrics_partitioned",
                outputs="primary_metrics_by_region",
                name="format_for_api",
            ),
        ],
        tags=["silver", "processing", "metrics"],
    )
