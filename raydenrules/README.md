# Rayden Rules

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-black)](https://github.com/astral-sh/ruff)

## Overview

Rayden Rules is an advanced climate analytics platform focused on providing actionable insights on urban heat patterns, heatwaves, and climate anomalies. Built on a robust data engineering foundation with Kedro and PySpark, it offers both API access to climate metrics and an intuitive web dashboard for data visualization.

## Long-Term Vision

Our long-term vision for Rayden Rules is to become the comprehensive platform for climate resilience planning, especially focusing on urban heat management and climate adaptation. We aim to:

1. **Expand geographic coverage** to include all major urban centers globally
2. **Increase temporal resolution** of climate data for more accurate predictions
3. **Develop advanced AI models** for predicting climate patterns and anomalies
4. **Create automated alerting systems** for early warning of extreme weather events
5. **Enable community collaboration** through shared insights and adaptation strategies
6. **Integrate with city planning tools** to help design climate-resilient urban spaces

## Project Components

Rayden Rules consists of several integrated components:

- **Data Pipeline**: Kedro-powered ETL processes that ingest, transform and prepare climate data
- **REST API**: FastAPI-based endpoints providing programmatic access to metrics and regions
- **Web Dashboard**: Streamlit application for interactive data visualization and alerting
- **Alert System**: Configurable rule-based system for climate event monitoring

## Latest Updates (October 21, 2025)

In our most recent release, we've made significant improvements to the codebase quality and features:

- **Code Quality Improvements**:
  - Fixed all linting issues identified by Ruff
  - Replaced magic numbers with meaningful constants
  - Added proper documentation and type annotations
  - Improved logging system replacing print statements

- **Feature Enhancements**:
  - Enhanced API reliability and error handling
  - Improved visualization components in the dashboard
  - Added new climate metrics (UHI index, anomaly z-scores)
  - Expanded test coverage for both API and UI components

## Architecture

The project follows a modular architecture with clear separation of concerns:

```
raydenrules/
├── api/         # FastAPI endpoints for data access
├── app/         # Streamlit dashboard application
│   ├── components/  # Reusable UI components
│   ├── pages/       # Dashboard pages (map, alerts, regions)
│   └── utils/       # Helper functions
└── pipelines/   # Kedro data processing pipelines
```

## Installation & Setup

### Prerequisites
- Python 3.10+
- PySpark 3.3+
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/raydenrules.git
   cd raydenrules
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up local configuration:
   ```
   cp conf/base/credentials.yml conf/local/credentials.yml
   # Edit conf/local/credentials.yml with your API keys and database credentials
   ```

## Running the Project

### Data Pipeline

Run the full data processing pipeline:
```
kedro run
```

Run specific pipeline nodes:
```
kedro run --pipeline=data_processing
kedro run --pipeline=feature_engineering
```

### API Server

Start the FastAPI server:
```
python -m src.raydenrules.api.api
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

### Web Dashboard

Launch the Streamlit dashboard:
```
streamlit run src/raydenrules/app/app.py
```

The dashboard will be accessible at `http://localhost:8501`.

## Testing

Run all tests:
```
pytest
```

Run specific test suites:
```
pytest tests/api/
pytest tests/ui/
```

### API Testing

For manual API testing, you can use the provided script:
```
python tests/api/manual_api_test.py
```

## Documentation

Generate project documentation:
```
kedro build-docs
```

View the documentation by opening `docs/build/html/index.html` in your browser.

## How to install dependencies

Declare any dependencies in `requirements.txt` for `pip` installation.

To install them, run:

```
pip install -r requirements.txt
```

## How to run your Kedro pipeline

You can run your Kedro project with:

```
kedro run
```

## How to test your Kedro project

Have a look at the files `tests/test_run.py` and `tests/pipelines/data_science/test_pipeline.py` for instructions on how to write your tests. Run the tests as follows:

```
pytest
```

You can configure the coverage threshold in your project's `pyproject.toml` file under the `[tool.coverage.report]` section.

## Project dependencies

To see and update the dependency requirements for your project use `requirements.txt`. Install the project requirements with `pip install -r requirements.txt`.

[Further information about project dependencies](https://docs.kedro.org/en/stable/kedro_project_setup/dependencies.html#project-specific-dependencies)

## How to work with Kedro and notebooks

> Note: Using `kedro jupyter` or `kedro ipython` to run your notebook provides these variables in scope: `catalog`, `context`, `pipelines` and `session`.
>
> Jupyter, JupyterLab, and IPython are already included in the project requirements by default, so once you have run `pip install -r requirements.txt` you will not need to take any extra steps before you use them.

### Jupyter
To use Jupyter notebooks in your Kedro project, you need to install Jupyter:

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
