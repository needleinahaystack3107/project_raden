"""
Rayden Rules - Climate Risk Intelligence Platform
Reflex-based Application
"""

import json
import os
from datetime import date, timedelta
from typing import Any

import pandas as pd
import reflex as rx
import requests

# API Configuration
# Note: The app will attempt to call external FastAPI on 8001, but falls back to mock data
API_BASE_URL = "http://localhost:8001"

# Constants
HTTP_OK = 200
ANOMALY_WARNING_THRESHOLD = 1
ANOMALY_CRITICAL_THRESHOLD = 2


class State(rx.State):
    """Application state management."""

    # Region data
    regions: list[dict[str, Any]] = []
    selected_region_id: str = "NYC001"
    selected_region_name: str = "New York City"

    # Date range
    start_date: str = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date: str = date.today().strftime("%Y-%m-%d")

    # Metrics data
    metrics_data: dict[str, Any] = {}
    metrics_df: pd.DataFrame = pd.DataFrame()

    # Chart options
    chart_type: str = "line"
    selected_variables: list[str] = ["lst_mean_c", "anomaly_zscore"]
    available_variables: list[str] = []

    # Computed metrics
    avg_lst: float = 0.0
    heatwave_days: int = 0
    today_cdd: float = 0.0
    today_hdd: float = 0.0
    anomaly_zscore: float = 0.0

    # Alert management (for alerts page)
    alerts: list[dict[str, Any]] = []
    alert_name: str = ""
    alert_region: str = "New York City"
    alert_metric: str = "lst_mean_c"
    alert_condition: str = ">="
    alert_threshold: float = 1.0
    alert_duration: int = 1
    alert_severity: str = "LOW"
    alert_channel: str = "EMAIL"
    alert_recipients: str = ""
    alert_start_date: str = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    alert_end_date: str = date.today().strftime("%Y-%m-%d")

    # Region management (for regions page)
    custom_regions: list[dict[str, Any]] = []
    new_region_name: str = ""

    @rx.var
    def region_names(self) -> list[str]:
        """Get list of region names for the select dropdown."""
        return [region["name"] for region in self.regions]

    @rx.var
    def chart_data(self) -> list[dict[str, Any]]:
        """Prepare data for charts."""
        if self.metrics_df.empty:
            return []

        data = []
        for _, row in self.metrics_df.iterrows():
            point = {"date": row["date"].strftime("%Y-%m-%d")}
            # Include all numeric columns for charts
            for col in self.metrics_df.columns:
                if col != "date":
                    point[col] = float(row[col]) if pd.notna(row[col]) else 0
            data.append(point)
        return data

    @rx.var
    def alert_stats(self) -> dict[str, int]:
        """Calculate alert statistics."""
        stats = {
            "total": len(self.alerts),
            "active": sum(1 for a in self.alerts if a["status"] == "ACTIVE"),
            "critical": sum(1 for a in self.alerts if a["severity"] == "CRITICAL"),
            "high": sum(1 for a in self.alerts if a["severity"] == "HIGH"),
        }
        return stats

    @rx.var
    def region_stats(self) -> dict[str, int]:
        """Calculate region statistics."""
        return {
            "builtin": len([r for r in self.regions if r.get("type") == "builtin"]),
            "custom": len(self.custom_regions),
            "total": len(self.regions) + len(self.custom_regions),
        }

    def on_load(self):
        """Load initial data when app starts."""
        self.load_regions()
        self.load_alerts()
        self.load_custom_regions()
        self.load_metrics_data()

    def load_regions(self):
        """Load available regions from API or mock data."""
        try:
            response = requests.get(f"{API_BASE_URL}/v1/regions", timeout=5)
            if response.status_code == HTTP_OK:
                self.regions = response.json()
                return
        except Exception:
            pass

        # Fallback to mock data
        self.regions = [
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
        ]

    def load_metrics_data(self):
        """Load metrics data for selected region and date range."""
        params = {
            "region_id": self.selected_region_id,
            "from_date": self.start_date,
            "to_date": self.end_date,
        }

        try:
            response = requests.get(f"{API_BASE_URL}/v1/metrics", params=params, timeout=5)
            if response.status_code == HTTP_OK:
                self.metrics_data = response.json()
                self.process_metrics()
                return
        except Exception:
            pass

        # Fallback to mock data
        self.load_mock_metrics()

    def load_mock_metrics(self):
        """Load mock metrics from file."""
        data_path = "unknown"
        try:
            # Navigate to data directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(
                current_dir,
                "..",
                "..",
                "..",
                "..",
                "data",
                "01_raw",
                "data_samples",
                "metrics_mock.json",
            )
            with open(data_path) as f:
                self.metrics_data = json.load(f)
            self.process_metrics()
        except Exception:
            # Failed to load mock metrics, use empty data
            self.metrics_data = {"metrics": []}
            self.metrics_df = pd.DataFrame()

    def process_metrics(self):
        """Process loaded metrics data."""
        if "metrics" in self.metrics_data:
            self.metrics_df = pd.DataFrame(self.metrics_data["metrics"])

            if not self.metrics_df.empty:
                self.metrics_df["date"] = pd.to_datetime(self.metrics_df["date"])

                # Calculate summary metrics
                self.avg_lst = float(self.metrics_df["lst_mean_c"].mean())
                self.heatwave_days = int(self.metrics_df["heatwave_flag"].sum())

                latest_day = self.metrics_df.iloc[-1]
                self.today_cdd = float(latest_day.get("cdd", 0))
                self.today_hdd = float(latest_day.get("hdd", 0))
                self.anomaly_zscore = float(latest_day.get("anomaly_zscore", 0))

                # Get available variables
                self.available_variables = [col for col in self.metrics_df.columns if col != "date"]

    def set_region(self, region_name: str):
        """Change selected region."""
        self.selected_region_name = region_name
        for region in self.regions:
            if region["name"] == region_name:
                self.selected_region_id = region["id"]
                break
        self.load_metrics_data()

    def set_start_date(self, new_date: str):
        """Update start date."""
        self.start_date = new_date
        self.load_metrics_data()

    def set_end_date(self, new_date: str):
        """Update end date."""
        self.end_date = new_date
        self.load_metrics_data()

    def set_chart_type(self, chart_type: str):
        """Change chart type."""
        self.chart_type = chart_type.lower()

    def toggle_variable(self, variable: str):
        """Toggle variable selection for chart."""
        if variable in self.selected_variables:
            self.selected_variables.remove(variable)
        else:
            self.selected_variables.append(variable)

    # Alert management methods
    def set_alert_name(self, value: str):
        """Set alert name."""
        self.alert_name = value

    def set_alert_metric(self, value: str):
        """Set alert metric."""
        self.alert_metric = value

    def set_alert_condition(self, value: str):
        """Set alert condition."""
        self.alert_condition = value

    def set_alert_threshold(self, value: str):
        """Set alert threshold."""
        self.alert_threshold = float(value) if value else 0.0

    def set_alert_duration(self, value: str):
        """Set alert duration."""
        self.alert_duration = int(value) if value else 1

    def set_alert_severity(self, value: str):
        """Set alert severity."""
        self.alert_severity = value

    def set_alert_channel(self, value: str):
        """Set alert channel."""
        self.alert_channel = value

    def set_alert_recipients(self, value: str):
        """Set alert recipients."""
        self.alert_recipients = value

    def set_alert_start_date(self, new_date: str):
        """Update alert start date."""
        self.alert_start_date = new_date

    def set_alert_end_date(self, new_date: str):
        """Update alert end date."""
        self.alert_end_date = new_date

    def load_alerts(self):
        """Load existing alerts."""
        self.alerts = [
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

    def create_alert(self):
        """Create a new alert."""
        rule = f"{self.alert_metric} {self.alert_condition} {self.alert_threshold} for {self.alert_duration} day(s)"
        new_alert = {
            "id": f"alert-{len(self.alerts) + 1:03d}",
            "name": self.alert_name,
            "region_id": self.selected_region_id,
            "rule": rule,
            "channel": self.alert_channel.lower(),
            "recipients": self.alert_recipients,
            "status": "ACTIVE",
            "severity": self.alert_severity,
        }
        self.alerts.append(new_alert)
        # Reset form
        self.alert_name = ""
        self.alert_recipients = ""

    # Region management methods
    def load_custom_regions(self):
        """Load custom regions."""
        self.custom_regions = [
            {
                "id": "CUSTOM001",
                "name": "Downtown Manhattan",
                "type": "custom",
                "bbox": [-74.0151, 40.7001, -73.9696, 40.7310],
                "created": "2025-10-15",
            }
        ]

    def set_new_region_name(self, value: str):
        """Set new region name."""
        self.new_region_name = value

    def upload_region(self):
        """Upload a new region."""
        if self.new_region_name:
            new_region = {
                "id": f"CUSTOM{len(self.custom_regions) + 1:03d}",
                "name": self.new_region_name,
                "type": "custom",
                "bbox": [-74.0, 40.7, -73.9, 40.8],
                "created": date.today().strftime("%Y-%m-%d"),
            }
            self.custom_regions.append(new_region)
            self.new_region_name = ""


def metric_card(title: str, value, subtitle=None, color_scheme: str = "blue") -> rx.Component:
    """Create a metric card component with hover effects."""
    # PyCharm-inspired color mapping
    color_map = {
        "red": "#CC7832",
        "orange": "#FFC66D",
        "blue": "#6897BB",
        "purple": "#9876AA",
        "green": "#6A8759",
        "cyan": "#287BDE",
    }
    accent_color = color_map.get(color_scheme, "#6897BB")

    return rx.box(
        rx.vstack(
            rx.text(
                title,
                size="2",
                weight="medium",
                color="#A9B7C6",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.heading(
                value,
                size="6",
                color=accent_color,
                font_family="'Inter', 'Segoe UI', sans-serif",
                font_weight="600",
            ),
            (
                rx.text(
                    subtitle,
                    size="1",
                    color="#808080",
                    font_family="'Inter', 'Segoe UI', sans-serif",
                )
                if subtitle
                else rx.box()
            ),
            spacing="2",
        ),
        padding="5",
        border_radius="6px",
        border="1px solid #3C3F41",
        background="#2B2B2B",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.3)",
        _hover={
            "box_shadow": "0 4px 6px rgba(0, 0, 0, 0.4)",
            "border_color": accent_color,
            "transform": "translateY(-2px)",
            "transition": "all 0.2s ease-in-out",
        },
        transition="all 0.2s ease-in-out",
    )


def index_page() -> rx.Component:
    """Main dashboard page."""
    return rx.box(
        rx.vstack(
            # Page header without duplicate title
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Climate Risk Intelligence Dashboard",
                        size="7",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                        font_weight="600",
                    ),
                    rx.hstack(
                        rx.text(
                            f"Region: {State.selected_region_name} | ID: {State.selected_region_id}",
                            size="3",
                            color="#A9B7C6",
                            font_family="'Inter', 'Segoe UI', sans-serif",
                        ),
                        rx.badge(
                            rx.cond(
                                State.chart_data.length() > 0,
                                f"✓ {State.chart_data.length()} data points loaded",
                                "⚠ No data loaded",
                            ),
                            color_scheme=rx.cond(State.chart_data.length() > 0, "green", "orange"),
                            size="2",
                        ),
                        spacing="4",
                        align_items="center",
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                background="#2B2B2B",
                margin_bottom="6",
                border="1px solid #3C3F41",
            ),
            # Sidebar controls
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Select Region",
                        weight="bold",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.select(
                        State.region_names,
                        value=State.selected_region_name,
                        on_change=State.set_region,
                        size="3",
                    ),
                    rx.divider(margin_top="4", margin_bottom="4", border_color="#3C3F41"),
                    rx.text(
                        "Date Range",
                        weight="bold",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.text("From:", size="2", color="#A9B7C6"),
                    rx.input(
                        type="date",
                        value=State.start_date,
                        on_change=State.set_start_date,
                        size="2",
                    ),
                    rx.text("To:", size="2", color="#A9B7C6", margin_top="3"),
                    rx.input(
                        type="date",
                        value=State.end_date,
                        on_change=State.set_end_date,
                        size="2",
                    ),
                    width="300px",
                    padding="6",
                    border_radius="6px",
                    background="#2B2B2B",
                    border="1px solid #3C3F41",
                    spacing="3",
                ),
                # Main content
                rx.vstack(
                    # KPI Cards
                    rx.heading(
                        "Risk Indicators",
                        size="6",
                        margin_bottom="4",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.grid(
                        metric_card(
                            "Surface Temperature",
                            f"{State.avg_lst:.1f}°C",
                            f"Variance: {State.avg_lst - 20:.1f}°C",
                            "red",
                        ),
                        metric_card(
                            "Heatwave Exposure",
                            f"{State.heatwave_days} Days",
                            f"YTD Delta: {State.heatwave_days - 3}",
                            "orange",
                        ),
                        metric_card(
                            "Energy Demand",
                            f"CDD: {State.today_cdd:.1f} | HDD: {State.today_hdd:.1f}",
                            "Cooling/Heating Degree Days",
                            "blue",
                        ),
                        metric_card(
                            "Anomaly Index",
                            f"{State.anomaly_zscore:.2f}σ",
                            "Status: NORMAL/ALERT/CRITICAL",
                            "purple",
                        ),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    # Chart section
                    rx.heading(
                        "Historical Trend Analysis",
                        size="6",
                        margin_top="6",
                        margin_bottom="4",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text(
                                    "Chart Type:",
                                    weight="bold",
                                    size="3",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.select(
                                    ["Line", "Bar", "Area"],
                                    value=State.chart_type.capitalize(),
                                    on_change=State.set_chart_type,
                                    size="2",
                                ),
                                justify="start",
                                spacing="3",
                            ),
                            # Main temperature chart
                            rx.cond(
                                State.chart_data.length() > 0,
                                rx.recharts.line_chart(
                                    rx.recharts.line(
                                        data_key="lst_mean_c",
                                        stroke="#EF4444",
                                        stroke_width=2,
                                        name="Temperature (°C)",
                                    ),
                                    rx.recharts.x_axis(
                                        data_key="date", angle=-45, text_anchor="end", height=80
                                    ),
                                    rx.recharts.y_axis(
                                        label={
                                            "value": "Temperature (°C)",
                                            "angle": -90,
                                            "position": "insideLeft",
                                        }
                                    ),
                                    rx.recharts.cartesian_grid(stroke_dasharray="3 3", opacity=0.3),
                                    rx.recharts.legend(),
                                    rx.recharts.tooltip(),
                                    data=State.chart_data,
                                    width="100%",
                                    height=300,
                                ),
                                rx.center(
                                    rx.vstack(
                                        rx.text(
                                            "📊 No data available",
                                            size="4",
                                            weight="bold",
                                            color="#A9B7C6",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        rx.text(
                                            "Select a date range and region to view temperature data",
                                            size="2",
                                            color="#808080",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        spacing="3",
                                    ),
                                    height="300px",
                                ),
                            ),
                            spacing="4",
                        ),
                        padding="6",
                        border_radius="6px",
                        background="#2B2B2B",
                        border="1px solid #3C3F41",
                        box_shadow="md",
                        width="100%",
                    ),
                    # Combined metrics chart
                    rx.heading(
                        "Multi-Metric Comparison",
                        size="6",
                        margin_top="6",
                        margin_bottom="4",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "Comparing Temperature, Z-Score, and UHI Index",
                                size="2",
                                color="#A9B7C6",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                                margin_bottom="3",
                            ),
                            rx.cond(
                                State.chart_data.length() > 0,
                                rx.recharts.line_chart(
                                    rx.recharts.line(
                                        data_key="lst_mean_c",
                                        stroke="#EF4444",
                                        stroke_width=2,
                                        name="Temp (°C)",
                                    ),
                                    rx.recharts.line(
                                        data_key="anomaly_zscore",
                                        stroke="#8B5CF6",
                                        stroke_width=2,
                                        name="Z-Score",
                                    ),
                                    rx.recharts.line(
                                        data_key="uhi_index",
                                        stroke="#10B981",
                                        stroke_width=2,
                                        name="UHI Index",
                                    ),
                                    rx.recharts.x_axis(
                                        data_key="date", angle=-45, text_anchor="end", height=80
                                    ),
                                    rx.recharts.y_axis(),
                                    rx.recharts.cartesian_grid(stroke_dasharray="3 3", opacity=0.3),
                                    rx.recharts.legend(),
                                    rx.recharts.tooltip(),
                                    data=State.chart_data,
                                    width="100%",
                                    height=300,
                                ),
                                rx.center(
                                    rx.vstack(
                                        rx.text(
                                            "📊 No data available",
                                            size="4",
                                            weight="bold",
                                            color="#A9B7C6",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        rx.text(
                                            "Adjust date range to view multi-metric comparison",
                                            size="2",
                                            color="#808080",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        spacing="3",
                                    ),
                                    height="300px",
                                ),
                            ),
                            spacing="4",
                        ),
                        padding="6",
                        border_radius="6px",
                        background="#2B2B2B",
                        border="1px solid #3C3F41",
                        width="100%",
                        margin_bottom="6",
                    ),
                    # Secondary charts grid
                    rx.heading(
                        "Detailed Metrics",
                        size="6",
                        margin_top="6",
                        margin_bottom="4",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.grid(
                        # Anomaly Z-Score chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Anomaly Z-Score",
                                    weight="bold",
                                    size="3",
                                    margin_bottom="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.cond(
                                    State.chart_data.length() > 0,
                                    rx.recharts.area_chart(
                                        rx.recharts.area(
                                            data_key="anomaly_zscore",
                                            stroke="#8B5CF6",
                                            fill="#8B5CF6",
                                            fill_opacity=0.6,
                                            name="Z-Score",
                                        ),
                                        rx.recharts.x_axis(
                                            data_key="date", angle=-45, text_anchor="end", height=60
                                        ),
                                        rx.recharts.y_axis(),
                                        rx.recharts.cartesian_grid(
                                            stroke_dasharray="3 3", opacity=0.3
                                        ),
                                        rx.recharts.tooltip(),
                                        rx.recharts.legend(),
                                        data=State.chart_data,
                                        width="100%",
                                        height=200,
                                    ),
                                    rx.center(
                                        rx.text(
                                            "📊 No data",
                                            color="#808080",
                                            size="2",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        height="200px",
                                    ),
                                ),
                                spacing="3",
                            ),
                            padding="5",
                            border_radius="6px",
                            background="#2B2B2B",
                            border="1px solid #3C3F41",
                        ),
                        # CDD chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Cooling Degree Days",
                                    weight="bold",
                                    size="3",
                                    margin_bottom="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.cond(
                                    State.chart_data.length() > 0,
                                    rx.recharts.bar_chart(
                                        rx.recharts.bar(
                                            data_key="cdd",
                                            fill="#3B82F6",
                                            name="CDD",
                                        ),
                                        rx.recharts.x_axis(
                                            data_key="date", angle=-45, text_anchor="end", height=60
                                        ),
                                        rx.recharts.y_axis(),
                                        rx.recharts.cartesian_grid(
                                            stroke_dasharray="3 3", opacity=0.3
                                        ),
                                        rx.recharts.tooltip(),
                                        rx.recharts.legend(),
                                        data=State.chart_data,
                                        width="100%",
                                        height=200,
                                    ),
                                    rx.center(
                                        rx.text(
                                            "📊 No data",
                                            color="#808080",
                                            size="2",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        height="200px",
                                    ),
                                ),
                                spacing="3",
                            ),
                            padding="5",
                            border_radius="6px",
                            background="#2B2B2B",
                            border="1px solid #3C3F41",
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                    ),
                    # Third row of charts - Additional metrics
                    rx.grid(
                        # Heating Degree Days chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Heating Degree Days",
                                    weight="bold",
                                    size="3",
                                    margin_bottom="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.cond(
                                    State.chart_data.length() > 0,
                                    rx.recharts.bar_chart(
                                        rx.recharts.bar(
                                            data_key="hdd",
                                            fill="#F59E0B",
                                            name="HDD",
                                        ),
                                        rx.recharts.x_axis(
                                            data_key="date", angle=-45, text_anchor="end", height=60
                                        ),
                                        rx.recharts.y_axis(),
                                        rx.recharts.cartesian_grid(
                                            stroke_dasharray="3 3", opacity=0.3
                                        ),
                                        rx.recharts.tooltip(),
                                        rx.recharts.legend(),
                                        data=State.chart_data,
                                        width="100%",
                                        height=200,
                                    ),
                                    rx.center(
                                        rx.text(
                                            "📊 No data",
                                            color="#808080",
                                            size="2",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        height="200px",
                                    ),
                                ),
                                spacing="3",
                            ),
                            padding="5",
                            border_radius="6px",
                            background="#2B2B2B",
                            border="1px solid #3C3F41",
                        ),
                        # Heatwave Flag chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Heatwave Events",
                                    weight="bold",
                                    size="3",
                                    margin_bottom="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.cond(
                                    State.chart_data.length() > 0,
                                    rx.recharts.bar_chart(
                                        rx.recharts.bar(
                                            data_key="heatwave_flag",
                                            fill="#EF4444",
                                            name="Heatwave",
                                        ),
                                        rx.recharts.x_axis(
                                            data_key="date", angle=-45, text_anchor="end", height=60
                                        ),
                                        rx.recharts.y_axis(),
                                        rx.recharts.cartesian_grid(
                                            stroke_dasharray="3 3", opacity=0.3
                                        ),
                                        rx.recharts.tooltip(),
                                        rx.recharts.legend(),
                                        data=State.chart_data,
                                        width="100%",
                                        height=200,
                                    ),
                                    rx.center(
                                        rx.text(
                                            "📊 No data",
                                            color="#808080",
                                            size="2",
                                            font_family="'Inter', 'Segoe UI', sans-serif",
                                        ),
                                        height="200px",
                                    ),
                                ),
                                spacing="3",
                            ),
                            padding="5",
                            border_radius="6px",
                            background="#2B2B2B",
                            border="1px solid #3C3F41",
                        ),
                        columns="2",
                        spacing="4",
                        width="100%",
                        margin_top="4",
                    ),
                    width="100%",
                ),
                spacing="4",
                width="100%",
                align_items="start",
            ),
            # Footer
            rx.divider(margin_top="8", border_color="#00D9FF", opacity="0.3"),
            rx.center(
                rx.hstack(
                    rx.text("⚡", size="2", color="#00D9FF"),
                    rx.text(
                        "RAYDEN RULES™",
                        size="2",
                        weight="bold",
                        color="#00D9FF",
                        font_family="'Rajdhani', sans-serif",
                        letter_spacing="0.1em",
                    ),
                    rx.text("|", size="2", color="#666"),
                    rx.text(
                        "Climate Risk Intelligence Platform",
                        size="2",
                        color="#999",
                        font_family="'Rajdhani', sans-serif",
                    ),
                    rx.text("|", size="2", color="#666"),
                    rx.text(
                        "© 2025",
                        size="2",
                        color="#666",
                        font_family="'Rajdhani', sans-serif",
                    ),
                    rx.text("⚡", size="2", color="#00D9FF"),
                    spacing="2",
                    align_items="center",
                ),
                padding_y="4",
            ),
            spacing="5",
            padding="8",
            max_width="1400px",
            margin="0 auto",
        ),
        width="100%",
        background="#1E1E1E",
        min_height="100vh",
    )


