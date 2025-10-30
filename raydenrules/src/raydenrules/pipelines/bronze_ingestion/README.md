# Bronze Ingestion Pipeline

## Overview

The Bronze Ingestion Pipeline transforms raw CMR (Common Metadata Repository) API discovery results into structured bronze-layer tables stored as Parquet files. This pipeline implements the **bronze layer** of a medallion architecture (bronze → silver → gold).

## Purpose

The bronze layer serves as the **raw data landing zone** with the following characteristics:
- Preserves data as-is from the source (CMR API)
- Minimal transformation (only structural changes)
- Serves as the single source of truth
- Enables data lineage tracking
- Supports reprocessing and backfilling

## Pipeline Nodes

### 1. `prepare_bronze_granules`
**Input:** CMR discovery results (JSON)
**Output:** Partitioned DataFrames by region

Converts raw CMR granule metadata into structured DataFrames with the following fields:
- `region_id`: Region identifier
- `granule_id`: Unique granule ID from CMR
- `title`: Granule title
- `time_start`, `time_end`: Temporal coverage
- `date`: Extracted date for easy filtering
- `product`: Product name (e.g., MOD11A1)
- `bbox_*`: Bounding box coordinates
- `cloud_cover`: Cloud coverage percentage
- `links`: Download/access links
- `ingestion_timestamp`: When data was ingested

### 2. `consolidate_bronze_granules`
**Input:** Partitioned bronze granules
**Output:** Single consolidated DataFrame

Combines all regional granule data into one unified bronze table for easier querying.

### 3. `create_bronze_manifest`
**Input:** Partitioned bronze granules
**Output:** Manifest DataFrame

Creates a manifest tracking:
- Record counts per region
- Date ranges covered
- Data quality indicators (e.g., mean cloud cover)
- Ingestion timestamps

### 4. `prepare_bronze_metadata`
**Input:** CMR discovery results + regions list
**Output:** Metadata DataFrame

Captures metadata about the ingestion process:
- Region information
- Discovery status
- Date ranges requested
- Error messages (if any)

## Data Storage

### Local Storage (Default)
Bronze data is stored as Parquet files in `data/01_raw/bronze/`:

```
data/01_raw/bronze/
├── granules/                    # Partitioned by region
│   ├── NYC001.parquet
│   ├── LAX001.parquet
│   ├── CHI001.parquet
│   └── MIA001.parquet
├── granules_consolidated.parquet
├── manifest.parquet
└── metadata.parquet
# Use environment variable
export AWS_PROFILE=your-profile
  # Optional: specify region

# Or specify in catalog
kedro run --pipeline=discovery_to_bronze --env=s3
```

## Usage

  # Optional: specify region
```bash
kedro run --pipeline=discovery_to_bronze
```

### Run Only Bronze Ingestion
```bash
# Assumes CMR discovery has already run
kedro run --pipeline=bronze_ingestion
```

### Run with Specific Date Range
Modify `conf/base/parameters.yml`:
```yaml
discovery:
  get_most_recent: false
  date_range:
    start: "2025-01-01"
    end: "2025-03-31"
```

## Parquet Benefits

Using Parquet format for bronze storage provides:
1. **Columnar storage** - Efficient compression and query performance
2. **Schema evolution** - Can add columns without reprocessing
3. **Compression** - Smaller file sizes (using Snappy)
4. **Type preservation** - Maintains data types
5. **Partitioning** - Fast filtering by region
6. **Cloud compatibility** - Works seamlessly with S3

## Data Layer Architecture

**Bronze (Intermediate) vs. Silver (Primary/Feature) vs. Gold (Reporting)**

| Layer | Kedro Folder | Purpose | Transformation Level |
|-------|--------------|---------|---------------------|
| Bronze | `02_intermediate/` | Structured CMR data | Minimal (parse API) |
| Silver | `03_primary/` & `04_feature/` | Calculated metrics | Enriched (LST, CDD, HDD) |
| Gold | `08_reporting/` | Aggregated KPIs | Business logic |

**Bronze Layer vs. JSON Discovery:**

| Aspect | JSON Discovery | Bronze Parquet |
|--------|---------------|----------------|
| Purpose | API response storage | Structured data lake |
| Format | JSON | Parquet |
| Layer | `01_raw/` | `02_intermediate/` |
| Structure | Nested objects | Flat tabular |
| Queryability | Limited | Efficient with SQL |
| Size | Larger | Compressed (smaller) |
| Schema | Flexible | Defined schema |
| Use case | Raw dumps | Analytics/Processing |

