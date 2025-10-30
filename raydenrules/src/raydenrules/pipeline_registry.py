"""Project pipelines."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline

from raydenrules.pipelines import (
    bronze_ingestion,
    data_discovery,
    gold_feature_engineering,
    silver_processing,
)


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    # Create individual pipelines
    data_discovery_pipeline = data_discovery.create_pipeline()
    bronze_ingestion_pipeline = bronze_ingestion.create_pipeline()
    silver_processing_pipeline = silver_processing.create_pipeline()
    gold_feature_engineering_pipeline = gold_feature_engineering.create_pipeline()

    # Find all other pipelines
    pipelines = find_pipelines()

    # Register pipelines explicitly
    pipelines["data_discovery"] = data_discovery_pipeline
    pipelines["bronze_ingestion"] = bronze_ingestion_pipeline
    pipelines["silver_processing"] = silver_processing_pipeline
    pipelines["gold_feature_engineering"] = gold_feature_engineering_pipeline

    # Create combined pipelines
    # Discovery → Bronze (metadata only)
    pipelines["discovery_to_bronze"] = data_discovery_pipeline + bronze_ingestion_pipeline

    # Bronze → Silver (process metrics)
    pipelines["bronze_to_silver"] = bronze_ingestion_pipeline + silver_processing_pipeline

    # Silver → Gold (aggregate for API)
    pipelines["silver_to_gold"] = silver_processing_pipeline + gold_feature_engineering_pipeline

    # Full pipeline: Discovery → Bronze → Silver → Gold/Feature
    pipelines["data_engineering"] = (
        data_discovery_pipeline
        + bronze_ingestion_pipeline
        + silver_processing_pipeline
        + gold_feature_engineering_pipeline
    )

    # Create the default pipeline that runs everything
    pipelines["__default__"] = pipelines["data_engineering"]

    return pipelines
