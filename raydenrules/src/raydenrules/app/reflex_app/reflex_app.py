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
API_BASE_URL = "http://localhost:8000"

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
    return rx.box(
        rx.vstack(
            rx.text(title, size="2", weight="medium", color=rx.color(color_scheme, 11)),
            rx.heading(value, size="6", color=rx.color(color_scheme, 12)),
            rx.text(subtitle, size="1", color="gray") if subtitle else rx.box(),
            spacing="1",
        ),
        padding="4",
        border_radius="lg",
        border="1px solid",
        border_color=rx.color("gray", 6),
        background=rx.color("gray", 1),
        box_shadow="sm",
        _hover={
            "box_shadow": "lg",
            "border_color": rx.color(color_scheme, 7),
            "transform": "translateY(-2px)",
            "transition": "all 0.2s ease-in-out",
        },
        transition="all 0.2s ease-in-out",
    )


def index_page() -> rx.Component:
    """Main dashboard page."""
    return rx.box(
        rx.vstack(
            # Header with gradient background
            rx.box(
                rx.vstack(
                    rx.heading(
                        "RAYDEN RULES - Climate Risk Intelligence",
                        size="8",
                        background_image="linear-gradient(90deg, #4F46E5 0%, #06B6D4 100%)",
                        background_clip="text",
                    ),
                    rx.hstack(
                        rx.text(
                            f"Region: {State.selected_region_name} | ID: {State.selected_region_id}",
                            size="3",
                            color="gray",
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
                        spacing="3",
                        align_items="center",
                    ),
                    spacing="2",
                ),
                padding="6",
                border_radius="lg",
                background=rx.color("gray", 2),
                margin_bottom="4",
            ),
            # Sidebar controls
            rx.hstack(
                rx.vstack(
                    rx.text("Select Region", weight="bold", size="3"),
                    rx.select(
                        State.region_names,
                        value=State.selected_region_name,
                        on_change=State.set_region,
                        size="3",
                    ),
                    rx.divider(margin_top="4", margin_bottom="4"),
                    rx.text("Date Range", weight="bold", size="3"),
                    rx.text("From:", size="2", color="gray"),
                    rx.input(
                        type="date",
                        value=State.start_date,
                        on_change=State.set_start_date,
                        size="2",
                    ),
                    rx.text("To:", size="2", color="gray", margin_top="2"),
                    rx.input(
                        type="date",
                        value=State.end_date,
                        on_change=State.set_end_date,
                        size="2",
                    ),
                    width="300px",
                    padding="5",
                    border_radius="lg",
                    background=rx.color("gray", 2),
                    box_shadow="md",
                    spacing="2",
                ),
                # Main content
                rx.vstack(
                    # KPI Cards
                    rx.heading("Risk Indicators", size="6", margin_bottom="3"),
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
                        "Historical Trend Analysis", size="6", margin_top="6", margin_bottom="3"
                    ),
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Chart Type:", weight="bold", size="3"),
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
                                            color="gray",
                                        ),
                                        rx.text(
                                            "Select a date range and region to view temperature data",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                    ),
                                    height="300px",
                                ),
                            ),
                            spacing="4",
                        ),
                        padding="6",
                        border_radius="lg",
                        background=rx.color("gray", 1),
                        border="1px solid",
                        border_color=rx.color("gray", 6),
                        box_shadow="md",
                        width="100%",
                    ),
                    # Combined metrics chart
                    rx.heading(
                        "Multi-Metric Comparison", size="6", margin_top="6", margin_bottom="3"
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "Comparing Temperature, Z-Score, and UHI Index",
                                size="2",
                                color="gray",
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
                                            color="gray",
                                        ),
                                        rx.text(
                                            "Adjust date range to view multi-metric comparison",
                                            size="2",
                                            color="gray",
                                        ),
                                        spacing="2",
                                    ),
                                    height="300px",
                                ),
                            ),
                            spacing="4",
                        ),
                        padding="6",
                        border_radius="lg",
                        background=rx.color("gray", 1),
                        border="1px solid",
                        border_color=rx.color("gray", 6),
                        box_shadow="md",
                        width="100%",
                        margin_bottom="6",
                    ),
                    # Secondary charts grid
                    rx.heading("Detailed Metrics", size="6", margin_top="6", margin_bottom="3"),
                    rx.grid(
                        # Anomaly Z-Score chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Anomaly Z-Score", weight="bold", size="3", margin_bottom="2"
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
                                        rx.text("📊 No data", color="gray", size="2"),
                                        height="200px",
                                    ),
                                ),
                                spacing="2",
                            ),
                            padding="4",
                            border_radius="lg",
                            background=rx.color("gray", 1),
                            border="1px solid",
                            border_color=rx.color("gray", 6),
                            box_shadow="sm",
                        ),
                        # CDD chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Cooling Degree Days",
                                    weight="bold",
                                    size="3",
                                    margin_bottom="2",
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
                                        rx.text("📊 No data", color="gray", size="2"),
                                        height="200px",
                                    ),
                                ),
                                spacing="2",
                            ),
                            padding="4",
                            border_radius="lg",
                            background=rx.color("gray", 1),
                            border="1px solid",
                            border_color=rx.color("gray", 6),
                            box_shadow="sm",
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
                                    margin_bottom="2",
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
                                        rx.text("📊 No data", color="gray", size="2"),
                                        height="200px",
                                    ),
                                ),
                                spacing="2",
                            ),
                            padding="4",
                            border_radius="lg",
                            background=rx.color("gray", 1),
                            border="1px solid",
                            border_color=rx.color("gray", 6),
                            box_shadow="sm",
                        ),
                        # Heatwave Flag chart
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "Heatwave Events", weight="bold", size="3", margin_bottom="2"
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
                                        rx.text("📊 No data", color="gray", size="2"),
                                        height="200px",
                                    ),
                                ),
                                spacing="2",
                            ),
                            padding="4",
                            border_radius="lg",
                            background=rx.color("gray", 1),
                            border="1px solid",
                            border_color=rx.color("gray", 6),
                            box_shadow="sm",
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
            rx.divider(margin_top="8"),
            rx.center(
                rx.text(
                    "RAYDEN RULES™ | Climate Risk Intelligence Platform | © 2025",
                    size="1",
                    color="gray",
                ),
            ),
            spacing="4",
            padding="8",
            max_width="1400px",
            margin="0 auto",
        ),
        width="100%",
        background=rx.color("gray", 1),
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
                        size="8",
                        background_image="linear-gradient(90deg, #F59E0B 0%, #EF4444 100%)",
                        background_clip="text",
                    ),
                    rx.text(
                        "Configure threshold-based notifications for climate risk factors",
                        size="3",
                        color="gray",
                    ),
                    spacing="2",
                ),
                padding="6",
                border_radius="lg",
                background=rx.color("gray", 2),
                margin_bottom="4",
            ),
            # Alert statistics
            rx.heading("Alert Statistics", size="6", margin_bottom="3"),
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
            # Alert trend chart
            rx.heading("Alert Frequency Trend", size="6", margin_bottom="3"),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Alert triggers over the past 30 days",
                        size="2",
                        color="gray",
                        margin_bottom="3",
                    ),
                    rx.recharts.bar_chart(
                        rx.recharts.bar(
                            data_key="count",
                            fill="#EF4444",
                        ),
                        rx.recharts.x_axis(data_key="date"),
                        rx.recharts.y_axis(),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
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
                        height=250,
                    ),
                    spacing="2",
                ),
                padding="6",
                border_radius="lg",
                background=rx.color("gray", 1),
                border="1px solid",
                border_color=rx.color("gray", 6),
                box_shadow="md",
                margin_bottom="6",
            ),
            # Existing alerts
            rx.heading("Configured Alerts", size="6", margin_top="6", margin_bottom="3"),
            rx.box(
                rx.foreach(
                    State.alerts,
                    lambda alert: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(alert["name"], weight="bold", size="3"),
                                rx.text(f"Region: {alert['region_id']}", size="2", color="gray"),
                                rx.text(f"Rule: {alert['rule']}", size="2"),
                                rx.text(
                                    f"Channel: {alert['channel']} → {alert['recipients']}",
                                    size="2",
                                    color="gray",
                                ),
                                spacing="1",
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
                        border_radius="lg",
                        border="1px solid",
                        border_color=rx.color("gray", 6),
                        background=rx.color("gray", 1),
                        box_shadow="sm",
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
            rx.heading("Create New Risk Alert", size="6", margin_top="6", margin_bottom="3"),
            rx.box(
                rx.vstack(
                    rx.text("Alert Name", weight="bold", size="3"),
                    rx.input(
                        placeholder="Enter alert name",
                        value=State.alert_name,
                        on_change=State.set_alert_name,
                        size="3",
                    ),
                    rx.text("Select Metric", weight="bold", margin_top="3", size="3"),
                    rx.select(
                        ["lst_mean_c", "heatwave_flag", "uhi_index", "anomaly_zscore", "cdd"],
                        value=State.alert_metric,
                        on_change=State.set_alert_metric,
                        size="3",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("Condition", weight="bold", size="3"),
                            rx.select(
                                [">=", ">", "=", "<", "<="],
                                value=State.alert_condition,
                                on_change=State.set_alert_condition,
                                size="2",
                            ),
                            align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Threshold", weight="bold", size="3"),
                            rx.input(
                                type="number",
                                value=State.alert_threshold,
                                on_change=State.set_alert_threshold,
                                size="2",
                            ),
                            align_items="start",
                        ),
                        rx.vstack(
                            rx.text("Duration (days)", weight="bold", size="3"),
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
                        margin_top="3",
                    ),
                    rx.text("Risk Level", weight="bold", margin_top="3", size="3"),
                    rx.select(
                        ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        value=State.alert_severity,
                        on_change=State.set_alert_severity,
                        size="3",
                    ),
                    rx.text("Notification Channel", weight="bold", margin_top="3", size="3"),
                    rx.select(
                        ["EMAIL", "SLACK", "WEBHOOK"],
                        value=State.alert_channel,
                        on_change=State.set_alert_channel,
                        size="3",
                    ),
                    rx.text("Recipients", weight="bold", margin_top="3", size="3"),
                    rx.input(
                        placeholder="Enter recipients",
                        value=State.alert_recipients,
                        on_change=State.set_alert_recipients,
                        size="3",
                    ),
                    rx.button(
                        "Create Alert",
                        on_click=State.create_alert,
                        margin_top="4",
                        size="3",
                        color_scheme="blue",
                    ),
                    spacing="2",
                ),
                padding="6",
                border_radius="lg",
                border="1px solid",
                border_color=rx.color("gray", 6),
                background=rx.color("gray", 1),
                box_shadow="md",
            ),
            spacing="4",
            padding="8",
            max_width="1200px",
            margin="0 auto",
        ),
        width="100%",
        background=rx.color("gray", 1),
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
                        size="8",
                        background_image="linear-gradient(90deg, #10B981 0%, #3B82F6 100%)",
                        background_clip="text",
                    ),
                    rx.text(
                        "Upload and manage custom geographic regions for climate risk analysis",
                        size="3",
                        color="gray",
                    ),
                    spacing="2",
                ),
                padding="6",
                border_radius="lg",
                background=rx.color("gray", 2),
                margin_bottom="4",
            ),
            # Region statistics
            rx.heading("Region Statistics", size="6", margin_bottom="3"),
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
            # Region distribution chart
            rx.heading("Region Distribution", size="6", margin_bottom="3"),
            rx.grid(
                # Pie chart for region types
                rx.box(
                    rx.vstack(
                        rx.text("Region Types", weight="bold", size="3", margin_bottom="2"),
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
                            height=250,
                        ),
                        spacing="2",
                    ),
                    padding="6",
                    border_radius="lg",
                    background=rx.color("gray", 1),
                    border="1px solid",
                    border_color=rx.color("gray", 6),
                    box_shadow="md",
                ),
                # Bar chart for region usage
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Data Queries by Region", weight="bold", size="3", margin_bottom="2"
                        ),
                        rx.recharts.bar_chart(
                            rx.recharts.bar(
                                data_key="queries",
                                fill="#10B981",
                            ),
                            rx.recharts.x_axis(data_key="name"),
                            rx.recharts.y_axis(),
                            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                            rx.recharts.tooltip(),
                            data=[
                                {"name": "NYC", "queries": 245},
                                {"name": "LAX", "queries": 189},
                                {"name": "CHI", "queries": 156},
                                {"name": "MIA", "queries": 134},
                            ],
                            width="100%",
                            height=250,
                        ),
                        spacing="2",
                    ),
                    padding="6",
                    border_radius="lg",
                    background=rx.color("gray", 1),
                    border="1px solid",
                    border_color=rx.color("gray", 6),
                    box_shadow="md",
                ),
                columns="2",
                spacing="4",
                width="100%",
                margin_bottom="6",
            ),
            # Built-in regions
            rx.heading("Built-in Regions", size="6", margin_top="6", margin_bottom="3"),
            rx.box(
                rx.foreach(
                    State.regions,
                    lambda region: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(region["name"], weight="bold", size="3"),
                                rx.text(f"ID: {region['id']}", size="2", color="gray"),
                                rx.text(f"BBox: {region['bbox']}", size="2", color="gray"),
                                spacing="1",
                                align_items="start",
                            ),
                            rx.badge("Built-in", color_scheme="green", size="2"),
                            justify="between",
                            width="100%",
                        ),
                        padding="5",
                        border_radius="lg",
                        border="1px solid",
                        border_color=rx.color("gray", 6),
                        background=rx.color("gray", 1),
                        box_shadow="sm",
                        margin_bottom="3",
                        _hover={
                            "box_shadow": "md",
                            "border_color": rx.color("green", 7),
                            "transform": "translateX(4px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                ),
            ),
            # Custom regions
            rx.heading("Custom Regions", size="6", margin_top="6", margin_bottom="3"),
            rx.box(
                rx.foreach(
                    State.custom_regions,
                    lambda region: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(region["name"], weight="bold", size="3"),
                                rx.text(f"ID: {region['id']}", size="2", color="gray"),
                                rx.text(f"Created: {region['created']}", size="2", color="gray"),
                                spacing="1",
                                align_items="start",
                            ),
                            rx.badge("Custom", color_scheme="purple", size="2"),
                            justify="between",
                            width="100%",
                        ),
                        padding="5",
                        border_radius="lg",
                        border="1px solid",
                        border_color=rx.color("gray", 6),
                        background=rx.color("gray", 1),
                        box_shadow="sm",
                        margin_bottom="3",
                        _hover={
                            "box_shadow": "md",
                            "border_color": rx.color("purple", 7),
                            "transform": "translateX(4px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                ),
            ),
            # Upload new region
            rx.heading("Upload New Region", size="6", margin_top="6", margin_bottom="3"),
            rx.box(
                rx.vstack(
                    rx.text("Region Name", weight="bold", size="3"),
                    rx.input(
                        placeholder="Enter region name",
                        value=State.new_region_name,
                        on_change=State.set_new_region_name,
                        size="3",
                    ),
                    rx.text("Upload GeoJSON", weight="bold", margin_top="3", size="3"),
                    rx.upload(
                        rx.button("Choose File", size="2"),
                        accept={".geojson": []},
                    ),
                    rx.button(
                        "Upload and Save Region",
                        on_click=State.upload_region,
                        margin_top="4",
                        size="3",
                        color_scheme="green",
                    ),
                    spacing="2",
                ),
                padding="6",
                border_radius="lg",
                border="1px solid",
                border_color=rx.color("gray", 6),
                background=rx.color("gray", 1),
                box_shadow="md",
            ),
            spacing="4",
            padding="8",
            max_width="1200px",
            margin="0 auto",
        ),
        width="100%",
        background=rx.color("gray", 1),
    )


