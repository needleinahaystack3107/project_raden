"""
Regions Page - Upload and manage custom geographic regions
"""

import os
import sys
import time
from datetime import datetime

import pandas as pd
import streamlit as st

# Set up path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from theme import apply_terminal_theme, terminal_header  # noqa: E402

# Apply terminal theme
apply_terminal_theme()

# Page header with terminal styling
st.markdown(
    """
    <div style="background-color: #0a0a0a; padding: 10px; border: 1px solid #00FF00; margin-bottom: 20px;">
        <h1 style="color: #00FF00; font-family: 'Courier New', monospace; margin: 0;">
            <span style="color: #7FFFD4;">> </span>GEOGRAPHIC REGIONS
        </h1>
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
            Upload and manage custom geographic regions for climate risk analysis
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display built-in regions
st.markdown(terminal_header("BUILT-IN REGIONS", level=2), unsafe_allow_html=True)
built_in_regions = [
    {
        "id": "NYC001",
        "name": "New York City",
        "type": "builtin",
        "bbox": [-74.2589, 40.4774, -73.7004, 40.9176],
    },
    {
        "id": "LAX001",
        "name": "Los Angeles",
        "type": "builtin",
        "bbox": [-118.6682, 33.7037, -118.1553, 34.3373],
    },
    {
        "id": "CHI001",
        "name": "Chicago",
        "type": "builtin",
        "bbox": [-87.9402, 41.6446, -87.5241, 42.0230],
    },
    {
        "id": "MIA001",
        "name": "Miami",
        "type": "builtin",
        "bbox": [-80.3198, 25.7095, -80.1398, 25.8557],
    },
]

# Add custom styling for table text - changing text color to black for better visibility
st.markdown(
    """
    <style>
    /* Overriding table text color to black for better visibility */
    .stDataFrame td, .stDataFrame th, .dataframe td, .dataframe th {
        color: #000000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

regions_df = pd.DataFrame(built_in_regions)
st.dataframe(
    regions_df,
    column_config={"id": "ID", "name": "Region Name", "type": "Type", "bbox": "Bounding Box"},
    use_container_width=True,
)

# User-defined regions section
st.markdown(terminal_header("CUSTOM REGIONS", level=2), unsafe_allow_html=True)

# Mock custom regions
custom_regions = [
    {
        "id": "CUSTOM001",
        "name": "Downtown Manhattan",
        "type": "custom",
        "bbox": [-74.0151, 40.7001, -73.9696, 40.7310],
        "created": "2025-10-15",
    }
]

if custom_regions:
    custom_df = pd.DataFrame(custom_regions)
    st.dataframe(
        custom_df,
        column_config={
            "id": "ID",
            "name": "Region Name",
            "type": "Type",
            "bbox": "Bounding Box",
            "created": "Created Date",
        },
        use_container_width=True,
    )
else:
    st.info("No custom regions defined yet.")

# Upload GeoJSON for custom region
st.markdown(terminal_header("UPLOAD NEW REGION", level=2), unsafe_allow_html=True)

with st.form("upload_region_form"):
    region_name = st.text_input("Region Name")
    geojson_file = st.file_uploader("Upload GeoJSON", type="geojson")

    col1, col2 = st.columns(2)
    with col1:
        submit_button = st.form_submit_button("Upload and Save Region")

# Add terminal styling for success message
if submit_button and geojson_file is not None and region_name:
    # Mock successful upload
    st.markdown(
        f"""
        <div style="background-color: #0a0a0a; padding: 8px; border: 1px solid #00FF00; margin: 10px 0;">
            <p style="color: #00FF00; font-family: 'Courier New', monospace; margin: 0;">
                ✓ Region '{region_name}' uploaded successfully!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display a progress bar to simulate processing
    progress_text = "Processing and indexing region..."
    progress_bar = st.progress(0, text=progress_text)

    for i in range(100):
        time.sleep(0.01)
        progress_bar.progress(i + 1, text=progress_text)

    st.markdown(
        f"""
        <div style="background-color: #0a0a0a; padding: 8px; border: 1px solid #00FF00; margin: 10px 0;">
            <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0;">
                Region '{region_name}' is ready to use.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Example of uploaded GeoJSON structure
    st.json(
        {
            "id": f"CUSTOM{len(custom_regions) + 1:03d}",
            "name": region_name,
            "type": "custom",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "properties": {"area_sqkm": 12.5, "perimeter_km": 15.8},  # Mock value  # Mock value
        }
    )

# App footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; font-size: 0.8em;">
            RAYDEN RULES™ | CLIMATE RISK INTELLIGENCE PLATFORM | © 2025 | VERSION 0.0.0
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
