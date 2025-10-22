"""
Regions Page - Upload and manage custom geographic regions
"""

import time
from datetime import datetime

import pandas as pd
import streamlit as st

# Page title
st.title("Geographic Regions")

# Display built-in regions
st.subheader("Built-in Regions")
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

regions_df = pd.DataFrame(built_in_regions)
st.dataframe(
    regions_df,
    column_config={"id": "ID", "name": "Region Name", "type": "Type", "bbox": "Bounding Box"},
    use_container_width=True,
)

# User-defined regions section
st.subheader("Custom Regions")

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
st.subheader("Upload New Region")

with st.form("upload_region_form"):
    region_name = st.text_input("Region Name")
    geojson_file = st.file_uploader("Upload GeoJSON", type="geojson")

    col1, col2 = st.columns(2)
    with col1:
        submit_button = st.form_submit_button("Upload and Save Region")

if submit_button and geojson_file is not None and region_name:
    # Mock successful upload
    st.success(f"Region '{region_name}' uploaded successfully!")

    # Display a progress bar to simulate processing
    progress_text = "Processing and indexing region..."
    progress_bar = st.progress(0, text=progress_text)

    for i in range(100):
        time.sleep(0.01)
        progress_bar.progress(i + 1, text=progress_text)

    st.info(f"Region '{region_name}' is ready to use.")

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

# Backfill section
st.subheader("Backfill Data for Region")

# Region selector for backfill
all_regions = [r["name"] for r in built_in_regions + custom_regions]
backfill_region = st.selectbox("Select Region for Backfill", all_regions)

# Date range for backfill
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date", datetime.now().replace(year=datetime.now().year - 1).date()
    )
with col2:
    end_date = st.date_input("End Date", datetime.now().date())

if st.button("Request Backfill"):
    # Mock backfill request
    st.success(f"Backfill requested for {backfill_region} from {start_date} to {end_date}!")

    # Show queue information
    st.info("Your backfill job has been queued. Job ID: BF-2025-10-21-001")

    # Mock job status
    st.metric(label="Estimated Processing Time", value="~15 minutes", delta=None)

    # Additional instructions
    st.markdown(
        """
    **What happens next?**
    1. Your backfill job is processed in the background
    2. When complete, data will be available in the Map and Overview pages
    3. You'll receive a notification when processing is finished
    """
    )