def alerts_page() -> rx.Component:
    """Alerts management page."""
    return rx.box(
        rx.vstack(
            # Header
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Risk Alert Management",
                        size="7",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                        font_weight="600",
                    ),
                    rx.text(
                        "Configure threshold-based notifications for climate risk factors",
                        size="3",
                        color="#A9B7C6",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                background="#2B2B2B",
                border="1px solid #3C3F41",
                margin_bottom="6",
            ),
            # Date filters for alerts
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Alert Filters",
                        size="5",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                        margin_bottom="3",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "From Date:",
                                size="2",
                                color="#A9B7C6",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                            ),
                            rx.input(
                                type="date",
                                value=State.alert_start_date,
                                on_change=State.set_alert_start_date,
                                size="2",
                            ),
                            align_items="start",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text(
                                "To Date:",
                                size="2",
                                color="#A9B7C6",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                            ),
                            rx.input(
                                type="date",
                                value=State.alert_end_date,
                                on_change=State.set_alert_end_date,
                                size="2",
                            ),
                            align_items="start",
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.text(
                                "Date Range:",
                                size="2",
                                weight="medium",
                                color="#D4D4D4",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                            ),
                            rx.badge(
                                f"{State.alert_start_date} to {State.alert_end_date}",
                                color_scheme="cyan",
                                size="2",
                            ),
                            align_items="start",
                            spacing="1",
                        ),
                        spacing="5",
                        align_items="end",
                        width="100%",
                    ),
                    spacing="3",
                ),
                padding="5",
                border_radius="6px",
                background="#2B2B2B",
                border="1px solid #3C3F41",
                margin_bottom="6",
            ),
            # Alert statistics
            rx.heading(
                "Alert Statistics",
                size="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.grid(
                metric_card(
                    "Total Alerts", State.alert_stats["total"], "All configured alerts", "blue"
                ),
                metric_card("Active", State.alert_stats["active"], "Currently monitoring", "green"),
                metric_card("Critical", State.alert_stats["critical"], "High priority", "red"),
                metric_card(
                    "High Severity", State.alert_stats["high"], "Medium priority", "orange"
                ),
                columns="4",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            # Two-column layout: Charts and Instructions
            rx.grid(
                # Left column - Alert trend chart
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "Alert Frequency Trend",
                            size="6",
                            margin_bottom="3",
                            color="#D4D4D4",
                            font_family="'Inter', 'Segoe UI', sans-serif",
                        ),
                        rx.text(
                            "Alert triggers over the past 30 days",
                            size="2",
                            color="#A9B7C6",
                            font_family="'Inter', 'Segoe UI', sans-serif",
                            margin_bottom="3",
                        ),
                        rx.recharts.bar_chart(
                            rx.recharts.bar(
                                data_key="count",
                                fill="#EF4444",
                                name="Alerts Triggered",
                            ),
                            rx.recharts.x_axis(
                                data_key="date", angle=-45, text_anchor="end", height=80
                            ),
                            rx.recharts.y_axis(
                                label={"value": "Count", "angle": -90, "position": "insideLeft"}
                            ),
                            rx.recharts.cartesian_grid(stroke_dasharray="3 3", opacity=0.3),
                            rx.recharts.legend(),
                            rx.recharts.tooltip(),
                            data=[
                                {"date": "Oct 1", "count": 3},
                                {"date": "Oct 5", "count": 5},
                                {"date": "Oct 10", "count": 2},
                                {"date": "Oct 15", "count": 7},
                                {"date": "Oct 20", "count": 4},
                                {"date": "Oct 25", "count": 6},
                                {"date": "Oct 30", "count": 3},
                            ],
                            width="100%",
                            height=350,
                        ),
                        spacing="3",
                    ),
                    padding="6",
                    border_radius="6px",
                    background="#2B2B2B",
                    border="1px solid #3C3F41",
                ),
                # Right column - How to Use Instructions
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "🔔 How to Set Up Alerts",
                            size="6",
                            margin_bottom="3",
                            color="#D4D4D4",
                            font_family="'Inter', 'Segoe UI', sans-serif",
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.text(
                                    "1", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Name Your Alert",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Choose a descriptive name that clearly identifies the risk you're monitoring.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.hstack(
                                rx.text(
                                    "2", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Select Metric & Threshold",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Pick a climate metric (temperature, z-score, UHI, etc.) and set the threshold value that triggers an alert.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.hstack(
                                rx.text(
                                    "3", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Set Duration & Severity",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Specify how many consecutive days the condition must persist, and assign a severity level (LOW, MEDIUM, HIGH, CRITICAL).",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.hstack(
                                rx.text(
                                    "4", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Configure Notifications",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Choose your notification channel (Email, Slack, Webhook) and enter recipient details.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        "💡 Pro Tips",
                                        weight="bold",
                                        size="3",
                                        color="#FFC66D",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "• Use anomaly_zscore for early warning signs\n• Set duration > 1 to avoid false positives\n• CRITICAL alerts for immediate action items\n• Test with low thresholds before deploying",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                        white_space="pre-wrap",
                                    ),
                                    align_items="start",
                                    spacing="2",
                                ),
                                padding="4",
                                border_radius="6px",
                                background="rgba(255, 198, 109, 0.1)",
                                border="1px solid rgba(255, 198, 109, 0.3)",
                            ),
                            spacing="4",
                        ),
                        spacing="4",
                    ),
                    padding="6",
                    border_radius="6px",
                    background="#2B2B2B",
                    border="1px solid #3C3F41",
                ),
                columns="2",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            # Alert severity distribution chart
            rx.heading(
                "Alert Distribution by Severity",
                size="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Breakdown of alerts by severity level",
                        size="2",
                        color="#A9B7C6",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                        margin_bottom="3",
                    ),
                    rx.recharts.pie_chart(
                        rx.recharts.pie(
                            data=[
                                {"name": "Critical", "value": 2, "fill": "#EF4444"},
                                {"name": "High", "value": 3, "fill": "#F59E0B"},
                                {"name": "Medium", "value": 5, "fill": "#FFC66D"},
                                {"name": "Low", "value": 4, "fill": "#10B981"},
                            ],
                            data_key="value",
                            name_key="name",
                            cx="50%",
                            cy="50%",
                            label=True,
                        ),
                        rx.recharts.legend(),
                        width="100%",
                        height=300,
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                background="#2B2B2B",
                border="1px solid #3C3F41",
                margin_bottom="6",
            ),
            # Existing alerts
            rx.heading(
                "Configured Alerts",
                size="6",
                margin_top="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.foreach(
                    State.alerts,
                    lambda alert: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    alert["name"],
                                    weight="bold",
                                    size="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"Region: {alert['region_id']}",
                                    size="2",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"Rule: {alert['rule']}",
                                    size="2",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"Channel: {alert['channel']} → {alert['recipients']}",
                                    size="2",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                spacing="2",
                                align_items="start",
                            ),
                            rx.hstack(
                                rx.badge(
                                    alert["severity"],
                                    color_scheme=rx.cond(
                                        alert["severity"] == "CRITICAL",
                                        "red",
                                        rx.cond(alert["severity"] == "HIGH", "orange", "yellow"),
                                    ),
                                    size="2",
                                ),
                                rx.badge(alert["status"], color_scheme="green", size="2"),
                                spacing="2",
                            ),
                            justify="between",
                            width="100%",
                        ),
                        padding="5",
                        border_radius="6px",
                        border="1px solid #3C3F41",
                        background="#2B2B2B",
                        margin_bottom="3",
                        _hover={
                            "box_shadow": "md",
                            "border_color": rx.color("blue", 7),
                            "transform": "translateX(4px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                ),
            ),
            # Create new alert
            rx.heading(
                "Create New Risk Alert",
                size="6",
                margin_top="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Alert Name",
                        weight="bold",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.input(
                        placeholder="Enter alert name",
                        value=State.alert_name,
                        on_change=State.set_alert_name,
                        size="3",
                    ),
                    rx.text(
                        "Select Metric",
                        weight="bold",
                        margin_top="4",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.select(
                        ["lst_mean_c", "heatwave_flag", "uhi_index", "anomaly_zscore", "cdd"],
                        value=State.alert_metric,
                        on_change=State.set_alert_metric,
                        size="3",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text(
                                "Condition",
                                weight="bold",
                                size="3",
                                color="#D4D4D4",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                            ),
                            rx.select(
                                [">=", ">", "=", "<", "<="],
                                value=State.alert_condition,
                                on_change=State.set_alert_condition,
                                size="2",
                            ),
                            align_items="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Threshold",
                                weight="bold",
                                size="3",
                                color="#D4D4D4",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                            ),
                            rx.input(
                                type="number",
                                value=State.alert_threshold,
                                on_change=State.set_alert_threshold,
                                size="2",
                            ),
                            align_items="start",
                        ),
                        rx.vstack(
                            rx.text(
                                "Duration (days)",
                                weight="bold",
                                size="3",
                                color="#D4D4D4",
                                font_family="'Inter', 'Segoe UI', sans-serif",
                            ),
                            rx.input(
                                type="number",
                                value=State.alert_duration,
                                on_change=State.set_alert_duration,
                                size="2",
                            ),
                            align_items="start",
                        ),
                        spacing="4",
                        width="100%",
                        margin_top="4",
                    ),
                    rx.text(
                        "Risk Level",
                        weight="bold",
                        margin_top="4",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.select(
                        ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        value=State.alert_severity,
                        on_change=State.set_alert_severity,
                        size="3",
                    ),
                    rx.text(
                        "Notification Channel",
                        weight="bold",
                        margin_top="4",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.select(
                        ["EMAIL", "SLACK", "WEBHOOK"],
                        value=State.alert_channel,
                        on_change=State.set_alert_channel,
                        size="3",
                    ),
                    rx.text(
                        "Recipients",
                        weight="bold",
                        margin_top="4",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.input(
                        placeholder="Enter recipients",
                        value=State.alert_recipients,
                        on_change=State.set_alert_recipients,
                        size="3",
                    ),
                    rx.button(
                        "Create Alert",
                        on_click=State.create_alert,
                        margin_top="5",
                        size="3",
                        color_scheme="blue",
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                border="1px solid #3C3F41",
                background="#2B2B2B",
            ),
            # Footer
            rx.divider(margin_top="8", border_color="#00D9FF", opacity="0.3"),
            rx.center(
                rx.hstack(
                    rx.text("⚡", size="2", color="#00D9FF"),
                    rx.text(
                        "RAYDEN RULES™",
                        size="2",
                        weight="bold",
                        color="#00D9FF",
                        font_family="'Rajdhani', sans-serif",
                        letter_spacing="0.1em",
                    ),
                    rx.text("|", size="2", color="#666"),
                    rx.text(
                        "Climate Risk Intelligence Platform",
                        size="2",
                        color="#999",
                        font_family="'Rajdhani', sans-serif",
                    ),
                    rx.text("|", size="2", color="#666"),
                    rx.text(
                        "© 2025",
                        size="2",
                        color="#666",
                        font_family="'Rajdhani', sans-serif",
                    ),
                    rx.text("⚡", size="2", color="#00D9FF"),
                    spacing="2",
                    align_items="center",
                ),
                padding_y="4",
            ),
            spacing="5",
            padding="8",
            max_width="1400px",
            margin="0 auto",
        ),
        width="100%",
        background="#1E1E1E",
        min_height="100vh",
    )


def regions_page() -> rx.Component:
    """Geographic regions management page."""
    return rx.box(
        rx.vstack(
            # Header
            rx.box(
                rx.vstack(
                    rx.heading(
                        "Geographic Regions",
                        size="7",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                        font_weight="600",
                    ),
                    rx.text(
                        "Upload and manage custom geographic regions for climate risk analysis",
                        size="3",
                        color="#A9B7C6",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                background="#2B2B2B",
                border="1px solid #3C3F41",
                margin_bottom="6",
            ),
            # Region statistics
            rx.heading(
                "Region Statistics",
                size="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.grid(
                metric_card(
                    "Total Regions", State.region_stats["total"], "Built-in + Custom", "blue"
                ),
                metric_card(
                    "Built-in", State.region_stats["builtin"], "Pre-configured regions", "green"
                ),
                metric_card(
                    "Custom", State.region_stats["custom"], "User-defined regions", "purple"
                ),
                metric_card("Coverage", "4 Cities", "Major metropolitan areas", "cyan"),
                columns="4",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            # Two-column layout: Charts and Instructions
            rx.heading(
                "Region Analytics",
                size="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.grid(
                # Left column - Region types pie chart (larger)
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Region Types Distribution",
                            weight="bold",
                            size="4",
                            margin_bottom="3",
                            color="#D4D4D4",
                            font_family="'Inter', 'Segoe UI', sans-serif",
                        ),
                        rx.recharts.pie_chart(
                            rx.recharts.pie(
                                data=[
                                    {
                                        "name": "Built-in",
                                        "value": State.region_stats["builtin"],
                                        "fill": "#3B82F6",
                                    },
                                    {
                                        "name": "Custom",
                                        "value": State.region_stats["custom"],
                                        "fill": "#8B5CF6",
                                    },
                                ],
                                data_key="value",
                                name_key="name",
                                cx="50%",
                                cy="50%",
                                label=True,
                            ),
                            rx.recharts.legend(),
                            width="100%",
                            height=350,
                        ),
                        spacing="3",
                    ),
                    padding="6",
                    border_radius="6px",
                    background="#2B2B2B",
                    border="1px solid #3C3F41",
                ),
                # Right column - How to Upload Instructions
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "🗺️ How to Upload Custom Regions",
                            size="6",
                            margin_bottom="3",
                            color="#D4D4D4",
                            font_family="'Inter', 'Segoe UI', sans-serif",
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.text(
                                    "1", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Prepare GeoJSON File",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Create or export a GeoJSON file with your region boundaries. Ensure it includes valid coordinates and geometry.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.hstack(
                                rx.text(
                                    "2", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Name Your Region",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Enter a descriptive name for easy identification in dropdown menus and reports.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.hstack(
                                rx.text(
                                    "3", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Upload & Validate",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Click 'Choose File' to select your GeoJSON, then 'Upload and Save Region'. The system will validate coordinates and create a bounding box.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.hstack(
                                rx.text(
                                    "4", size="5", weight="bold", color="#00D9FF", width="30px"
                                ),
                                rx.vstack(
                                    rx.text(
                                        "Start Analyzing",
                                        weight="bold",
                                        size="3",
                                        color="#D4D4D4",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "Your custom region will appear in the Dashboard's region selector and can be used for all climate risk analyses.",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    align_items="start",
                                    spacing="1",
                                ),
                                align_items="start",
                                spacing="3",
                                width="100%",
                            ),
                            rx.divider(border_color="#3C3F41"),
                            rx.box(
                                rx.vstack(
                                    rx.text(
                                        "📍 GeoJSON Tips",
                                        weight="bold",
                                        size="3",
                                        color="#51CF66",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                    ),
                                    rx.text(
                                        "• Use WGS84 (EPSG:4326) coordinate system\n• Keep file size < 5MB for best performance\n• Polygon or MultiPolygon geometries work best\n• Export from QGIS, ArcGIS, or geojson.io",
                                        size="2",
                                        color="#A9B7C6",
                                        font_family="'Inter', 'Segoe UI', sans-serif",
                                        white_space="pre-wrap",
                                    ),
                                    align_items="start",
                                    spacing="2",
                                ),
                                padding="4",
                                border_radius="6px",
                                background="rgba(81, 207, 102, 0.1)",
                                border="1px solid rgba(81, 207, 102, 0.3)",
                            ),
                            spacing="4",
                        ),
                        spacing="4",
                    ),
                    padding="6",
                    border_radius="6px",
                    background="#2B2B2B",
                    border="1px solid #3C3F41",
                ),
                columns="2",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            # Data queries by region - Full width chart
            rx.heading(
                "Region Usage Metrics",
                size="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Number of data queries per region (last 30 days)",
                        weight="medium",
                        size="3",
                        margin_bottom="3",
                        color="#A9B7C6",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="queries",
                            fill="#10B981",
                            name="Data Queries",
                        ),
                        rx.recharts.x_axis(
                            data_key="name",
                            label={"value": "Region", "position": "insideBottom", "offset": -5},
                        ),
                        rx.recharts.y_axis(
                            label={"value": "Query Count", "angle": -90, "position": "insideLeft"}
                        ),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3", opacity=0.3),
                        rx.recharts.tooltip(),
                        rx.recharts.legend(),
                        data=[
                            {"name": "New York City", "queries": 245},
                            {"name": "Los Angeles", "queries": 189},
                            {"name": "Chicago", "queries": 156},
                            {"name": "Miami", "queries": 134},
                            {"name": "Downtown Manhattan", "queries": 87},
                        ],
                        width="100%",
                        height=350,
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                background="#2B2B2B",
                border="1px solid #3C3F41",
                margin_bottom="6",
            ),
            # Built-in regions
            rx.heading(
                "Built-in Regions",
                size="6",
                margin_top="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.foreach(
                    State.regions,
                    lambda region: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    region["name"],
                                    weight="bold",
                                    size="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"ID: {region['id']}",
                                    size="2",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"BBox: {region['bbox']}",
                                    size="2",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                spacing="2",
                                align_items="start",
                            ),
                            rx.badge("Built-in", color_scheme="green", size="2"),
                            justify="between",
                            width="100%",
                        ),
                        padding="5",
                        border_radius="6px",
                        border="1px solid #3C3F41",
                        background="#2B2B2B",
                        margin_bottom="3",
                        _hover={
                            "border_color": "#6A8759",
                            "transform": "translateX(4px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                ),
            ),
            # Custom regions
            rx.heading(
                "Custom Regions",
                size="6",
                margin_top="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.foreach(
                    State.custom_regions,
                    lambda region: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(
                                    region["name"],
                                    weight="bold",
                                    size="3",
                                    color="#D4D4D4",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"ID: {region['id']}",
                                    size="2",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                rx.text(
                                    f"Created: {region['created']}",
                                    size="2",
                                    color="#A9B7C6",
                                    font_family="'Inter', 'Segoe UI', sans-serif",
                                ),
                                spacing="2",
                                align_items="start",
                            ),
                            rx.badge("Custom", color_scheme="purple", size="2"),
                            justify="between",
                            width="100%",
                        ),
                        padding="5",
                        border_radius="6px",
                        border="1px solid #3C3F41",
                        background="#2B2B2B",
                        margin_bottom="3",
                        _hover={
                            "border_color": "#9876AA",
                            "transform": "translateX(4px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                ),
            ),
            # Upload new region
            rx.heading(
                "Upload New Region",
                size="6",
                margin_top="6",
                margin_bottom="4",
                color="#D4D4D4",
                font_family="'Inter', 'Segoe UI', sans-serif",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Region Name",
                        weight="bold",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.input(
                        placeholder="Enter region name",
                        value=State.new_region_name,
                        on_change=State.set_new_region_name,
                        size="3",
                    ),
                    rx.text(
                        "Upload GeoJSON",
                        weight="bold",
                        margin_top="4",
                        size="3",
                        color="#D4D4D4",
                        font_family="'Inter', 'Segoe UI', sans-serif",
                    ),
                    rx.upload(
                        rx.button("Choose File", size="2"),
                        accept={".geojson": []},
                    ),
                    rx.button(
                        "Upload and Save Region",
                        on_click=State.upload_region,
                        margin_top="5",
                        size="3",
                        color_scheme="green",
                    ),
                    spacing="3",
                ),
                padding="6",
                border_radius="6px",
                border="1px solid #3C3F41",
                background="#2B2B2B",
            ),
            # Footer
            rx.divider(margin_top="8", border_color="#00D9FF", opacity="0.3"),
            rx.center(
                rx.hstack(
                    rx.text("⚡", size="2", color="#00D9FF"),
                    rx.text(
                        "RAYDEN RULES™",
                        size="2",
                        weight="bold",
                        color="#00D9FF",
                        font_family="'Rajdhani', sans-serif",
                        letter_spacing="0.1em",
                    ),
                    rx.text("|", size="2", color="#666"),
                    rx.text(
                        "Climate Risk Intelligence Platform",
                        size="2",
                        color="#999",
                        font_family="'Rajdhani', sans-serif",
                    ),
                    rx.text("|", size="2", color="#666"),
                    rx.text(
                        "© 2025",
                        size="2",
                        color="#666",
                        font_family="'Rajdhani', sans-serif",
                    ),
                    rx.text("⚡", size="2", color="#00D9FF"),
                    spacing="2",
                    align_items="center",
                ),
                padding_y="4",
            ),
            spacing="5",
            padding="8",
            max_width="1400px",
            margin="0 auto",
        ),
        width="100%",
        background="#1E1E1E",
        min_height="100vh",
    )


