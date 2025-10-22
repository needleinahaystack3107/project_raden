"""
This module contains example tests for a Kedro project.
Tests should be placed in ``src/tests``, in modules that mirror your
project's structure, and in files named test_*.py.
"""

from pathlib import Path

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

# The tests below are here for the demonstration purpose
# and should be replaced with the ones testing the project
# functionality


class TestKedroRun:
    def test_kedro_run(self):
        # Skip if PySpark is not installed
        import importlib.util

        import pytest

        if importlib.util.find_spec("pyspark") is None:
            pytest.skip("PySpark not installed. Skipping Kedro pipeline test.")

        # Use the raydenrules subdirectory instead of cwd
        project_path = Path.cwd() / "raydenrules"

        # Skip this test if not in the correct directory context
        if not (project_path / "pyproject.toml").exists():
            pytest.skip("Not running from the correct project directory context")

        bootstrap_project(project_path)

        with KedroSession.create(project_path=project_path) as session:
            assert session.run() is not None
