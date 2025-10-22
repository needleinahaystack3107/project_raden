"""
Unit tests for Rayden Rules UI components
"""

# Import paths to make relative imports work
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

# Constants for test values
LST_MAX_VALUE = 35
LST_MIN_VALUE = 20
ANOMALY_MAX_VALUE = 3
ANOMALY_MIN_VALUE = -1
HEATWAVE_THRESHOLD = 0.3
MULTI_DAY_DURATION = 2
SINGLE_DAY_DURATION = 1
THREE_DAY_DURATION = 3
FLOAT_TOLERANCE = 0.001  # Tolerance for floating point comparisons

# Mock data for testing
MOCK_DATA = {
    "meta": {
        "region_id": "NYC001",
        "region_name": "New York City",
        "bbox": [-74.2589, 40.4774, -73.7004, 40.9176],
    },
    "metrics": [
        {
            "date": "2025-10-01",
            "lst_mean_c": 23.4,
            "cdd": 8.4,
            "hdd": 0.0,
            "heatwave_flag": 0,
            "uhi_index": 3.2,
            "anomaly_zscore": 1.2,
        },
        {
            "date": "2025-10-02",
            "lst_mean_c": 24.1,
            "cdd": 9.1,
            "hdd": 0.0,
            "heatwave_flag": 0,
            "uhi_index": 3.4,
            "anomaly_zscore": 1.4,
        },
    ],
    "kpi_summary": {
        "ytd": {
            "avg_lst_c": 24.3,
            "heatwave_days": 4,
            "max_uhi_index": 4.7,
            "max_anomaly_zscore": 3.0,
        },
        "today": {"lst_mean_c": 19.5, "cdd": 4.5, "hdd": 0.0, "anomaly_zscore": 0.0},
    },
}


# Helper function to simulate the data loading function in the Streamlit app
def load_mock_data():
    """Simulate the load_mock_data function from the Streamlit app"""
    metrics_df = pd.DataFrame(MOCK_DATA["metrics"])
    metrics_df["date"] = pd.to_datetime(metrics_df["date"])
    return MOCK_DATA, metrics_df


# Tests for data loading and processing
def test_load_mock_data():
    """Test that data loading works correctly"""
    data, metrics_df = load_mock_data()

    # Check the data structure
    assert "metrics" in data
    assert "meta" in data
    assert "kpi_summary" in data

    # Check that the DataFrame is created correctly
    assert isinstance(metrics_df, pd.DataFrame)
    assert len(metrics_df) == len(data["metrics"])
    assert "date" in metrics_df.columns
    assert "lst_mean_c" in metrics_df.columns

    # Check that date conversion worked
    assert pd.api.types.is_datetime64_dtype(metrics_df["date"])


# Test for map data creation (from the map page)
def test_create_mock_heatmap_data():
    """Test the mock heatmap data creation"""
    bbox = MOCK_DATA["meta"]["bbox"]
    region_center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]

    # Function to recreate the heatmap data (simplified from the map page)
    def create_mock_heatmap_data(selected_layer):
        lon_range = bbox[2] - bbox[0]
        lat_range = bbox[3] - bbox[1]

        grid_size = 20
        points = []

        for i in range(grid_size):
            for j in range(grid_size):
                lon = bbox[0] + (i / grid_size) * lon_range
                lat = bbox[1] + (j / grid_size) * lat_range

                dist_from_center = (
                    (lon - region_center[0]) ** 2 + (lat - region_center[1]) ** 2
                ) ** 0.5
                max_dist = ((lon_range / 2) ** 2 + (lat_range / 2) ** 2) ** 0.5
                normalized_dist = dist_from_center / max_dist

                if selected_layer == "Land Surface Temperature":
                    value = LST_MAX_VALUE - (normalized_dist * 15)
                elif selected_layer == "Anomaly":
                    value = ANOMALY_MAX_VALUE - (normalized_dist * 4)
                else:
                    value = 1 if normalized_dist < HEATWAVE_THRESHOLD else 0

                points.append({"lat": lat, "lon": lon, "value": value})

        return pd.DataFrame(points)

    # Test for different layer types
    lst_data = create_mock_heatmap_data("Land Surface Temperature")
    anomaly_data = create_mock_heatmap_data("Anomaly")
    heatwave_data = create_mock_heatmap_data("Heatwave Flag")

    # Check DataFrame structure
    assert all(isinstance(df, pd.DataFrame) for df in [lst_data, anomaly_data, heatwave_data])
    assert all(
        set(df.columns) == {"lat", "lon", "value"} for df in [lst_data, anomaly_data, heatwave_data]
    )

    # Check data ranges
    assert lst_data["value"].max() <= LST_MAX_VALUE
    # Allow for small floating point precision differences
    assert abs(lst_data["value"].min() - LST_MIN_VALUE) < FLOAT_TOLERANCE

    assert anomaly_data["value"].max() <= ANOMALY_MAX_VALUE
    # Allow for small floating point precision differences
    assert abs(anomaly_data["value"].min() - ANOMALY_MIN_VALUE) < FLOAT_TOLERANCE

    assert set(heatwave_data["value"].unique()).issubset({0, 1})


# Test for alert rule generation in the alerts page
def test_generate_alert_rule():
    """Test alert rule generation logic"""

    def generate_rule(metric, condition, threshold, duration):
        return f"{metric} {condition} {threshold} for {duration} day{'s' if duration > 1 else ''}"

    # Test various combinations
    assert (
        generate_rule("lst_mean_c", ">=", 30, SINGLE_DAY_DURATION) == "lst_mean_c >= 30 for 1 day"
    )
    assert (
        generate_rule("heatwave_flag", "=", 1, THREE_DAY_DURATION) == "heatwave_flag = 1 for 3 days"
    )
    assert generate_rule("uhi_index", ">", 4.5, MULTI_DAY_DURATION) == "uhi_index > 4.5 for 2 days"


# Test for region filtering in the regions page
def test_filter_regions():
    """Test region filtering logic"""
    regions = [
        {"id": "NYC001", "name": "New York City", "type": "builtin"},
        {"id": "LAX001", "name": "Los Angeles", "type": "builtin"},
        {"id": "CUSTOM001", "name": "Downtown Manhattan", "type": "custom"},
    ]

    # Filter function
    def filter_regions_by_type(regions, type_filter):
        return [r for r in regions if r["type"] == type_filter]

    # Test filtering
    builtin_regions = filter_regions_by_type(regions, "builtin")
    custom_regions = filter_regions_by_type(regions, "custom")

    assert len(builtin_regions) == 2  # noqa: PLR2004
    assert all(r["type"] == "builtin" for r in builtin_regions)
    assert [r["id"] for r in builtin_regions] == ["NYC001", "LAX001"]

    assert len(custom_regions) == 1
    assert custom_regions[0]["id"] == "CUSTOM001"
    assert custom_regions[0]["type"] == "custom"