def music_player() -> rx.Component:
    """Floating music player for background music - Death Stranding themed."""
    return rx.html(
        """
        <script>
            // Initialize persistent audio element and state
            if (!window.persistentAudio) {
                window.persistentAudio = new Audio('/dont_be_so_serious.mp3');
                window.persistentAudio.loop = true;
                window.persistentAudio.preload = 'auto';
                window.persistentAudio.volume = 0.7;
                console.log('🎵 Persistent audio initialized');
            }
        </script>

        <div id="music-player" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 16px;
            border-radius: 8px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #00D9FF;
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.4);
            width: 300px;
            z-index: 1000;
            transition: all 0.3s ease-in-out;
        "
        onmouseenter="this.style.boxShadow='0 6px 25px rgba(0, 217, 255, 0.6)'; this.style.transform='translateY(-2px)';"
        onmouseleave="this.style.boxShadow='0 4px 20px rgba(0, 217, 255, 0.4)'; this.style.transform='translateY(0)';"
        >
            <div style="display: flex; align-items: center; gap: 12px;">
                <span id="music-icon" style="
                    font-size: 24px;
                    color: #00D9FF;
                    text-shadow: 0 0 10px #00D9FF;
                ">♪</span>

                <div style="flex-grow: 1;">
                    <div style="
                        font-size: 11px;
                        font-weight: 600;
                        color: #D4D4D4;
                        font-family: 'Inter', sans-serif;
                    ">Don't Be So Serious</div>
                    <div style="
                        font-size: 10px;
                        color: #A9B7C6;
                        font-family: 'Inter', sans-serif;
                    ">Death Stranding OST</div>
                </div>

                <button
                    id="music-toggle-btn"
                    style="
                        background-color: rgba(0, 217, 255, 0.15);
                        color: #00D9FF;
                        border: 1px solid rgba(0, 217, 255, 0.3);
                        padding: 6px 12px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 16px;
                        transition: all 0.2s;
                    "
                    onmouseover="this.style.backgroundColor='rgba(0, 217, 255, 0.25)';"
                    onmouseout="this.style.backgroundColor='rgba(0, 217, 255, 0.15)';"
                    onclick="
                        // Initialize audio if not exists
                        if (!window.persistentAudio) {
                            window.persistentAudio = new Audio('/dont_be_so_serious.mp3');
                            window.persistentAudio.loop = true;
                            window.persistentAudio.preload = 'auto';
                            window.persistentAudio.volume = 0.7;
                            console.log('🎵 Audio initialized on click');
                        }

                        const audio = window.persistentAudio;
                        const btn = document.getElementById('music-toggle-btn');
                        const icon = document.getElementById('music-icon');

                        if (audio && audio.paused) {
                            audio.play().then(() => {
                                btn.innerHTML = '⏸';
                                icon.innerHTML = '♫';
                                icon.style.animation = 'pulse-music 1.5s ease-in-out infinite';
                                console.log('✓ Music playing');
                            }).catch(e => {
                                console.error('✗ Audio play failed:', e.message);
                                alert('Could not play audio: ' + e.message);
                            });
                        } else if (audio) {
                            audio.pause();
                            btn.innerHTML = '▶';
                            icon.innerHTML = '♪';
                            icon.style.animation = 'none';
                            console.log('⏸ Music paused');
                        }
                    "
                >▶</button>
            </div>

            <script>
                // Sync UI with current audio state on page load
                (function() {
                    setTimeout(() => {
                        const audio = window.persistentAudio;
                        const btn = document.getElementById('music-toggle-btn');
                        const icon = document.getElementById('music-icon');

                        if (audio && btn && icon && !audio.paused) {
                            btn.innerHTML = '⏸';
                            icon.innerHTML = '♫';
                            icon.style.animation = 'pulse-music 1.5s ease-in-out infinite';
                            console.log('🎵 Music player synced - playing');
                        } else if (!audio) {
                            console.log('🎵 Audio not initialized yet - will init on first click');
                        }
                    }, 100);
                })();
            </script>

            <style>
                @keyframes pulse-music {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.7; transform: scale(1.1); }
                }
            </style>
        </div>
        """
    )


