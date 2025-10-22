"""
Alerts Page - Create and manage climate alerts
"""

from datetime import datetime

import pandas as pd
import streamlit as st

# Page title
st.title("Climate Alerts")

# Mock existing alerts data
existing_alerts = [
    {
        "id": "alert-001",
        "name": "NYC Heatwave Alert",
        "region_id": "NYC001",
        "rule": "heatwave_flag >= 1 for 3 days",
        "channel": "email",
        "recipients": "alerts@example.com",
        "status": "active",
    },
    {
        "id": "alert-002",
        "name": "UHI Critical Level",
        "region_id": "NYC001",
        "rule": "uhi_index > 4.5",
        "channel": "slack",
        "recipients": "#climate-alerts",
        "status": "active",
    },
]

# Display existing alerts
st.subheader("Existing Alerts")

if existing_alerts:
    alerts_df = pd.DataFrame(existing_alerts)
    st.dataframe(
        alerts_df,
        column_config={
            "id": "ID",
            "name": "Alert Name",
            "region_id": "Region",
            "rule": "Rule",
            "channel": "Channel",
            "recipients": "Recipients",
            "status": "Status",
        },
        use_container_width=True,
    )

    # Select alert to edit or delete
    selected_alert = st.selectbox(
        "Select an alert to edit or delete:",
        ["None"] + [alert["name"] for alert in existing_alerts],
    )
else:
    st.info("No alerts configured yet.")
    selected_alert = "None"

# Create new alert form
st.subheader("Create New Alert")

with st.form("create_alert_form"):
    # Basic alert information
    alert_name = st.text_input("Alert Name")

    # Region selector
    regions = ["New York City", "Los Angeles", "Chicago", "Miami"]
    selected_region = st.selectbox("Select Region", regions)

    # Rule configuration
    st.subheader("Rule Configuration")
    metric_options = ["lst_mean_c", "heatwave_flag", "uhi_index", "anomaly_zscore", "cdd"]
    selected_metric = st.selectbox("Select Metric", metric_options)

    col1, col2 = st.columns(2)
    with col1:
        condition = st.selectbox("Condition", [">=", ">", "=", "<", "<="])
    with col2:
        threshold = st.number_input("Threshold", value=1.0)

    duration = st.slider("Duration (days)", 1, 7, 1)

    rule_preview = (
        f"{selected_metric} {condition} {threshold} for {duration} day{'s' if duration > 1 else ''}"
    )
    st.info(f"Rule: {rule_preview}")

    # Notification channel
    st.subheader("Notification")
    channel = st.selectbox("Notification Channel", ["Email", "Slack", "Webhook"])

    if channel == "Email":
        recipients = st.text_input("Email Addresses (comma-separated)")
    elif channel == "Slack":
        recipients = st.text_input("Slack Channel (e.g., #climate-alerts)")
    else:  # Webhook
        recipients = st.text_input("Webhook URL")

    # Test and submit
    col1, col2 = st.columns(2)
    with col1:
        test_button = st.form_submit_button("Test Alert")
    with col2:
        submit_button = st.form_submit_button("Create Alert")

if test_button:
    st.success("Alert test successful! A notification was sent via the selected channel.")

if submit_button:
    if alert_name and selected_region and recipients:
        st.success(f"Alert '{alert_name}' created successfully!")
        st.json(
            {
                "name": alert_name,
                "region": selected_region,
                "rule": rule_preview,
                "channel": channel.lower(),
                "recipients": recipients,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    else:
        st.error("Please fill in all required fields.")

# Delete section (only shown when an alert is selected)
if selected_alert != "None":
    st.subheader("Delete Alert")
    st.warning(f"Are you sure you want to delete the alert '{selected_alert}'?")
    if st.button("Delete Alert"):
        st.success(f"Alert '{selected_alert}' deleted successfully!")
