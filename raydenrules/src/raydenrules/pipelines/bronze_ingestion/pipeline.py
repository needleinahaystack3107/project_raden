"""
Bronze Ingestion Pipeline

This pipeline transforms CMR discovery results into bronze-layer tables
stored as parquet files. The bronze layer preserves raw data with minimal
transformation.
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    consolidate_bronze_granules,
    create_bronze_manifest,
    prepare_bronze_for_metrics,
    prepare_bronze_granules,
    prepare_bronze_metadata,
)


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create the bronze ingestion pipeline.

    This pipeline:
    1. Takes CMR discovery results
    2. Prepares bronze granule tables per region
    3. Creates a consolidated bronze table
    4. Generates a manifest for tracking
    5. Stores metadata about the ingestion

    Returns:
        A pipeline for bronze data ingestion
    """
    return pipeline(
        [
            node(
                func=prepare_bronze_granules,
                inputs="cmr_discovery_results",
                outputs="bronze_granules_partitioned",
                name="prepare_bronze_granules",
            ),
            node(
                func=consolidate_bronze_granules,
                inputs="bronze_granules_partitioned",
                outputs="bronze_granules_consolidated",
                name="consolidate_bronze_granules",
            ),
            node(
                func=create_bronze_manifest,
                inputs="bronze_granules_partitioned",
                outputs="bronze_manifest",
                name="create_bronze_manifest",
            ),
            node(
                func=prepare_bronze_metadata,
                inputs=["cmr_discovery_results", "regions_list"],
                outputs="bronze_metadata",
                name="prepare_bronze_metadata",
            ),
            node(
                func=prepare_bronze_for_metrics,
                inputs="bronze_granules_partitioned",
                outputs="bronze_metrics_prep",
                name="prepare_bronze_for_metrics",
            ),
        ],
        tags=["bronze", "ingestion"],
    )
