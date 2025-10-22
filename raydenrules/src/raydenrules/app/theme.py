"""
Custom Bloomberg-like terminal theme for Rayden Rules application
"""

import streamlit as st

# Constants
HEADER_LEVEL_TWO = 2


def apply_terminal_theme():
    """
    Apply a Bloomberg-like terminal theme (black background with green text)
    to the Streamlit application - strict black and green only
    """
    # Custom CSS for the terminal look
    st.markdown(
        """
    <style>
        /* Main background and text */
        .stApp {
            background-color: #000000 !important;
            color: #00FF00 !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #00FF00 !important;
            font-family: 'Courier New', monospace !important;
        }

        /* Text elements */
        p, div, span, label, a, small {
            color: #00FF00 !important;
            font-family: 'Courier New', monospace !important;
        }

        /* Sidebar and all panels - background color only */
        .css-1d391kg, .css-1wrcr25, .css-ffhzg2, .css-1rs6os, .css-z5fcl4,
        .css-1dp5vir, .css-1k8d7ej, section[data-testid="stSidebar"],
        div[data-testid="stSidebarUserContent"], .css-18e3th9 {
            background-color: #000000 !important;
        }

        /* Reset specific sidebar buttons to avoid text */
        button[data-testid="collapsedControl"],
        section[data-testid="stSidebar"] button[kind="headerNoPadding"],
        button[aria-label="Collapse"],
        button[aria-label="Expand"] {
            background-color: transparent !important;
            border: none !important;
            color: transparent !important;
        }

        /* Target only the SVG icons in the sidebar and nothing else */
        button[data-testid="collapsedControl"] svg,
        section[data-testid="stSidebar"] button svg {
            color: #00FF00 !important;
            fill: #00FF00 !important;
            stroke: #00FF00 !important;
        }

        /* Hide any text in the sidebar collapse buttons */
        button[data-testid="collapsedControl"] span,
        section[data-testid="stSidebar"] button[kind="headerNoPadding"] span {
            display: none !important;
        }

        /* All inputs and widgets */
        .stTextInput > div, .stNumberInput > div, .stDateInput > div,
        .stTimeInput > div, .stSelectbox > div, .stMultiSelect > div,
        .stSlider > div, div[data-baseweb="base-input"],
        div[data-baseweb="select"], div[data-baseweb="input"],
        .stDateInput > div[data-baseweb="input"], .stTimeInput > div[data-baseweb="input"],
        .stSelectbox > div[data-baseweb="select"] {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border-color: #00FF00 !important;
        }

        /* Input text */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input,
        div[data-baseweb="input"] input {
            color: #00FF00 !important;
            background-color: #000000 !important;
            border-color: #00FF00 !important;
        }

        /* Fix for dropdown menus - completely separate from other elements */
        div[role="listbox"],
        div[data-baseweb="popover"],
        div[role="menu"],
        div[data-baseweb="menu"],
        div[data-baseweb="select-dropdown"],
        div[role="dialog"] {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border: 1px solid #00FF00 !important;
            position: absolute !important; /* Force absolute positioning */
            z-index: 9999999 !important; /* Extremely high z-index */
        }

        /* Reset position for stExpander elements */
        .stExpander {
            position: static !important;
        }

        /* Fix for expander headers to prevent overlap */
        details summary, .streamlit-expanderHeader {
            z-index: auto !important;
            position: relative !important;
        }

        /* RAW DATA TERMINAL - special handling */
        details[open] {
            position: static !important;
            display: block !important;
        }

        /* Push form elements below headers */
        form {
            position: relative !important;
            z-index: 1 !important;
        }

        /* Menu items */
        div[role="menuitem"], li[role="option"] {
            background-color: #000000 !important;
            color: #00FF00 !important;
        }

        div[role="menuitem"]:hover, li[role="option"]:hover {
            background-color: #003300 !important;
        }

        /* Selected options */
        div[aria-selected="true"] {
            background-color: #003300 !important;
            color: #00FF00 !important;
        }

        /* Button styles - strict green on black */
        .stButton>button, div[role="button"] {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border: 1px solid #00FF00 !important;
        }

        .stButton>button:hover, div[role="button"]:hover {
            background-color: #003300 !important;
            color: #00FF00 !important;
        }

        /* Download button */
        .stDownloadButton>button {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border: 1px solid #00FF00 !important;
        }

        .stDownloadButton>button:hover {
            background-color: #003300 !important;
            color: #00FF00 !important;
        }

        /* Metric cards */
        .stMetric {
            background-color: #0a0a0a !important;
            padding: 10px !important;
            border: 1px solid #00FF00 !important;
            border-radius: 5px !important;
        }

        .stMetric label, .stMetric div {
            color: #00FF00 !important;  /* All text in metrics is green */
        }

        /* DataFrame styling */
        .stDataFrame {
            background-color: #000000 !important;
            color: #00FF00 !important;
        }

        .stDataFrame th, .stDataFrame td {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border: 1px solid #003300 !important;
        }

        /* DataFrame pagination controls */
        .stDataFrame [data-testid="StyledFullScreenButton"],
        .stDataFrame button, .stDataFrame span {
            background-color: #000000 !important;
            color: #00FF00 !important;
        }

        /* Remove all chart styling to let them render with default colors */
        /* This section intentionally left blank to allow charts to render normally */

        /* Expanders - fix z-index to prevent dropdown overlap */
        .streamlit-expanderHeader, details {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border: 1px solid #00FF00 !important;
            position: relative;
            z-index: 1;
        }

        /* Ensure expander content is below the header */
        details[open] > div {
            position: relative;
            z-index: 0;
        }

        /* Radio buttons */
        .stRadio > div {
            background-color: #000000 !important;
            border-radius: 5px !important;
            padding: 10px !important;
            border: 1px solid #00FF00 !important;
        }

        .stRadio label {
            color: #00FF00 !important;
        }

        /* Checkbox */
        .stCheckbox > div {
            background-color: #000000 !important;
        }

        .stCheckbox label {
            color: #00FF00 !important;
        }

        /* Multiselect labels and tokens */
        .stMultiSelect span[data-baseweb="tag"] {
            background-color: #003300 !important;
            color: #00FF00 !important;
        }

        /* Info, warning and error boxes */
        .stAlert, [data-baseweb="notification"], .element-container div[class*="stAlert"] {
            background-color: #000000 !important;
            color: #00FF00 !important;
            border: 1px solid #00FF00 !important;
        }

        /* Progress bar */
        .stProgress > div {
            background-color: #003300 !important;
        }

        .stProgress > div > div {
            background-color: #00FF00 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #000000 !important;
        }

        .stTabs [data-baseweb="tab"] {
            color: #00FF00 !important;
            background-color: #000000 !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: #003300 !important;
            border-bottom: 2px solid #00FF00 !important;
        }

        /* Custom header styling with terminal-like prefix */
        h1::before {
            content: "> ";
            color: #00FF00;
        }

        h2::before {
            content: ">> ";
            color: #00FF00;
        }

        /* Special styling for KPI cards */
        .kpi-card {
            background-color: #0a0a0a;
            border: 1px solid #00FF00;
            border-radius: 5px;
            padding: 10px;
            margin: 5px;
        }

        /* Force all text to be green except in charts */
        body :not([data-testid="stChart"] *):not(.element-container svg *) {
            color: #00FF00 !important;
        }

        /* Override any white backgrounds anywhere */
        [style*="background-color: white"], [style*="background-color: #fff"], [style*="background-color: #ffffff"],
        [style*="background: white"], [style*="background: #fff"], [style*="background: #ffffff"] {
            background-color: #000000 !important;
        }

        /* Override any white text anywhere */
        [style*="color: white"], [style*="color: #fff"], [style*="color: #ffffff"] {
            color: #00FF00 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def format_metric_card(title, value, subtitle=None):
    """Create a custom styled metric card with terminal-like appearance"""
    html = f"""
    <div class="kpi-card">
        <small style="color: #7FFFD4; font-family: 'Courier New', monospace;">{title}</small>
        <h3 style="margin:0; color: #00FF00; font-family: 'Courier New', monospace;">{value}</h3>
    """

    if subtitle:
        html += f"<small style=\"color: #7FFFD4; font-family: 'Courier New', monospace;\">{subtitle}</small>"

    html += "</div>"

    return html


def terminal_header(text, level=1):
    """Creates a terminal-style header with blinking cursor effect"""
    cursor = '<span class="blinking-cursor">▋</span>'

    if level == 1:
        prefix = ">"
    elif level == HEADER_LEVEL_TWO:
        prefix = ">>"
    else:
        prefix = ">>>"

    return f"""
    <div style="font-family: 'Courier New', monospace; margin-bottom: 10px;">
        <span style="color: #7FFFD4;">{prefix}</span>
        <span style="color: #00FF00; font-weight: bold;"> {text}</span>
        {cursor}
    </div>
    """
