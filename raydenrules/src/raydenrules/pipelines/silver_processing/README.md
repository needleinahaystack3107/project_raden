# Silver Processing Pipeline

## Overview

The Silver Processing Pipeline transforms bronze-layer granule metadata into actionable climate metrics by downloading and analyzing actual NASA raster data.

## What It Does

1. **Downloads Raster Data**: Fetches HDF files from NASA's LP DAAC (Land Processes Distributed Active Archive Center)
2. **Extracts LST Values**: Uses rasterio to read Land Surface Temperature from MODIS HDF files
3. **Calculates Metrics**:
   - `lst_mean_c`: Mean Land Surface Temperature in Celsius
   - `lst_min_c`, `lst_max_c`: Min/Max temperatures
   - `cdd`: Cooling Degree Days
   - `hdd`: Heating Degree Days
   - `uhi_index`: Urban Heat Island Index
   - `anomaly_zscore`: Temperature anomaly detection
   - `heatwave_flag`: Consecutive hot day detection
4. **Formats for API**: Structures data to match the target API schema
5. **Stores in Primary Layer**: Saves processed metrics ready for API consumption

## Pipeline Nodes

### 1. `process_region_granules`
- **Input**: Bronze granules with metadata and download URLs
- **Output**: Partitioned DataFrames with calculated metrics per region
- **Processing**: Downloads HDF, extracts LST, calculates metrics

### 2. `format_for_api`
- **Input**: Processed metrics DataFrames
- **Output**: JSON-formatted data matching API schema
- **Processing**: Transforms to match `metrics_mock.json` structure

## Configuration

### Parameters (`conf/base/parameters.yml`)

```yaml
silver:
  # Whether to actually download files (False for testing with mock data)
  enable_download: false

  # Directory to store downloaded HDF files
  download_dir: "data/01_raw/nasa_granules"

  # NASA Earthdata authentication token (optional, required for downloads)
  # Get token from: https://urs.earthdata.nasa.gov/
  nasa_auth_token: null

  # Processing options
  base_temperature: 18.0  # Base temp for degree days (Celsius)
  heatwave_threshold: 32.0  # Temperature threshold for heatwave detection
  heatwave_consecutive_days: 3  # Minimum consecutive days for heatwave
  rural_baseline_temp: 20.0  # Rural baseline for UHI calculation
```

## Dependencies

The pipeline requires additional packages for raster processing:

```bash
pip install rasterio gdal requests
```

## Usage

### Test Mode (Mock Data)
Run without downloading actual files to test the pipeline:

```bash
kedro run --pipeline=silver_processing
```

This uses synthetic LST values for testing.

### Production Mode (Real Downloads)

1. **Get NASA Earthdata Token**:
   - Register at https://urs.earthdata.nasa.gov/
   - Generate an access token
   - Add to `conf/local/credentials.yml`:

   ```yaml
   nasa:
     earthdata_token: "your-token-here"
   ```

2. **Update Parameters** in `conf/base/parameters.yml`:
   ```yaml
   silver:
     enable_download: true
     nasa_auth_token: ${nasa.earthdata_token}
   ```

3. **Run Pipeline**:
   ```bash
   kedro run --pipeline=silver_processing
   ```

### Run Full Pipeline (Discovery → Bronze → Silver)

```bash
kedro run
```

## Output Structure

### Silver Layer (`data/02_intermediate/silver_metrics`)
Partitioned parquet files per region with all calculated metrics:
```
data/02_intermediate/silver_metrics/
├── NYC001.parquet
├── LAX001.parquet
├── CHI001.parquet
└── MIA001.parquet
```

### Primary Layer (`data/03_primary/metrics_by_region`)
API-ready JSON files per region:
```
data/03_primary/metrics_by_region/
├── NYC001.json
├── LAX001.json
├── CHI001.json
└── MIA001.json
```

Each file contains:
```json
{
  "meta": {
    "region_id": "NYC001",
    "product": "MOD11A1",
    "bbox": [-74.2589, 40.4774, -73.7004, 40.9176],
    "date_range": {"start": "2025-08-01", "end": "2025-10-30"},
    "record_count": 50,
    "last_updated": "2025-10-30T20:00:00"
  },
  "metrics": [
    {
      "date": "2025-08-01",
      "lst_mean_c": 23.4,
      "cdd": 5.4,
      "hdd": 0.0,
      "heatwave_flag": 0,
      "uhi_index": 3.4,
      "anomaly_zscore": 0.5
    },
    ...
  ]
}
```

## Data Quality

- **Cloud Cover Filtering**: Metrics flagged for quality based on cloud cover < 50%
- **Valid Pixel Count**: Tracks number of valid pixels in LST extraction
- **Processing Status**: Each record marked as "processed" or "failed"
- **Missing Data Handling**: NULL values for failed downloads/extractions

## Scalability Considerations

### Current Implementation
- Sequential processing per granule
- Downloads to local disk
- Suitable for: 4 regions × 50 granules = 200 files

### Future Enhancements for Scale
1. **Parallel Processing**: Use Kedro's `ParallelRunner`
2. **S3 Storage**: Store HDF files in S3 instead of local disk
3. **Batch Processing**: Process granules in batches
4. **Caching**: Skip re-downloading existing files
5. **Distributed Computing**: Use Dask/Spark for large-scale processing

## Troubleshooting

### Download Failures
- Check NASA Earthdata credentials
- Verify network connectivity to `data.lpdaac.earthdatacloud.nasa.gov`
- Check download URL format in bronze granules

### Rasterio Errors
- Ensure GDAL is properly installed
- Check HDF file format compatibility
- Verify bounding box coordinates

### Memory Issues
- Process fewer regions at once
- Use chunked reading for large rasters
- Increase available memory

## Next Steps

After silver processing:
1. **API Integration**: Use primary layer data in FastAPI endpoints
2. **Visualization**: Create dashboards with processed metrics
3. **Analysis**: Run statistical analysis on time-series data
4. **Alerting**: Set up notifications for heatwave events
