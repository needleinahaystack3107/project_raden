"""
Alerts Management - Configure and monitor climate risk threshold notifications
"""

import os
import sys

import pandas as pd
import streamlit as st

# Set up path for imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

from theme import apply_terminal_theme  # noqa: E402

# Apply terminal theme
apply_terminal_theme()

# Page header with terminal styling
st.markdown(
    """
    <div style="background-color: #0a0a0a; padding: 10px; border: 1px solid #00FF00; margin-bottom: 20px;">
        <h1 style="color: #00FF00; font-family: 'Courier New', monospace; margin: 0;">
            <span style="color: #7FFFD4;">> </span>RISK ALERT MANAGEMENT
        </h1>
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
            Configure threshold-based notifications for climate risk factors
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

# Mock existing alerts data
existing_alerts = [
    {
        "id": "alert-001",
        "name": "NYC Heatwave Risk Monitor",
        "region_id": "NYC001",
        "rule": "heatwave_flag >= 1 for 3 days",
        "channel": "email",
        "recipients": "risk-team@example.com",
        "status": "ACTIVE",
        "severity": "HIGH",
    },
    {
        "id": "alert-002",
        "name": "Urban Heat Index Threshold",
        "region_id": "NYC001",
        "rule": "uhi_index > 4.5",
        "channel": "slack",
        "recipients": "#climate-risk",
        "status": "ACTIVE",
        "severity": "CRITICAL",
    },
]

# Display existing alerts with terminal styling
st.markdown(
    """
    <div style="font-family: 'Courier New', monospace; margin: 20px 0 10px 0;">
        <span style="color: #7FFFD4;">>></span>
        <span style="color: #00FF00; font-weight: bold;"> CONFIGURED ALERTS</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if existing_alerts:
    alerts_df = pd.DataFrame(existing_alerts)

    # Add styling header
    st.markdown(
        """
        <div style="background-color: #0a0a0a; padding: 5px; border-top: 1px solid #00FF00; border-left: 1px solid #00FF00; border-right: 1px solid #00FF00;">
            <p style="color: #7FFFD4; font-family: 'Courier New', monospace; text-align: center; margin: 0;">
                ACTIVE MONITORING ALERTS
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.dataframe(
        alerts_df,
        column_config={
            "id": "ALERT ID",
            "name": "DESCRIPTION",
            "region_id": "MARKET",
            "rule": "THRESHOLD RULE",
            "channel": "NOTIFICATION METHOD",
            "recipients": "RECIPIENTS",
            "status": "STATUS",
            "severity": "RISK LEVEL",
        },
        use_container_width=True,
    )

    # Select alert to edit or delete - with terminal styling
    st.markdown(
        """
        <div style="background-color: #0a0a0a; padding: 5px; margin-top: 15px; border: 1px solid #00FF00;">
            <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
                ALERT MANAGEMENT
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_alert = st.selectbox(
        "SELECT ALERT TO MANAGE:",
        ["NONE"] + [alert["name"] for alert in existing_alerts],
    )
else:
    st.info("NO ALERTS CONFIGURED")
    selected_alert = "NONE"

# Create new alert form with terminal styling
st.markdown(
    """
    <div style="font-family: 'Courier New', monospace; margin: 20px 0 10px 0;">
        <span style="color: #7FFFD4;">>></span>
        <span style="color: #00FF00; font-weight: bold;"> CREATE NEW RISK ALERT</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Terminal-styled form container
st.markdown(
    """
    <div style="background-color: #0a0a0a; padding: 5px; border-top: 1px solid #00FF00; border-left: 1px solid #00FF00; border-right: 1px solid #00FF00;">
        <p style="color: #7FFFD4; font-family: 'Courier New', monospace; text-align: center; margin: 0;">
            ALERT CONFIGURATION TERMINAL
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("create_alert_form"):
    # Basic alert information
    alert_name = st.text_input("ALERT NAME")

    # Region selector
    regions = ["New York City", "Los Angeles", "Chicago", "Miami"]
    selected_region = st.selectbox("SELECT MARKET", regions)

    # Rule configuration
    st.markdown(
        """
        <div style="font-family: 'Courier New', monospace; margin: 10px 0 5px 0;">
            <span style="color: #7FFFD4;">></span>
            <span style="color: #00FF00;"> RULE CONFIGURATION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_options = {
        "lst_mean_c": "Surface Temperature (°C)",
        "heatwave_flag": "Heatwave Flag",
        "uhi_index": "Urban Heat Index",
        "anomaly_zscore": "Anomaly Z-Score",
        "cdd": "Cooling Degree Days",
    }

    selected_metric_name = st.selectbox("SELECT METRIC", list(metric_options.values()))
    selected_metric = list(metric_options.keys())[
        list(metric_options.values()).index(selected_metric_name)
    ]

    col1, col2 = st.columns(2)
    with col1:
        condition = st.selectbox("CONDITION", [">=", ">", "=", "<", "<="])
    with col2:
        threshold = st.number_input("THRESHOLD VALUE", value=1.0)

    duration = st.slider("DURATION (DAYS)", 1, 7, 1)

    # Risk level selector
    severity = st.selectbox("RISK LEVEL", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    rule_preview = (
        f"{selected_metric} {condition} {threshold} for {duration} day{'s' if duration > 1 else ''}"
    )

    st.markdown(
        f"""
        <div style="background-color: #0a0a0a; padding: 8px; border: 1px solid #00FF00; margin: 10px 0;">
            <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
                RULE PREVIEW: <span style="color: #00FF00;">{rule_preview}</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Notification channel
    st.markdown(
        """
        <div style="font-family: 'Courier New', monospace; margin: 10px 0 5px 0;">
            <span style="color: #7FFFD4;">></span>
            <span style="color: #00FF00;"> NOTIFICATION SETTINGS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    channel = st.selectbox("NOTIFICATION METHOD", ["EMAIL", "SLACK", "WEBHOOK"])

    if channel == "EMAIL":
        recipients = st.text_input("EMAIL ADDRESSES (comma-separated)")
    elif channel == "SLACK":
        recipients = st.text_input("SLACK CHANNEL (e.g., #climate-risk)")
    else:  # Webhook
        recipients = st.text_input("WEBHOOK URL")

    # Submit button
    submit = st.form_submit_button("CREATE ALERT")

if submit:
    st.success("✓ ALERT CONFIGURATION COMPLETE")

    # Display a preview of the created alert with terminal styling
    st.markdown(
        f"""
        <div style="background-color: #0a0a0a; padding: 10px; border: 1px solid #00FF00; margin: 10px 0;">
            <p style="color: #7FFFD4; font-family: 'Courier New', monospace; margin: 0; font-size: 0.9em;">
                ALERT CREATED:
            </p>
            <div style="font-family: 'Courier New', monospace; margin: 5px 0; color: #00FF00;">
                NAME: {alert_name}<br>
                MARKET: {selected_region}<br>
                RULE: {rule_preview}<br>
                RISK LEVEL: <span style="color: {'#00FF00' if severity == 'LOW' else '#FFFF00' if severity == 'MEDIUM' else '#FFA500' if severity == 'HIGH' else '#FF0000'}">{severity}</span><br>
                NOTIFICATION: {channel} to {recipients}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
