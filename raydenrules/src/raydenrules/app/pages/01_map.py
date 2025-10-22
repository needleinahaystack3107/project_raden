"""
Map Page - Visualize geospatial heat and climate data
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd
import pydeck as pdk
import streamlit as st

# Page title
st.title("Climate Map View")


# Load mock data
@st.cache_data
def load_mock_data():
    """Load mock metrics data from JSON file"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(
        script_dir, "..", "..", "..", "data", "01_raw", "data_samples", "metrics_mock.json"
    )

    with open(data_path) as f:
        data = json.load(f)

    return data


# Load data
data = load_mock_data()
bbox = data["meta"]["bbox"]
region_center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]

# Layer selector
st.sidebar.header("Map Settings")
map_layers = [
    "Land Surface Temperature",
    "Anomaly",
    "Heatwave Flag",
    "Urban Heat Island",
    "CDD/HDD",
]
selected_layer = st.sidebar.selectbox("Select Layer", map_layers)

# Date selector
current_date = datetime.now().date()
selected_date = st.sidebar.date_input("Select Date", current_date)


# Create mock heatmap data
def create_mock_heatmap_data():
    # Create a grid of points within the bounding box
    lon_range = bbox[2] - bbox[0]
    lat_range = bbox[3] - bbox[1]

    grid_size = 20
    points = []

    for i in range(grid_size):
        for j in range(grid_size):
            lon = bbox[0] + (i / grid_size) * lon_range
            lat = bbox[1] + (j / grid_size) * lat_range

            # Create a heat value that's higher in the center (simulating an urban heat island)
            dist_from_center = (
                (lon - region_center[0]) ** 2 + (lat - region_center[1]) ** 2
            ) ** 0.5
            max_dist = ((lon_range / 2) ** 2 + (lat_range / 2) ** 2) ** 0.5
            normalized_dist = dist_from_center / max_dist

            if selected_layer == "Land Surface Temperature":
                value = 35 - (normalized_dist * 15)  # 20-35°C range
            elif selected_layer == "Anomaly":
                value = 3 - (normalized_dist * 4)  # -1 to 3 range
            elif selected_layer == "Heatwave Flag":
                HEATWAVE_THRESHOLD = 0.3  # Threshold for heatwave flag
                value = 1 if normalized_dist < HEATWAVE_THRESHOLD else 0  # Binary 0 or 1
            elif selected_layer == "Urban Heat Island":
                value = 5 - (normalized_dist * 5)  # 0-5 range
            else:  # CDD/HDD
                value = 10 - (normalized_dist * 10)  # 0-10 range

            points.append({"lat": lat, "lon": lon, "value": value})

    return pd.DataFrame(points)


heatmap_data = create_mock_heatmap_data()


# Create the map with PyDeck
def get_color_scale():
    if selected_layer == "Land Surface Temperature":
        return [[20, [65, 105, 225]], [30, [173, 216, 230]], [35, [255, 0, 0]]]
    elif selected_layer == "Anomaly":
        return [[-1, [0, 0, 255]], [0, [255, 255, 255]], [3, [255, 0, 0]]]
    elif selected_layer == "Heatwave Flag":
        return [[0, [173, 216, 230]], [1, [255, 0, 0]]]
    elif selected_layer == "Urban Heat Island":
        return [[0, [173, 216, 230]], [3, [255, 255, 0]], [5, [255, 0, 0]]]
    else:  # CDD/HDD
        return [[0, [173, 216, 230]], [5, [255, 255, 0]], [10, [255, 0, 0]]]


layer = pdk.Layer(
    "HeatmapLayer",
    data=heatmap_data,
    opacity=0.8,
    get_position=["lon", "lat"],
    get_weight="value",
    threshold=0.05,
    aggregation='"MEAN"',
    color_range=get_color_scale(),
)

view_state = pdk.ViewState(
    longitude=region_center[0],
    latitude=region_center[1],
    zoom=10,
    pitch=0,
)

r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v9",
    tooltip={"text": "{value}"},
)

# Render the map
st.pydeck_chart(r)

# Legend
st.subheader("Legend")
legend_col1, legend_col2, legend_col3 = st.columns(3)

with legend_col1:
    if selected_layer == "Land Surface Temperature":
        st.markdown("🔵 20°C")
    elif selected_layer == "Anomaly":
        st.markdown("🔵 -1°C (below average)")
    elif selected_layer == "Heatwave Flag":
        st.markdown("🔵 No heatwave")
    elif selected_layer == "Urban Heat Island":
        st.markdown("🔵 0 (no UHI effect)")
    else:  # CDD/HDD
        st.markdown("🔵 0 CDD")

with legend_col2:
    if selected_layer == "Land Surface Temperature":
        st.markdown("🟢 30°C")
    elif selected_layer == "Anomaly":
        st.markdown("⚪ 0°C (average)")
    elif selected_layer == "Heatwave Flag":
        st.markdown("")
    elif selected_layer == "Urban Heat Island":
        st.markdown("🟡 3 (moderate UHI)")
    else:  # CDD/HDD
        st.markdown("🟡 5 CDD")

with legend_col3:
    if selected_layer == "Land Surface Temperature":
        st.markdown("🔴 35°C")
    elif selected_layer == "Anomaly":
        st.markdown("🔴 +3°C (above average)")
    elif selected_layer == "Heatwave Flag":
        st.markdown("🔴 Heatwave")
    elif selected_layer == "Urban Heat Island":
        st.markdown("🔴 5 (severe UHI)")
    else:  # CDD/HDD
        st.markdown("🔴 10 CDD")

# Date slider for animation (non-functional in this prototype)
st.slider(
    "Animation timeline",
    min_value=datetime.now().date() - timedelta(days=30),
    max_value=datetime.now().date(),
    value=selected_date,
    format="YYYY-MM-DD",
    disabled=True,
)

# Placeholder for future functionality
st.caption(
    "Note: This is a prototype with simulated data. In the full version, you'll be able to animate through time and download/analyze specific areas."
)
