# Rayden Rules

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-black)](https://github.com/astral-sh/ruff)

## Overview

Rayden Rules is an advanced climate analytics platform focused on urban heat patterns, heatwaves, and climate anomalies. Built with Kedro, FastAPI, and Reflex, it provides both API access and an interactive web dashboard for climate data visualization and risk monitoring.

## Architecture

```
raydenrules/
├── src/raydenrules/
│   ├── api/              # FastAPI REST endpoints
│   ├── app/              # Reflex web application
│   │   └── reflex_app/   # Main application module
│   └── pipelines/        # Kedro data pipelines
├── data/                 # Data storage (raw, processed)
├── conf/                 # Configuration files
└── tests/                # Test suite
```

## Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment activated

### Installation

```bash
pip install -r requirements.txt
```

## Running the Application

### 1. Start the Backend API

```bash
cd src/raydenrules/api
./start_api.sh
```

Access at: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

### 2. Start the Frontend

```bash
cd src/raydenrules/app
./start_app.sh
```

Access at: **http://localhost:3000**

## Features

### Dashboard
- **Region Selection**: Choose from built-in regions (NYC, LA, Chicago, Miami)
- **Date Range Picker**: Select custom time periods
- **KPI Cards**: Temperature, Heatwave Days, Energy Demand, Anomaly Index
- **Interactive Charts**: Line, Bar, and Area charts with multiple variables

### Alerts
- **View Alerts**: Monitor configured climate risk alerts
- **Create Alerts**: Set custom thresholds and notification rules
- **Severity Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Notification Channels**: Email, Slack, Webhook

### Regions
- **Built-in Regions**: Pre-configured major urban areas
- **Custom Regions**: Upload GeoJSON files for custom areas
- **Region Management**: View and manage geographic areas

## Data Pipeline


Run Kedro pipelines:
```bash
kedro run
```

Run specific pipelines:
```bash
kedro run --pipeline=data_processing
```

## API Endpoints

### Regions
- `GET /v1/regions` - List available regions
- `POST /v1/regions` - Upload custom region (GeoJSON)

### Metrics
- `GET /v1/metrics` - Get climate metrics
  - Parameters: `region_id`, `from_date`, `to_date`, `vars`

### Alerts
- `POST /v1/alerts` - Create alert rule

### Tiles
- `GET /v1/tiles/{layer}/{z}/{x}/{y}.png` - Map tiles

## Testing

Run all tests:
```bash
pytest
```

Run specific test suites:
```bash
pytest tests/api/
pytest tests/ui/
```

## Development

### Code Quality
```bash
ruff check .
black --check .
```

### Auto-format
```bash
ruff check --fix .
black .
```

## Configuration

Configuration files are in `conf/`:
- `base/` - Default configuration
- `local/` - Local overrides (git-ignored)

## Project Structure

- **data/** - Data layers (01_raw → 08_reporting)
- **conf/** - Configuration (YAML files)
- **src/raydenrules/** - Source code
- **tests/** - Test suite
- **notebooks/** - Jupyter notebooks

## Technology Stack

- **Backend**: FastAPI, Uvicorn
- **Frontend**: Reflex (React-based)
- **Data Pipeline**: Kedro, PySpark
- **Data Processing**: Pandas, NumPy
- **Code Quality**: Ruff, Black

## Latest Updates

**October 30, 2025**
- ✅ Migrated from Streamlit to Reflex
- ✅ Simplified project structure
- ✅ Fixed all Reflex compatibility issues
- ✅ Cleaned up documentation
- ✅ Removed test scripts and backup files

## Contributing

1. Follow code style guidelines (Ruff + Black)
2. Add tests for new features
3. Update documentation
4. Run tests before committing

## License

See LICENSE file for details.

```
pip install jupyter
```

After installing Jupyter, you can start a local notebook server:

```
kedro jupyter notebook
```

### JupyterLab
To use JupyterLab, you need to install it:

```
pip install jupyterlab
```

You can also start JupyterLab:

```
kedro jupyter lab
```

### IPython
And if you want to run an IPython session:

```
kedro ipython
```

### How to ignore notebook output cells in `git`
To automatically strip out all output cell contents before committing to `git`, you can use tools like [`nbstripout`](https://github.com/kynan/nbstripout). For example, you can add a hook in `.git/config` with `nbstripout --install`. This will run `nbstripout` before anything is committed to `git`.

> *Note:* Your output cells will be retained locally.

## Package your Kedro project

[Further information about building project documentation and packaging your project](https://docs.kedro.org/en/stable/tutorial/package_a_project.html)
