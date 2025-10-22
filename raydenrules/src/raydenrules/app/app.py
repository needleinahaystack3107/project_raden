"""
Rayden Rules - Climate Analysis and Heat Monitoring Platform
Main Streamlit application entry point
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Rayden Rules - Climate Analysis Platform",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Load mock data
@st.cache_data
def load_mock_data():
    """Load mock metrics data from JSON file"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(
        script_dir, "..", "..", "data", "01_raw", "data_samples", "metrics_mock.json"
    )

    with open(data_path) as f:
        data = json.load(f)

    # Convert metrics to dataframe
    metrics_df = pd.DataFrame(data["metrics"])
    metrics_df["date"] = pd.to_datetime(metrics_df["date"])

    return data, metrics_df


# Load data
data, metrics_df = load_mock_data()

# Sidebar
st.sidebar.title("Rayden Rules")
st.sidebar.info("Climate Analysis and Heat Monitoring Platform")

# Time range selector
st.sidebar.header("Settings")
today = datetime.now().date()
date_range = st.sidebar.date_input(
    "Select Date Range", value=(today - timedelta(days=7), today), max_value=today
)

# Region selector
regions = ["New York City", "Los Angeles", "Chicago", "Miami"]  # Mock regions
selected_region = st.sidebar.selectbox("Select Region", regions)

# Main dashboard
st.title("Climate Monitoring Overview")

# KPI cards
st.subheader("Key Indicators")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric(
        label="Average LST",
        value=f"{data['kpi_summary']['ytd']['avg_lst_c']}°C",
        delta="+1.2°C",
    )

with kpi_col2:
    st.metric(
        label="Heatwave Days (YTD)",
        value=data["kpi_summary"]["ytd"]["heatwave_days"],
        delta="+2 days",
    )

with kpi_col3:
    st.metric(label="CDD Today", value=data["kpi_summary"]["today"]["cdd"], delta="-0.5")

with kpi_col4:
    st.metric(
        label="Anomaly Z-Score", value=data["kpi_summary"]["today"]["anomaly_zscore"], delta="0.0"
    )

# Metrics chart
st.subheader("Temperature Trends")
st.line_chart(metrics_df.set_index("date")[["lst_mean_c", "uhi_index"]])

# Download data button
st.download_button(
    label="Download CSV",
    data=metrics_df.to_csv(index=False).encode("utf-8"),
    file_name=f"climate_data_{selected_region.lower().replace(' ', '_')}.csv",
    mime="text/csv",
)

# App footer
st.markdown("---")
st.caption("© 2025 Rayden Rules - Climate Analysis Platform | Day 0 POC Demo")