def navbar() -> rx.Component:
    """Navigation bar with enhanced styling - Raiden/Thunder God themed."""
    return rx.box(
        rx.hstack(
            # Title with lightning theme
            rx.hstack(
                rx.text(
                    "⚡",
                    size="8",
                    color="#00D9FF",
                    style={
                        "text-shadow": "0 0 10px #00D9FF, 0 0 20px #00D9FF, 0 0 30px #00D9FF",
                        "animation": "pulse 2s ease-in-out infinite",
                    },
                ),
                rx.heading(
                    "RAYDEN",
                    size="8",
                    color="#FFFFFF",
                    font_family="'Rajdhani', 'Impact', 'Arial Black', sans-serif",
                    font_weight="900",
                    letter_spacing="0.1em",
                    style={
                        "text-shadow": "0 0 10px #00D9FF, 0 0 20px #4A90E2, 2px 2px 4px rgba(0,0,0,0.8)",
                        "text-transform": "uppercase",
                    },
                ),
                rx.heading(
                    "RULES",
                    size="8",
                    color="#00D9FF",
                    font_family="'Rajdhani', 'Impact', 'Arial Black', sans-serif",
                    font_weight="900",
                    letter_spacing="0.1em",
                    style={
                        "text-shadow": "0 0 10px #00D9FF, 0 0 20px #4A90E2, 2px 2px 4px rgba(0,0,0,0.8)",
                        "text-transform": "uppercase",
                    },
                ),
                rx.text(
                    "⚡",
                    size="8",
                    color="#00D9FF",
                    style={
                        "text-shadow": "0 0 10px #00D9FF, 0 0 20px #00D9FF, 0 0 30px #00D9FF",
                        "animation": "pulse 2s ease-in-out infinite",
                    },
                ),
                spacing="2",
                align_items="center",
            ),
            rx.spacer(),
            # Navigation links with enhanced hover effects
            rx.hstack(
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.text("📊", size="3"),
                            rx.text(
                                "Dashboard",
                                size="3",
                                weight="bold",
                                color="#E0E0E0",
                                font_family="'Rajdhani', 'Inter', sans-serif",
                                letter_spacing="0.05em",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        padding_x="5",
                        padding_y="2",
                        border_radius="6px",
                        border="2px solid transparent",
                        _hover={
                            "background": "linear-gradient(135deg, #1a1a2e 0%, #2a2a4e 100%)",
                            "border_color": "#00D9FF",
                            "transform": "translateY(-2px)",
                            "box_shadow": "0 4px 12px rgba(0, 217, 255, 0.4)",
                            "transition": "all 0.3s ease-in-out",
                        },
                        transition="all 0.3s ease-in-out",
                    ),
                    href="/",
                ),
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.text("⚠️", size="3"),
                            rx.text(
                                "Alerts",
                                size="3",
                                weight="bold",
                                color="#E0E0E0",
                                font_family="'Rajdhani', 'Inter', sans-serif",
                                letter_spacing="0.05em",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        padding_x="5",
                        padding_y="2",
                        border_radius="6px",
                        border="2px solid transparent",
                        _hover={
                            "background": "linear-gradient(135deg, #2e1a1a 0%, #4e2a2a 100%)",
                            "border_color": "#FF6B6B",
                            "transform": "translateY(-2px)",
                            "box_shadow": "0 4px 12px rgba(255, 107, 107, 0.4)",
                            "transition": "all 0.3s ease-in-out",
                        },
                        transition="all 0.3s ease-in-out",
                    ),
                    href="/alerts",
                ),
                rx.link(
                    rx.box(
                        rx.hstack(
                            rx.text("🗺️", size="3"),
                            rx.text(
                                "Regions",
                                size="3",
                                weight="bold",
                                color="#E0E0E0",
                                font_family="'Rajdhani', 'Inter', sans-serif",
                                letter_spacing="0.05em",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        padding_x="5",
                        padding_y="2",
                        border_radius="6px",
                        border="2px solid transparent",
                        _hover={
                            "background": "linear-gradient(135deg, #1a2e1a 0%, #2a4e2a 100%)",
                            "border_color": "#51CF66",
                            "transform": "translateY(-2px)",
                            "box_shadow": "0 4px 12px rgba(81, 207, 102, 0.4)",
                            "transition": "all 0.3s ease-in-out",
                        },
                        transition="all 0.3s ease-in-out",
                    ),
                    href="/regions",
                ),
                spacing="3",
            ),
            justify="between",
            width="100%",
            align_items="center",
        ),
        padding_x="8",
        padding_y="4",
        border_bottom="2px solid #00D9FF",
        background="linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        box_shadow="0 4px 20px rgba(0, 217, 255, 0.3), 0 0 40px rgba(0, 217, 255, 0.1)",
        width="100%",
        style={
            "backdrop_filter": "blur(10px)",
        },
    )


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap",
    ],
    style={
        "@keyframes pulse": {
            "0%, 100%": {
                "opacity": "1",
                "transform": "scale(1)",
            },
            "50%": {
                "opacity": "0.7",
                "transform": "scale(1.1)",
            },
        },
        "@keyframes lightning-flicker": {
            "0%, 100%": {
                "text-shadow": "0 0 10px #00D9FF, 0 0 20px #00D9FF, 0 0 30px #00D9FF",
            },
            "50%": {
                "text-shadow": "0 0 20px #00D9FF, 0 0 40px #4A90E2, 0 0 60px #00D9FF",
            },
        },
    },
)

# Add pages
app.add_page(
    lambda: rx.fragment(navbar(), index_page(), music_player()),
    route="/",
    title="⚡ Rayden Rules - Dashboard",
    on_load=State.on_load,
)

app.add_page(
    lambda: rx.fragment(navbar(), alerts_page(), music_player()),
    route="/alerts",
    title="⚡ Rayden Rules - Alerts",
)

app.add_page(
    lambda: rx.fragment(navbar(), regions_page(), music_player()),
    route="/regions",
    title="⚡ Rayden Rules - Regions",
)
