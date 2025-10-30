"""
Bronze Ingestion Pipeline

This pipeline handles raw data ingestion from CMR API responses,
storing them as-is in the bronze layer (data/01_raw) with minimal transformation.
"""

from .pipeline import create_pipeline

__all__ = ["create_pipeline"]
