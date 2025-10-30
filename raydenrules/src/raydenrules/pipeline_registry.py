"""Project pipelines."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline

from raydenrules.pipelines import bronze_ingestion, data_discovery, silver_processing


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    # Create individual pipelines
    data_discovery_pipeline = data_discovery.create_pipeline()
    bronze_ingestion_pipeline = bronze_ingestion.create_pipeline()
    silver_processing_pipeline = silver_processing.create_pipeline()

    # Find all other pipelines
    pipelines = find_pipelines()

    # Register pipelines explicitly
    pipelines["data_discovery"] = data_discovery_pipeline
    pipelines["bronze_ingestion"] = bronze_ingestion_pipeline
    pipelines["silver_processing"] = silver_processing_pipeline

    # Create combined pipelines
    # Discovery → Bronze (metadata only)
    pipelines["discovery_to_bronze"] = data_discovery_pipeline + bronze_ingestion_pipeline

    # Bronze → Silver (process metrics)
    pipelines["bronze_to_silver"] = bronze_ingestion_pipeline + silver_processing_pipeline

    # Full pipeline: Discovery → Bronze → Silver → Primary
    pipelines["full_pipeline"] = (
        data_discovery_pipeline + bronze_ingestion_pipeline + silver_processing_pipeline
    )

    # Create the default pipeline that runs everything
    pipelines["__default__"] = pipelines["full_pipeline"]

    return pipelines
