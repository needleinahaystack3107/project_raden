# Gold Feature Engineering Pipeline

This pipeline aggregates silver-layer metrics from all regions into an API-ready format stored in the feature layer (data/04_feature).

## Pipeline Flow

```
silver_metrics_partitioned → aggregate_region_metrics → add_region_metadata → gold_metrics_by_region
```

## Nodes

### 1. aggregate_region_metrics
- **Input**: silver_metrics_partitioned (Dict of DataFrames per region)
- **Output**: gold_metrics_aggregated (Dict of API-ready metrics)
- **Function**: Transforms silver metrics into JSON-compatible format with KPI summaries

### 2. add_region_metadata
- **Input**: gold_metrics_aggregated, regions_list
- **Output**: gold_metrics_by_region (Partitioned JSON files per region)
- **Function**: Enriches metrics with region metadata (name, bbox, center)

## Output Format

Each region's metrics are stored as:
```json
{
  "meta": {
    "region_id": "NYC001",
    "region_name": "New York City",
    "bbox": [...],
    "last_updated": "2025-10-30T..."
  },
  "metrics": [
    {
      "date": "2025-10-01",
      "lst_mean_c": 23.4,
      "cdd": 8.4,
      "hdd": 0.0,
      "heatwave_flag": 0,
      "uhi_index": 3.2,
      "anomaly_zscore": 1.2
    }
  ],
  "kpi_summary": {
    "ytd": {
      "avg_lst_c": 24.3,
      "heatwave_days": 4,
      "max_uhi_index": 4.7,
      "max_anomaly_zscore": 3.0
    },
    "today": {
      "lst_mean_c": 19.5,
      "cdd": 4.5,
      "hdd": 0.0,
      "anomaly_zscore": 0.0
    }
  }
}
```

## Run Pipeline

```bash
kedro run --pipeline=gold_feature_engineering
```