def navbar() -> rx.Component:
    """Navigation bar with enhanced styling."""
    return rx.box(
        rx.hstack(
            rx.heading(
                "RAYDEN RULES",
                size="7",
                background_image="linear-gradient(90deg, #4F46E5 0%, #06B6D4 100%)",
                background_clip="text",
            ),
            rx.spacer(),
            rx.hstack(
                rx.link(
                    rx.box(
                        rx.text("Dashboard", size="3", weight="medium"),
                        padding="2",
                        border_radius="md",
                        _hover={
                            "background": rx.color("blue", 3),
                            "transform": "translateY(-2px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                    href="/",
                ),
                rx.link(
                    rx.box(
                        rx.text("Alerts", size="3", weight="medium"),
                        padding="2",
                        border_radius="md",
                        _hover={
                            "background": rx.color("orange", 3),
                            "transform": "translateY(-2px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                    href="/alerts",
                ),
                rx.link(
                    rx.box(
                        rx.text("Regions", size="3", weight="medium"),
                        padding="2",
                        border_radius="md",
                        _hover={
                            "background": rx.color("green", 3),
                            "transform": "translateY(-2px)",
                            "transition": "all 0.2s ease-in-out",
                        },
                        transition="all 0.2s ease-in-out",
                    ),
                    href="/regions",
                ),
                spacing="4",
            ),
            justify="between",
            width="100%",
            align_items="center",
        ),
        padding="4",
        border_bottom="2px solid",
        border_color=rx.color("gray", 6),
        background=rx.color("gray", 1),
        box_shadow="sm",
        width="100%",
    )


app = rx.App()

# Add pages
app.add_page(
    lambda: rx.box(navbar(), index_page()),
    route="/",
    title="Rayden Rules - Dashboard",
    on_load=State.on_load,
)

app.add_page(
    lambda: rx.box(navbar(), alerts_page()),
    route="/alerts",
    title="Rayden Rules - Alerts",
)

app.add_page(
    lambda: rx.box(navbar(), regions_page()),
    route="/regions",
    title="Rayden Rules - Regions",
)
