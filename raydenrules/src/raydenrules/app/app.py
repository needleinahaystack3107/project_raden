"""
Rayden Rules - Climate Risk Intelligence Platform
Main application entry point
"""

import json
import os
import sys
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st
from theme import apply_terminal_theme, format_metric_card

# Add current directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Apply terminal theme before any other Streamlit elements
apply_terminal_theme()

# Set page configuration
st.set_page_config(
    page_title="Rayden Rules - Climate Risk Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API configuration
API_BASE_URL = "http://localhost:8000"

# Constants
HTTP_OK = 200
ANOMALY_WARNING_THRESHOLD = 1
ANOMALY_CRITICAL_THRESHOLD = 2


# Function to fetch regions from API (with fallback to mock data)
@st.cache_data(ttl=3600)
def load_regions() -> list[dict]:
    """
    Load available regions from the API or mock data.

    Returns:
        List of region dictionaries with id, name, bbox, and type
    """
    try:
        response = requests.get(f"{API_BASE_URL}/v1/regions", timeout=5)
        if response.status_code == HTTP_OK:
            regions = response.json()
            return regions
    except Exception as e:
        st.warning(f"API Connection Failed: {str(e)}")

    # Fallback to mock data
    return [
        {
            "id": "NYC001",
            "name": "New York City",
            "bbox": [-74.2589, 40.4774, -73.7004, 40.9176],
            "type": "builtin",
        },
        {
            "id": "LAX001",
            "name": "Los Angeles",
            "bbox": [-118.6682, 33.7037, -118.1553, 34.3373],
            "type": "builtin",
        },
        {
            "id": "CHI001",
            "name": "Chicago",
            "bbox": [-87.9402, 41.6445, -87.5245, 42.0229],
            "type": "builtin",
        },
        {
            "id": "MIA001",
            "name": "Miami",
            "bbox": [-80.3187, 25.7095, -80.1155, 25.8901],
            "type": "builtin",
        },
        {
            "id": "CUSTOM001",
            "name": "Downtown Manhattan",
            "bbox": [-74.0315, 40.7002, -73.9701, 40.7382],
            "type": "custom",
        },
    ]


# Function to fetch metrics from API (with fallback to mock data)
@st.cache_data(ttl=300)
def load_metrics(
    region_id: str, from_date: str, to_date: str, variables: str = None
) -> tuple[dict, pd.DataFrame]:
    """
    Load climate risk metrics for a specific region and time range.

    Args:
        region_id: Region identifier
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        variables: Comma-separated list of variables to include

    Returns:
        Tuple of (data_dict, metrics_dataframe)
    """
    params = {
        "region_id": region_id,
        "from_date": from_date,
        "to_date": to_date,
    }

    if variables:
        params["vars"] = variables

    try:
        response = requests.get(f"{API_BASE_URL}/v1/metrics", params=params, timeout=5)
        if response.status_code == HTTP_OK:
            data = response.json()
            # Convert metrics to dataframe
            metrics_df = pd.DataFrame(data["metrics"])
            if not metrics_df.empty:
                metrics_df["date"] = pd.to_datetime(metrics_df["date"])
            return data, metrics_df
    except Exception as e:
        st.warning(f"Data Retrieval Failed: {str(e)}")

    # Fallback to mock data
    return load_mock_data()


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


# Sidebar with terminal-like styling
st.sidebar.markdown(
    """
    <div style="text-align: center;">
        <h1 style="color: #00FF00; font-family: 'Courier New', monospace; margin-bottom: 0;">RAYDEN RULES</h1>
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin-top: 0;">CLIMATE RISK INTELLIGENCE</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# Region selector
st.sidebar.markdown(
    """
    <div style="font-family: 'Courier New', monospace;">
        <span style="color: #7FFFD4;">></span>
        <span style="color: #00FF00;"> SELECT REGION</span>
    </div>
    """,
    unsafe_allow_html=True,
)
regions = load_regions()
region_options = {region["name"]: region["id"] for region in regions}
selected_region_name = st.sidebar.selectbox(
    "Market Coverage",
    options=list(region_options.keys()),
    index=0,
    help="Select geographic market for climate risk analysis",
)
selected_region_id = region_options[selected_region_name]

# Get selected region details
selected_region = next((r for r in regions if r["id"] == selected_region_id), None)

# Time range selector
st.sidebar.markdown(
    """
    <div style="font-family: 'Courier New', monospace; margin-top: 20px;">
        <span style="color: #7FFFD4;">></span>
        <span style="color: #00FF00;"> TIMEFRAME</span>
    </div>
    """,
    unsafe_allow_html=True,
)
today = date.today()
default_start = today - timedelta(days=30)
default_end = today

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("FROM", value=default_start)
with col2:
    end_date = st.date_input("TO", value=default_end)

# Load data for selected region and time range
data, metrics_df = load_metrics(
    region_id=selected_region_id,
    from_date=start_date.strftime("%Y-%m-%d"),
    to_date=end_date.strftime("%Y-%m-%d"),
)

# Display header with terminal-style formatting
st.markdown(
    f"""
    <div style="background-color: #0a0a0a; padding: 10px; border: 1px solid #00FF00; margin-bottom: 20px;">
        <h1 style="color: #00FF00; font-family: 'Courier New', monospace; margin: 0;">
            <span style="color: #7FFFD4;">MARKET:</span> {selected_region_name.upper()}
        </h1>
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
            ID: {selected_region_id} | LAT/LON: {selected_region['bbox'] if selected_region else 'N/A'}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# KPI Cards - Summary Risk Indicators
st.markdown(
    """
    <div style="font-family: 'Courier New', monospace; margin-bottom: 10px;">
        <span style="color: #7FFFD4;">>></span>
        <span style="color: #00FF00; font-weight: bold;"> RISK INDICATORS</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Calculate summary metrics
if not metrics_df.empty:
    avg_lst = metrics_df["lst_mean_c"].mean()
    heatwave_days = metrics_df["heatwave_flag"].sum()
    latest_day = metrics_df.iloc[-1]
    today_cdd = latest_day.get("cdd", 0)
    today_hdd = latest_day.get("hdd", 0)
    anomaly_zscore = latest_day.get("anomaly_zscore", 0)
else:
    # Fallback values if no data
    avg_lst = 0
    heatwave_days = 0
    today_cdd = 0
    today_hdd = 0
    anomaly_zscore = 0

# Display KPI cards in a grid with terminal styling
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(
        format_metric_card(
            "SURFACE TEMP",
            f"{avg_lst:.1f}°C",
            f"VARIANCE: {avg_lst - 20:.1f}°C" if avg_lst > 0 else "NO DATA",
        ),
        unsafe_allow_html=True,
    )

with kpi_col2:
    st.markdown(
        format_metric_card(
            "HEATWAVE EXPOSURE",
            f"{heatwave_days} DAYS",
            f"YTD DELTA: {heatwave_days - 3}" if heatwave_days > 0 else "NO EXPOSURE",
        ),
        unsafe_allow_html=True,
    )

with kpi_col3:
    st.markdown(
        format_metric_card(
            "ENERGY DEMAND",
            f"CDD: {today_cdd:.1f} | HDD: {today_hdd:.1f}",
            "COOLING/HEATING DEGREE DAYS",
        ),
        unsafe_allow_html=True,
    )

with kpi_col4:
    color = (
        "#00FF00"
        if abs(anomaly_zscore) < ANOMALY_WARNING_THRESHOLD
        else "#FFFF00" if abs(anomaly_zscore) < ANOMALY_CRITICAL_THRESHOLD else "#FF0000"
    )
    st.markdown(
        f"""
        <div class="kpi-card">
            <small style="color: #7FFFD4; font-family: 'Courier New', monospace;">ANOMALY INDEX</small>
            <h3 style="margin:0; color: {color}; font-family: 'Courier New', monospace;">{anomaly_zscore:.2f}σ</h3>
            <small style="color: #7FFFD4; font-family: 'Courier New', monospace;">
                {'NORMAL' if abs(anomaly_zscore) < ANOMALY_WARNING_THRESHOLD else 'ALERT' if abs(anomaly_zscore) < ANOMALY_CRITICAL_THRESHOLD else 'CRITICAL'}
            </small>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Time series visualization
st.markdown(
    """
    <div style="font-family: 'Courier New', monospace; margin: 20px 0 10px 0;">
        <span style="color: #7FFFD4;">>></span>
        <span style="color: #00FF00; font-weight: bold;"> HISTORICAL TREND ANALYSIS</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Chart type selector with terminal styling
st.markdown(
    """
    <div style="background-color: #0a0a0a; padding: 10px; border: 1px solid #00FF00; margin-bottom: 10px;">
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0 0 5px 0; font-size: 0.9em;">
            SELECT VISUALIZATION TYPE:
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
chart_type = st.radio("", ["LINE", "BAR", "AREA"], horizontal=True)

# Create time series chart
if not metrics_df.empty:
    # Variables selector for the chart with terminal styling
    st.markdown(
        """
        <div style="background-color: #0a0a0a; padding: 10px; border: 1px solid #00FF00; margin: 10px 0;">
            <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
                SELECT METRICS TO DISPLAY:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Variables selector for the chart
    available_vars = [col for col in metrics_df.columns if col != "date"]
    variable_labels = {
        "lst_mean_c": "Surface Temperature (°C)",
        "lst_min_c": "Min Temperature (°C)",
        "lst_max_c": "Max Temperature (°C)",
        "anomaly_zscore": "Anomaly Z-Score",
        "heatwave_flag": "Heatwave Flag",
        "uhi_index": "Urban Heat Index",
        "cdd": "Cooling Degree Days",
        "hdd": "Heating Degree Days",
    }

    # Create readable labels for variables
    display_options = {
        variable_labels.get(var, var.replace("_", " ").title()): var for var in available_vars
    }

    selected_display_vars = st.multiselect(
        "",
        options=list(display_options.keys()),
        default=(
            ["Surface Temperature (°C)", "Anomaly Z-Score"]
            if "lst_mean_c" in available_vars and "anomaly_zscore" in available_vars
            else list(display_options.keys())[:2]
        ),
    )

    # Map display names back to actual column names
    selected_vars = [display_options[display_var] for display_var in selected_display_vars]

    if selected_vars:
        # Create the chart
        chart_data = metrics_df.set_index("date")[selected_vars]

        # Rename columns for display
        inv_variable_labels = {v: k for k, v in variable_labels.items()}
        chart_data.columns = [
            inv_variable_labels.get(col, col.replace("_", " ").title())
            for col in chart_data.columns
        ]

        # Add styling info before displaying chart
        st.markdown(
            """
            <div style="background-color: #0a0a0a; padding: 5px; border-top: 1px solid #00FF00; border-left: 1px solid #00FF00; border-right: 1px solid #00FF00;">
                <p style="color: #7FFFD4; font-family: 'Courier New', monospace; text-align: center; margin: 0;">
                    TREND VISUALIZATION
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if chart_type == "LINE":
            st.line_chart(chart_data)
        elif chart_type == "BAR":
            st.bar_chart(chart_data)
        else:  # AREA
            st.area_chart(chart_data)
    else:
        st.info("SELECT AT LEAST ONE METRIC TO DISPLAY")
else:
    st.warning("NO DATA AVAILABLE FOR SELECTED MARKET AND TIMEFRAME")

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
