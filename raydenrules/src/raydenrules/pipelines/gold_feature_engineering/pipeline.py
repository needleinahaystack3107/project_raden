"""
Gold Feature Engineering Pipeline Definition
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import add_region_metadata, aggregate_region_metrics


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create the gold feature engineering pipeline that aggregates
    region metrics into API-ready format.

    Returns:
        Pipeline: Gold feature engineering pipeline
    """
    return pipeline(
        [
            node(
                func=aggregate_region_metrics,
                inputs="silver_metrics_partitioned",
                outputs="gold_metrics_aggregated",
                name="aggregate_region_metrics_node",
            ),
            node(
                func=add_region_metadata,
                inputs=["gold_metrics_aggregated", "regions_list"],
                outputs="gold_metrics_by_region",
                name="add_region_metadata_node",
            ),
        ],
        tags=["gold", "feature_engineering"],
    )
