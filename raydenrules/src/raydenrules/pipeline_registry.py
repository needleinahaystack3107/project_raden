"""Project pipelines."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline

from raydenrules.pipelines import bronze_ingestion, data_discovery


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    # Create the data discovery pipeline
    data_discovery_pipeline = data_discovery.create_pipeline()

    # Create the bronze ingestion pipeline
    bronze_ingestion_pipeline = bronze_ingestion.create_pipeline()

    # Find all other pipelines
    pipelines = find_pipelines()

    # Register pipelines explicitly
    pipelines["data_discovery"] = data_discovery_pipeline
    pipelines["bronze_ingestion"] = bronze_ingestion_pipeline

    # Create combined pipeline that runs discovery then bronze ingestion
    pipelines["discovery_to_bronze"] = data_discovery_pipeline + bronze_ingestion_pipeline

    # Create the default pipeline that runs all pipelines
    pipelines["__default__"] = pipelines["discovery_to_bronze"]

    return pipelines