## Manifest Usage

The manifest provides a quick overview of ingested data:

# Load manifest (latest version)
manifest = pd.read_parquet('data/02_intermediate/manifest.parquet')

# Load manifest
manifest = pd.read_parquet('data/01_raw/bronze/manifest.parquet')

# Check data coverage
print(manifest[['region_id', 'date_min', 'date_max', 'record_count']])

# Identify data quality issues
print(manifest[manifest['cloud_cover_mean'] > 50])
```

## Next Steps: Silver Layer

The bronze layer feeds into a **silver layer** (to be implemented) that will:
1. Download actual raster data using the granule links
2. Extract LST values
3. Calculate derived metrics (CDD, HDD, UHI, anomalies)
4. Match the structure expected by the API (as defined in `metrics_mock.json`)

## Monitoring and Quality

### Check Ingestion Status
```python
# Load metadata
metadata = pd.read_parquet('data/01_raw/bronze/metadata.parquet')

# Check for failures
failures = metadata[metadata['discovery_status'] != 'success']
print(failures[['region_id', 'error_message']])
metadata = pd.read_parquet('data/02_intermediate/metadata.parquet')

### Validate Data
```python
# Load consolidated bronze data
bronze = pd.read_parquet('data/01_raw/bronze/granules_consolidated.parquet')

# Check date coverage
print(bronze.groupby('region_id')['date'].agg(['min', 'max', 'count']))

bronze = pd.read_parquet('data/02_intermediate/granules_consolidated.parquet')
date_range = pd.date_range(bronze['date'].min(), bronze['date'].max())
missing = set(date_range) - set(bronze['date'])
print(f"Missing dates: {len(missing)}")
```

## Configuration

### Catalog Configuration (`conf/base/catalog.yml`)

Bronze datasets are configured with:
- **Type:** `pandas.ParquetDataset` or `PartitionedDataset`
- **Engine:** PyArrow
- **Compression:** Snappy
- **Versioning:** Enabled for tracking changes

### Parameters (`conf/base/parameters.yml`)

Bronze ingestion inherits parameters from discovery:
- `discovery.get_most_recent`: Use recent data (last 3 months)
- `discovery.date_range`: Specific date range when `get_most_recent=false`

## Troubleshooting

### Issue: "No module named 'pyarrow'"
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: S3 access denied
**Solution:** Check credentials and bucket permissions:
```bash
aws s3 ls s3://your-bucket-name/raydenrules/
```

### Issue: Empty bronze tables
**Solution:** Ensure discovery pipeline ran successfully:
```bash
kedro run --pipeline=data_discovery
# Check output in data/02_intermediate/cmr_discovery_results.json/
```

## Architecture Diagram

```
┌─────────────────────────┐
│  CMR API Discovery      │
│  (data_discovery)       │
└───────────┬─────────────┘
            │ JSON results
            ▼
┌─────────────────────────┐
│  Bronze Ingestion       │
│  (bronze_ingestion)     │
├─────────────────────────┤
│ • Parse granule data    │
│ • Add metadata          │
│ • Create manifest       │
┌─────────────────────────────┐
│  CMR API Discovery          │
│  (data_discovery)           │
│  Output: 01_raw/            │
└──────────┬──────────────────┘
           │ JSON results
           ▼
┌─────────────────────────────┐
│  Bronze Ingestion           │
│  (bronze_ingestion)         │
├─────────────────────────────┤
│ • Parse granule data        │
│ • Add metadata              │
│ • Create manifest           │
│ • Prepare for metrics       │
└──────────┬──────────────────┘
           │ Parquet files
           ▼
┌─────────────────────────────┐
│  Bronze = Intermediate      │
│  (02_intermediate/)         │
├─────────────────────────────┤
│ • granules (partitioned)    │
│ • granules_consolidated     │
│ • manifest                  │
│ • metadata                  │
│ • metrics_prep              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Silver = Primary/Feature   │
│  (03_primary/, 04_feature/) │
│  [Future Implementation]    │
├─────────────────────────────┤
│ • Calculate LST metrics     │
│ • CDD/HDD/UHI/Anomalies    │
│ • Match mock_data schema    │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Gold = Reporting           │
│  (08_reporting/)            │
│  [Future Implementation]    │
└─────────────────────────────┘
