"""Project pipelines."""

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline

from raydenrules.pipelines import data_discovery


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """
    # Create the data discovery pipeline
    data_discovery_pipeline = data_discovery.create_pipeline()

    # Find all other pipelines
    pipelines = find_pipelines()

    # Register the data discovery pipeline explicitly
    pipelines["data_discovery"] = data_discovery_pipeline

    # Create the default pipeline that runs all pipelines
    pipelines["__default__"] = sum(pipelines.values())

    return pipelines
