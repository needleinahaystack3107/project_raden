"""
Silver Layer Processing Pipeline

This pipeline downloads actual raster data from NASA and processes it to calculate
LST metrics for each region.
"""

from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
