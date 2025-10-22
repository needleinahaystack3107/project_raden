"""
Data Discovery Pipeline

This pipeline handles the discovery of Earth observation data from NASA's CMR API
and stores the results in S3 or locally.
"""

from kedro.pipeline import Pipeline, node

from .nodes import discover_lst_data_for_regions, get_all_regions


def create_pipeline(**kwargs) -> Pipeline:
    """
    Create the data discovery pipeline.

    Returns:
        A pipeline for data discovery from CMR API
    """
    return Pipeline(
        [
            node(
                func=get_all_regions,
                inputs=None,
                outputs="regions_list",
                name="get_regions_for_discovery",
            ),
            node(
                func=discover_lst_data_for_regions,
                inputs=[
                    "regions_list",
                    "params:discovery.date_range",
                    "params:discovery.get_most_recent",
                ],
                outputs="cmr_discovery_results",
                name="discover_lst_data",
            ),
        ]
    )
